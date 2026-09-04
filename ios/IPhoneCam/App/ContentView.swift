import SwiftUI

struct ContentView: View {
    @ObservedObject var model: CameraStreamerModel

    private let brandLime = Color(red: 0.78, green: 1.0, blue: 0.18)
    private let panel = Color(red: 0.06, green: 0.075, blue: 0.055)
    private let muted = Color(red: 0.56, green: 0.60, blue: 0.53)

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            VStack(spacing: 22) {
                HStack(alignment: .firstTextBaseline, spacing: 10) {
                    Text("IosCam")
                        .font(.system(size: 42, weight: .black, design: .rounded))
                        .foregroundStyle(.white)
                    Text("/ STUDIO TOOL")
                        .font(.caption2.bold())
                        .foregroundStyle(muted)
                    Spacer()
                }

                HStack(spacing: 10) {
                    Circle()
                        .fill(statusColor)
                        .frame(width: 10, height: 10)
                        .shadow(color: statusColor.opacity(0.8), radius: 8)
                    Text(model.status.text.uppercased())
                        .font(.caption.bold())
                        .foregroundStyle(.white)
                    Spacer()
                }
                .padding(14)
                .background(panel, in: RoundedRectangle(cornerRadius: 16))
                .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color.white.opacity(0.08)))

                VStack(alignment: .leading, spacing: 14) {
                    row("STREAM", "1920×1080 @ 60")
                    row("CODEC", "H.264 / 12 Mbit/s")
                    row("USB TCP", "2345")
                    row("CONTROL", "Windows GUI")
                }
                .padding(18)
                .background(panel, in: RoundedRectangle(cornerRadius: 18))
                .overlay(RoundedRectangle(cornerRadius: 18).stroke(brandLime.opacity(0.18)))

                Button(action: model.toggle) {
                    HStack {
                        Text(model.isRunning ? "STOP CAMERA" : "START CAMERA")
                            .font(.headline.bold())
                        Spacer()
                        Image(systemName: model.isRunning ? "stop.fill" : "arrow.up.right")
                    }
                    .foregroundStyle(.black)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 15)
                    .background(brandLime, in: RoundedRectangle(cornerRadius: 16))
                    .shadow(color: brandLime.opacity(0.18), radius: 18)
                }
                .buttonStyle(.plain)

                Text("Lens, zoom, exposure and focus are controlled from the Windows IosCam panel while the video stays on the USB cable.")
                    .font(.footnote)
                    .foregroundStyle(muted)
                    .multilineTextAlignment(.leading)

                Spacer()
            }
            .padding(24)
        }
        .preferredColorScheme(.dark)
    }

    private func row(_ title: String, _ value: String) -> some View {
        HStack {
            Text(title)
                .font(.caption.bold())
                .foregroundStyle(brandLime)
            Spacer()
            Text(value)
                .font(.system(.body, design: .monospaced).weight(.semibold))
                .foregroundStyle(.white)
        }
    }

    private var statusColor: Color {
        switch model.status {
        case .error: return .red
        case .connected: return brandLime
        default: return muted
        }
    }
}
