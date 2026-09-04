import Foundation

@main
struct PacketProtocolTests {
    static func main() throws {
        let payload = Data([0xAA, 0xBB, 0xCC])
        let packet = try ICAMPacket.video(
            payload: payload,
            timestampNs: 0x0102030405060708,
            sequence: 0x11223344,
            isKeyframe: true
        )

        precondition(packet.count == 27)
        precondition(Array(packet[0..<4]) == Array("ICAM".utf8))
        precondition(packet[4] == 1)
        precondition(packet[5] == 0x02)
        precondition(Array(packet[6..<8]) == [0x00, 0x01])
        precondition(Array(packet[8..<12]) == [0x00, 0x00, 0x00, 0x03])
        precondition(Array(packet[12..<20]) == [1,2,3,4,5,6,7,8])
        precondition(Array(packet[20..<24]) == [0x11,0x22,0x33,0x44])
        precondition(Array(packet[24..<27]) == [0xAA,0xBB,0xCC])

        let hello = StreamHello(codec: "h264", width: 1920, height: 1080, fps: 60, bitrate: 12_000_000)
        let helloPacket = try ICAMPacket.hello(metadata: hello, timestampNs: 9, sequence: 1)
        precondition(helloPacket[5] == 0x01)
        precondition(helloPacket.count > 24)
        print("PacketProtocolTests: OK")
    }
}
