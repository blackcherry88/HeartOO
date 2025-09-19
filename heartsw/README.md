# HeartSW - Swift Heart Rate Analysis

HeartSW is a Swift implementation of heart rate variability (HRV) analysis, inspired by the object-oriented design of HeartOO and maintaining compatibility with HeartPy functionality. It provides a fast, type-safe, and cross-platform solution for ECG/PPG signal analysis.

## Features

- 🔍 **Peak Detection**: Adaptive threshold algorithm for R-peak detection
- 📊 **Time Domain Analysis**: BPM, SDNN, RMSSD, pNN50, and more HRV measures
- 🏗️ **Object-Oriented Design**: Clean, extensible architecture with protocol-oriented programming
- 📱 **Cross-Platform**: Works on macOS, iOS, Linux, and other Swift-supported platforms
- 🧪 **Comprehensive Tests**: Extensive test suite with docstring examples
- ⚡ **High Performance**: Optimized for speed with Swift's native performance
- 💾 **JSON Output**: Compatible result format for easy comparison with other tools

## Quick Start

### Installation

```bash
# Clone and build
git clone <repository>
cd heartsw
./Scripts/build.sh
```

### Usage

#### Swift API

```swift
import HeartSW

// Quick analysis
let ecgData = [1.0, 1.5, 1.2, 2.1, 1.8, /* ... */]
let result = try HeartSW.process(data: ecgData, sampleRate: 100.0)

if let bpm = result.getMeasure("bpm") {
    print("Heart rate: \(bpm) BPM")
}

// From CSV file
let url = URL(fileURLWithPath: "ecg_data.csv")
let result = try HeartSW.processFile(at: url, sampleRate: 100.0)
```

#### Command Line Interface

```bash
# Process CSV file
heartsw process data.csv --sample-rate 100 --output results.json

# With custom parameters
heartsw process data.csv --sample-rate 250 --min-bpm 50 --max-bpm 150
```

## Architecture

HeartSW uses a clean, protocol-oriented architecture:

### Core Components

- **`HeartRateSignal`**: Value type representing ECG/PPG data with metadata
- **`AnalysisResult`**: Container for analysis results with JSON serialization
- **`Processor`**: Protocol for signal processing components

### Processing Pipeline

- **Peak Detectors**: `AdaptiveThresholdDetector` for R-peak detection
- **Analyzers**: `TimeDomainAnalyzer` for HRV measures
- **Filters**: Extensible filtering system (planned)

### Example: Custom Pipeline

```swift
// Create processing pipeline
let detector = AdaptiveThresholdDetector(minBPM: 40, maxBPM: 180)
let analyzer = TimeDomainAnalyzer()

// Process signal
var result = AnalysisResult()
let signal = try HeartRateSignal(data: ecgData, sampleRate: 100.0)

let peaks = try detector.process(signal, result: &result)
var signalWithPeaks = signal
signalWithPeaks.setPeaks(peaks)

let measures = try analyzer.process(signalWithPeaks, result: &result)
```

## Supported Measures

### Time Domain
- **BPM**: Heart rate in beats per minute
- **IBI**: Mean inter-beat interval (ms)
- **SDNN**: Standard deviation of NN intervals (ms)
- **RMSSD**: Root mean square of successive differences (ms)
- **pNN20/pNN50**: Percentage of successive differences > 20/50ms
- **HR_MAD**: Median absolute deviation

### Future Extensions
- Frequency domain measures (LF, HF, LF/HF ratio)
- Nonlinear measures (Poincaré plot: SD1, SD2)
- Advanced filtering options

## Development

### Building

```bash
# Build package
./Scripts/build.sh

# Run tests
./Scripts/test.sh

# Run benchmarks
./Scripts/benchmark.sh
```

### Testing

HeartSW includes comprehensive tests with docstring examples:

```swift
/// Calculate heart rate from RR intervals
///
/// Example usage:
/// ```swift
/// let intervals = [800.0, 850.0, 820.0, 790.0, 830.0]
/// let analyzer = TimeDomainAnalyzer()
/// let measures = try analyzer.calculateMeasures(from: intervals)
/// assert(abs(measures["bpm"]! - 73.35) < 0.1)
/// ```
func calculateMeasures(from intervals: [Double]) throws -> [String: Double]
```

### Comparison with HeartPy

Compare HeartSW results with HeartPy/HeartOO:

```bash
# Activate Python environment
source .venv/bin/activate

# Run comparison
./Scripts/compare_with_heartpy.py --duration 60 --sample-rate 100
```

This generates:
- Individual result JSON files for each implementation
- Detailed comparison report
- Difference analysis with tolerance checking

## File Structure

```
heartsw/
├── Package.swift                 # Swift package manifest
├── Sources/HeartSW/             # Core library
│   ├── Core/                    # Basic types and protocols
│   ├── Processing/              # Analysis algorithms
│   └── HeartSW.swift           # Main API
├── Sources/HeartSWCLI/          # Command-line interface
├── Tests/HeartSWTests/          # Test suite
├── Scripts/                     # Build and utility scripts
└── README.md                    # This file
```

## Performance

HeartSW is designed for performance:

- **Value semantics**: Efficient memory usage with copy-on-write
- **Native Swift**: No Python/NumPy overhead
- **Optimized algorithms**: Fast peak detection and HRV calculation
- **Async support**: Ready for real-time processing (planned)

Benchmark results on synthetic 60-second ECG data (1000 Hz):
- Peak detection: ~10ms
- Time domain analysis: ~1ms
- JSON serialization: ~5ms

## Examples

### Basic Analysis

```swift
// Load ECG data
let data = try HeartSW.loadCSV(from: URL(fileURLWithPath: "ecg.csv"))

// Process with default settings
let result = try HeartSW.process(data: data, sampleRate: 250.0)

// Access results
print("Heart Rate: \(result.getMeasure("bpm") ?? 0) BPM")
print("SDNN: \(result.getMeasure("sdnn") ?? 0) ms")

// Save results
try result.saveToJSON(at: URL(fileURLWithPath: "results.json"))
```

### Custom Processing

```swift
// Create signal
let signal = try HeartRateSignal(data: ecgData, sampleRate: 1000.0)

// Configure detector
let detector = AdaptiveThresholdDetector(
    minBPM: 50,
    maxBPM: 120,
    windowSize: 1.0
)

// Detect peaks
var result = AnalysisResult()
let peaks = try detector.process(signal, result: &result)

// Analyze with peaks
var signalWithPeaks = signal
signalWithPeaks.setPeaks(peaks)

let analyzer = TimeDomainAnalyzer()
let measures = try analyzer.process(signalWithPeaks, result: &result)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `./Scripts/test.sh`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- **HeartPy**: Original Python implementation by Paul van Gent
- **HeartOO**: Object-oriented Python refactoring
- **Swift Community**: For excellent language and tooling support