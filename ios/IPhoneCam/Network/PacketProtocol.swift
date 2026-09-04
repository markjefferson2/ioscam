import Foundation

enum ICAMPacketType: UInt8 {
    case hello = 0x01
    case video = 0x02
    case stats = 0x03
    case ping = 0x04
    case pong = 0x05
}

enum ICAMPacketError: Error {
    case payloadTooLarge(Int)
}

struct StreamHello: Codable, Equatable {
    let codec: String
    let width: Int
    let height: Int
    let fps: Int
    let bitrate: Int
}

enum ICAMPacket {
    static let magic = Data("ICAM".utf8)
    static let version: UInt8 = 1
    static let headerSize = 24
    static let videoFlagKeyframe: UInt16 = 0x0001

    static func hello(
        metadata: StreamHello,
        timestampNs: UInt64 = DispatchTime.now().uptimeNanoseconds,
        sequence: UInt32 = 0
    ) throws -> Data {
        let payload = try JSONEncoder().encode(metadata)
        return try make(
            type: .hello,
            flags: 0,
            payload: payload,
            timestampNs: timestampNs,
            sequence: sequence
        )
    }

    static func video(
        payload: Data,
        timestampNs: UInt64,
        sequence: UInt32,
        isKeyframe: Bool
    ) throws -> Data {
        try make(
            type: .video,
            flags: isKeyframe ? videoFlagKeyframe : 0,
            payload: payload,
            timestampNs: timestampNs,
            sequence: sequence
        )
    }

    static func make(
        type: ICAMPacketType,
        flags: UInt16,
        payload: Data,
        timestampNs: UInt64,
        sequence: UInt32
    ) throws -> Data {
        guard payload.count <= Int(UInt32.max) else {
            throw ICAMPacketError.payloadTooLarge(payload.count)
        }

        var packet = Data(capacity: headerSize + payload.count)
        packet.append(magic)
        packet.append(version)
        packet.append(type.rawValue)
        packet.appendBigEndian(flags)
        packet.appendBigEndian(UInt32(payload.count))
        packet.appendBigEndian(timestampNs)
        packet.appendBigEndian(sequence)
        packet.append(payload)
        return packet
    }
}

private extension Data {
    mutating func appendBigEndian<T: FixedWidthInteger>(_ value: T) {
        var bigEndian = value.bigEndian
        Swift.withUnsafeBytes(of: &bigEndian) { rawBuffer in
            append(contentsOf: rawBuffer)
        }
    }
}
