import Foundation

@main
struct AnnexBConverterTests {
    static func main() throws {
        // AVCC: [len=3][NAL 65 01 02][len=2][NAL 41 03]
        let avcc = Data([0,0,0,3, 0x65,0x01,0x02, 0,0,0,2, 0x41,0x03])
        let annexB = try AVCCAnnexBConverter.convertSampleData(avcc, nalLengthSize: 4)
        precondition(Array(annexB) == [0,0,0,1,0x65,0x01,0x02, 0,0,0,1,0x41,0x03])

        let withSets = AVCCAnnexBConverter.prependParameterSets(
            [Data([0x67,0x64]), Data([0x68,0xEE])],
            to: Data([0,0,0,1,0x65])
        )
        precondition(Array(withSets) == [
            0,0,0,1,0x67,0x64,
            0,0,0,1,0x68,0xEE,
            0,0,0,1,0x65
        ])

        do {
            _ = try AVCCAnnexBConverter.convertSampleData(Data([0,0,0,5,1,2]), nalLengthSize: 4)
            preconditionFailure("truncated NAL must throw")
        } catch {
            // expected
        }
        print("AnnexBConverterTests: OK")
    }
}
