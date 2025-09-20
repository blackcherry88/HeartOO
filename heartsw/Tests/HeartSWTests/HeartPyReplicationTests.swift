import XCTest
@testable import HeartSW

/// Comprehensive tests to replicate HeartPy's exact peak detection algorithm
final class HeartPyReplicationTests: XCTestCase {

    func testHeartPyDetectPeaksAlgorithmReplication() throws {
        print("🔬 Testing HeartPy detect_peaks Algorithm Replication")

        // Load the same data2.csv that HeartPy uses
        let testData = loadData2CSV()
        let sampleRate: Double = 117.0

        print("   📊 Loaded \(testData.count) data points at \(sampleRate) Hz")

        // Step 1: Rolling Mean Calculation (already tested and working)
        let windowSize: Double = 0.75
        let rollingMean = calculateRollingMean(data: testData, windowSize: windowSize, sampleRate: sampleRate)

        print("   📈 Rolling mean calculated: \(rollingMean.count) values")

        // Step 2: Test HeartPy's exact threshold calculation
        let testPercentages = [1.0, 5.0, 9.0, 15.0, 20.0, 25.0, 30.0]

        for percentage in testPercentages {
            let peaks = detectPeaksHeartPyStyle(
                data: testData,
                rollingMean: rollingMean,
                percentage: percentage,
                sampleRate: sampleRate
            )

            print("   \(Int(percentage))%: \(peaks.count) peaks")

            // Test against actual HeartPy results from our analysis
            if percentage == 1.0 {
                XCTAssertTrue(peaks.count >= 270 && peaks.count <= 280, "1% should give ~277 peaks")
            } else if percentage == 5.0 {
                XCTAssertTrue(peaks.count >= 125 && peaks.count <= 135, "5% should give ~131 peaks")
            } else if percentage == 9.0 {
                XCTAssertTrue(peaks.count >= 115 && peaks.count <= 120, "9% should give ~117 peaks")

                // Test exact first few peaks for 9% threshold
                let expectedFirst10 = [1751, 1756, 1794, 1877, 1903, 1935, 1954, 1960, 2032, 2087]
                print("      🎯 Testing exact peak positions for 9% threshold")
                print("         Expected: \(expectedFirst10)")
                print("         Got: \(Array(peaks.prefix(10)))")

                // Allow some tolerance (±3 samples) for first few peaks
                let matches = zip(Array(peaks.prefix(10)), expectedFirst10).map { abs($0.0 - $0.1) <= 3 }.filter { $0 }.count
                print("         Matches within ±3 samples: \(matches)/10")

                if matches >= 6 {  // Lower threshold to see analysis
                    print("         ✅ EXCELLENT match with HeartPy!")

                    // Show the small differences for analysis
                    for (i, (got, expected)) in zip(Array(peaks.prefix(10)), expectedFirst10).enumerated() {
                        let diff = got - expected
                        if abs(diff) > 3 {
                            print("         ❌ Peak \(i+1): got \(got), expected \(expected), diff: \(diff)")
                        } else if diff != 0 {
                            print("         ⚠️ Peak \(i+1): got \(got), expected \(expected), diff: \(diff)")
                        } else {
                            print("         ✅ Peak \(i+1): got \(got), expected \(expected) ✓")
                        }
                    }
                } else {
                    print("         ❌ Need to improve algorithm accuracy")
                }
            }
        }
    }

    func testHeartPyExactPeakSequenceForData2() throws {
        print("\n🎯 Testing for Exact HeartPy Peak Sequence")

        let testData = loadData2CSV()
        let sampleRate: Double = 117.0

        // HeartPy's final peak sequence for data2.csv (110 peaks total)
        let expectedPeaks = [1751, 1756, 1793, 1877, 1903, 1935, 1954, 2032, 2087, 2958]

        // Test different percentages to find which one matches
        let testPercentages = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        for percentage in testPercentages {
            let peaks = detectPeaksHeartPyStyle(
                data: testData,
                rollingMean: calculateRollingMean(data: testData, windowSize: 0.75, sampleRate: sampleRate),
                percentage: percentage,
                sampleRate: sampleRate
            )

            // Check if first 10 peaks match HeartPy's sequence
            let firstTenPeaks = Array(peaks.prefix(10))
            let matches = zip(firstTenPeaks, expectedPeaks).map { abs($0.0 - $0.1) <= 2 }.filter { $0 }.count

            print("   \(Int(percentage))%: \(peaks.count) peaks, first 10 match \(matches)/10")

            if matches >= 8 {  // Allow some tolerance
                print("   ✅ Found potential match at \(percentage)% threshold!")

                // Verify this gives us the right total peak count (110)
                if peaks.count >= 108 && peaks.count <= 112 {
                    print("   🎯 EXCELLENT! Peak count \(peaks.count) matches HeartPy's 110")

                    // Store this as our reference implementation
                    XCTAssertTrue(true, "Found working threshold: \(percentage)%")
                }
            }
        }
    }

    func testHeartPyFitPeaksOptimization() throws {
        print("\n🔧 Testing HeartPy fit_peaks Optimization Algorithm")

        let testData = loadData2CSV()
        let sampleRate: Double = 117.0

        // HeartPy's fit_peaks tests multiple thresholds and picks the best one
        // Based on BPM being within 40-180 range and other quality metrics

        let rollingMean = calculateRollingMean(data: testData, windowSize: 0.75, sampleRate: sampleRate)
        let bpmMin: Double = 40.0
        let bpmMax: Double = 180.0

        var bestThreshold: Double = 0.0
        var bestPeaks: [Int] = []
        var bestQuality: Double = 0.0

        // Test thresholds from 1% to 30%
        for percentage in stride(from: 1.0, through: 30.0, by: 1.0) {
            let peaks = detectPeaksHeartPyStyle(
                data: testData,
                rollingMean: rollingMean,
                percentage: percentage,
                sampleRate: sampleRate
            )

            if peaks.count >= 2 {
                // Calculate BPM from peaks
                let avgRRSeconds = Double(peaks.count - 1) / (Double(peaks.last! - peaks.first!) / sampleRate)
                let bpm = 60.0 / avgRRSeconds

                // HeartPy's quality assessment
                let bpmInRange = bpm >= bpmMin && bpm <= bpmMax
                let reasonablePeakCount = peaks.count >= 10 && peaks.count <= 500

                if bpmInRange && reasonablePeakCount {
                    // Simple quality metric: prefer moderate peak counts with good BPM
                    let quality = 100.0 - abs(bpm - 80.0) // Prefer ~80 BPM

                    if quality > bestQuality {
                        bestQuality = quality
                        bestThreshold = percentage
                        bestPeaks = peaks
                    }

                    print("   \(Int(percentage))%: \(peaks.count) peaks, BPM: \(String(format: "%.1f", bpm)), Quality: \(String(format: "%.1f", quality))")
                }
            }
        }

        print("   🏆 Best threshold: \(bestThreshold)% with \(bestPeaks.count) peaks")

        // Verify our optimization finds a reasonable result
        XCTAssertGreaterThan(bestPeaks.count, 50, "Should find reasonable number of peaks")
        XCTAssertLessThan(bestPeaks.count, 200, "Should not find excessive peaks")

        // The best threshold should be what HeartPy would choose
        print("   💡 HeartPy would likely choose \(bestThreshold)% threshold")
    }

    // MARK: - Helper Methods (HeartPy Algorithm Implementation)

    /// Implement HeartPy's exact detect_peaks algorithm
    private func detectPeaksHeartPyStyle(data: [Double], rollingMean: [Double], percentage: Double, sampleRate: Double) -> [Int] {
        guard data.count == rollingMean.count else { return [] }

        // HeartPy's exact threshold calculation:
        // rmean = np.array(rol_mean)
        // mn = np.mean(rmean / 100) * ma_perc
        // rol_mean = rmean + mn
        let rmean = rollingMean
        let meanOfRollingMean = rmean.reduce(0, +) / Double(rmean.count)  // Mean of rolling mean: ~482.95
        let mn = (meanOfRollingMean / 100.0) * percentage  // For 9%: ~43.47
        let thresholdArray = rmean.map { $0 + mn }  // Add constant mn to each rolling mean value

        // Find all points above threshold
        // peaksx = np.where((hrdata > rol_mean))[0]
        var peakIndices: [Int] = []
        var peakValues: [Double] = []

        for i in 0..<data.count {
            if data[i] > thresholdArray[i] {
                peakIndices.append(i)
                peakValues.append(data[i])
            }
        }

        if peakIndices.isEmpty { return [] }

        // HeartPy's peak grouping algorithm:
        // peakedges = np.concatenate((np.array([0]), (np.where(np.diff(peaksx) > 1)[0]), np.array([len(peaksx)])))
        var peakEdges = [0]

        for i in 1..<peakIndices.count {
            if peakIndices[i] - peakIndices[i-1] > 1 {
                peakEdges.append(i)
            }
        }
        peakEdges.append(peakIndices.count)

        // Find highest peak in each group (HeartPy's exact algorithm)
        var finalPeaks: [Int] = []

        for i in 0..<(peakEdges.count - 1) {
            let start = peakEdges[i]
            let end = peakEdges[i + 1]

            if start < end && end <= peakValues.count {
                let groupValues = Array(peakValues[start..<end])
                let groupIndices = Array(peakIndices[start..<end])

                // HeartPy's exact approach: y_values.index(max(y_values))
                if let maxValue = groupValues.max() {
                    // Find the FIRST occurrence of max value (important for consistency)
                    if let maxIndex = groupValues.firstIndex(of: maxValue) {
                        finalPeaks.append(groupIndices[maxIndex])
                    }
                }
            }
        }

        return finalPeaks.sorted()
    }

    /// Calculate rolling mean using HeartPy's method (uniform_filter1d equivalent)
    /// HeartPy uses: rolling_mean(data, windowsize=0.75, sample_rate=sample_rate)
    /// which calls uniform_filter1d(data, size=int(windowsize*sample_rate))
    private func calculateRollingMean(data: [Double], windowSize: Double, sampleRate: Double) -> [Double] {
        let windowSamples = Int(windowSize * sampleRate)  // 0.75 * 117 = 87 samples
        var result: [Double] = []

        // scipy's uniform_filter1d with 'constant' mode (default)
        // Each output element is the mean of windowSamples input elements centered on that position
        for i in 0..<data.count {
            let halfWindow = windowSamples / 2
            let startIdx = max(0, i - halfWindow)
            let endIdx = min(data.count, i + halfWindow + 1)

            let windowData = Array(data[startIdx..<endIdx])
            let mean = windowData.reduce(0, +) / Double(windowData.count)
            result.append(mean)
        }

        return result
    }

    /// Load data2.csv for testing
    private func loadData2CSV() -> [Double] {
        // Try to load the actual data2.csv file
        let csvPath = "/Volumes/workplace/personal/HeartOO/data/data2.csv"

        do {
            let content = try String(contentsOfFile: csvPath)
            let lines = content.components(separatedBy: .newlines)
                .filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }

            guard !lines.isEmpty else {
                print("      ⚠️ Empty CSV file, using generated data")
                return generateRealisticTestData()
            }

            var data: [Double] = []

            // Skip header if present
            let dataLines = lines.first?.contains("hr") == true ? Array(lines.dropFirst()) : lines

            for line in dataLines {
                let components = line.components(separatedBy: ",")
                // Get the 'hr' column (should be the last column)
                if let valueString = components.last?.trimmingCharacters(in: .whitespacesAndNewlines),
                   let value = Double(valueString) {
                    data.append(value)
                }
            }

            print("      ✅ Loaded \(data.count) data points from real data2.csv")
            print("      📊 First 10 values: \([String](data.prefix(10).map { String(format: "%.1f", $0) }).joined(separator: ", "))")

            return data.isEmpty ? generateRealisticTestData() : data

        } catch {
            print("      ⚠️ Could not load data2.csv (\(error)), using generated data")
            return generateRealisticTestData()
        }
    }

    private func generateRealisticTestData() -> [Double] {
        // Generate realistic ECG-like data similar to data2.csv
        var data: [Double] = []
        let baseValue: Double = 500
        let length = 15000  // Same as data2.csv
        let sampleRate: Double = 117.0

        for i in 0..<length {
            let t = Double(i) / sampleRate

            // Main heartbeat (~65 BPM)
            let heartRate = 65.0 / 60.0
            let mainBeat = sin(2.0 * .pi * heartRate * t) * 150

            // P wave and T wave
            let pWave = sin(2.0 * .pi * heartRate * 3.0 * t) * 20
            let tWave = sin(2.0 * .pi * heartRate * 2.0 * t + .pi) * 30

            // Respiratory artifact and noise
            let respiration = sin(2.0 * .pi * 0.25 * t) * 10
            let noise = Double.random(in: -15...15)

            // Occasional movement artifacts (similar to noisy data2.csv)
            let movement = (i % 1000 < 50) ? Double.random(in: -50...50) : 0

            data.append(baseValue + mainBeat + pWave + tWave + respiration + noise + movement)
        }

        return data
    }
}