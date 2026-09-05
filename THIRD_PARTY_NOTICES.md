# Third-party notices

IosCam project source in this repository is licensed under MIT. Dependencies and external applications keep their own licenses and terms; the MIT license does **not** relicense them.

Key runtime/build dependencies include:

- **pymobiledevice3** — https://github.com/doronz88/pymobiledevice3 — upstream repository states GPL-3.0.
- **PyAV** — https://github.com/PyAV-Org/PyAV — project source is BSD-3-Clause; binary wheels also bundle/link FFmpeg components whose licenses depend on the build configuration.
- **OpenCV / opencv-python** — https://pypi.org/project/opencv-python/ — OpenCV and wheel packaging include their own license/third-party notices.
- **OBS Studio** — https://obsproject.com/ — external application, not bundled in this repository.
- **OBS2MF** — https://github.com/mbales-tech/OBS2MF — optional Windows 11 Media Foundation bridge using `MFCreateVirtualCamera`; not bundled as source/binary in IosCam, downloaded/built separately under its upstream notices and license terms.
- **Sideloadly** — https://sideloadly.io/ — external signing/install tool, not bundled in this repository.
- **Apple iOS SDK / Xcode / iTunes / Apple Mobile Device Service** — Apple software and SDKs under Apple's terms, not bundled here.

Before redistributing a packaged binary that bundles third-party code, review the exact licenses of the versions and binary wheels you distribute. In particular, FFmpeg codec/build options can affect redistribution obligations.
