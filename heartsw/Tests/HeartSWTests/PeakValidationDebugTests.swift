// HeartSW - Swift Heart Rate Analysis
// Peak validation debug tests

import XCTest
@testable import HeartSW

final class PeakValidationDebugTests: XCTestCase {

    func testPeakValidationLogic() throws {
        print("\n🔬 Peak Validation Debug Test")
        print("=" * 40)

        // Use exact RR intervals from data2.csv (first 10)
        let rrIntervals: [Double] = [
            42.73504273504273,
            316.2393162393162,
            717.9487179487179,
            222.2222222222222,
            273.50427350427356,
            162.3931623931624,
            666.6666666666666,
            470.0854700854701,
            7444.444444444444,
            418.8034188034188
        ]

        let detector = AdaptiveThresholdDetector()
        let binaryPeaklist = detector.validatePeaks(rrIntervals: rrIntervals)

        print("📊 RR Intervals and Validation:")
        for (i, rr) in rrIntervals.enumerated() {
            print(String(format: "   RR[%2d]: %8.1f ms", i, rr))
        }

        // Calculate thresholds manually
        let meanRR = rrIntervals.reduce(0, +) / Double(rrIntervals.count)
        let thirtyPercent = 0.3 * meanRR
        let upperThreshold = thirtyPercent <= 300 ? meanRR + 300 : meanRR + thirtyPercent
        let lowerThreshold = thirtyPercent <= 300 ? meanRR - 300 : meanRR - thirtyPercent

        print(String(format: "\n🎯 Thresholds:"))
        print(String(format: "   Mean RR: %.1f ms", meanRR))
        print(String(format: "   30%% of mean: %.1f ms", thirtyPercent))
        print(String(format: "   Upper: %.1f ms", upperThreshold))
        print(String(format: "   Lower: %.1f ms", lowerThreshold))

        print(String(format: "\n🔍 Binary Peaklist:"))
        for (i, valid) in binaryPeaklist.enumerated() {
            print(String(format: "   Peak[%2d]: %.0f", i, valid))
        }

        // Expected results based on Python analysis
        // HeartOO ground truth: [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        let expectedBinary: [Double] = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        print(String(format: "\n✅ Expected vs Actual:"))
        for i in 0..<min(expectedBinary.count, binaryPeaklist.count) {
            let match = abs(expectedBinary[i] - binaryPeaklist[i]) < 0.1 ? "✅" : "❌"
            print(String(format: "   Peak[%2d]: Expected %.0f, Got %.0f %@", i, expectedBinary[i], binaryPeaklist[i], match))
        }

        // Test manual validation
        print(String(format: "\n🧮 Manual Validation Logic:"))
        var manualBinary: [Double] = Array(repeating: 1.0, count: rrIntervals.count + 1)
        for i in 0..<rrIntervals.count {
            let isInvalid = rrIntervals[i] <= lowerThreshold || rrIntervals[i] >= upperThreshold
            if isInvalid {
                manualBinary[i + 1] = 0.0
                print(String(format: "   RR[%d] = %.1f -> Mark Peak[%d] as invalid", i, rrIntervals[i], i + 1))
            }
        }

        print(String(format: "\n🎯 Manual Binary: %@", manualBinary.prefix(11).map { String(format: "%.0f", $0) }.joined(separator: ", ")))
        print(String(format: "   Actual Binary: %@", binaryPeaklist.prefix(11).map { String(format: "%.0f", $0) }.joined(separator: ", ")))

        // Assert first few key values match expected
        XCTAssertEqual(binaryPeaklist[0], 1.0, "First peak should be valid")
        XCTAssertEqual(binaryPeaklist[1], 0.0, "Second peak should be invalid (RR[0] too small)")
        XCTAssertEqual(binaryPeaklist[2], 0.0, "Third peak should be invalid (RR[1] too small)")
    }
}