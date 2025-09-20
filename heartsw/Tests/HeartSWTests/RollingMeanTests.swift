import XCTest
@testable import HeartSW

/// Unit tests for rolling mean calculation to match HeartPy's uniform_filter1d
final class RollingMeanTests: XCTestCase {

    func testRollingMeanBasicFunctionality() throws {
        print("🔬 Testing Basic Rolling Mean Functionality")
        print("=" * 50)

        // Simple test data
        let testData: [Double] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        let sampleRate: Double = 100.0
        let windowSize: Double = 0.3  // 0.3 seconds = 30 samples at 100Hz

        let detector = AdaptiveThresholdDetector()
        let windowLength = Int(windowSize * sampleRate) // 30 samples

        // This should not crash
        let rollingMean = detector.calculateRollingMeanPublic(data: testData, windowLength: windowLength)

        print("📊 Basic Test Results:")
        print("   Input: \(testData)")
        print("   Window length: \(windowLength)")
        print("   Rolling mean: \(rollingMean.map { String(format: "%.2f", $0) })")

        XCTAssertEqual(rollingMean.count, testData.count, "Rolling mean should have same length as input")
        XCTAssertFalse(rollingMean.contains(where: { $0.isNaN || $0.isInfinite }), "Rolling mean should not contain NaN or Inf")
    }

    func testRollingMeanEdgeCases() throws {
        print("\n🔬 Testing Rolling Mean Edge Cases")
        print("=" * 50)

        let detector = AdaptiveThresholdDetector()

        // Test 1: Empty data
        let emptyResult = detector.calculateRollingMeanPublic(data: [], windowLength: 10)
        XCTAssertEqual(emptyResult.count, 0, "Empty input should return empty output")

        // Test 2: Single element
        let singleResult = detector.calculateRollingMeanPublic(data: [5.0], windowLength: 3)
        XCTAssertEqual(singleResult.count, 1, "Single element should return single result")
        XCTAssertEqual(singleResult[0], 5.0, accuracy: 0.001, "Single element should equal itself")

        // Test 3: Window larger than data
        let smallData: [Double] = [1, 2, 3]
        let largeWindowResult = detector.calculateRollingMeanPublic(data: smallData, windowLength: 10)
        XCTAssertEqual(largeWindowResult.count, 3, "Should handle window larger than data")

        // Test 4: Zero window length
        let zeroWindowResult = detector.calculateRollingMeanPublic(data: [1, 2, 3], windowLength: 0)
        XCTAssertEqual(zeroWindowResult.count, 3, "Should handle zero window length")

        print("✅ Edge cases passed")
    }

    func testRollingMeanVsHeartPyReference() throws {
        print("\n🔬 Testing Rolling Mean vs HeartPy Reference")
        print("=" * 50)

        // Load real data2.csv for comparison
        let testData = loadData2CSV()
        let sampleRate: Double = 117.0
        let windowSize: Double = 0.75

        let detector = AdaptiveThresholdDetector()
        let windowLength = Int(windowSize * sampleRate) // 87 samples

        print("📊 Test Parameters:")
        print("   Data length: \(testData.count)")
        print("   Sample rate: \(sampleRate) Hz")
        print("   Window size: \(windowSize) seconds")
        print("   Window length: \(windowLength) samples")

        // Calculate rolling mean with HeartSW
        let heartswRollingMean = detector.calculateRollingMeanPublic(data: testData, windowLength: windowLength)

        print("\n📈 HeartSW Rolling Mean Results:")
        print("   Output length: \(heartswRollingMean.count)")
        print("   First 10 values: \(heartswRollingMean.prefix(10).map { String(format: "%.2f", $0) })")

        // Load HeartPy reference values from Python
        let heartpyReference = getHeartPyRollingMeanReference()

        if heartpyReference.count > 0 {
            print("\n📋 HeartPy Reference:")
            print("   Output length: \(heartpyReference.count)")
            print("   First 10 values: \(heartpyReference.prefix(10).map { String(format: "%.2f", $0) })")

            // Compare lengths
            XCTAssertEqual(heartswRollingMean.count, heartpyReference.count, "Output lengths should match")

            // Compare first 10 values with tolerance
            let tolerance = 1.0  // 1.0 tolerance for rolling mean values
            var matchCount = 0

            for i in 0..<min(10, heartswRollingMean.count, heartpyReference.count) {
                let diff = abs(heartswRollingMean[i] - heartpyReference[i])
                if diff <= tolerance {
                    matchCount += 1
                }
                print("   Position \(i): HeartSW=\(String(format: "%.2f", heartswRollingMean[i])), HeartPy=\(String(format: "%.2f", heartpyReference[i])), diff=\(String(format: "%.2f", diff))")
            }

            print("\n📊 Comparison Results:")
            print("   Matches within tolerance: \(matchCount)/10")

            // We expect at least 7/10 to match closely
            XCTAssertGreaterThanOrEqual(matchCount, 7, "At least 7/10 values should match within tolerance")
        } else {
            print("⚠️ No HeartPy reference data available, testing basic properties")
        }

        // Test basic properties
        XCTAssertEqual(heartswRollingMean.count, testData.count, "Rolling mean should have same length as input")
        XCTAssertFalse(heartswRollingMean.contains(where: { $0.isNaN || $0.isInfinite }), "Should not contain NaN or Inf")

        // Rolling mean should be smoother than original data
        let originalVariance = calculateVariance(testData)
        let smoothedVariance = calculateVariance(heartswRollingMean)
        XCTAssertLessThan(smoothedVariance, originalVariance, "Rolling mean should reduce variance (smoother)")

        print("✅ Rolling mean validation completed")
    }

    func testRollingMeanBoundsChecking() throws {
        print("\n🔬 Testing Rolling Mean Bounds Checking")
        print("=" * 50)

        let detector = AdaptiveThresholdDetector()

        // Test data that might cause bounds issues
        let testData: [Double] = Array(0..<100).map { Double($0) }

        // Test different window sizes that might cause edge issues
        let windowSizes = [1, 5, 10, 50, 99, 100, 150]

        for windowLength in windowSizes {
            print("Testing window length: \(windowLength)")

            // This should never crash
            let result = detector.calculateRollingMeanPublic(data: testData, windowLength: windowLength)

            XCTAssertEqual(result.count, testData.count, "Should return correct length for window \(windowLength)")
            XCTAssertFalse(result.contains(where: { $0.isNaN || $0.isInfinite }), "Should not contain invalid values for window \(windowLength)")

            // Basic sanity check - rolling mean should be within reasonable bounds of original data
            let minOriginal = testData.min() ?? 0
            let maxOriginal = testData.max() ?? 0
            let minRolling = result.min() ?? 0
            let maxRolling = result.max() ?? 0

            XCTAssertGreaterThanOrEqual(minRolling, minOriginal - 1.0, "Rolling mean min should be reasonable for window \(windowLength)")
            XCTAssertLessThanOrEqual(maxRolling, maxOriginal + 1.0, "Rolling mean max should be reasonable for window \(windowLength)")
        }

        print("✅ Bounds checking passed")
    }

    // MARK: - Helper Methods

    private func calculateVariance(_ data: [Double]) -> Double {
        guard data.count > 1 else { return 0.0 }
        let mean = data.reduce(0, +) / Double(data.count)
        let squaredDifferences = data.map { pow($0 - mean, 2) }
        return squaredDifferences.reduce(0, +) / Double(data.count - 1)
    }

    private func loadData2CSV() -> [Double] {
        let csvPath = "/Volumes/workplace/personal/HeartOO/data/data2.csv"

        do {
            let content = try String(contentsOfFile: csvPath)
            let lines = content.components(separatedBy: .newlines)
                .filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }

            guard !lines.isEmpty else {
                return generateFallbackData()
            }

            var data: [Double] = []
            let dataLines = lines.first?.contains("hr") == true ? Array(lines.dropFirst()) : lines

            for line in dataLines {
                let components = line.components(separatedBy: ",")
                if let valueString = components.last?.trimmingCharacters(in: .whitespacesAndNewlines),
                   let value = Double(valueString) {
                    data.append(value)
                }
            }

            return data.isEmpty ? generateFallbackData() : data

        } catch {
            return generateFallbackData()
        }
    }

    private func generateFallbackData() -> [Double] {
        // Generate realistic test data if file not available
        return Array(0..<1000).map { i in
            500.0 + 50.0 * sin(Double(i) * 0.1) + Double.random(in: -10...10)
        }
    }

    private func getHeartPyRollingMeanReference() -> [Double] {
        // Try to load HeartPy reference data from our previous analysis
        let referencePath = "/Volumes/workplace/personal/HeartOO/heartpy_rolling_mean_reference.json"

        do {
            let jsonData = try Data(contentsOf: URL(fileURLWithPath: referencePath))
            let json = try JSONSerialization.jsonObject(with: jsonData) as? [String: Any]

            if let rollingMeanArray = json?["rolling_mean"] as? [Double] {
                return rollingMeanArray
            }
        } catch {
            // Reference data not available
        }

        return []
    }
}

// Extension to expose private method for testing
extension AdaptiveThresholdDetector {
    func calculateRollingMeanPublic(data: [Double], windowLength: Int) -> [Double] {
        return calculateRollingMean(data: data, windowLength: windowLength)
    }
}