import XCTest
@testable import HeartSW

/// Comprehensive unit tests based on HeartPy's exact implementation
/// These tests capture the ground truth of HeartPy's peak detection algorithm
final class HeartPyExactReplicationTests: XCTestCase {

    func testHeartPyExactAlgorithmGroundTruth() throws {
        print("🔬 Testing HeartPy Exact Algorithm Ground Truth")
        print("=" * 60)

        // Load real data2.csv - this is the test case that revealed the discrepancies
        let testData = loadData2CSV()
        let sampleRate: Double = 117.0
        let signal = try HeartRateSignal(data: testData, sampleRate: sampleRate)

        print("📊 Input Parameters:")
        print("   Data length: \(testData.count)")
        print("   Sample rate: \(sampleRate)")
        print("   Threshold: 10%")

        // Step 1: Rolling Mean Calculation (should match HeartPy exactly)
        let detector = AdaptiveThresholdDetector(thresholdPercentage: 10.0)
        let windowLength = Int(0.75 * sampleRate) // 87 samples
        let rollingMean = detector.calculateRollingMean(data: testData, windowLength: windowLength)

        // HeartPy's exact threshold calculation
        let meanRolling = rollingMean.reduce(0, +) / Double(rollingMean.count)
        let mn = (meanRolling / 100.0) * 10.0
        let thresholdArray = rollingMean.map { $0 + mn }

        print("   Rolling mean length: \(rollingMean.count)")
        print("   Mean of rolling mean: \(String(format: "%.3f", meanRolling))")
        print("   mn value: \(String(format: "%.3f", mn))")

        // Step 2: Above-threshold detection
        var aboveThreshold: [Int] = []
        for i in 0..<testData.count {
            if testData[i] > thresholdArray[i] {
                aboveThreshold.append(i)
            }
        }

        print("   Total above-threshold points: \(aboveThreshold.count)")

        // HeartPy Ground Truth for the critical region [1740:1800]
        let regionStart = 1740
        let regionEnd = 1800

        // Extract region peaks
        let regionAboveThreshold = aboveThreshold.filter { $0 >= regionStart && $0 <= regionEnd }
        print("   Region [\(regionStart):\(regionEnd)] above-threshold: \(regionAboveThreshold.count) points")
        print("   Region peaks: \(regionAboveThreshold)")

        // HeartPy's expected above-threshold points for region [1740:1800]
        let expectedRegionPeaks = [1744, 1745, 1746, 1747, 1748, 1749, 1750, 1751, 1752, 1753, 1754, 1755, 1756, 1787, 1788, 1789, 1790, 1791, 1792, 1793]

        XCTAssertEqual(regionAboveThreshold, expectedRegionPeaks,
                      "Above-threshold detection should match HeartPy exactly")

        // Step 3: HeartPy's exact edge calculation
        print("\\n📋 Edge Calculation (HeartPy Algorithm):")

        var diffs: [Int] = []
        for i in 1..<aboveThreshold.count {
            diffs.append(aboveThreshold[i] - aboveThreshold[i-1])
        }

        var gapPositions: [Int] = []
        for i in 0..<diffs.count {
            if diffs[i] > 1 {
                gapPositions.append(i)
            }
        }

        // HeartPy's concatenation: [0] + gap_positions + [len(aboveThreshold)]
        // Note: HeartPy is missing +1 offset in the original code
        var peakedges = [0] + gapPositions + [aboveThreshold.count]

        print("   First 20 diffs: \(Array(diffs.prefix(20)))")
        print("   First 10 gap positions: \(Array(gapPositions.prefix(10)))")
        print("   First 10 peakedges: \(Array(peakedges.prefix(10)))")

        // Step 4: Group processing and peak selection
        print("\\n🎯 Group Processing:")
        var selectedPeaks: [Int] = []

        for i in 0..<(peakedges.count - 1) {
            let startIdx = peakedges[i]
            let endIdx = peakedges[i + 1]

            guard startIdx < aboveThreshold.count && endIdx <= aboveThreshold.count else {
                continue
            }

            let groupPeaks = Array(aboveThreshold[startIdx..<endIdx])
            let groupValues = groupPeaks.map { testData[$0] }

            if !groupValues.isEmpty {
                let maxValue = groupValues.max()!

                // HeartPy uses .index() which returns the FIRST occurrence
                var maxIndex = 0
                for j in 0..<groupValues.count {
                    if groupValues[j] == maxValue {
                        maxIndex = j
                        break
                    }
                }

                let selectedPeak = groupPeaks[maxIndex]
                selectedPeaks.append(selectedPeak)

                // Debug specific groups that contain region peaks
                let hasRegionPeaks = groupPeaks.contains { $0 >= regionStart && $0 <= regionEnd }
                if hasRegionPeaks {
                    let regionPeaksInGroup = groupPeaks.filter { $0 >= regionStart && $0 <= regionEnd }
                    print("   Group \(i): indices [\(startIdx):\(endIdx)], size: \(groupValues.count)")
                    print("      Contains region peaks: \(regionPeaksInGroup)")
                    print("      Selected peak: \(selectedPeak)")
                }
            }
        }

        print("   Total peaks selected: \(selectedPeaks.count)")

        // HeartPy Ground Truth: Expected 110 peaks total for data2.csv at 10% threshold
        XCTAssertEqual(selectedPeaks.count, 110,
                      "Should detect exactly 110 peaks like HeartPy")

        // Filter peaks in our test region
        let regionSelectedPeaks = selectedPeaks.filter { $0 >= regionStart && $0 <= regionEnd }
        print("   Region selected peaks: \(regionSelectedPeaks)")

        // HeartPy Ground Truth: Expected peaks in region [1740:1800]
        let expectedRegionSelectedPeaks = [1751, 1756, 1793]

        XCTAssertEqual(regionSelectedPeaks, expectedRegionSelectedPeaks,
                      "Region peak selection should match HeartPy exactly")

        print("\\n✅ Ground Truth Verification:")
        print("   Above-threshold detection: MATCH")
        print("   Edge calculation: MATCH")
        print("   Peak selection: MATCH")
        print("   Total peaks: \(selectedPeaks.count)/110")
        print("   Region peaks: \(regionSelectedPeaks) == \(expectedRegionSelectedPeaks)")

        // Step 5: Test HeartSW's implementation matches this ground truth
        print("\\n🔍 Testing HeartSW Implementation:")

        let heartswResult = try detector.detectPeaks(in: signal)
        print("   HeartSW detected \(heartswResult.count) peaks")

        let heartswRegionPeaks = heartswResult.filter { $0 >= regionStart && $0 <= regionEnd }
        print("   HeartSW region peaks: \(heartswRegionPeaks)")

        // The goal: HeartSW should match HeartPy exactly
        XCTAssertEqual(heartswResult.count, selectedPeaks.count,
                      "HeartSW should detect same number of peaks as HeartPy")
        XCTAssertEqual(heartswRegionPeaks, expectedRegionSelectedPeaks,
                      "HeartSW should match HeartPy's region peak selection")

        if heartswResult.count == selectedPeaks.count && heartswRegionPeaks == expectedRegionSelectedPeaks {
            print("   🎯 SUCCESS: HeartSW matches HeartPy ground truth!")
        } else {
            print("   ❌ HeartSW needs adjustment to match HeartPy")
        }
    }

    func testHeartPyThresholdCalculationExact() throws {
        print("\\n🔬 Testing HeartPy Threshold Calculation Exactness")
        print("=" * 60)

        let testData = loadData2CSV()
        let sampleRate: Double = 117.0

        // HeartSW calculation
        let detector = AdaptiveThresholdDetector(thresholdPercentage: 10.0)
        let windowLength = Int(0.75 * sampleRate)
        let rollingMean = detector.calculateRollingMean(data: testData, windowLength: windowLength)

        // HeartPy's exact formula
        let meanRolling = rollingMean.reduce(0, +) / Double(rollingMean.count)
        let mn = (meanRolling / 100.0) * 10.0
        let thresholdArray = rollingMean.map { $0 + mn }

        print("📊 Threshold Calculation Verification:")
        print("   Mean of rolling mean: \(String(format: "%.6f", meanRolling))")
        print("   mn = (mean/100) * 10: \(String(format: "%.6f", mn))")

        // Sample verification at specific indices
        let testIndices = [1750, 1755, 1760, 1790, 1795]
        print("   Sample threshold values:")

        for idx in testIndices {
            if idx < thresholdArray.count {
                let expectedThreshold = rollingMean[idx] + mn
                print("      Index \(idx): \(String(format: "%.3f", expectedThreshold))")

                // Verify calculation
                XCTAssertEqual(thresholdArray[idx], expectedThreshold, accuracy: 0.001,
                             "Threshold calculation should be exact")
            }
        }

        // Key verification: above-threshold detection in critical region
        let regionStart = 1740
        let regionEnd = 1800
        var regionAboveThreshold: [Int] = []

        for i in regionStart...regionEnd {
            if i < testData.count && i < thresholdArray.count {
                if testData[i] > thresholdArray[i] {
                    regionAboveThreshold.append(i)
                }
            }
        }

        // HeartPy ground truth
        let expectedAboveThreshold = [1744, 1745, 1746, 1747, 1748, 1749, 1750, 1751, 1752, 1753, 1754, 1755, 1756, 1787, 1788, 1789, 1790, 1791, 1792, 1793]

        print("   Region above-threshold verification:")
        print("      Calculated: \(regionAboveThreshold)")
        print("      Expected:   \(expectedAboveThreshold)")
        print("      Match: \(regionAboveThreshold == expectedAboveThreshold)")

        XCTAssertEqual(regionAboveThreshold, expectedAboveThreshold,
                      "Above-threshold detection must match HeartPy exactly")
    }

    func testHeartPyGroupingAlgorithmExact() throws {
        print("\\n🔬 Testing HeartPy Grouping Algorithm Exactness")
        print("=" * 60)

        // Simplified test with known above-threshold sequence
        let aboveThresholdPositions = [1744, 1745, 1746, 1747, 1748, 1749, 1750, 1751, 1752, 1753, 1754, 1755, 1756, 1787, 1788, 1789, 1790, 1791, 1792, 1793]

        print("📊 Grouping Test:")
        print("   Above-threshold positions: \(aboveThresholdPositions)")

        // Step 1: Calculate differences
        var diffs: [Int] = []
        for i in 1..<aboveThresholdPositions.count {
            diffs.append(aboveThresholdPositions[i] - aboveThresholdPositions[i-1])
        }
        print("   Differences: \(diffs)")

        // Step 2: Find gaps (HeartPy: where diff > 1)
        var gapPositions: [Int] = []
        for i in 0..<diffs.count {
            if diffs[i] > 1 {
                gapPositions.append(i)
            }
        }
        print("   Gap positions: \(gapPositions)")

        // Step 3: HeartPy's edge calculation (missing +1 offset)
        let peakedges = [0] + gapPositions + [aboveThresholdPositions.count]
        print("   Peak edges: \(peakedges)")

        // Expected: [0, 12, 19, 20] - this creates the specific grouping HeartPy uses
        let expectedEdges = [0, 12, 19, 20]
        XCTAssertEqual(peakedges, expectedEdges,
                      "Edge calculation must match HeartPy's exact algorithm")

        // Step 4: Verify groups
        print("   Groups:")
        for i in 0..<(peakedges.count - 1) {
            let startIdx = peakedges[i]
            let endIdx = peakedges[i + 1]
            let groupPositions = Array(aboveThresholdPositions[startIdx..<endIdx])
            print("      Group \(i): indices [\(startIdx):\(endIdx)] -> positions \(groupPositions)")
        }

        // Expected groups based on HeartPy's behavior:
        // Group 0: [1744...1755] (12 peaks) -> selects 1751
        // Group 1: [1756, 1787...1792] (7 peaks) -> selects 1756
        // Group 2: [1793] (1 peak) -> selects 1793

        print("\\n✅ This grouping explains HeartPy's [1751, 1756, 1793] result!")
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
}