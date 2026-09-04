import AVFoundation
import CoreMedia
import CoreVideo
import Foundation

enum CameraCaptureError: Error, LocalizedError {
    case permissionDenied
    case cameraUnavailable
    case format1080p60Unavailable
    case cannotAddInput
    case cannotAddOutput
    case configuration(Error)

    var errorDescription: String? {
        switch self {
        case .permissionDenied: return "Camera permission was denied"
        case .cameraUnavailable: return "Rear wide camera is unavailable"
        case .format1080p60Unavailable: return "Rear wide camera has no 1920x1080 format supporting 60 fps"
        case .cannotAddInput: return "AVCaptureSession cannot add the rear camera input"
        case .cannotAddOutput: return "AVCaptureSession cannot add the video data output"
        case .configuration(let error): return "Camera configuration failed: \(error.localizedDescription)"
        }
    }
}

final class CameraCapture: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    var onSampleBuffer: ((CMSampleBuffer) -> Void)?

    private let session = AVCaptureSession()
    private let captureQueue = DispatchQueue(label: "dev.local.IPhoneCam.capture", qos: .userInteractive)
    private var configured = false

    func start() async throws {
        let authorized: Bool
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            authorized = true
        case .notDetermined:
            authorized = await AVCaptureDevice.requestAccess(for: .video)
        default:
            authorized = false
        }
        guard authorized else { throw CameraCaptureError.permissionDenied }

        try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
            captureQueue.async { [weak self] in
                guard let self else {
                    continuation.resume(returning: ())
                    return
                }
                do {
                    if !self.configured {
                        try self.configureSession()
                        self.configured = true
                    }
                    if !self.session.isRunning {
                        self.session.startRunning()
                    }
                    continuation.resume(returning: ())
                } catch {
                    continuation.resume(throwing: error)
                }
            }
        }
    }

    func stop() {
        captureQueue.async { [weak self] in
            guard let self, self.session.isRunning else { return }
            self.session.stopRunning()
        }
    }

    private func configureSession() throws {
        session.beginConfiguration()
        defer { session.commitConfiguration() }
        session.sessionPreset = .inputPriority

        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back) else {
            throw CameraCaptureError.cameraUnavailable
        }

        let format = camera.formats.first { candidate in
            let dimensions = CMVideoFormatDescriptionGetDimensions(candidate.formatDescription)
            guard dimensions.width == 1920, dimensions.height == 1080 else { return false }
            return candidate.videoSupportedFrameRateRanges.contains { range in
                range.minFrameRate <= 60.0 && range.maxFrameRate >= 60.0
            }
        }
        guard let format else { throw CameraCaptureError.format1080p60Unavailable }

        do {
            try camera.lockForConfiguration()
            camera.activeFormat = format
            let frameDuration = CMTime(value: 1, timescale: 60)
            camera.activeVideoMinFrameDuration = frameDuration
            camera.activeVideoMaxFrameDuration = frameDuration
            camera.unlockForConfiguration()
        } catch {
            throw CameraCaptureError.configuration(error)
        }

        let input: AVCaptureDeviceInput
        do {
            input = try AVCaptureDeviceInput(device: camera)
        } catch {
            throw CameraCaptureError.configuration(error)
        }
        guard session.canAddInput(input) else { throw CameraCaptureError.cannotAddInput }
        session.addInput(input)

        let output = AVCaptureVideoDataOutput()
        output.alwaysDiscardsLateVideoFrames = true
        output.videoSettings = [
            kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange
        ]
        output.setSampleBufferDelegate(self, queue: captureQueue)
        guard session.canAddOutput(output) else { throw CameraCaptureError.cannotAddOutput }
        session.addOutput(output)
    }

    func captureOutput(
        _ output: AVCaptureOutput,
        didOutput sampleBuffer: CMSampleBuffer,
        from connection: AVCaptureConnection
    ) {
        onSampleBuffer?(sampleBuffer)
    }
}
