// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "HeartSW",
    platforms: [
        .macOS(.v13),
        .iOS(.v16),
        .watchOS(.v9),
        .tvOS(.v16)
    ],
    products: [
        // Products define the executables and libraries a package produces, making them visible to other packages.
        .library(
            name: "HeartSW",
            targets: ["HeartSW"]),
        .executable(
            name: "HeartSWCLI",
            targets: ["HeartSWCLI"])
    ],
    dependencies: [
        // Dependencies declare other packages that this package depends on.
        .package(url: "https://github.com/apple/swift-numerics", from: "1.0.0"),
        .package(url: "https://github.com/apple/swift-algorithms", from: "1.0.0"),
    ],
    targets: [
        // Targets are the basic building blocks of a package, defining a module or a test suite.
        .target(
            name: "HeartSW",
            dependencies: [
                .product(name: "Numerics", package: "swift-numerics"),
                .product(name: "Algorithms", package: "swift-algorithms"),
            ]),
        .executableTarget(
            name: "HeartSWCLI",
            dependencies: ["HeartSW"]),
        .testTarget(
            name: "HeartSWTests",
            dependencies: ["HeartSW"]),
    ]
)