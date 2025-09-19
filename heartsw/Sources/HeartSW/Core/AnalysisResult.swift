// HeartSW - Swift Heart Rate Analysis
// Analysis result management

import Foundation

/// Container for heart rate analysis results
public struct AnalysisResult: Codable {
    private var measures: [String: Double] = [:]
    private var workingData: [String: AnyCodable] = [:]
    private var segments: [AnalysisResult] = []

    /// Initialize empty analysis result
    public init() {}

    // MARK: - Measure Management

    /// Set a numerical measure
    ///
    /// Example usage:
    /// ```swift
    /// var result = AnalysisResult()
    /// result.setMeasure("bpm", value: 72.5)
    /// assert(result.getMeasure("bpm") == 72.5)
    /// ```
    public mutating func setMeasure(_ key: String, value: Double) {
        measures[key] = value
    }

    /// Get a numerical measure
    ///
    /// Example usage:
    /// ```swift
    /// let result = AnalysisResult()
    /// assert(result.getMeasure("nonexistent") == nil)
    /// ```
    public func getMeasure(_ key: String) -> Double? {
        return measures[key]
    }

    /// Get all measures
    ///
    /// Example usage:
    /// ```swift
    /// var result = AnalysisResult()
    /// result.setMeasure("bpm", value: 72.0)
    /// result.setMeasure("sdnn", value: 45.2)
    /// let measures = result.getAllMeasures()
    /// assert(measures.count == 2)
    /// assert(measures["bpm"] == 72.0)
    /// ```
    public func getAllMeasures() -> [String: Double] {
        return measures
    }

    /// Get measures by category prefix
    ///
    /// Example usage:
    /// ```swift
    /// var result = AnalysisResult()
    /// result.setMeasure("time_bpm", value: 72.0)
    /// result.setMeasure("time_sdnn", value: 45.2)
    /// result.setMeasure("freq_lf", value: 150.0)
    /// let timeMeasures = result.getMeasuresByCategory("time_")
    /// assert(timeMeasures.count == 2)
    /// assert(timeMeasures["time_bpm"] == 72.0)
    /// ```
    public func getMeasuresByCategory(_ prefix: String) -> [String: Double] {
        return measures.filter { key, _ in key.hasPrefix(prefix) }
    }

    // MARK: - Working Data Management

    /// Set working data of any codable type
    ///
    /// Example usage:
    /// ```swift
    /// var result = AnalysisResult()
    /// result.setWorkingData("peaks", value: [10, 50, 90])
    /// let peaks: [Int]? = result.getWorkingData("peaks", as: [Int].self)
    /// assert(peaks == [10, 50, 90])
    /// ```
    public mutating func setWorkingData<T: Codable>(_ key: String, value: T) {
        workingData[key] = AnyCodable(value)
    }

    /// Get working data of specified type
    public func getWorkingData<T: Codable>(_ key: String, as type: T.Type) -> T? {
        return workingData[key]?.value as? T
    }

    // MARK: - Segment Management

    /// Add a segment result for segmented analysis
    ///
    /// Example usage:
    /// ```swift
    /// var result = AnalysisResult()
    /// var segment = AnalysisResult()
    /// segment.setMeasure("bpm", value: 75.0)
    /// result.addSegment(segment)
    /// assert(result.segments.count == 1)
    /// ```
    public mutating func addSegment(_ segment: AnalysisResult) {
        segments.append(segment)
    }

    /// Get all segment results
    public var allSegments: [AnalysisResult] {
        return segments
    }

    // MARK: - Comparison

    /// Compare with another analysis result
    ///
    /// Example usage:
    /// ```swift
    /// var result1 = AnalysisResult()
    /// result1.setMeasure("bpm", value: 72.0)
    /// result1.setMeasure("sdnn", value: 45.0)
    ///
    /// var result2 = AnalysisResult()
    /// result2.setMeasure("bpm", value: 72.001) // Very close
    /// result2.setMeasure("rmssd", value: 30.0) // Different measure
    ///
    /// let comparison = result1.compare(with: result2, tolerance: 0.01)
    /// assert(comparison.identicalMeasures.contains("bpm"))
    /// assert(comparison.onlyInFirst.contains("sdnn"))
    /// assert(comparison.onlyInSecond.contains("rmssd"))
    /// ```
    public func compare(with other: AnalysisResult, tolerance: Double = 1e-6) -> ComparisonResult {
        var identical: [String] = []
        var different: [String: (Double, Double)] = [:]
        var onlyInSelf: [String] = []
        var onlyInOther: [String] = []

        let allKeys = Set(measures.keys).union(Set(other.measures.keys))

        for key in allKeys {
            switch (measures[key], other.measures[key]) {
            case let (val1?, val2?):
                if abs(val1 - val2) <= tolerance {
                    identical.append(key)
                } else {
                    different[key] = (val1, val2)
                }
            case (nil, _):
                onlyInOther.append(key)
            case (_, nil):
                onlyInSelf.append(key)
            }
        }

        return ComparisonResult(
            identicalMeasures: identical.sorted(),
            differentMeasures: different,
            onlyInFirst: onlyInSelf.sorted(),
            onlyInSecond: onlyInOther.sorted()
        )
    }

    // MARK: - JSON Operations

    /// Save to JSON file
    ///
    /// Example usage:
    /// ```swift
    /// var result = AnalysisResult()
    /// result.setMeasure("bpm", value: 72.0)
    /// let url = URL(fileURLWithPath: "/tmp/result.json")
    /// try result.saveToJSON(at: url)
    /// ```
    public func saveToJSON(at url: URL) throws {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(self)
        try data.write(to: url)
    }

    /// Load from JSON file
    ///
    /// Example usage:
    /// ```swift
    /// let url = URL(fileURLWithPath: "/path/to/result.json")
    /// let result = try AnalysisResult.loadFromJSON(at: url)
    /// ```
    public static func loadFromJSON(at url: URL) throws -> AnalysisResult {
        let data = try Data(contentsOf: url)
        let decoder = JSONDecoder()
        return try decoder.decode(AnalysisResult.self, from: data)
    }

    /// Compare two JSON result files
    ///
    /// Example usage:
    /// ```swift
    /// let url1 = URL(fileURLWithPath: "result1.json")
    /// let url2 = URL(fileURLWithPath: "result2.json")
    /// let comparison = try AnalysisResult.compareJSONFiles(url1, url2, tolerance: 0.01)
    /// print("Identical measures: \(comparison.identicalMeasures)")
    /// ```
    public static func compareJSONFiles(_ file1: URL, _ file2: URL, tolerance: Double = 1e-6) throws -> ComparisonResult {
        let result1 = try loadFromJSON(at: file1)
        let result2 = try loadFromJSON(at: file2)
        return result1.compare(with: result2, tolerance: tolerance)
    }
}

/// Result of comparing two AnalysisResult objects
public struct ComparisonResult {
    public let identicalMeasures: [String]
    public let differentMeasures: [String: (Double, Double)]
    public let onlyInFirst: [String]
    public let onlyInSecond: [String]

    /// Human-readable summary of comparison
    ///
    /// Example usage:
    /// ```swift
    /// let comparison = result1.compare(with: result2)
    /// print(comparison.summary)
    /// // Output: "Comparison: 5 identical, 2 different, 1 only in first, 3 only in second"
    /// ```
    public var summary: String {
        return "Comparison: \(identicalMeasures.count) identical, " +
               "\(differentMeasures.count) different, " +
               "\(onlyInFirst.count) only in first, " +
               "\(onlyInSecond.count) only in second"
    }

    /// Detailed comparison report
    public var detailedReport: String {
        var report = [summary, ""]

        if !identicalMeasures.isEmpty {
            report.append("Identical measures:")
            report.append(contentsOf: identicalMeasures.map { "  \($0)" })
            report.append("")
        }

        if !differentMeasures.isEmpty {
            report.append("Different measures:")
            for (key, values) in differentMeasures.sorted(by: { $0.key < $1.key }) {
                report.append("  \(key): \(values.0) vs \(values.1) (diff: \(values.1 - values.0))")
            }
            report.append("")
        }

        if !onlyInFirst.isEmpty {
            report.append("Only in first: \(onlyInFirst.joined(separator: ", "))")
            report.append("")
        }

        if !onlyInSecond.isEmpty {
            report.append("Only in second: \(onlyInSecond.joined(separator: ", "))")
        }

        return report.joined(separator: "\n")
    }
}

/// Type-erased wrapper for Codable values
public struct AnyCodable: Codable {
    public let value: Any

    public init<T: Codable>(_ value: T) {
        self.value = value
    }

    public init(_ value: Any) {
        self.value = value
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()

        if let intValue = try? container.decode(Int.self) {
            value = intValue
        } else if let doubleValue = try? container.decode(Double.self) {
            value = doubleValue
        } else if let stringValue = try? container.decode(String.self) {
            value = stringValue
        } else if let boolValue = try? container.decode(Bool.self) {
            value = boolValue
        } else if let arrayValue = try? container.decode([AnyCodable].self) {
            value = arrayValue.map(\.value)
        } else if let dictValue = try? container.decode([String: AnyCodable].self) {
            value = dictValue.mapValues(\.value)
        } else {
            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "Cannot decode AnyCodable value"
            )
        }
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()

        switch value {
        case let intValue as Int:
            try container.encode(intValue)
        case let doubleValue as Double:
            try container.encode(doubleValue)
        case let stringValue as String:
            try container.encode(stringValue)
        case let boolValue as Bool:
            try container.encode(boolValue)
        case let arrayValue as [Any]:
            let codableArray: [AnyCodable] = arrayValue.map { AnyCodable($0) }
            try container.encode(codableArray)
        case let dictValue as [String: Any]:
            let codableDict: [String: AnyCodable] = dictValue.mapValues { AnyCodable($0) }
            try container.encode(codableDict)
        default:
            let context = EncodingError.Context(
                codingPath: container.codingPath,
                debugDescription: "Cannot encode value of type \(type(of: value))"
            )
            throw EncodingError.invalidValue(value, context)
        }
    }
}