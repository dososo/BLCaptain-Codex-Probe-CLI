// swift-tools-version: 6.0

import PackageDescription

let package = Package(
    name: "CodexProbeBar",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(name: "CodexProbeBar", targets: ["CodexProbeBar"])
    ],
    targets: [
        .executableTarget(
            name: "CodexProbeBar",
            path: "Sources/CodexProbeBar"
        )
    ]
)
