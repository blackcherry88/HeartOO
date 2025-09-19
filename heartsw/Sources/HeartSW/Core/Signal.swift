// HeartSW - Swift Heart Rate Analysis
// Core signal types and protocols

import Foundation

/// Base protocol for time series signals
public protocol Signal {
    associatedtype DataType: FloatingPoint & Codable

    var data: [DataType] { get }
    var sampleRate: Double { get }
    var metadata: [String: String] { get }
    var duration: TimeInterval { get }

    func slice(from startTime: TimeInterval, to endTime: TimeInterval) throws -> Self
    func timeAxis() -> [TimeInterval]
}

/// Heart rate signal implementation
public struct HeartRateSignal: Signal, Codable {
    public typealias DataType = Double

    public let data: [Double]
    public let sampleRate: Double
    public let metadata: [String: String]

    private var _peaks: [Int]?
    private var _rrIntervals: [Double]?

    /// Signal duration in seconds
    public var duration: TimeInterval {
        Double(data.count) / sampleRate
    }

    /// Detected peaks (sample indices)
    public var peaks: [Int]? {
        return _peaks
    }

    /// RR intervals in milliseconds
    public var rrIntervals: [Double]? {
        if _rrIntervals == nil && _peaks != nil {
            return calculateRRIntervals()
        }
        return _rrIntervals
    }

    /// Average heart rate in BPM
    public var heartRate: Double? {
        guard let intervals = rrIntervals, !intervals.isEmpty else { return nil }
        return 60000.0 / (intervals.reduce(0, +) / Double(intervals.count))
    }

    /// Initialize a heart rate signal
    ///
    /// Example usage:
    /// ```swift
    /// let signal = try HeartRateSignal(data: [1.0, 2.0, 3.0, 2.0, 1.0],
    ///                                  sampleRate: 100.0)
    /// assert(signal.duration == 0.05) // 5 samples at 100 Hz = 0.05 seconds
    /// assert(signal.data.count == 5)
    /// ```
    public init(data: [Double],
                sampleRate: Double,
                metadata: [String: String] = [:]) throws {
        try Validation.validateSampleRate(sampleRate)
        try Validation.validateDataCount(data)

        self.data = data
        self.sampleRate = sampleRate
        self.metadata = metadata
        self._peaks = nil
        self._rrIntervals = nil
    }

    /// Set detected peaks
    ///
    /// Example usage:
    /// ```swift
    /// var signal = try HeartRateSignal(data: [1.0, 3.0, 1.0, 4.0, 1.0], sampleRate: 100.0)
    /// signal.setPeaks([1, 3]) // Peak at indices 1 and 3
    /// assert(signal.peaks == [1, 3])
    /// assert(signal.rrIntervals?.count == 1) // One RR interval between peaks
    /// ```
    public mutating func setPeaks(_ peaks: [Int]) {
        self._peaks = peaks
        self._rrIntervals = nil // Reset cached intervals
    }

    /// Get time slice of signal
    ///
    /// Example usage:
    /// ```swift
    /// let signal = try HeartRateSignal(data: Array(0...99).map(Double.init), sampleRate: 100.0)
    /// let slice = try signal.slice(from: 0.1, to: 0.2) // 0.1s to 0.2s
    /// assert(slice.data.count == 10) // 0.1s * 100Hz = 10 samples
    /// ```
    public func slice(from startTime: TimeInterval, to endTime: TimeInterval) throws -> HeartRateSignal {
        try Validation.validateTimeRange(start: startTime, end: endTime, duration: duration)

        let startIndex = Int(startTime * sampleRate)
        let endIndex = Int(endTime * sampleRate)

        let slicedData = Array(data[startIndex..<min(endIndex, data.count)])
        return try HeartRateSignal(data: slicedData, sampleRate: sampleRate, metadata: metadata)
    }

    /// Get time axis for the signal
    ///
    /// Example usage:
    /// ```swift
    /// let signal = try HeartRateSignal(data: [1.0, 2.0, 3.0], sampleRate: 2.0)
    /// let timeAxis = signal.timeAxis()
    /// assert(timeAxis == [0.0, 0.5, 1.0]) // Time points at 2 Hz
    /// ```
    public func timeAxis() -> [TimeInterval] {
        return (0..<data.count).map { Double($0) / sampleRate }
    }

    /// Scale signal data to specified range
    ///
    /// Example usage:
    /// ```swift
    /// let signal = try HeartRateSignal(data: [0.0, 5.0, 10.0], sampleRate: 1.0)
    /// let scaled = signal.scaled(to: 0.0...1.0)
    /// assert(scaled.data == [0.0, 0.5, 1.0])
    /// ```
    public func scaled(to range: ClosedRange<Double>) -> HeartRateSignal {
        let minVal = data.min() ?? 0.0
        let maxVal = data.max() ?? 1.0
        let dataRange = maxVal - minVal

        guard dataRange > 0 else {
            // If all values are the same, return middle of target range
            let midpoint = (range.lowerBound + range.upperBound) / 2
            let scaledData = Array(repeating: midpoint, count: data.count)
            return try! HeartRateSignal(data: scaledData, sampleRate: sampleRate, metadata: metadata)
        }

        let targetRange = range.upperBound - range.lowerBound
        let scaledData = data.map { value in
            ((value - minVal) / dataRange) * targetRange + range.lowerBound
        }

        return try! HeartRateSignal(data: scaledData, sampleRate: sampleRate, metadata: metadata)
    }

    // MARK: - Private Methods

    private func calculateRRIntervals() -> [Double]? {
        guard let peaks = _peaks, peaks.count > 1 else { return nil }

        return zip(peaks, peaks.dropFirst()).map { current, next in
            Double(next - current) / sampleRate * 1000.0 // Convert to milliseconds
        }
    }

    // MARK: - Codable

    private enum CodingKeys: String, CodingKey {
        case data, sampleRate, metadata, _peaks, _rrIntervals
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        data = try container.decode([Double].self, forKey: .data)
        sampleRate = try container.decode(Double.self, forKey: .sampleRate)
        metadata = try container.decode([String: String].self, forKey: .metadata)
        _peaks = try container.decodeIfPresent([Int].self, forKey: ._peaks)
        _rrIntervals = try container.decodeIfPresent([Double].self, forKey: ._rrIntervals)

        // Validate after decoding
        try Validation.validateSampleRate(sampleRate)
        try Validation.validateDataCount(data)
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(data, forKey: .data)
        try container.encode(sampleRate, forKey: .sampleRate)
        try container.encode(metadata, forKey: .metadata)
        try container.encodeIfPresent(_peaks, forKey: ._peaks)
        try container.encodeIfPresent(_rrIntervals, forKey: ._rrIntervals)
    }
}