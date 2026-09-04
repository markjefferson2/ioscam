import Foundation
import Network

enum StreamServerState: Equatable {
    case stopped
    case waiting
    case connected
    case error(String)
}

final class StreamServer {
    var onStateChange: ((StreamServerState) -> Void)?

    private let port: UInt16
    private let metadata: StreamHello
    private let queue = DispatchQueue(label: "dev.local.IPhoneCam.network", qos: .userInteractive)

    private var listener: NWListener?
    private var connection: NWConnection?
    private var connectionReady = false
    private var sendInFlight = false
    private var pendingVideoPacket: Data?

    init(port: UInt16 = 2345, metadata: StreamHello) {
        self.port = port
        self.metadata = metadata
    }

    func start() throws {
        guard listener == nil else { return }
        guard let nwPort = NWEndpoint.Port(rawValue: port) else {
            throw NSError(domain: "IPhoneCam.StreamServer", code: 1, userInfo: [NSLocalizedDescriptionKey: "Invalid TCP port \(port)"])
        }

        let parameters = NWParameters.tcp
        parameters.allowLocalEndpointReuse = true
        let listener = try NWListener(using: parameters, on: nwPort)
        self.listener = listener

        listener.stateUpdateHandler = { [weak self] state in
            guard let self else { return }
            self.queue.async {
                switch state {
                case .ready:
                    self.emit(.waiting)
                case .failed(let error):
                    self.emit(.error("TCP listener failed: \(error.localizedDescription)"))
                    self.stopLocked()
                case .cancelled:
                    self.emit(.stopped)
                default:
                    break
                }
            }
        }

        listener.newConnectionHandler = { [weak self] newConnection in
            self?.queue.async {
                self?.accept(newConnection)
            }
        }
        listener.start(queue: queue)
    }

    func stop() {
        queue.async { [weak self] in
            self?.stopLocked()
        }
    }

    func enqueueVideo(data: Data, timestampNs: UInt64, sequence: UInt32, isKeyframe: Bool) {
        let packet: Data
        do {
            packet = try ICAMPacket.video(
                payload: data,
                timestampNs: timestampNs,
                sequence: sequence,
                isKeyframe: isKeyframe
            )
        } catch {
            emit(.error("Packet serialization failed: \(error.localizedDescription)"))
            return
        }

        queue.async { [weak self] in
            self?.enqueueVideoPacketLocked(packet)
        }
    }

    private func accept(_ newConnection: NWConnection) {
        connection?.cancel()
        connection = newConnection
        connectionReady = false
        sendInFlight = false
        pendingVideoPacket = nil

        newConnection.stateUpdateHandler = { [weak self, weak newConnection] state in
            guard let self, let newConnection else { return }
            self.queue.async {
                guard self.connection === newConnection else { return }
                switch state {
                case .ready:
                    self.connectionReady = true
                    self.emit(.connected)
                    self.sendHelloLocked()
                case .failed(let error):
                    self.handleDisconnectLocked(message: "Client connection failed: \(error.localizedDescription)")
                case .cancelled:
                    self.handleDisconnectLocked(message: nil)
                default:
                    break
                }
            }
        }
        newConnection.start(queue: queue)
    }

    private func sendHelloLocked() {
        do {
            let hello = try ICAMPacket.hello(metadata: metadata)
            sendLocked(hello)
        } catch {
            emit(.error("HELLO serialization failed: \(error.localizedDescription)"))
        }
    }

    private func enqueueVideoPacketLocked(_ packet: Data) {
        guard connectionReady, connection != nil else { return }
        if sendInFlight {
            // Keep exactly one pending frame; replacing it prevents an unbounded app queue.
            pendingVideoPacket = packet
            return
        }
        sendLocked(packet)
    }

    private func sendLocked(_ packet: Data) {
        guard connectionReady, let connection else { return }
        sendInFlight = true
        connection.send(content: packet, completion: .contentProcessed { [weak self, weak connection] error in
            guard let self, let connection else { return }
            self.queue.async {
                guard self.connection === connection else { return }
                self.sendInFlight = false
                if let error {
                    self.handleDisconnectLocked(message: "TCP send failed: \(error.localizedDescription)")
                    return
                }
                if let next = self.pendingVideoPacket {
                    self.pendingVideoPacket = nil
                    self.sendLocked(next)
                }
            }
        })
    }

    private func handleDisconnectLocked(message: String?) {
        connection?.cancel()
        connection = nil
        connectionReady = false
        sendInFlight = false
        pendingVideoPacket = nil
        if let message {
            emit(.error(message))
        }
        if listener != nil {
            emit(.waiting)
        }
    }

    private func stopLocked() {
        connection?.cancel()
        listener?.cancel()
        connection = nil
        listener = nil
        connectionReady = false
        sendInFlight = false
        pendingVideoPacket = nil
        emit(.stopped)
    }

    private func emit(_ state: StreamServerState) {
        onStateChange?(state)
    }
}
