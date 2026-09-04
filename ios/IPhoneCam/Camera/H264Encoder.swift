import AVFoundation
import CoreMedia
import Foundation
import VideoToolbox

final class H264FrameContext {
    let timestampNs: UInt64
    let sequence: UInt32

    init(timestampNs: UInt64, sequence: UInt32) {
        self.timestampNs = timestampNs
        self.sequence = sequence
    }
}

enum H264EncoderError: Error, LocalizedError {
    case sessionCreate(OSStatus)
    case property(String, OSStatus)
    case prepare(OSStatus)
    case missingImageBuffer
    case encode(OSStatus)
    case output(OSStatus)
    case missingBlockBuffer
    case blockBufferCopy(OSStatus)
    case missingFormatDescription
    case parameterSet(OSStatus)
    case annexB(Error)

    var errorDescription: String? {
        switch self {
        case .sessionCreate(let status): return "VTCompressionSessionCreate failed: \(status)"
        case .property(let key, let status): return "VideoToolbox property \(key) failed: \(status)"
        case .prepare(let status): return "VTCompressionSessionPrepareToEncodeFrames failed: \(status)"
        case .missingImageBuffer: return "Camera sample has no CVImageBuffer"
        case .encode(let status): return "VTCompressionSessionEncodeFrame failed: \(status)"
        case .output(let status): return "VideoToolbox output callback failed: \(status)"
        case .missingBlockBuffer: return "Encoded sample has no CMBlockBuffer"
        case .blockBufferCopy(let status): return "CMBlockBufferCopyDataBytes failed: \(status)"
        case .missingFormatDescription: return "Encoded sample has no H.264 format description"
        case .parameterSet(let status): return "Failed to read H.264 parameter sets: \(status)"
        case .annexB(let error): return "AVCC to Annex-B conversion failed: \(error)"
        }
    }
}

private let h264CompressionOutputCallback: VTCompressionOutputCallback = {
    outputCallbackRefCon,
    sourceFrameRefCon,
    status,
    _,
    sampleBuffer in

    guard let outputCallbackRefCon else { return }
    let encoder = Unmanaged<H264Encoder>.fromOpaque(outputCallbackRefCon).takeUnretainedValue()

    var frameContext: H264FrameContext?
    if let sourceFrameRefCon {
        frameContext = Unmanaged<H264FrameContext>.fromOpaque(sourceFrameRefCon).takeRetainedValue()
    }

    guard status == noErr else {
        encoder.report(error: H264EncoderError.output(status))
        return
    }
    guard let sampleBuffer, CMSampleBufferDataIsReady(sampleBuffer), let frameContext else {
        return
    }

    encoder.handleEncodedSample(sampleBuffer, context: frameContext)
}

final class H264Encoder {
    typealias AccessUnitHandler = (_ data: Data, _ timestampNs: UInt64, _ sequence: UInt32, _ isKeyframe: Bool) -> Void

    var onAccessUnit: AccessUnitHandler?
    var onError: ((Error) -> Void)?

    private let width: Int32
    private let height: Int32
    private let fps: Int32
    private let bitrate: Int
    private var compressionSession: VTCompressionSession?
    private var sequence: UInt32 = 0

    init(width: Int32 = 1920, height: Int32 = 1080, fps: Int32 = 60, bitrate: Int = 12_000_000) {
        self.width = width
        self.height = height
        self.fps = fps
        self.bitrate = bitrate
    }

    deinit {
        stop()
    }

    func start() throws {
        guard compressionSession == nil else { return }

        let encoderSpecification: CFDictionary = [
            kVTVideoEncoderSpecification_RequireHardwareAcceleratedVideoEncoder: kCFBooleanTrue as Any
        ] as CFDictionary

        var session: VTCompressionSession?
        let createStatus = VTCompressionSessionCreate(
            allocator: kCFAllocatorDefault,
            width: width,
            height: height,
            codecType: kCMVideoCodecType_H264,
            encoderSpecification: encoderSpecification,
            imageBufferAttributes: nil,
            compressedDataAllocator: nil,
            outputCallback: h264CompressionOutputCallback,
            refcon: Unmanaged.passUnretained(self).toOpaque(),
            compressionSessionOut: &session
        )
        guard createStatus == noErr, let session else {
            throw H264EncoderError.sessionCreate(createStatus)
        }

        do {
            try setProperty(session, key: kVTCompressionPropertyKey_RealTime, value: kCFBooleanTrue, name: "RealTime")
            try setProperty(session, key: kVTCompressionPropertyKey_AllowFrameReordering, value: kCFBooleanFalse, name: "AllowFrameReordering")
            try setProperty(session, key: kVTCompressionPropertyKey_AverageBitRate, value: NSNumber(value: bitrate), name: "AverageBitRate")
            try setProperty(session, key: kVTCompressionPropertyKey_ExpectedFrameRate, value: NSNumber(value: fps), name: "ExpectedFrameRate")
            try setProperty(session, key: kVTCompressionPropertyKey_MaxKeyFrameInterval, value: NSNumber(value: fps), name: "MaxKeyFrameInterval")
            try setProperty(session, key: kVTCompressionPropertyKey_ProfileLevel, value: kVTProfileLevel_H264_High_AutoLevel, name: "ProfileLevel")

            let prepareStatus = VTCompressionSessionPrepareToEncodeFrames(session)
            guard prepareStatus == noErr else {
                throw H264EncoderError.prepare(prepareStatus)
            }
            compressionSession = session
        } catch {
            VTCompressionSessionInvalidate(session)
            throw error
        }
    }

    func stop() {
        guard let session = compressionSession else { return }
        VTCompressionSessionCompleteFrames(session, untilPresentationTimeStamp: .invalid)
        VTCompressionSessionInvalidate(session)
        compressionSession = nil
    }

    func encode(sampleBuffer: CMSampleBuffer) {
        guard let session = compressionSession else { return }
        guard let imageBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else {
            report(error: H264EncoderError.missingImageBuffer)
            return
        }

        let presentationTime = CMSampleBufferGetPresentationTimeStamp(sampleBuffer)
        let timestampNs = Self.nanoseconds(from: presentationTime)
        let currentSequence = sequence
        sequence &+= 1

        let context = H264FrameContext(timestampNs: timestampNs, sequence: currentSequence)
        let contextPointer = Unmanaged.passRetained(context).toOpaque()
        var infoFlags = VTEncodeInfoFlags()
        let status = VTCompressionSessionEncodeFrame(
            session,
            imageBuffer: imageBuffer,
            presentationTimeStamp: presentationTime,
            duration: CMTime(value: 1, timescale: CMTimeScale(fps)),
            frameProperties: nil,
            sourceFrameRefcon: contextPointer,
            infoFlagsOut: &infoFlags
        )

        if status != noErr {
            Unmanaged<H264FrameContext>.fromOpaque(contextPointer).release()
            report(error: H264EncoderError.encode(status))
        }
    }

    fileprivate func handleEncodedSample(_ sampleBuffer: CMSampleBuffer, context: H264FrameContext) {
        do {
            let isKeyframe = Self.isKeyframe(sampleBuffer)
            guard let blockBuffer = CMSampleBufferGetDataBuffer(sampleBuffer) else {
                throw H264EncoderError.missingBlockBuffer
            }
            guard let formatDescription = CMSampleBufferGetFormatDescription(sampleBuffer) else {
                throw H264EncoderError.missingFormatDescription
            }

            var nalUnitHeaderLength: Int32 = 4
            let headerStatus = CMVideoFormatDescriptionGetH264ParameterSetAtIndex(
                formatDescription,
                parameterSetIndex: 0,
                parameterSetPointerOut: nil,
                parameterSetSizeOut: nil,
                parameterSetCountOut: nil,
                nalUnitHeaderLengthOut: &nalUnitHeaderLength
            )
            guard headerStatus == noErr else {
                throw H264EncoderError.parameterSet(headerStatus)
            }

            let dataLength = CMBlockBufferGetDataLength(blockBuffer)
            var avcc = Data(count: dataLength)
            let copyStatus: OSStatus = avcc.withUnsafeMutableBytes { buffer in
                guard let baseAddress = buffer.baseAddress else { return kCMBlockBufferBadCustomBlockSourceErr }
                return CMBlockBufferCopyDataBytes(
                    blockBuffer,
                    atOffset: 0,
                    dataLength: dataLength,
                    destination: baseAddress
                )
            }
            guard copyStatus == kCMBlockBufferNoErr else {
                throw H264EncoderError.blockBufferCopy(copyStatus)
            }

            let accessUnit: Data
            do {
                accessUnit = try AVCCAnnexBConverter.convertSampleData(avcc, nalLengthSize: Int(nalUnitHeaderLength))
            } catch {
                throw H264EncoderError.annexB(error)
            }

            let output: Data
            if isKeyframe {
                output = AVCCAnnexBConverter.prependParameterSets(
                    try Self.parameterSets(from: formatDescription),
                    to: accessUnit
                )
            } else {
                output = accessUnit
            }

            onAccessUnit?(output, context.timestampNs, context.sequence, isKeyframe)
        } catch {
            report(error: error)
        }
    }

    fileprivate func report(error: Error) {
        onError?(error)
    }

    private func setProperty(_ session: VTCompressionSession, key: CFString, value: CFTypeRef, name: String) throws {
        let status = VTSessionSetProperty(session, key: key, value: value)
        guard status == noErr else {
            throw H264EncoderError.property(name, status)
        }
    }

    private static func isKeyframe(_ sampleBuffer: CMSampleBuffer) -> Bool {
        guard
            let attachments = CMSampleBufferGetSampleAttachmentsArray(sampleBuffer, createIfNecessary: false) as? [[CFString: Any]],
            let first = attachments.first
        else {
            return true
        }
        return (first[kCMSampleAttachmentKey_NotSync] as? Bool) != true
    }

    private static func parameterSets(from formatDescription: CMFormatDescription) throws -> [Data] {
        var parameterSetCount = 0
        var nalUnitHeaderLength: Int32 = 0
        let countStatus = CMVideoFormatDescriptionGetH264ParameterSetAtIndex(
            formatDescription,
            parameterSetIndex: 0,
            parameterSetPointerOut: nil,
            parameterSetSizeOut: nil,
            parameterSetCountOut: &parameterSetCount,
            nalUnitHeaderLengthOut: &nalUnitHeaderLength
        )
        guard countStatus == noErr else {
            throw H264EncoderError.parameterSet(countStatus)
        }

        var result: [Data] = []
        result.reserveCapacity(parameterSetCount)
        for index in 0..<parameterSetCount {
            var pointer: UnsafePointer<UInt8>?
            var size = 0
            let status = CMVideoFormatDescriptionGetH264ParameterSetAtIndex(
                formatDescription,
                parameterSetIndex: index,
                parameterSetPointerOut: &pointer,
                parameterSetSizeOut: &size,
                parameterSetCountOut: nil,
                nalUnitHeaderLengthOut: nil
            )
            guard status == noErr, let pointer else {
                throw H264EncoderError.parameterSet(status)
            }
            result.append(Data(bytes: pointer, count: size))
        }
        return result
    }

    private static func nanoseconds(from time: CMTime) -> UInt64 {
        guard time.isNumeric else { return DispatchTime.now().uptimeNanoseconds }
        let scaled = CMTimeConvertScale(time, timescale: 1_000_000_000, method: .default)
        guard scaled.value >= 0 else { return 0 }
        return UInt64(scaled.value)
    }
}
