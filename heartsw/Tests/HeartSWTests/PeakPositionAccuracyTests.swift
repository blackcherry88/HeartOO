import XCTest
@testable import HeartSW

/// Tests for exact peak position accuracy comparing HeartSW vs HeartPy
final class PeakPositionAccuracyTests: XCTestCase {

    func testPeakDetectionInProblematicRegion() throws {
        print("🔬 Testing Peak Detection in Problematic Region")
        print("=" * 60)

        // Load HeartPy reference data
        let referenceData = loadHeartPyReference()

        let testData = loadData2CSV()
        let sampleRate: Double = 117.0
        let signal = try HeartRateSignal(data: testData, sampleRate: sampleRate)

        // Test HeartSW's 10% threshold detection
        let detector = AdaptiveThresholdDetector(thresholdPercentage: 10.0)
        var result = AnalysisResult()
        let heartswPeaks = try detector.process(signal, result: &result)

        print("📊 Peak Detection Results:")
        print("   HeartSW peaks: \(heartswPeaks.count)")
        print("   HeartPy expected: 110 peaks")

        // Focus on the problematic region [1740:1850]
        let regionStart = 1740
        let regionEnd = 1850

        let heartswRegionPeaks = heartswPeaks.filter { $0 >= regionStart && $0 <= regionEnd }
        let heartpyRegionPeaks: [Int]
        if let problemRegion = referenceData["problematic_region"] as? [String: Any],
           let peaks = problemRegion["heartpy_peaks_in_region"] as? [Int] {
            heartpyRegionPeaks = peaks
        } else {
            heartpyRegionPeaks = []
        }

        print("\n🔍 Problematic Region [\(regionStart):\(regionEnd)]:")
        print("   HeartSW peaks: \(heartswRegionPeaks)")
        print("   HeartPy peaks: \(heartpyRegionPeaks)")

        // Test rolling mean accuracy first
        let windowLength = Int(0.75 * sampleRate) // 87 samples
        let heartswRollingMean = detector.calculateRollingMean(data: testData, windowLength: windowLength)

        if let problemRegion = referenceData["problematic_region"] as? [String: Any],
           let referenceRollingMean = problemRegion["rolling_mean"] as? [Double] {
            print("\n📈 Rolling Mean Comparison:")

            for i in regionStart..<min(regionStart + 10, testData.count) {
                let heartswValue = heartswRollingMean[i]
                let heartpyValue = referenceRollingMean[i - regionStart]
                let diff = abs(heartswValue - heartpyValue)

                print("   Position \(i): HeartSW=\(String(format: "%.2f", heartswValue)), HeartPy=\(String(format: "%.2f", heartpyValue)), diff=\(String(format: "%.2f", diff))")

                XCTAssertLessThan(diff, 1.0, "Rolling mean should match within 1.0 at position \(i)")
            }
        }

        // Test threshold calculation
        if let thresholdCalc = referenceData["threshold_calculation"] as? [String: Any],
           let meanRollingMean = thresholdCalc["mean_of_rolling_mean"] as? Double,
           let mn = thresholdCalc["mn_10_percent"] as? Double {

            print("\n🎯 Threshold Calculation:")
            let heartswMean = heartswRollingMean.reduce(0, +) / Double(heartswRollingMean.count)
            let heartswMn = (heartswMean / 100.0) * 10.0

            print("   HeartSW mean rolling: \(String(format: "%.2f", heartswMean))")
            print("   HeartPy mean rolling: \(String(format: "%.2f", meanRollingMean))")
            print("   HeartSW mn: \(String(format: "%.2f", heartswMn))")
            print("   HeartPy mn: \(String(format: "%.2f", mn))")

            XCTAssertEqual(heartswMean, meanRollingMean, accuracy: 1.0, "Mean of rolling mean should match")
        }

        // Test above-threshold detection
        if let problemRegion = referenceData["problematic_region"] as? [String: Any],
           let aboveThresholdIndices = problemRegion["above_threshold_indices"] as? [Int] {
            print("\n🔍 Above-Threshold Points:")
            print("   HeartPy found: \(aboveThresholdIndices.count) points above threshold")

            // Test HeartSW's threshold detection manually
            let heartswMean = heartswRollingMean.reduce(0, +) / Double(heartswRollingMean.count)
            let mn = (heartswMean / 100.0) * 10.0
            let thresholdArray = heartswRollingMean.map { $0 + mn }

            var heartswAboveThreshold: [Int] = []
            for i in regionStart..<regionEnd {
                if i < testData.count && testData[i] > thresholdArray[i] {
                    heartswAboveThreshold.append(i)
                }
            }

            print("   HeartSW found: \(heartswAboveThreshold.count) points above threshold")
            print("   HeartPy points: \(aboveThresholdIndices)")
            print("   HeartSW points: \(heartswAboveThreshold)")

            // The sets should be very similar
            let commonPoints = Set(heartswAboveThreshold).intersection(Set(aboveThresholdIndices))
            let matchRatio = Double(commonPoints.count) / Double(max(heartswAboveThreshold.count, aboveThresholdIndices.count))

            print("   Common points: \(commonPoints.count)")
            print("   Match ratio: \(String(format: "%.2f", matchRatio))")

            XCTAssertGreaterThan(matchRatio, 0.8, "Should match at least 80% of above-threshold points")
        }

        // Final assertion - we want exact peak matches
        XCTAssertEqual(heartswRegionPeaks, heartpyRegionPeaks, "Peak positions should match HeartPy exactly in problematic region")

        if heartswRegionPeaks != heartpyRegionPeaks {
            print("\n❌ MISMATCH ANALYSIS:")
            print("   Expected: \(heartpyRegionPeaks)")
            print("   Got: \(heartswRegionPeaks)")

            for (i, expected) in heartpyRegionPeaks.enumerated() {
                if i < heartswRegionPeaks.count {
                    let actual = heartswRegionPeaks[i]
                    let diff = actual - expected
                    print("   Peak \(i + 1): expected \(expected), got \(actual), diff: \(diff)")
                } else {
                    print("   Peak \(i + 1): expected \(expected), got MISSING")
                }
            }
        }
    }

    // MARK: - Helper Methods

    private func loadData2CSV() -> [Double] {
        let csvPath = "/Volumes/workplace/personal/HeartOO/data/data2.csv"

        do {
            let content = try String(contentsOfFile: csvPath)
            let lines = content.components(separatedBy: .newlines)
                .filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }

            guard !lines.isEmpty else {
                return []
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

            return data

        } catch {
            return []
        }
    }

    private func loadHeartPyReference() -> [String: Any] {
        let referencePath = "/Volumes/workplace/personal/HeartOO/heartpy_rolling_mean_reference.json"

        do {
            let jsonData = try Data(contentsOf: URL(fileURLWithPath: referencePath))
            let json = try JSONSerialization.jsonObject(with: jsonData) as? [String: Any]
            return json ?? [:]
        } catch {
            return [:]
        }
    }
}