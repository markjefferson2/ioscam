import Foundation

enum AVCCAnnexBError: Error, Equatable {
    case invalidNALLengthSize(Int)
    case truncatedLengthPrefix
    case truncatedNAL(expected: Int, available: Int)
}

enum AVCCAnnexBConverter {
    static let startCode: [UInt8] = [0, 0, 0, 1]

    static func convertSampleData(_ data: Data, nalLengthSize: Int) throws -> Data {
        guard (1...4).contains(nalLengthSize) else {
            throw AVCCAnnexBError.invalidNALLengthSize(nalLengthSize)
        }

        let bytes = [UInt8](data)
        var offset = 0
        var output = Data(capacity: data.count + 32)

        while offset < bytes.count {
            guard offset + nalLengthSize <= bytes.count else {
                throw AVCCAnnexBError.truncatedLengthPrefix
            }

            var nalLength = 0
            for index in 0..<nalLengthSize {
                nalLength = (nalLength << 8) | Int(bytes[offset + index])
            }
            offset += nalLengthSize

            let available = bytes.count - offset
            guard nalLength <= available else {
                throw AVCCAnnexBError.truncatedNAL(expected: nalLength, available: available)
            }

            output.append(contentsOf: startCode)
            if nalLength > 0 {
                output.append(contentsOf: bytes[offset..<(offset + nalLength)])
            }
            offset += nalLength
        }

        return output
    }

    static func prependParameterSets(_ parameterSets: [Data], to accessUnit: Data) -> Data {
        var output = Data()
        output.reserveCapacity(parameterSets.reduce(accessUnit.count) { $0 + $1.count + startCode.count })
        for parameterSet in parameterSets {
            output.append(contentsOf: startCode)
            output.append(parameterSet)
        }
        output.append(accessUnit)
        return output
    }
}
