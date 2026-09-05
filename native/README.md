# IosCam native compatibility mode (Windows 11)

This optional mode keeps the normal IosCam/OBS workflow intact and adds a second camera exposure path for Windows applications that prefer Media Foundation.

Runtime path:

```text
iPhone -> USB/usbmux -> IosCam Python filters -> OBS Virtual Camera driver
       -> OBS2MF broker -> Windows Media Foundation virtual camera -> browser/app
```

OBS Studio's UI does **not** need to be open in this mode. The OBS Virtual Camera driver is used only as the local frame handoff. IosCam writes frames into it directly through `pyvirtualcam`; the open-source OBS2MF bridge republishes that feed with Windows 11 `MFCreateVirtualCamera`.

The resulting device remains a **virtual camera**. Windows intentionally labels Media Foundation software cameras as virtual cameras; this mode does not spoof hardware identity or bypass a site's policy.

## One-time build/install

Simplest path: run `install_native_camera.bat`. It downloads the latest OBS2MF release installer if one is not already present in `native/dist/` or Downloads, then prompts for UAC.

For reproducible/self-built binaries, push the project and run Actions -> **Build native Media Foundation bridge**, download `IosCam-native-bridge`, extract `OBS2MF-Setup-*.exe`, then run `install_native_camera.bat`.

After installation, use `start_ioscam_native.bat`.

## Third-party component

The bridge is fetched at build time from `mbales-tech/OBS2MF`. Its own source and license remain upstream; the workflow records the exact commit used in `OBS2MF_COMMIT.txt`. OBS2MF implements the Windows 11 Media Foundation source/Frame Server side and uses `MFCreateVirtualCamera`.
