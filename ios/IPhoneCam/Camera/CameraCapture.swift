import AVFoundation
import CoreMedia
import CoreVideo
import Foundation

enum CameraCaptureError: Error, LocalizedError {
    case permissionDenied
    case cameraUnavailable(IosCamCameraKind)
    case format1080p60Unavailable(IosCamCameraKind)
    case cannotAddInput
    case cannotAddOutput
    case configuration(Error)

    var errorDescription: String? {
        switch self {
        case .permissionDenied: return "Camera permission was denied"
        case .cameraUnavailable(let kind): return "Camera \(kind.rawValue) is unavailable"
        case .format1080p60Unavailable(let kind): return "Camera \(kind.rawValue) has no 1920x1080 format supporting 60 fps"
        case .cannotAddInput: return "AVCaptureSession cannot add the selected camera input"
        case .cannotAddOutput: return "AVCaptureSession cannot add the video data output"
        case .configuration(let error): return "Camera configuration failed: \(error.localizedDescription)"
        }
    }
}

final class CameraCapture: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    var onSampleBuffer: ((CMSampleBuffer) -> Void)?
    var onError: ((Error) -> Void)?

    private let session = AVCaptureSession()
    private let captureQueue = DispatchQueue(label: "dev.local.IPhoneCam.capture", qos: .userInteractive)
    private var configured = false
    private var activeInput: AVCaptureDeviceInput?
    private var activeDevice: AVCaptureDevice?
    private var activeKind: IosCamCameraKind = .rearWide
    private var currentControl = CameraControlCommand(
        camera: .rearWide,
        zoom: 1.0,
        exposureBias: 0.0,
        autofocus: true,
        focusPosition: 0.5
    )

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

    func apply(control: CameraControlCommand) {
        captureQueue.async { [weak self] in
            guard let self else { return }
            do {
                if control.camera != self.activeKind {
                    try self.switchCamera(to: control.camera)
                }
                self.currentControl = control
                try self.applyDeviceControls(control)
            } catch {
                self.onError?(error)
            }
        }
    }

    private func configureSession() throws {
        session.beginConfiguration()
        defer { session.commitConfiguration() }
        session.sessionPreset = .inputPriority

        let camera = try makeDevice(for: .rearWide)
        try configure1080p60(camera, kind: .rearWide)
        let input: AVCaptureDeviceInput
        do {
            input = try AVCaptureDeviceInput(device: camera)
        } catch {
            throw CameraCaptureError.configuration(error)
        }
        guard session.canAddInput(input) else { throw CameraCaptureError.cannotAddInput }
        session.addInput(input)
        activeInput = input
        activeDevice = camera
        activeKind = .rearWide

        let output = AVCaptureVideoDataOutput()
        output.alwaysDiscardsLateVideoFrames = true
        output.videoSettings = [
            kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange
        ]
        output.setSampleBufferDelegate(self, queue: captureQueue)
        guard session.canAddOutput(output) else { throw CameraCaptureError.cannotAddOutput }
        session.addOutput(output)

        try applyDeviceControls(currentControl)
    }

    private func makeDevice(for kind: IosCamCameraKind) throws -> AVCaptureDevice {
        let deviceType: AVCaptureDevice.DeviceType
        let position: AVCaptureDevice.Position
        switch kind {
        case .rearWide:
            deviceType = .builtInWideAngleCamera
            position = .back
        case .rearUltraWide:
            deviceType = .builtInUltraWideCamera
            position = .back
        case .rearTelephoto:
            deviceType = .builtInTelephotoCamera
            position = .back
        case .front:
            deviceType = .builtInWideAngleCamera
            position = .front
        }
        guard let device = AVCaptureDevice.default(deviceType, for: .video, position: position) else {
            throw CameraCaptureError.cameraUnavailable(kind)
        }
        return device
    }

    private func configure1080p60(_ camera: AVCaptureDevice, kind: IosCamCameraKind) throws {
        let format = camera.formats.first { candidate in
            let dimensions = CMVideoFormatDescriptionGetDimensions(candidate.formatDescription)
            guard dimensions.width == 1920, dimensions.height == 1080 else { return false }
            return candidate.videoSupportedFrameRateRanges.contains { range in
                range.minFrameRate <= 60.0 && range.maxFrameRate >= 60.0
            }
        }
        guard let format else { throw CameraCaptureError.format1080p60Unavailable(kind) }

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
    }

    private func switchCamera(to kind: IosCamCameraKind) throws {
        let newDevice = try makeDevice(for: kind)
        try configure1080p60(newDevice, kind: kind)
        let newInput: AVCaptureDeviceInput
        do {
            newInput = try AVCaptureDeviceInput(device: newDevice)
        } catch {
            throw CameraCaptureError.configuration(error)
        }

        session.beginConfiguration()
        let oldInput = activeInput
        if let oldInput {
            session.removeInput(oldInput)
        }
        guard session.canAddInput(newInput) else {
            if let oldInput, session.canAddInput(oldInput) { session.addInput(oldInput) }
            session.commitConfiguration()
            throw CameraCaptureError.cannotAddInput
        }
        session.addInput(newInput)
        session.commitConfiguration()

        activeInput = newInput
        activeDevice = newDevice
        activeKind = kind
    }

    private func applyDeviceControls(_ control: CameraControlCommand) throws {
        guard let device = activeDevice else { return }
        do {
            try device.lockForConfiguration()
            defer { device.unlockForConfiguration() }

            let zoom = max(device.minAvailableVideoZoomFactor, min(CGFloat(control.zoom), min(device.maxAvailableVideoZoomFactor, 5.0)))
            device.videoZoomFactor = zoom

            let bias = max(device.minExposureTargetBias, min(Float(control.exposureBias), device.maxExposureTargetBias))
            device.setExposureTargetBias(bias, completionHandler: nil)

            if control.autofocus {
                if device.isFocusModeSupported(.continuousAutoFocus) {
                    device.focusMode = .continuousAutoFocus
                }
            } else if device.isFocusModeSupported(.locked) {
                let position = max(0.0, min(Float(control.focusPosition), 1.0))
                device.setFocusModeLocked(lensPosition: position, completionHandler: nil)
            }
        } catch {
            throw CameraCaptureError.configuration(error)
        }
    }

    func captureOutput(
        _ output: AVCaptureOutput,
        didOutput sampleBuffer: CMSampleBuffer,
        from connection: AVCaptureConnection
    ) {
        onSampleBuffer?(sampleBuffer)
    }
}
