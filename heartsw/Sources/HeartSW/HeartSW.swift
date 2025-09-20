// HeartSW - Swift Heart Rate Analysis
// Main module file

import Foundation

/// Main HeartSW namespace
public enum HeartSW {
    /// Version information
    public static let version = "1.0.0"

    /// Supported file formats
    public enum FileFormat {
        case csv
        case json
    }
}

/// Convenience functions for quick analysis (similar to HeartPy API)
public extension HeartSW {

    /// Process heart rate signal with default settings
    ///
    /// Example usage:
    /// ```swift
    /// // Load ECG data from array
    /// let ecgData = [1.0, 1.5, 1.2, 2.1, 1.8, 1.0, 0.8, 1.1, 2.0, 1.5]
    /// let sampleRate = 100.0
    ///
    /// // Process with default settings
    /// let result = try HeartSW.process(data: ecgData, sampleRate: sampleRate)
    ///
    /// // Access results
    /// if let bpm = result.getMeasure("bpm") {
    ///     assert(bpm > 0 && bpm < 200) // Reasonable BPM range
    /// }
    /// ```
    static func process(data: [Double],
                       sampleRate: Double,
                       minBPM: Double = 40,
                       maxBPM: Double = 180,
                       thresholdPercentage: Double = 20) throws -> AnalysisResult {
        // Create signal
        let signal = try HeartRateSignal(data: data, sampleRate: sampleRate)

        // Create processing pipeline (following HeartPy's approach)
        let detector = AdaptiveThresholdDetector(minBPM: minBPM, maxBPM: maxBPM, thresholdPercentage: thresholdPercentage)
        let validator = PeakValidator()
        let analyzer = TimeDomainAnalyzer()

        var result = AnalysisResult()

        // Process: detect peaks, validate them, then analyze (HeartPy pipeline)
        let peaks = try detector.process(signal, result: &result)

        // Update signal with peaks
        var signalWithPeaks = signal
        signalWithPeaks.setPeaks(peaks)

        // Validate peaks and mark outliers (HeartPy's check_peaks behavior)
        let validatedSignal = try validator.process(signalWithPeaks, result: &result)

        // Analyze time domain measures with validated data
        _ = try analyzer.process(validatedSignal, result: &result)

        return result
    }

    /// Load and process CSV file
    ///
    /// CSV format: first column = time (optional), second column = signal data
    ///
    /// Example usage:
    /// ```swift
    /// let url = URL(fileURLWithPath: "/path/to/ecg.csv")
    /// let result = try HeartSW.processFile(at: url, sampleRate: 100.0)
    /// print("Heart rate: \(result.getMeasure("bpm") ?? 0) BPM")
    /// ```
    static func processFile(at url: URL,
                           sampleRate: Double,
                           minBPM: Double = 40,
                           maxBPM: Double = 180,
                           thresholdPercentage: Double = 20) throws -> AnalysisResult {
        let data = try loadCSV(from: url)
        return try process(data: data, sampleRate: sampleRate, minBPM: minBPM, maxBPM: maxBPM, thresholdPercentage: thresholdPercentage)
    }

    /// Load data from CSV file
    ///
    /// Example CSV content:
    /// ```
    /// time,ecg
    /// 0.0,1.2
    /// 0.01,1.5
    /// 0.02,1.1
    /// ```
    ///
    /// Or simple single column:
    /// ```
    /// 1.2
    /// 1.5
    /// 1.1
    /// ```
    static func loadCSV(from url: URL) throws -> [Double] {
        let content = try String(contentsOf: url)
        let lines = content.components(separatedBy: CharacterSet.newlines)
            .filter { !$0.trimmingCharacters(in: CharacterSet.whitespacesAndNewlines).isEmpty }

        guard !lines.isEmpty else {
            throw HRVError.invalidData("Empty CSV file")
        }

        var data: [Double] = []

        // Check if first line is header
        let firstLine = lines[0]
        let hasHeader = firstLine.contains(",") && Double(firstLine.components(separatedBy: ",")[0]) == nil

        let dataLines = hasHeader ? Array(lines.dropFirst()) : lines

        for line in dataLines {
            let components = line.components(separatedBy: ",")

            // Get the last component (signal data)
            let valueString = components.last?.trimmingCharacters(in: CharacterSet.whitespacesAndNewlines) ?? ""

            guard let value = Double(valueString) else {
                throw HRVError.invalidData("Cannot parse number: \(valueString)")
            }

            data.append(value)
        }

        guard !data.isEmpty else {
            throw HRVError.invalidData("No valid data found in CSV")
        }

        return data
    }
}

/// Quick analysis pipeline
public struct QuickPipeline {
    public let detector: AdaptiveThresholdDetector
    public let analyzer: TimeDomainAnalyzer

    public init(minBPM: Double = 40, maxBPM: Double = 180) {
        self.detector = AdaptiveThresholdDetector(minBPM: minBPM, maxBPM: maxBPM)
        self.analyzer = TimeDomainAnalyzer()
    }

    /// Run complete analysis on signal
    ///
    /// Example usage:
    /// ```swift
    /// let pipeline = QuickPipeline(minBPM: 50, maxBPM: 160)
    /// let signal = try HeartRateSignal(data: ecgData, sampleRate: 100.0)
    /// let result = try pipeline.analyze(signal)
    ///
    /// // Results contain both peak detection and time domain measures
    /// assert(result.getWorkingData("peaklist", as: [Int].self) != nil)
    /// assert(result.getMeasure("bpm") != nil)
    /// assert(result.getMeasure("sdnn") != nil)
    /// ```
    public func analyze(_ signal: HeartRateSignal) throws -> AnalysisResult {
        var result = AnalysisResult()

        // Detect peaks
        let peaks = try detector.process(signal, result: &result)

        // Set peaks on signal copy for analysis
        var signalWithPeaks = signal
        signalWithPeaks.setPeaks(peaks)

        // Analyze
        _ = try analyzer.process(signalWithPeaks, result: &result)

        return result
    }
}