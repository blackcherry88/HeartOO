// HeartSW - Swift Heart Rate Analysis
// Time domain HRV analysis

import Foundation
import Numerics

/// Time domain HRV analyzer
public struct TimeDomainAnalyzer: HeartRateProcessor {
    public typealias InputType = HeartRateSignal
    public typealias OutputType = [String: Double]

    public let name = "TimeDomainAnalyzer"

    public var parameters: [String: Any] {
        return [:]
    }

    public init() {}

    /// Process signal and calculate time domain measures
    ///
    /// Example usage:
    /// ```swift
    /// var signal = try HeartRateSignal(data: ecgData, sampleRate: 100.0)
    /// signal.setPeaks([100, 180, 260, 340, 420]) // 5 peaks, 4 RR intervals
    ///
    /// var result = AnalysisResult()
    /// let analyzer = TimeDomainAnalyzer()
    /// let measures = try analyzer.process(signal, result: &result)
    ///
    /// // Verify we get expected measures
    /// assert(measures["bpm"] != nil)
    /// assert(measures["sdnn"] != nil)
    /// assert(measures["rmssd"] != nil)
    /// ```
    public func process(_ signal: HeartRateSignal, result: inout AnalysisResult) throws -> [String: Double] {
        guard let intervals = signal.rrIntervals, !intervals.isEmpty else {
            throw HRVError.noPeaksDetected
        }

        let measures = try calculateMeasures(from: intervals)

        // Store in result
        for (key, value) in measures {
            result.setMeasure(key, value: value)
        }

        return measures
    }

    /// Calculate time domain measures from RR intervals
    ///
    /// Example with known values:
    /// ```swift
    /// let analyzer = TimeDomainAnalyzer()
    /// // RR intervals: 800, 850, 820, 790, 830 ms (mean = 818 ms)
    /// let intervals = [800.0, 850.0, 820.0, 790.0, 830.0]
    /// let measures = try analyzer.calculateMeasures(from: intervals)
    ///
    /// // BPM should be approximately 60000/818 ≈ 73.35
    /// assert(abs(measures["bpm"]! - 73.35) < 0.1)
    ///
    /// // SDNN (standard deviation) for this data ≈ 23.45
    /// assert(abs(measures["sdnn"]! - 23.45) < 1.0)
    ///
    /// // RMSSD from successive differences
    /// // Differences: 50, -30, -30, 40 → RMSSD ≈ 39.05
    /// assert(abs(measures["rmssd"]! - 39.05) < 1.0)
    /// ```
    public func calculateMeasures(from intervals: [Double]) throws -> [String: Double] {
        guard !intervals.isEmpty else {
            throw HRVError.insufficientData(0)
        }

        let count = Double(intervals.count)
        let mean = intervals.reduce(0, +) / count

        // Basic measures
        let bpm = 60000.0 / mean
        let ibi = mean

        // Standard deviation of NN intervals (SDNN)
        let variance = intervals.map { pow($0 - mean, 2) }.reduce(0, +) / (count - 1)
        let sdnn = sqrt(variance)

        // Successive differences for RMSSD, pNN20, pNN50
        let successiveDifferences = zip(intervals, intervals.dropFirst()).map { abs($1 - $0) }

        // Root mean square of successive differences (RMSSD)
        let rmssd: Double
        if successiveDifferences.isEmpty {
            rmssd = 0.0
        } else {
            let sumSquaredDiffs = successiveDifferences.map { pow($0, 2) }.reduce(0, +)
            rmssd = sqrt(sumSquaredDiffs / Double(successiveDifferences.count))
        }

        // Standard deviation of successive differences (SDSD)
        let sdsd: Double
        if successiveDifferences.count > 1 {
            let diffMean = successiveDifferences.reduce(0, +) / Double(successiveDifferences.count)
            let diffVariance = successiveDifferences.map { pow($0 - diffMean, 2) }.reduce(0, +) /
                             Double(successiveDifferences.count - 1)
            sdsd = sqrt(diffVariance)
        } else {
            sdsd = 0.0
        }

        // pNN20: percentage of successive RR intervals that differ by more than 20ms
        let pnn20: Double
        if !successiveDifferences.isEmpty {
            let count20 = successiveDifferences.filter { $0 > 20.0 }.count
            pnn20 = Double(count20) / Double(successiveDifferences.count) * 100.0
        } else {
            pnn20 = 0.0
        }

        // pNN50: percentage of successive RR intervals that differ by more than 50ms
        let pnn50: Double
        if !successiveDifferences.isEmpty {
            let count50 = successiveDifferences.filter { $0 > 50.0 }.count
            pnn50 = Double(count50) / Double(successiveDifferences.count) * 100.0
        } else {
            pnn50 = 0.0
        }

        // Median absolute deviation (HR_MAD)
        let sortedIntervals = intervals.sorted()
        let median = sortedIntervals.count % 2 == 0 ?
            (sortedIntervals[sortedIntervals.count / 2 - 1] + sortedIntervals[sortedIntervals.count / 2]) / 2.0 :
            sortedIntervals[sortedIntervals.count / 2]

        let deviations = intervals.map { abs($0 - median) }.sorted()
        let hrMad = deviations.count % 2 == 0 ?
            (deviations[deviations.count / 2 - 1] + deviations[deviations.count / 2]) / 2.0 :
            deviations[deviations.count / 2]

        return [
            "bpm": bpm,
            "ibi": ibi,
            "sdnn": sdnn,
            "sdsd": sdsd,
            "rmssd": rmssd,
            "pnn20": pnn20,
            "pnn50": pnn50,
            "hr_mad": hrMad
        ]
    }
}

// MARK: - Mathematical utilities

private extension Double {
    /// Square root function using Swift Numerics
    func squareRoot() -> Double {
        return Foundation.sqrt(self)
    }
}