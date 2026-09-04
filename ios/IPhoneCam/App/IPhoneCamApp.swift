import SwiftUI

@main
struct IPhoneCamApp: App {
    @StateObject private var model = CameraStreamerModel()

    var body: some Scene {
        WindowGroup {
            ContentView(model: model)
        }
    }
}
