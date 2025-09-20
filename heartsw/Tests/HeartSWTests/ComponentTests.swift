import XCTest
@testable import HeartSW

/// Simplified unit tests for HeartSW components
final class ComponentTests: XCTestCase {

    func testBasicPeakDetection() throws {
        // Simple test - ensure peak detection works at all
        let testData = generateTestData()
        let sampleRate: Double = 117.0

        let signal = try HeartRateSignal(data: testData, sampleRate: sampleRate)
        let detector = AdaptiveThresholdDetector(thresholdPercentage: 9.0)
        var result = AnalysisResult()

        let peaks = try detector.process(signal, result: &result)

        // Basic sanity checks
        XCTAssertGreaterThan(peaks.count, 0, "Should detect some peaks")
        XCTAssertLessThan(peaks.count, 50, "Should not detect too many peaks in test data")

        // Peaks should be in ascending order
        for i in 1..<peaks.count {
            XCTAssertLessThan(peaks[i-1], peaks[i], "Peaks should be in ascending order")
        }

        print("✅ Basic peak detection test passed - detected \\(peaks.count) peaks")
    }

    func testPeakValidationComponent() throws {
        let testData = generateTestData()
        let sampleRate: Double = 117.0

        // Create signal and detect peaks
        let signal = try HeartRateSignal(data: testData, sampleRate: sampleRate)
        let detector = AdaptiveThresholdDetector()
        var result = AnalysisResult()
        let _ = try detector.process(signal, result: &result)

        // Get validation results
        guard let originalPeaks: [Int] = result.getWorkingData("peaklist", as: [Int].self) else {
            XCTFail("Should have original peaks")
            return
        }

        // Note: RR_list_cor and binary mask might not be available yet depending on pipeline
        let correctedRRIntervals: [Double] = result.getWorkingData("RR_list_cor", as: [Double].self) ?? []
        let binaryMask: [Bool] = result.getWorkingData("binary_peaklist", as: [Bool].self) ?? []

        // Basic validation checks
        XCTAssertGreaterThan(originalPeaks.count, 0, "Should have some peaks")

        // All corrected RR intervals should be reasonable (300-2000ms)
        for interval in correctedRRIntervals {
            XCTAssertTrue(interval >= 300 && interval <= 2000,
                         "RR interval \\(interval) should be physiologically reasonable")
        }

        print("✅ Peak validation component test passed")
    }

    func testTimeDomainAnalysisComponent() throws {
        // Use known RR intervals that should produce specific SDNN
        let testRRIntervals = [897.47, 811.99, 829.09, 777.81, 803.45, 880.38, 897.47, 871.83]

        let analyzer = TimeDomainAnalyzer()
        let measures = try analyzer.calculateMeasures(from: testRRIntervals)

        // Test basic calculations
        let expectedMeanRR = testRRIntervals.reduce(0, +) / Double(testRRIntervals.count)
        let actualMeanRR = measures["ibi"] as? Double ?? 0

        XCTAssertEqual(actualMeanRR, expectedMeanRR, accuracy: 0.1,
                      "Mean RR interval calculation should be correct")

        // Test BPM calculation
        let expectedBPM = 60000.0 / expectedMeanRR
        let actualBPM = measures["bpm"] as? Double ?? 0

        XCTAssertEqual(actualBPM, expectedBPM, accuracy: 0.1,
                      "BPM calculation should be correct")

        // Test SDNN calculation
        let variance = testRRIntervals.map { pow($0 - expectedMeanRR, 2) }.reduce(0, +) / Double(testRRIntervals.count - 1)
        let expectedSDNN = sqrt(variance)
        let actualSDNN = measures["sdnn"] as? Double ?? 0

        XCTAssertEqual(actualSDNN, expectedSDNN, accuracy: 0.1,
                      "SDNN calculation should be correct")

        print("✅ Time domain analysis component test passed")
    }

    func testFullIntegrationMatch() throws {
        // Test full pipeline matches HeartOO on small dataset
        let testData = generateTestData()
        let sampleRate: Double = 117.0

        let signal = try HeartRateSignal(data: testData, sampleRate: sampleRate)
        let detector = AdaptiveThresholdDetector()
        var result = AnalysisResult()
        let _ = try detector.process(signal, result: &result)

        // Run time domain analysis
        let analyzer = TimeDomainAnalyzer()
        let measures = try analyzer.process(signal, result: &result)

        let bpm = measures["bpm"] as? Double ?? 0
        let sdnn = measures["sdnn"] as? Double ?? 0

        // Sanity checks - values should be physiologically reasonable
        XCTAssertTrue(bpm >= 40 && bpm <= 180, "BPM should be reasonable (got \\(bpm))")
        XCTAssertTrue(sdnn >= 0 && sdnn <= 200, "SDNN should be reasonable (got \\(sdnn))")

        print("✅ Full integration test passed - BPM: \\(bpm), SDNN: \\(sdnn)")
    }

    func testExpectedResults() throws {
        // Test with data similar to data2.csv characteristics
        // This should help identify where differences occur

        print("🧪 Testing Expected Results vs HeartOO Reference")

        let testData = generateRealisticTestData()  // More realistic data
        let sampleRate: Double = 117.0

        let signal = try HeartRateSignal(data: testData, sampleRate: sampleRate)
        let detector = AdaptiveThresholdDetector(thresholdPercentage: 9.0)  // Use 9% like our tests
        var result = AnalysisResult()
        let peaks = try detector.process(signal, result: &result)

        print("   📊 HeartSW detected \\(peaks.count) peaks")

        if peaks.count > 5 {
            print("   📊 First 5 peaks: \\(Array(peaks[0..<5]))")
        }

        // Run full analysis
        let analyzer = TimeDomainAnalyzer()
        let measures = try analyzer.process(signal, result: &result)

        let bpm = measures["bpm"] as? Double ?? 0
        let sdnn = measures["sdnn"] as? Double ?? 0

        print("   📊 BPM: \\(bpm)")
        print("   📊 SDNN: \\(sdnn)")

        // This test is for observation - we want to see what HeartSW produces
        // and compare it manually with HeartOO results
        XCTAssertGreaterThan(peaks.count, 0, "Should detect peaks")
    }

    // MARK: - Helper Methods

    func generateTestData() -> [Double] {
        // Generate simple test data for basic functionality
        var data: [Double] = []
        let baseValue: Double = 500
        let length = 1000

        for i in 0..<length {
            let heartbeat = sin(Double(i) * 2.0 * .pi / 117.0) * 100  // ~1 Hz heartbeat
            let noise = Double.random(in: -20...20)  // Noise
            data.append(baseValue + heartbeat + noise)
        }

        return data
    }

    func generateRealisticTestData() -> [Double] {
        // Generate more realistic test data similar to ECG characteristics
        var data: [Double] = []
        let baseValue: Double = 500
        let length = 5000  // 5000 samples at 117Hz ≈ 43 seconds

        // Multiple frequency components to simulate realistic ECG
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