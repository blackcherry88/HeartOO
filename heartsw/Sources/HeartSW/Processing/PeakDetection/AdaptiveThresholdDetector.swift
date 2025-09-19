// HeartSW - Swift Heart Rate Analysis
// Adaptive threshold peak detection

import Foundation

/// Adaptive threshold peak detector
public struct AdaptiveThresholdDetector: HeartRateProcessor {
    public typealias InputType = HeartRateSignal
    public typealias OutputType = [Int]

    public let name = "AdaptiveThresholdDetector"
    public let minBPM: Double
    public let maxBPM: Double
    public let windowSize: Double

    public var parameters: [String: Any] {
        return [
            "minBPM": minBPM,
            "maxBPM": maxBPM,
            "windowSize": windowSize
        ]
    }

    /// Initialize adaptive threshold detector
    ///
    /// Example usage:
    /// ```swift
    /// let detector = AdaptiveThresholdDetector(minBPM: 40, maxBPM: 180, windowSize: 0.75)
    /// assert(detector.minBPM == 40)
    /// assert(detector.maxBPM == 180)
    /// assert(detector.windowSize == 0.75)
    /// ```
    public init(minBPM: Double = 40, maxBPM: Double = 180, windowSize: Double = 0.75) {
        self.minBPM = minBPM
        self.maxBPM = maxBPM
        self.windowSize = windowSize
    }

    /// Process signal and detect peaks
    ///
    /// Example usage:
    /// ```swift
    /// // Create a synthetic ECG-like signal with clear peaks
    /// let sampleRate = 100.0
    /// let duration = 10.0 // 10 seconds
    /// let heartRate = 60.0 // 60 BPM = 1 beat per second
    ///
    /// // Generate synthetic signal with peaks every second (at samples 0, 100, 200, ...)
    /// var data = Array(repeating: 0.0, count: Int(duration * sampleRate))
    /// for i in 0..<10 {
    ///     let peakIndex = i * 100 // Every 100 samples (1 second at 100 Hz)
    ///     if peakIndex < data.count {
    ///         data[peakIndex] = 1.0 // Peak value
    ///         // Add some context around peak
    ///         if peakIndex > 0 { data[peakIndex - 1] = 0.5 }
    ///         if peakIndex < data.count - 1 { data[peakIndex + 1] = 0.5 }
    ///     }
    /// }
    ///
    /// let signal = try HeartRateSignal(data: data, sampleRate: sampleRate)
    /// var result = AnalysisResult()
    /// let detector = AdaptiveThresholdDetector(minBPM: 40, maxBPM: 180)
    /// let peaks = try detector.process(signal, result: &result)
    ///
    /// // Should detect approximately 10 peaks
    /// assert(peaks.count >= 8 && peaks.count <= 12)
    /// ```
    public func process(_ signal: HeartRateSignal, result: inout AnalysisResult) throws -> [Int] {
        let peaks = try detectPeaks(in: signal)

        // Store results
        result.setWorkingData("peaklist", value: peaks)
        result.setWorkingData("ybeat", value: peaks.map { signal.data[$0] })

        return peaks
    }

    /// Detect peaks using adaptive threshold algorithm
    ///
    /// Example with simple synthetic data:
    /// ```swift
    /// // Create signal with obvious peaks at indices 10, 30, 50
    /// var data = Array(repeating: 0.1, count: 100)
    /// data[10] = 1.0  // Peak 1
    /// data[30] = 1.2  // Peak 2 (higher)
    /// data[50] = 0.9  // Peak 3
    ///
    /// let signal = try HeartRateSignal(data: data, sampleRate: 100.0)
    /// let detector = AdaptiveThresholdDetector()
    /// let peaks = try detector.detectPeaks(in: signal)
    ///
    /// // Should detect the peaks we created
    /// assert(peaks.contains(10))
    /// assert(peaks.contains(30))
    /// assert(peaks.contains(50))
    /// ```
    public func detectPeaks(in signal: HeartRateSignal) throws -> [Int] {
        let data = signal.data
        guard data.count > 10 else {
            throw HRVError.insufficientData(data.count)
        }

        let windowLength = Int(windowSize * signal.sampleRate)
        var peaks: [Int] = []

        // Calculate minimum distance between peaks based on max BPM
        let minDistance = Int(60.0 / maxBPM * signal.sampleRate)

        // Initial moving average window
        var windowStart = 0
        var windowEnd = min(windowLength, data.count)

        var lastPeakIndex = -minDistance

        // Iterate through the signal with bounds checking
        let endIndex = max(windowLength, data.count - windowLength)
        guard windowLength < endIndex else {
            // Signal too short for the window size, fall back to simpler detection
            return try simpleThresholdDetection(in: signal)
        }

        for i in windowLength..<endIndex {
            // Update moving window
            windowStart = max(0, i - windowLength / 2)
            windowEnd = min(data.count, i + windowLength / 2)

            // Calculate threshold as moving average + some margin
            let windowData = Array(data[windowStart..<windowEnd])
            let movingAverage = windowData.reduce(0, +) / Double(windowData.count)
            let threshold = movingAverage * 1.3 // 30% above moving average

            // Check if current point is a local maximum above threshold
            let currentValue = data[i]
            let isLocalMax = currentValue > threshold &&
                           i > 0 && currentValue > data[i-1] &&
                           i < data.count - 1 && currentValue > data[i+1]

            // Check minimum distance constraint
            let isValidDistance = i - lastPeakIndex >= minDistance

            if isLocalMax && isValidDistance {
                // Verify this is actually a peak in a larger neighborhood
                let neighborhoodStart = max(0, i - 5)
                let neighborhoodEnd = min(data.count, i + 5)

                let isRealPeak = (neighborhoodStart..<neighborhoodEnd).allSatisfy { j in
                    data[i] >= data[j]
                }

                if isRealPeak {
                    peaks.append(i)
                    lastPeakIndex = i
                }
            }
        }

        // Validate heart rate range
        if peaks.count > 1 {
            let duration = Double(data.count) / signal.sampleRate
            let estimatedBPM = Double(peaks.count - 1) * 60.0 / duration

            if estimatedBPM < minBPM || estimatedBPM > maxBPM {
                // Try with adjusted threshold if heart rate is out of range
                return try detectPeaksWithAdjustedThreshold(in: signal, estimatedBPM: estimatedBPM)
            }
        }

        return peaks
    }

    /// Fallback method with adjusted threshold
    private func detectPeaksWithAdjustedThreshold(in signal: HeartRateSignal, estimatedBPM: Double) throws -> [Int] {
        let data = signal.data
        let windowLength = Int(windowSize * signal.sampleRate)

        // Adjust threshold multiplier based on estimated BPM
        let thresholdMultiplier: Double
        if estimatedBPM < minBPM {
            thresholdMultiplier = 1.1 // Lower threshold to find more peaks
        } else {
            thresholdMultiplier = 1.5 // Higher threshold to find fewer peaks
        }

        var peaks: [Int] = []
        let minDistance = Int(60.0 / maxBPM * signal.sampleRate)
        var lastPeakIndex = -minDistance

        for i in windowLength..<(data.count - windowLength) {
            let windowStart = max(0, i - windowLength / 2)
            let windowEnd = min(data.count, i + windowLength / 2)

            let windowData = Array(data[windowStart..<windowEnd])
            let movingAverage = windowData.reduce(0, +) / Double(windowData.count)
            let threshold = movingAverage * thresholdMultiplier

            let currentValue = data[i]
            let isLocalMax = currentValue > threshold &&
                           i > 0 && currentValue > data[i-1] &&
                           i < data.count - 1 && currentValue > data[i+1]

            let isValidDistance = i - lastPeakIndex >= minDistance

            if isLocalMax && isValidDistance {
                peaks.append(i)
                lastPeakIndex = i
            }
        }

        return peaks
    }

    /// Simple threshold detection for short signals
    private func simpleThresholdDetection(in signal: HeartRateSignal) throws -> [Int] {
        let data = signal.data
        guard data.count > 2 else { return [] }

        // Calculate minimum distance between peaks
        let minDistance = Int(60.0 / maxBPM * signal.sampleRate)

        // Use global statistics for short signals
        let mean = data.reduce(0, +) / Double(data.count)
        let threshold = mean * 1.5

        var peaks: [Int] = []
        var lastPeakIndex = -minDistance

        for i in 1..<(data.count - 1) {
            let isLocalMax = data[i] > threshold &&
                           data[i] > data[i-1] &&
                           data[i] > data[i+1]

            let isValidDistance = i - lastPeakIndex >= minDistance

            if isLocalMax && isValidDistance {
                peaks.append(i)
                lastPeakIndex = i
            }
        }

        return peaks
    }
}