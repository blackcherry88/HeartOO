#!/bin/bash

# HeartSW Test Script
# Runs tests for the HeartSW Swift package

set -e  # Exit on any error

echo "🧪 Running HeartSW Tests..."

# Change to package directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PACKAGE_DIR"

# Run tests with coverage if available
echo "🏃 Running unit tests..."

if command -v xcrun &> /dev/null; then
    # On macOS, use Xcode tools for better output
    echo "Using Xcode tools for testing..."
    swift test --enable-code-coverage

    # Show coverage report if available
    if [ -d ".build" ]; then
        echo ""
        echo "📊 Generating code coverage report..."
        xcrun llvm-cov show .build/debug/HeartSWPackageTests.xctest/Contents/MacOS/HeartSWPackageTests \
            -instr-profile=.build/debug/codecov/default.profdata \
            Sources/ \
            -ignore-filename-regex=".build|Tests" \
            -format=text > coverage_report.txt 2>/dev/null || echo "Coverage report generation failed"

        if [ -f coverage_report.txt ]; then
            echo "Coverage report saved to: coverage_report.txt"
            echo "📈 Coverage summary:"
            tail -10 coverage_report.txt
        fi
    fi
else
    # On Linux or other platforms
    echo "Using standard Swift test runner..."
    swift test
fi

echo ""
echo "✅ All tests completed!"

# Run doctest validation
echo ""
echo "📚 Validating docstring examples..."
echo "Note: Swift doesn't have built-in doctest, but examples are validated in unit tests"

echo ""
echo "🎯 Next steps:"
echo "   - Review test output above"
echo "   - Check coverage report if generated"
echo "   - Run benchmarks with: ./Scripts/benchmark.sh"