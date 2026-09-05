import Foundation

@MainActor
final class CameraStreamerModel: ObservableObject {
    enum Status: Equatable {
        case stopped
        case starting
        case waitingForPC
        case connected
        case error(String)

        var text: String {
            switch self {
            case .stopped: return "Stopped"
            case .starting: return "Starting camera…"
            case .waitingForPC: return "Waiting for PC over USB…"
            case .connected: return "PC connected"
            case .error(let message): return "Error: \(message)"
            }
        }
    }

    @Published private(set) var status: Status = .stopped
    @Published private(set) var isRunning = false

    private let camera = CameraCapture()
    private let encoder = H264Encoder(width: 1920, height: 1080, fps: 60, bitrate: 12_000_000)
    private let server = StreamServer(
        port: 2345,
        metadata: StreamHello(codec: "h264", width: 1920, height: 1080, fps: 60, bitrate: 12_000_000)
    )

    init() {
        camera.onError = { [weak self] error in
            Task { @MainActor in self?.status = .error(error.localizedDescription) }
        }
        camera.onSampleBuffer = { [weak self] sampleBuffer in
            self?.encoder.encode(sampleBuffer: sampleBuffer)
        }
        encoder.onAccessUnit = { [weak self] data, timestampNs, sequence, isKeyframe in
            self?.server.enqueueVideo(
                data: data,
                timestampNs: timestampNs,
                sequence: sequence,
                isKeyframe: isKeyframe
            )
        }
        encoder.onError = { [weak self] error in
            Task { @MainActor in
                self?.status = .error(error.localizedDescription)
            }
        }
        server.onControlCommand = { [weak self] command in
            self?.camera.apply(control: command)
        }
        server.onClientConnected = { [weak self] in
            self?.encoder.requestKeyframe()
        }
        server.onStateChange = { [weak self] serverState in
            Task { @MainActor in
                guard let self else { return }
                switch serverState {
                case .stopped:
                    if self.isRunning { self.status = .waitingForPC }
                case .waiting:
                    self.status = .waitingForPC
                case .connected:
                    self.status = .connected
                case .error(let message):
                    self.status = .error(message)
                }
            }
        }
    }

    func toggle() {
        if isRunning {
            stop()
        } else {
            Task { await start() }
        }
    }

    func start() async {
        guard !isRunning else { return }
        status = .starting
        do {
            try encoder.start()
            try server.start()
            try await camera.start()
            isRunning = true
            status = .waitingForPC
        } catch {
            camera.stop()
            encoder.stop()
            server.stop()
            isRunning = false
            status = .error(error.localizedDescription)
        }
    }

    func stop() {
        camera.stop()
        encoder.stop()
        server.stop()
        isRunning = false
        status = .stopped
    }
}
