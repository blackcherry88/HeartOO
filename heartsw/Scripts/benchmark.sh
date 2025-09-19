#!/bin/bash

# HeartSW Benchmark Script
# Runs performance benchmarks for HeartSW

set -e  # Exit on any error

echo "⚡ Running HeartSW Benchmarks..."

# Change to package directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PACKAGE_DIR"

# Build in release mode for accurate benchmarks
echo "🔨 Building in release mode for benchmarks..."
swift build -c release

# Run performance tests
echo "🏁 Running performance tests..."
swift test -c release --filter HeartSWTests.testPerformanceLargeSignal

# Create benchmark data if needed
echo "📊 Creating benchmark data..."
BENCHMARK_DIR="$PACKAGE_DIR/benchmark_data"
mkdir -p "$BENCHMARK_DIR"

# Generate test ECG data
cat > "$BENCHMARK_DIR/generate_test_data.swift" << 'EOF'
import Foundation

// Generate synthetic ECG data for benchmarking
let sampleRate = 1000.0 // 1kHz
let duration = 60.0     // 60 seconds
let heartRate = 70.0    // 70 BPM

var ecgData: [Double] = []

for i in 0..<Int(duration * sampleRate) {
    let time = Double(i) / sampleRate
    let heartPeriod = 60.0 / heartRate

    // Create realistic ECG-like signal
    let phaseInCycle = (time.truncatingRemainder(dividingBy: heartPeriod)) / heartPeriod
    var value = 0.0

    if phaseInCycle > 0.35 && phaseInCycle < 0.65 {
        // QRS complex region
        let qrsPhase = (phaseInCycle - 0.35) / 0.3
        if qrsPhase < 0.3 {
            // P wave
            value = 0.2 * sin(qrsPhase * .pi / 0.3)
        } else if qrsPhase > 0.4 && qrsPhase < 0.7 {
            // QRS complex
            value = 3.0 * sin((qrsPhase - 0.4) * .pi / 0.3)
        } else if qrsPhase > 0.8 {
            // T wave
            value = 0.4 * sin((qrsPhase - 0.8) * .pi / 0.2)
        }
    }

    // Add some noise
    value += Double.random(in: -0.05...0.05)

    ecgData.append(value)
}

// Save as CSV
let csvData = ecgData.enumerated().map { index, value in
    "\(Double(index) / sampleRate),\(value)"
}.joined(separator: "\n")

let header = "time,ecg\n"
let fullCSV = header + csvData

try! fullCSV.write(toFile: "benchmark_data/synthetic_ecg_60s_1khz.csv", atomically: true, encoding: .utf8)

print("Generated \(ecgData.count) samples (\(duration)s at \(sampleRate)Hz)")
print("Saved to: benchmark_data/synthetic_ecg_60s_1khz.csv")
EOF

# Run data generation
echo "🎲 Generating synthetic ECG data..."
swift "$BENCHMARK_DIR/generate_test_data.swift"

# Create benchmark CLI tool
cat > "$BENCHMARK_DIR/benchmark_cli.swift" << 'EOF'
import Foundation

// Simple benchmark CLI
print("HeartSW Benchmark CLI")
print("====================")

// This would import HeartSW and run benchmarks
// For now, just a placeholder

let csvFile = "benchmark_data/synthetic_ecg_60s_1khz.csv"
if FileManager.default.fileExists(atPath: csvFile) {
    print("✅ Test data available: \(csvFile)")

    // Read file size
    let fileSize = try! FileManager.default.attributesOfItem(atPath: csvFile)[.size] as! UInt64
    print("📏 File size: \(fileSize) bytes")

    // Count lines
    let content = try! String(contentsOfFile: csvFile)
    let lineCount = content.components(separatedBy: .newlines).count - 1
    print("📊 Data points: \(lineCount)")

    print("\n🚀 Ready for benchmarking!")
    print("   To benchmark with real HeartSW:")
    print("   1. Import HeartSW in your benchmark code")
    print("   2. Load the CSV file with HeartSW.loadCSV()")
    print("   3. Process with HeartSW.process()")
    print("   4. Measure execution time")
} else {
    print("❌ Test data not found")
}
EOF

swift "$BENCHMARK_DIR/benchmark_cli.swift"

echo ""
echo "✅ Benchmark setup completed!"
echo ""
echo "📊 Benchmark results:"
echo "   - Performance tests: Check output above"
echo "   - Test data generated: $BENCHMARK_DIR/synthetic_ecg_60s_1khz.csv"
echo ""
echo "🎯 To run custom benchmarks:"
echo "   1. Use the generated test data in $BENCHMARK_DIR/"
echo "   2. Create your own benchmark scripts using HeartSW"
echo "   3. Measure performance with different signal sizes"