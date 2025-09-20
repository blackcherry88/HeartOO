import XCTest
@testable import HeartSW

/// Detailed tests for peak validation and RR correction to debug SDNN discrepancy
final class PeakValidationDetailedTests: XCTestCase {

    func testPeakValidationPipelineStepByStep() throws {
        print("🔬 Detailed Peak Validation Pipeline Analysis")
        print("=" * 60)

        let testData = loadData2CSV()
        let sampleRate: Double = 117.0

        // Step 1: Peak Detection (we know this works - 110 peaks at 10%)
        let signal = try HeartRateSignal(data: testData, sampleRate: sampleRate)
        let detector = AdaptiveThresholdDetector(thresholdPercentage: 10.0)  // Use optimal threshold
        var result = AnalysisResult()

        let peaks = try detector.process(signal, result: &result)

        print("📊 Step 1 - Peak Detection:")
        print("   Detected peaks: \(peaks.count)")
        print("   First 10 peaks: \(Array(peaks.prefix(10)))")

        // Get original RR intervals from peak detection
        guard let originalRR: [Double] = result.getWorkingData("RR_list", as: [Double].self) else {
            XCTFail("Should have original RR intervals")
            return
        }

        print("\n📊 Step 2 - Original RR Intervals:")
        print("   RR count: \(originalRR.count)")
        print("   First 5 RR: \(originalRR.prefix(5).map { String(format: "%.1f", $0) })")

        // Calculate SDNN from original RR (what we expect HeartSW might be using incorrectly)
        let originalSDNN = calculateSDNN(from: originalRR)
        print("   SDNN from original RR: \(String(format: "%.1f", originalSDNN)) ms")

        // Step 3: Peak Validation
        var signalWithPeaks = signal
        signalWithPeaks.setPeaks(peaks)

        let validator = PeakValidator()
        let _ = try validator.process(signalWithPeaks, result: &result)

        // Get validation results
        guard let correctedRR: [Double] = result.getWorkingData("RR_list_cor", as: [Double].self) else {
            XCTFail("Should have corrected RR intervals after validation")
            return
        }

        guard let binaryMask: [Bool] = result.getWorkingData("binary_peaklist", as: [Bool].self) else {
            XCTFail("Should have binary mask after validation")
            return
        }

        print("\n📊 Step 3 - Peak Validation Results:")
        print("   Original RR count: \(originalRR.count)")
        print("   Corrected RR count: \(correctedRR.count)")
        print("   Binary mask length: \(binaryMask.count)")
        print("   Valid peaks: \(binaryMask.filter { $0 }.count)/\(binaryMask.count)")
        print("   First 5 corrected RR: \(correctedRR.prefix(5).map { String(format: "%.1f", $0) })")

        // Calculate SDNN from corrected RR (what HeartPy uses)
        let correctedSDNN = calculateSDNN(from: correctedRR)
        print("   SDNN from corrected RR: \(String(format: "%.1f", correctedSDNN)) ms")

        // Step 4: Compare with expected HeartPy results
        print("\n📊 Step 4 - HeartPy Comparison:")
        print("   HeartPy expected:")
        print("     - 110 peaks")
        print("     - ~109 original RR intervals")
        print("     - ~78 corrected RR intervals")
        print("     - SDNN ~65ms from corrected RR")

        print("\n   HeartSW actual:")
        print("     - \(peaks.count) peaks")
        print("     - \(originalRR.count) original RR intervals")
        print("     - \(correctedRR.count) corrected RR intervals")
        print("     - SDNN \(String(format: "%.1f", correctedSDNN))ms from corrected RR")

        // Step 5: Analyze the differences
        let peakCountDiff = peaks.count - 110
        let originalRRDiff = originalRR.count - 109
        let correctedRRDiff = correctedRR.count - 78
        let sdnnDiff = correctedSDNN - 65.0

        print("\n📊 Step 5 - Difference Analysis:")
        print("   Peak count difference: \(peakCountDiff) (0 is perfect)")
        print("   Original RR difference: \(originalRRDiff)")
        print("   Corrected RR difference: \(correctedRRDiff)")
        print("   SDNN difference: \(String(format: "%.1f", sdnnDiff))ms")

        // Step 6: Key insights
        print("\n💡 Key Insights:")
        if correctedRRDiff > 0 {
            print("   🔍 HeartSW filters FEWER RR intervals than HeartPy")
            print("   📈 More intervals = higher variance = higher SDNN")
            print("   🎯 Need to make validation MORE aggressive")
        } else if correctedRRDiff < 0 {
            print("   🔍 HeartSW filters MORE RR intervals than HeartPy")
            print("   📉 Fewer intervals but still high SDNN suggests outliers remain")
        } else {
            print("   🔍 Same corrected RR count - issue might be in individual interval values")
        }

        if abs(correctedSDNN - originalSDNN) < 10 {
            print("   ⚠️ Original and corrected SDNN are very similar - validation not working properly")
        }

        // Test assertions
        XCTAssertEqual(peaks.count, 110, "Should detect exactly 110 peaks like HeartPy")
        XCTAssertLessThan(correctedRR.count, originalRR.count, "Validation should filter some intervals")
        XCTAssertLessThan(abs(correctedSDNN - 65.0), 20.0, "SDNN should be much closer to HeartPy's 65ms")
    }

    func testRRIntervalValidationThresholds() throws {
        print("\n🔬 Testing RR Interval Validation Thresholds")
        print("=" * 60)

        // Create test data with known outliers
        let testPeaks = [1000, 1100, 1200, 1300, 1350, 1450, 1550, 1650, 1750, 1850]  // 10 peaks
        let sampleRate: Double = 117.0

        // Calculate RR intervals
        var rrIntervals: [Double] = []
        for i in 1..<testPeaks.count {
            let intervalSamples = testPeaks[i] - testPeaks[i-1]
            let intervalMs = (Double(intervalSamples) / sampleRate) * 1000.0
            rrIntervals.append(intervalMs)
        }

        print("📊 Test RR Intervals:")
        print("   Count: \(rrIntervals.count)")
        print("   Values: \(rrIntervals.map { String(format: "%.1f", $0) })")

        let mean = rrIntervals.reduce(0, +) / Double(rrIntervals.count)
        let lowerThreshold = mean * 0.7  // HeartPy uses ±30%
        let upperThreshold = mean * 1.3

        print("   Mean: \(String(format: "%.1f", mean))ms")
        print("   Lower threshold (70%): \(String(format: "%.1f", lowerThreshold))ms")
        print("   Upper threshold (130%): \(String(format: "%.1f", upperThreshold))ms")

        // Check which intervals would be filtered
        var validCount = 0
        var filteredIndices: [Int] = []

        for (i, interval) in rrIntervals.enumerated() {
            if interval >= lowerThreshold && interval <= upperThreshold {
                validCount += 1
            } else {
                filteredIndices.append(i)
                print("   🚫 Filtered RR[\(i)]: \(String(format: "%.1f", interval))ms (outside \(String(format: "%.1f", lowerThreshold))-\(String(format: "%.1f", upperThreshold)))")
            }
        }

        print("   Valid intervals: \(validCount)/\(rrIntervals.count)")

        // Test with HeartSW's validator
        let validator = PeakValidator()

        // Create a minimal test signal and result
        let testData = Array(repeating: 500.0, count: 2000)
        let signal = try HeartRateSignal(data: testData, sampleRate: sampleRate)
        var signalWithPeaks = signal
        signalWithPeaks.setPeaks(testPeaks)

        var result = AnalysisResult()
        result.setWorkingData("RR_list", value: rrIntervals)

        let _ = try validator.process(signalWithPeaks, result: &result)

        if let correctedRR: [Double] = result.getWorkingData("RR_list_cor", as: [Double].self) {
            print("\n📊 HeartSW Validation Results:")
            print("   Original RR: \(rrIntervals.count)")
            print("   Corrected RR: \(correctedRR.count)")
            print("   Filtered: \(rrIntervals.count - correctedRR.count)")

            let originalSDNN = calculateSDNN(from: rrIntervals)
            let correctedSDNN = calculateSDNN(from: correctedRR)

            print("   Original SDNN: \(String(format: "%.2f", originalSDNN))ms")
            print("   Corrected SDNN: \(String(format: "%.2f", correctedSDNN))ms")
            print("   SDNN reduction: \(String(format: "%.1f", ((originalSDNN - correctedSDNN) / originalSDNN) * 100))%")
        }
    }

    func testHeartPyVsHeartSWValidationComparison() throws {
        print("\n🔬 HeartPy vs HeartSW Validation Comparison")
        print("=" * 60)

        // Use our reference HeartPy data to compare validation logic
        let testData = loadData2CSV()
        let sampleRate: Double = 117.0

        // First get HeartSW's results at 10% threshold
        let signal = try HeartRateSignal(data: testData, sampleRate: sampleRate)
        let detector = AdaptiveThresholdDetector(thresholdPercentage: 10.0)
        var result = AnalysisResult()

        let peaks = try detector.process(signal, result: &result)

        var signalWithPeaks = signal
        signalWithPeaks.setPeaks(peaks)

        let validator = PeakValidator()
        let _ = try validator.process(signalWithPeaks, result: &result)

        guard let heartsw_original: [Double] = result.getWorkingData("RR_list", as: [Double].self),
              let heartsw_corrected: [Double] = result.getWorkingData("RR_list_cor", as: [Double].self),
              let heartsw_mask: [Bool] = result.getWorkingData("binary_peaklist", as: [Bool].self) else {
            XCTFail("Failed to get HeartSW validation data")
            return
        }

        print("📊 HeartSW Validation Results:")
        print("   Peaks: \(peaks.count)")
        print("   Original RR: \(heartsw_original.count)")
        print("   Corrected RR: \(heartsw_corrected.count)")
        print("   Binary mask valid: \(heartsw_mask.filter { $0 }.count)/\(heartsw_mask.count)")

        let heartsw_original_sdnn = calculateSDNN(from: heartsw_original)
        let heartsw_corrected_sdnn = calculateSDNN(from: heartsw_corrected)

        print("   Original SDNN: \(String(format: "%.1f", heartsw_original_sdnn))ms")
        print("   Corrected SDNN: \(String(format: "%.1f", heartsw_corrected_sdnn))ms")

        // Expected HeartPy results (from our previous analysis)
        let heartpy_peaks = 110
        let heartpy_original_rr = 109
        let heartpy_corrected_rr = 78
        let heartpy_corrected_sdnn = 64.6

        print("\n📊 HeartPy Expected Results:")
        print("   Peaks: \(heartpy_peaks)")
        print("   Original RR: \(heartpy_original_rr)")
        print("   Corrected RR: \(heartpy_corrected_rr)")
        print("   Corrected SDNN: \(String(format: "%.1f", heartpy_corrected_sdnn))ms")

        // Calculate differences
        let peak_diff = peaks.count - heartpy_peaks
        let original_rr_diff = heartsw_original.count - heartpy_original_rr
        let corrected_rr_diff = heartsw_corrected.count - heartpy_corrected_rr
        let sdnn_diff = heartsw_corrected_sdnn - heartpy_corrected_sdnn
        let sdnn_ratio = heartsw_corrected_sdnn / heartpy_corrected_sdnn

        print("\n📊 Differences (HeartSW - HeartPy):")
        print("   Peak difference: \(peak_diff)")
        print("   Original RR difference: \(original_rr_diff)")
        print("   Corrected RR difference: \(corrected_rr_diff)")
        print("   SDNN difference: \(String(format: "%.1f", sdnn_diff))ms")
        print("   SDNN ratio: \(String(format: "%.2f", sdnn_ratio))x")

        print("\n💡 Diagnosis:")
        if corrected_rr_diff > 5 {
            print("   🎯 PRIMARY ISSUE: HeartSW keeps \(corrected_rr_diff) more RR intervals than HeartPy")
            print("   📈 This increases variance and inflates SDNN")
            print("   🔧 SOLUTION: Make RR validation more aggressive to match HeartPy's 78 intervals")
        } else if abs(corrected_rr_diff) <= 5 && sdnn_ratio > 2.0 {
            print("   🎯 PRIMARY ISSUE: Similar interval count but different interval values")
            print("   📊 This suggests peak positions or validation logic differs")
            print("   🔧 SOLUTION: Check individual RR interval values and validation thresholds")
        }

        // Test key assertions
        XCTAssertEqual(peaks.count, heartpy_peaks, "Peak count should match HeartPy exactly")
        XCTAssertLessThan(abs(corrected_rr_diff), 10, "Corrected RR count should be close to HeartPy")
        XCTAssertLessThan(sdnn_ratio, 2.0, "SDNN should be less than 2x HeartPy's value")
    }

    // MARK: - Helper Methods

    private func calculateSDNN(from intervals: [Double]) -> Double {
        guard intervals.count > 1 else { return 0.0 }

        let mean = intervals.reduce(0, +) / Double(intervals.count)
        let variance = intervals.map { pow($0 - mean, 2) }.reduce(0, +) / Double(intervals.count - 1)
        return sqrt(variance)
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
        return Array(repeating: 500.0, count: 15000)
    }
}

extension String {
    static func *(lhs: String, rhs: Int) -> String {
        return String(repeating: lhs, count: rhs)
    }
}