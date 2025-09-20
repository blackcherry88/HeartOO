import XCTest
@testable import HeartSW

/// Detailed component comparison tests between HeartSW and HeartOO reference
final class DetailedComponentTests: XCTestCase {

    func testPeakValidationVsHeartOO() throws {
        print("🔍 Testing Peak Validation vs HeartOO Reference")

        // Use the same realistic test data as before
        let testData = generateRealisticTestData()
        let sampleRate: Double = 117.0

        // Step 1: Peak Detection
        let signal = try HeartRateSignal(data: testData, sampleRate: sampleRate)
        let detector = AdaptiveThresholdDetector(thresholdPercentage: 9.0)
        var result = AnalysisResult()
        let peaks = try detector.process(signal, result: &result)

        print("   📊 Peak Detection Results:")
        print("      Detected peaks: \\(peaks.count)")
        print("      First 10 peaks: \\(Array(peaks.prefix(10)))")

        // Get RR intervals from peak detection
        guard let originalRR: [Double] = result.getWorkingData("RR_list", as: [Double].self) else {
            XCTFail("Should have original RR intervals")
            return
        }

        print("      Original RR count: \\(originalRR.count)")
        print("      First 5 RR intervals: \\(Array(originalRR.prefix(5)))")

        // Calculate SDNN from original RR intervals (what HeartSW might be using)
        let originalSDNN = calculateSDNN(from: originalRR)
        print("      SDNN from original RR: \\(originalSDNN) ms")

        // Step 2: Peak Validation (the key component we're testing)
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

        print("\\n   📊 Peak Validation Results:")
        print("      Corrected RR count: \\(correctedRR.count)")
        print("      Valid peaks: \\(binaryMask.filter { $0 }.count)/\\(binaryMask.count)")
        print("      First 5 corrected RR: \\(Array(correctedRR.prefix(5)))")

        // Calculate SDNN from corrected RR intervals (what HeartOO uses)
        let correctedSDNN = calculateSDNN(from: correctedRR)
        print("      SDNN from corrected RR: \\(correctedSDNN) ms")

        // Step 3: Analysis
        let filteringRatio = Double(correctedRR.count) / Double(originalRR.count) * 100
        let sdnnDifference = abs(originalSDNN - correctedSDNN)
        let sdnnReduction = ((originalSDNN - correctedSDNN) / originalSDNN) * 100

        print("\\n   📊 Validation Analysis:")
        print("      Filtering ratio: \\(filteringRatio:.1f)% intervals kept")
        print("      SDNN difference: \\(sdnnDifference:.1f) ms")
        print("      SDNN reduction: \\(sdnnReduction:.1f)%")

        // Step 4: HeartOO Reference Comparison
        // Based on our previous tests, HeartOO achieves:
        // - 110 peaks on full data2.csv
        // - SDNN ~65ms using corrected intervals
        // - Significant filtering of RR intervals

        print("\\n   🎯 HeartOO Reference Comparison:")
        print("      HeartOO typically filters ~29% of RR intervals (78/109)")
        print("      HeartOO SDNN on data2.csv: ~65ms")
        print("      HeartSW current approach likely uses original RR for SDNN")

        // Key insights
        if filteringRatio < 80 {
            print("\\n   🔍 Key Insight: Heavy RR filtering detected!")
            print("      This explains SDNN discrepancy if HeartSW uses original RR")
        }

        if sdnnReduction > 50 {
            print("\\n   💡 Solution: HeartSW should use corrected RR for time domain analysis")
        }

        // Test assertions
        XCTAssertGreaterThan(peaks.count, 0, "Should detect peaks")
        XCTAssertGreaterThan(correctedRR.count, 0, "Should have corrected RR intervals")
        XCTAssertLessThan(correctedRR.count, originalRR.count, "Validation should filter some intervals")
    }

    func testTimeDomainAnalysisInputs() throws {
        print("\\n🔍 Testing Time Domain Analysis Inputs")

        let testRRIntervals = [897.47, 811.99, 829.09, 777.81, 803.45, 880.38, 897.47, 871.83, 900.12, 845.33]
        let noisyRRIntervals = testRRIntervals + [300.0, 1800.0, 250.0, 2200.0] // Add obvious outliers

        print("   📊 Testing with clean RR intervals:")
        let cleanSDNN = calculateSDNN(from: testRRIntervals)
        print("      Clean SDNN: \\(cleanSDNN) ms")

        print("\\n   📊 Testing with noisy RR intervals (outliers added):")
        let noisySDNN = calculateSDNN(from: noisyRRIntervals)
        print("      Noisy SDNN: \\(noisySDNN) ms")

        let sdnnInflation = (noisySDNN / cleanSDNN) * 100
        print("      SDNN inflation: \\(sdnnInflation:.1f)%")

        print("\\n   💡 Key Insight:")
        print("      Outlier RR intervals dramatically inflate SDNN")
        print("      This is why HeartPy/HeartOO filter RR intervals")
        print("      HeartSW's 2.4x SDNN suggests it includes outliers")

        // Test the analyzer with both datasets
        let analyzer = TimeDomainAnalyzer()

        let cleanMeasures = try analyzer.calculateMeasures(from: testRRIntervals)
        let noisyMeasures = try analyzer.calculateMeasures(from: noisyRRIntervals)

        let cleanAnalyzerSDNN = cleanMeasures["sdnn"] as? Double ?? 0
        let noisyAnalyzerSDNN = noisyMeasures["sdnn"] as? Double ?? 0

        print("\\n   📊 TimeDomainAnalyzer Results:")
        print("      Clean data SDNN: \\(cleanAnalyzerSDNN) ms")
        print("      Noisy data SDNN: \\(noisyAnalyzerSDNN) ms")

        XCTAssertTrue(noisyAnalyzerSDNN > cleanAnalyzerSDNN * 2, "Noisy data should significantly increase SDNN")
    }

    func testFullPipelineWithCorrection() throws {
        print("\\n🔍 Testing Full Pipeline with RR Correction")

        let testData = generateRealisticTestData()
        let sampleRate: Double = 117.0

        // Full pipeline test
        let signal = try HeartRateSignal(data: testData, sampleRate: sampleRate)
        let detector = AdaptiveThresholdDetector(thresholdPercentage: 9.0)
        var result = AnalysisResult()

        // Step 1: Peak detection
        let peaks = try detector.process(signal, result: &result)

        // Step 2: Peak validation (this is the key step HeartSW might be missing)
        var signalWithPeaks = signal
        signalWithPeaks.setPeaks(peaks)
        let validator = PeakValidator()
        let _ = try validator.process(signalWithPeaks, result: &result)

        // Step 3: Time domain analysis using corrected data
        let analyzer = TimeDomainAnalyzer()
        let measures = try analyzer.process(signalWithPeaks, result: &result)

        let finalSDNN = measures["sdnn"] as? Double ?? 0
        let finalBPM = measures["bpm"] as? Double ?? 0

        print("   📊 Full Pipeline Results:")
        print("      Peaks detected: \\(peaks.count)")
        print("      Final SDNN: \\(finalSDNN) ms")
        print("      Final BPM: \\(finalBPM)")

        // Compare with analysis using original RR intervals
        if let originalRR: [Double] = result.getWorkingData("RR_list", as: [Double].self) {
            let originalSDNN = calculateSDNN(from: originalRR)
            let sdnnImprovement = ((originalSDNN - finalSDNN) / originalSDNN) * 100

            print("\\n   📊 Pipeline Comparison:")
            print("      Original RR SDNN: \\(originalSDNN) ms")
            print("      Corrected RR SDNN: \\(finalSDNN) ms")
            print("      SDNN improvement: \\(sdnnImprovement:.1f)% reduction")

            print("\\n   🎯 Recommendation:")
            if sdnnImprovement > 20 {
                print("      ✅ RR correction significantly improves SDNN accuracy")
                print("      🔧 Ensure HeartSW uses corrected RR intervals for analysis")
            } else {
                print("      ⚠️ RR correction has minimal impact on this data")
                print("      🔍 SDNN differences may be due to other factors")
            }
        }

        XCTAssertGreaterThan(peaks.count, 0, "Should detect peaks")
        XCTAssertTrue(finalBPM >= 40 && finalBPM <= 180, "BPM should be physiologically reasonable")
    }

    // MARK: - Helper Methods

    func calculateSDNN(from intervals: [Double]) -> Double {
        guard intervals.count > 1 else { return 0.0 }

        let mean = intervals.reduce(0, +) / Double(intervals.count)
        let variance = intervals.map { pow($0 - mean, 2) }.reduce(0, +) / Double(intervals.count - 1)
        return sqrt(variance)
    }

    func generateRealisticTestData() -> [Double] {
        // Generate more realistic test data similar to ECG characteristics
        var data: [Double] = []
        let baseValue: Double = 500
        let length = 5000  // 5000 samples at 117Hz ≈ 43 seconds

        for i in 0..<length {
            let t = Double(i) / 117.0  // Time in seconds

            // Main heartbeat (~65 BPM = 1.08 Hz)
            let heartRate = 65.0 / 60.0  // Hz
            let mainBeat = sin(2.0 * .pi * heartRate * t) * 150

            // P wave and T wave components
            let pWave = sin(2.0 * .pi * heartRate * 3.0 * t) * 20
            let tWave = sin(2.0 * .pi * heartRate * 2.0 * t + .pi) * 30

            // Respiratory artifact
            let respiration = sin(2.0 * .pi * 0.25 * t) * 10  // 0.25 Hz breathing

            // Noise
            let noise = Double.random(in: -15...15)

            // Movement artifact (occasional)
            let movement = (i % 1000 < 50) ? Double.random(in: -50...50) : 0

            data.append(baseValue + mainBeat + pWave + tWave + respiration + noise + movement)
        }

        return data
    }
}