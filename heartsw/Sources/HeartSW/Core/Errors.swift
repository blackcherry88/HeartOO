// HeartSW - Swift Heart Rate Analysis
// Error definitions

import Foundation

/// Errors that can occur during heart rate analysis
public enum HRVError: Error, LocalizedError, Equatable {
    case invalidSampleRate(Double)
    case insufficientData(Int)
    case noPeaksDetected
    case filteringFailed(String)
    case invalidTimeRange(start: Double, end: Double, duration: Double)
    case fileNotFound(String)
    case invalidData(String)
    case analysisError(String)

    public var errorDescription: String? {
        switch self {
        case .invalidSampleRate(let rate):
            return "Sample rate must be positive, got: \(rate)"
        case .insufficientData(let count):
            return "Insufficient data for analysis, need at least 2 points, got: \(count)"
        case .noPeaksDetected:
            return "No peaks detected in signal"
        case .filteringFailed(let reason):
            return "Filtering failed: \(reason)"
        case .invalidTimeRange(let start, let end, let duration):
            return "Invalid time range [\(start), \(end)] for signal duration \(duration)"
        case .fileNotFound(let path):
            return "File not found: \(path)"
        case .invalidData(let reason):
            return "Invalid data: \(reason)"
        case .analysisError(let reason):
            return "Analysis error: \(reason)"
        }
    }
}

/// Validation utilities
public enum Validation {
    /// Validates sample rate
    ///
    /// Example usage:
    /// ```swift
    /// try Validation.validateSampleRate(100.0) // OK
    /// try Validation.validateSampleRate(-1.0)  // Throws HRVError.invalidSampleRate
    /// ```
    public static func validateSampleRate(_ rate: Double) throws {
        guard rate > 0 else {
            throw HRVError.invalidSampleRate(rate)
        }
    }

    /// Validates data count
    ///
    /// Example usage:
    /// ```swift
    /// try Validation.validateDataCount([1.0, 2.0, 3.0]) // OK
    /// try Validation.validateDataCount([1.0])           // Throws HRVError.insufficientData
    /// ```
    public static func validateDataCount<T>(_ data: [T], minimum: Int = 2) throws {
        guard data.count >= minimum else {
            throw HRVError.insufficientData(data.count)
        }
    }

    /// Validates time range
    ///
    /// Example usage:
    /// ```swift
    /// try Validation.validateTimeRange(start: 0.0, end: 10.0, duration: 20.0) // OK
    /// try Validation.validateTimeRange(start: 15.0, end: 25.0, duration: 20.0) // Throws
    /// ```
    public static func validateTimeRange(start: Double, end: Double, duration: Double) throws {
        guard start >= 0 && end <= duration && start < end else {
            throw HRVError.invalidTimeRange(start: start, end: end, duration: duration)
        }
    }
}