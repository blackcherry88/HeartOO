// HeartSW - Swift Heart Rate Analysis
// Base processor protocol and implementations

import Foundation

/// Base protocol for signal processors
public protocol Processor {
    associatedtype InputType
    associatedtype OutputType

    func process(_ input: InputType, result: inout AnalysisResult) throws -> OutputType
}

/// Protocol for processors that work with heart rate signals
public protocol HeartRateProcessor: Processor where InputType == HeartRateSignal {
    var name: String { get }
    var parameters: [String: Any] { get }
}

/// Default implementations for HeartRateProcessor
public extension HeartRateProcessor {
    var parameters: [String: Any] { [:] }
}

/// Utility for chaining multiple processors
public struct ProcessorChain {
    private var processors: [AnyHeartRateProcessor] = []

    public init() {}

    /// Add a processor to the chain
    ///
    /// Example usage:
    /// ```swift
    /// var chain = ProcessorChain()
    /// let filter = ButterworthFilter(cutoff: .single(0.05), type: .lowpass, order: 3)
    /// chain.add(filter)
    /// ```
    public mutating func add<P: HeartRateProcessor>(_ processor: P) {
        processors.append(AnyHeartRateProcessor(processor))
    }

    /// Process signal through all processors in order
    ///
    /// Example usage:
    /// ```swift
    /// let signal = try HeartRateSignal(data: ecgData, sampleRate: 100.0)
    /// var result = AnalysisResult()
    /// let processedSignal = try chain.process(signal, result: &result)
    /// ```
    public func process(_ signal: HeartRateSignal, result: inout AnalysisResult) throws -> HeartRateSignal {
        var currentSignal = signal

        for processor in processors {
            if let outputSignal = try processor.process(currentSignal, result: &result) as? HeartRateSignal {
                currentSignal = outputSignal
            }
        }

        return currentSignal
    }

    /// Get names of all processors in chain
    public var processorNames: [String] {
        return processors.map(\.name)
    }
}

/// Type-erased wrapper for HeartRateProcessor
public struct AnyHeartRateProcessor {
    public let name: String
    public let parameters: [String: Any]
    private let _process: (HeartRateSignal, inout AnalysisResult) throws -> Any

    public init<P: HeartRateProcessor>(_ processor: P) {
        self.name = processor.name
        self.parameters = processor.parameters
        self._process = { signal, result in
            return try processor.process(signal, result: &result)
        }
    }

    public func process(_ signal: HeartRateSignal, result: inout AnalysisResult) throws -> Any {
        return try _process(signal, &result)
    }
}