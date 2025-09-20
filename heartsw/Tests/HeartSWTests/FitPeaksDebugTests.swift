import XCTest
@testable import HeartSW

/// Debug tests to identify the exact fit_peaks crash location
final class FitPeaksDebugTests: XCTestCase {

    func testFitPeaksWithRealData() throws {
        print("🔬 Testing fit_peaks with Real Data2.csv")
        print("=" * 50)

        // Load real data that causes the crash
        let testData = loadData2CSV()
        let sampleRate: Double = 117.0

        print("📊 Test Setup:")
        print("   Data length: \(testData.count)")
        print("   Sample rate: \(sampleRate)")

        // Create signal
        let signal = try HeartRateSignal(data: testData, sampleRate: sampleRate)

        // Test individual components that might crash
        print("\n🔍 Testing Individual Components:")

        // 1. Test rolling mean calculation
        let detector = AdaptiveThresholdDetector()
        let windowLength = Int(0.75 * sampleRate) // 87 samples

        print("   1. Rolling mean calculation...")
        let rollingMean = detector.calculateRollingMean(data: testData, windowLength: windowLength)
        print("      ✅ Rolling mean: \(rollingMean.count) values")

        // 2. Test single threshold detection
        print("   2. Single threshold detection (10%)...")
        var result = AnalysisResult()
        let peaks10 = try detector.process(signal, result: &result)
        print("      ✅ 10% threshold: \(peaks10.count) peaks")

        // 3. Test fit_peaks algorithm step by step
        print("   3. Testing fit_peaks algorithm...")

        // Test the fit_peaks thresholds one by one
        let thresholdPercentages: [Double] = [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 150, 200, 300]

        var validCandidates: [(rrsd: Double, bpm: Double, threshold: Double, peaks: [Int])] = []

        for (index, testThreshold) in thresholdPercentages.enumerated() {
            print("      Testing threshold \(Int(testThreshold))% (\(index + 1)/\(thresholdPercentages.count))...")

            do {
                // Use the private method directly
                let peaks = try detector.detectPeaksWithSpecificThreshold(in: signal, threshold: testThreshold)

                // Calculate BPM and RRSD
                let bpm = (Double(peaks.count) / (Double(testData.count) / sampleRate)) * 60.0
                let rrIntervals = detector.calculateRRIntervalsPublic(peaks: peaks, sampleRate: sampleRate)
                let rrsd = rrIntervals.count > 1 ? detector.calculateStandardDeviationPublic(rrIntervals) : 0.0

                print("         ✅ \(peaks.count) peaks, BPM: \(String(format: "%.1f", bpm)), RRSD: \(String(format: "%.2f", rrsd))")

                // Check HeartPy's validation criteria
                if rrsd > 0.1 && bpm >= 40 && bpm <= 180 {
                    validCandidates.append((rrsd: rrsd, bpm: bpm, threshold: testThreshold, peaks: peaks))
                    print("         🎯 Valid candidate!")
                }

            } catch {
                print("         ❌ ERROR: \(error)")
                throw error // Re-throw to fail the test and show where it crashes
            }
        }

        print("\n📊 Fit_peaks Results:")
        print("   Valid candidates: \(validCandidates.count)")

        if !validCandidates.isEmpty {
            // Find best candidate (minimum RRSD)
            if let bestCandidate = validCandidates.min(by: { $0.rrsd < $1.rrsd }) {
                print("   Best threshold: \(bestCandidate.threshold)%")
                print("   Best RRSD: \(String(format: "%.2f", bestCandidate.rrsd))")
                print("   Best peaks: \(bestCandidate.peaks.count)")
                print("   First 10 peaks: \(bestCandidate.peaks.prefix(10))")

                // This should match HeartPy's optimization
                XCTAssertEqual(bestCandidate.peaks.count, 110, "Should find 110 peaks like HeartPy")
            }
        } else {
            XCTFail("No valid candidates found")
        }

        print("\n✅ fit_peaks algorithm completed successfully")
    }

    func testDetectPeaksWithThreshold() throws {
        print("\n🔬 Testing detectPeaksWithThreshold Method")
        print("=" * 50)

        let testData = loadData2CSV()
        let sampleRate: Double = 117.0
        let signal = try HeartRateSignal(data: testData, sampleRate: sampleRate)

        let detector = AdaptiveThresholdDetector()

        // Test the method that might be causing the crash
        print("   Testing 10% threshold...")
        let peaks = try detector.detectPeaksWithSpecificThreshold(in: signal, threshold: 10.0)

        print("   Results: \(peaks.count) peaks")
        print("   First 10: \(peaks.prefix(10))")

        XCTAssertGreaterThan(peaks.count, 0, "Should detect some peaks")
        XCTAssertEqual(peaks.count, 110, "Should match HeartPy's 110 peaks at 10% threshold")
    }

    // MARK: - Helper Methods

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
        return Array(0..<1000).map { i in
            500.0 + 50.0 * sin(Double(i) * 0.1) + Double.random(in: -10...10)
        }
    }
}

// Extensions to expose internal methods for testing
extension AdaptiveThresholdDetector {
    func calculateRRIntervalsPublic(peaks: [Int], sampleRate: Double) -> [Double] {
        return calculateRRIntervals(peaks: peaks, sampleRate: sampleRate)
    }

    func calculateStandardDeviationPublic(_ values: [Double]) -> Double {
        return calculateStandardDeviation(values)
    }
}