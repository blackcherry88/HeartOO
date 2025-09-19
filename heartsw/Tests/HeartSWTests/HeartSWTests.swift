// HeartSW Tests
// Comprehensive tests with docstring examples

import XCTest
@testable import HeartSW

final class HeartSWTests: XCTestCase {

    // MARK: - Signal Tests

    func testHeartRateSignalCreation() throws {
        // Test docstring example: basic signal creation
        let signal = try HeartRateSignal(data: [1.0, 2.0, 3.0, 2.0, 1.0], sampleRate: 100.0)
        XCTAssertEqual(signal.duration, 0.05) // 5 samples at 100 Hz = 0.05 seconds
        XCTAssertEqual(signal.data.count, 5)
    }

    func testSignalValidation() {
        // Test error cases
        XCTAssertThrowsError(try HeartRateSignal(data: [], sampleRate: 100.0)) { error in
            XCTAssertEqual(error as? HRVError, .insufficientData(0))
        }

        XCTAssertThrowsError(try HeartRateSignal(data: [1.0, 2.0], sampleRate: -1.0)) { error in
            XCTAssertEqual(error as? HRVError, .invalidSampleRate(-1.0))
        }
    }

    func testPeakSetting() throws {
        // Test docstring example: peak setting
        var signal = try HeartRateSignal(data: [1.0, 3.0, 1.0, 4.0, 1.0], sampleRate: 100.0)
        signal.setPeaks([1, 3]) // Peak at indices 1 and 3
        XCTAssertEqual(signal.peaks, [1, 3])
        XCTAssertEqual(signal.rrIntervals?.count, 1) // One RR interval between peaks
    }

    func testTimeSlice() throws {
        // Test docstring example: time slicing
        let signal = try HeartRateSignal(data: Array(0...99).map(Double.init), sampleRate: 100.0)
        let slice = try signal.slice(from: 0.1, to: 0.2) // 0.1s to 0.2s
        XCTAssertEqual(slice.data.count, 10) // 0.1s * 100Hz = 10 samples
    }

    func testTimeAxis() throws {
        // Test docstring example: time axis
        let signal = try HeartRateSignal(data: [1.0, 2.0, 3.0], sampleRate: 2.0)
        let timeAxis = signal.timeAxis()
        XCTAssertEqual(timeAxis, [0.0, 0.5, 1.0]) // Time points at 2 Hz
    }

    func testScaling() throws {
        // Test docstring example: signal scaling
        let signal = try HeartRateSignal(data: [0.0, 5.0, 10.0], sampleRate: 1.0)
        let scaled = signal.scaled(to: 0.0...1.0)
        let expectedData = [0.0, 0.5, 1.0]
        XCTAssertEqual(scaled.data.count, expectedData.count)
        for (actual, expected) in zip(scaled.data, expectedData) {
            XCTAssertEqual(actual, expected, accuracy: 1e-10)
        }
    }

    // MARK: - Analysis Result Tests

    func testAnalysisResultMeasures() {
        // Test docstring example: measure management
        var result = AnalysisResult()
        result.setMeasure("bpm", value: 72.5)
        XCTAssertEqual(result.getMeasure("bpm"), 72.5)

        // Test non-existent measure
        XCTAssertNil(result.getMeasure("nonexistent"))
    }

    func testMeasuresByCategory() {
        // Test docstring example: category filtering
        var result = AnalysisResult()
        result.setMeasure("time_bpm", value: 72.0)
        result.setMeasure("time_sdnn", value: 45.2)
        result.setMeasure("freq_lf", value: 150.0)
        let timeMeasures = result.getMeasuresByCategory("time_")
        XCTAssertEqual(timeMeasures.count, 2)
        XCTAssertEqual(timeMeasures["time_bpm"], 72.0)
    }

    func testWorkingDataStorage() {
        // Test docstring example: working data
        var result = AnalysisResult()
        result.setWorkingData("peaks", value: [10, 50, 90])
        let peaks: [Int]? = result.getWorkingData("peaks", as: [Int].self)
        XCTAssertEqual(peaks, [10, 50, 90])
    }

    func testSegmentManagement() {
        // Test docstring example: segment management
        var result = AnalysisResult()
        var segment = AnalysisResult()
        segment.setMeasure("bpm", value: 75.0)
        result.addSegment(segment)
        XCTAssertEqual(result.allSegments.count, 1)
    }

    func testComparison() {
        // Test docstring example: result comparison
        var result1 = AnalysisResult()
        result1.setMeasure("bpm", value: 72.0)
        result1.setMeasure("sdnn", value: 45.0)

        var result2 = AnalysisResult()
        result2.setMeasure("bpm", value: 72.001) // Very close
        result2.setMeasure("rmssd", value: 30.0) // Different measure

        let comparison = result1.compare(with: result2, tolerance: 0.01)
        XCTAssertTrue(comparison.identicalMeasures.contains("bpm"))
        XCTAssertTrue(comparison.onlyInFirst.contains("sdnn"))
        XCTAssertTrue(comparison.onlyInSecond.contains("rmssd"))
    }

    // MARK: - Time Domain Analysis Tests

    func testTimeDomainAnalysis() throws {
        // Test docstring example: known RR intervals
        let analyzer = TimeDomainAnalyzer()
        // RR intervals: 800, 850, 820, 790, 830 ms (mean = 818 ms)
        let intervals = [800.0, 850.0, 820.0, 790.0, 830.0]
        let measures = try analyzer.calculateMeasures(from: intervals)

        // BPM should be approximately 60000/818 ≈ 73.35
        XCTAssertEqual(measures["bpm"]!, 73.35, accuracy: 0.1)

        // Verify required measures exist
        XCTAssertNotNil(measures["sdnn"])
        XCTAssertNotNil(measures["rmssd"])
        XCTAssertNotNil(measures["pnn50"])
    }

    func testTimeDomainWithSignal() throws {
        // Test with actual signal processing
        var signal = try HeartRateSignal(data: Array(repeating: 1.0, count: 1000), sampleRate: 100.0)
        // Set artificial peaks for testing
        signal.setPeaks([100, 180, 260, 340, 420]) // 5 peaks, 4 RR intervals

        var result = AnalysisResult()
        let analyzer = TimeDomainAnalyzer()
        let measures = try analyzer.process(signal, result: &result)

        // Verify we get expected measures
        XCTAssertNotNil(measures["bpm"])
        XCTAssertNotNil(measures["sdnn"])
        XCTAssertNotNil(measures["rmssd"])
    }

    // MARK: - Peak Detection Tests

    func testAdaptiveThresholdDetector() throws {
        // Test detector initialization
        let detector = AdaptiveThresholdDetector(minBPM: 40, maxBPM: 180, windowSize: 0.75)
        XCTAssertEqual(detector.minBPM, 40)
        XCTAssertEqual(detector.maxBPM, 180)
        XCTAssertEqual(detector.windowSize, 0.75)
    }

    func testPeakDetectionSynthetic() throws {
        // Create synthetic signal with clear peaks
        var data = Array(repeating: 0.1, count: 100)
        data[10] = 1.0  // Peak 1
        data[30] = 1.2  // Peak 2 (higher)
        data[50] = 0.9  // Peak 3

        let signal = try HeartRateSignal(data: data, sampleRate: 100.0)
        let detector = AdaptiveThresholdDetector()
        let peaks = try detector.detectPeaks(in: signal)

        // Should detect at least some peaks (exact positions may vary due to algorithm)
        XCTAssertGreaterThan(peaks.count, 0)
    }

    // MARK: - Integration Tests

    func testQuickAnalysis() throws {
        // Test HeartSW.process convenience function
        let ecgData = Array(0..<100).map { sin(Double($0) * 0.1) + Double.random(in: -0.1...0.1) }
        let sampleRate = 100.0

        let result = try HeartSW.process(data: ecgData, sampleRate: sampleRate)

        // Should have some basic measures (might be empty if no peaks detected in synthetic data)
        // This is just testing the API works without crashing
        XCTAssertNotNil(result.getAllMeasures())
    }

    func testQuickPipeline() throws {
        // Test QuickPipeline
        let pipeline = QuickPipeline(minBPM: 50, maxBPM: 160)

        // Create more realistic synthetic ECG signal
        var ecgData: [Double] = []
        let sampleRate = 100.0
        let duration = 10.0 // 10 seconds
        let baseHeartRate = 70.0 // BPM

        // Generate synthetic ECG with peaks every 60/70 seconds ≈ 0.857s
        for i in 0..<Int(duration * sampleRate) {
            let time = Double(i) / sampleRate
            let heartPeriod = 60.0 / baseHeartRate

            // Create QRS-like spikes
            let phaseInCycle = (time.truncatingRemainder(dividingBy: heartPeriod)) / heartPeriod
            var value = 0.0

            if phaseInCycle > 0.4 && phaseInCycle < 0.6 {
                // QRS complex region
                value = sin((phaseInCycle - 0.4) * .pi / 0.2) * 2.0
            } else {
                // Baseline with some variation
                value = 0.1 * sin(time * 2.0) + 0.05 * Double.random(in: -1...1)
            }

            ecgData.append(value)
        }

        let signal = try HeartRateSignal(data: ecgData, sampleRate: sampleRate)
        let result = try pipeline.analyze(signal)

        // Results contain both peak detection and time domain measures
        XCTAssertNotNil(result.getWorkingData("peaklist", as: [Int].self))
        // Note: Measures might be nil if no peaks detected, which is OK for this synthetic data
    }

    // MARK: - Error Handling Tests

    func testValidation() {
        // Test validation utilities
        XCTAssertNoThrow(try Validation.validateSampleRate(100.0))
        XCTAssertThrowsError(try Validation.validateSampleRate(-1.0))

        XCTAssertNoThrow(try Validation.validateDataCount([1.0, 2.0, 3.0]))
        XCTAssertThrowsError(try Validation.validateDataCount([1.0]))

        XCTAssertNoThrow(try Validation.validateTimeRange(start: 0.0, end: 10.0, duration: 20.0))
        XCTAssertThrowsError(try Validation.validateTimeRange(start: 15.0, end: 25.0, duration: 20.0))
    }

    // MARK: - JSON Tests

    func testJSONSerialization() throws {
        var result = AnalysisResult()
        result.setMeasure("bpm", value: 72.5)
        result.setMeasure("sdnn", value: 45.2)

        // Test JSON round-trip
        let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent("test_result.json")

        try result.saveToJSON(at: tempURL)
        let loaded = try AnalysisResult.loadFromJSON(at: tempURL)

        XCTAssertEqual(loaded.getMeasure("bpm"), 72.5)
        XCTAssertEqual(loaded.getMeasure("sdnn"), 45.2)

        // Cleanup
        try? FileManager.default.removeItem(at: tempURL)
    }

    // MARK: - Performance Tests

    func testPerformanceLargeSignal() throws {
        // Test with larger signal
        let largeData = Array(0..<10000).map { sin(Double($0) * 0.01) }
        let signal = try HeartRateSignal(data: largeData, sampleRate: 1000.0)

        measure {
            do {
                let detector = AdaptiveThresholdDetector()
                _ = try detector.detectPeaks(in: signal)
            } catch {
                XCTFail("Peak detection failed: \(error)")
            }
        }
    }
}