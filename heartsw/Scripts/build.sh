#!/bin/bash

# HeartSW Build Script
# Builds the HeartSW Swift package

set -e  # Exit on any error

echo "🔨 Building HeartSW Swift Package..."

# Change to package directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PACKAGE_DIR"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
swift package clean

# Resolve dependencies
echo "📦 Resolving dependencies..."
swift package resolve

# Build the package
echo "🔨 Building package..."
swift build -c release

# Build CLI tool if it exists
if [ -d "Sources/HeartSWCLI" ]; then
    echo "🖥️  Building CLI tool..."
    swift build -c release --product HeartSWCLI
fi

echo "✅ Build completed successfully!"

# Show build products
echo ""
echo "📋 Build products:"
find .build/release -type f -perm +111 -name "*HeartSW*" 2>/dev/null || echo "No executables found"

echo ""
echo "🎯 To run tests, use: ./Scripts/test.sh"
echo "🎯 To run benchmarks, use: ./Scripts/benchmark.sh"