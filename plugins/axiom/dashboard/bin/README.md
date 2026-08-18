# Prebuilt Dashboard binaries

Release packaging places platform-specific single binaries here:

```text
bin/
├── darwin-aarch64/axiom-dashboard
├── darwin-x86_64/axiom-dashboard
├── linux-x86_64/axiom-dashboard
├── linux-aarch64/axiom-dashboard       # optional when a release provides it
└── windows-x86_64/axiom-dashboard.exe
```

The v0.1.3 release workflow builds macOS Apple Silicon, macOS Intel, Linux x86_64, and Windows x86_64. Linux ARM64 remains a supported launcher layout and can be added by a downstream or future release build.

Source archives intentionally may leave these directories empty. The launchers use Cargo as a development fallback. Release Plugin ZIPs overlay the binaries produced by CI, preserving one-install distribution without making Axiom Core depend on the Dashboard.
