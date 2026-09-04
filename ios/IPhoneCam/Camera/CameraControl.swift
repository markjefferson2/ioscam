import Foundation

enum IosCamCameraKind: String, Codable, CaseIterable {
    case rearWide
    case rearUltraWide
    case rearTelephoto
    case front
}

struct CameraControlCommand: Codable, Equatable {
    let camera: IosCamCameraKind
    let zoom: Double
    let exposureBias: Double
    let autofocus: Bool
    let focusPosition: Double
}
