import SwiftUI

struct ContentView: View {
    @ObservedObject var model: CameraStreamerModel

    var body: some View {
        NavigationStack {
            VStack(spacing: 22) {
                VStack(spacing: 8) {
                    Text("iPhone USB Cam")
                        .font(.largeTitle.bold())
                    Text("Native H.264 → USB/usbmux → Windows")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }

                VStack(alignment: .leading, spacing: 12) {
                    row("Camera", "Rear Wide 1×")
                    row("Mode", "1920×1080 @ 60 fps")
                    row("Codec", "H.264 / 12 Mbit/s")
                    row("TCP port", "2345")
                }
                .padding()
                .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 16))

                Text(model.status.text)
                    .font(.headline)
                    .multilineTextAlignment(.center)
                    .foregroundStyle(statusColor)

                Button(action: model.toggle) {
                    Text(model.isRunning ? "Stop Camera" : "Start Camera")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                }
                .buttonStyle(.borderedProminent)

                Text("Video is sent only when a PC connects to device port 2345 through the USB cable.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)

                Spacer()
            }
            .padding()
        }
    }

    private func row(_ title: String, _ value: String) -> some View {
        HStack {
            Text(title).foregroundStyle(.secondary)
            Spacer()
            Text(value).fontWeight(.medium)
        }
    }

    private var statusColor: Color {
        switch model.status {
        case .error: return .red
        case .connected: return .green
        default: return .primary
        }
    }
}
