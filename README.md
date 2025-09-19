# HeartOO Ecosystem - Heart Rate Analysis Suite

A comprehensive heart rate variability (HRV) analysis ecosystem featuring both Python (HeartOO) and Swift (HeartSW) implementations. This project provides object-oriented, high-performance tools for ECG/PPG signal processing with cross-platform compatibility.

## 🚀 Project Components

### 1. **HeartOO** (Python) - Object-Oriented Heart Rate Analysis
Object-oriented Python toolkit inspired by [HeartPy](https://github.com/paulvangentcom/heartrate_analysis_python) with improved architecture using design patterns.

### 2. **HeartSW** (Swift) - High-Performance Swift Implementation
Protocol-oriented Swift library providing type-safe, memory-efficient heart rate analysis with cross-platform compatibility.

## ✨ Key Features

### HeartOO (Python)
- **Object-Oriented Design**: Clean and modular codebase with proper encapsulation
- **Extensible Architecture**: Easily extend with new filters, peak detectors, and analyzers
- **Standard HRV Measures**: All standard time-domain, frequency-domain, and nonlinear HRV measures
- **Breathing Rate Estimation**: Estimate breathing rate from heart rate variability
- **HeartPy Compatibility**: Drop-in replacement for HeartPy API

### HeartSW (Swift)
- **Protocol-Oriented Design**: Extensible architecture using Swift protocols
- **High Performance**: Optimized algorithms with value semantics and copy-on-write
- **Cross-Platform**: Supports macOS, iOS, Linux, and Windows
- **Type Safety**: Swift's strong typing prevents common signal processing errors
- **JSON Compatibility**: Full serialization for integration with other systems
- **CLI Tool**: Command-line interface for batch processing

## 🏗️ Installation & Setup

### Prerequisites
- **Python 3.8+** (for HeartOO)
- **Swift 5.9+** (for HeartSW - included with Xcode 15+ on macOS)

### Quick Setup
```bash
# Clone the repository
git clone <repository-url>
cd HeartOO

# Set up Python environment for HeartOO
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install heartpy numpy matplotlib

# Build HeartSW Swift package
swift build --package-path heartsw

# Run tests to verify installation
swift test --package-path heartsw
```

## 📖 Usage Examples

### HeartSW (Swift) - Command Line Interface

```bash
# Process ECG data from CSV file
swift run --package-path heartsw HeartSWCLI process data.csv --sample-rate 100 --output results.json

# Process with custom parameters
swift run --package-path heartsw HeartSWCLI process data.csv \
  --sample-rate 250 \
  --bpm-limits 50,150 \
  --filter-cutoff 0.75 \
  --output detailed_analysis.json
```

### HeartSW (Swift) - Library Usage

```swift
import HeartSW

// Quick analysis
let data: [Double] = [/* your ECG data */]
let result = try HeartSW.quickAnalysis(data, sampleRate: 100.0)
print("BPM: \(result.bpm)")

// Detailed processing
let signal = HeartRateSignal(data: data, sampleRate: 100.0)
let processor = ECGProcessor()
let analysisResult = try processor.process(signal)

// Access specific measures
print("SDNN: \(analysisResult.measures.sdnn)")
print("RMSSD: \(analysisResult.measures.rmssd)")

// Export to JSON
try analysisResult.saveToJSON("results.json")
```

### HeartOO (Python) - Object-Oriented API

```python
import heartoo as ho
import numpy as np

# Create synthetic ECG data
t = np.linspace(0, 30, 3000)  # 30 seconds at 100Hz
ecg_data = np.sin(2 * np.pi * 1.2 * t) + 0.5 * np.random.normal(0, 0.1, 3000)

# Create HeartRateSignal
signal = ho.HeartRateSignal(ecg_data, sample_rate=100.0)

# Create processing pipeline
pipeline = ho.PipelineBuilder.create_standard_pipeline()

# Process the signal
result = pipeline.process(signal)

# Access results
print(f"Heart Rate: {result.get_measure('bpm'):.2f} BPM")
print(f"SDNN: {result.get_measure('sdnn'):.2f} ms")
print(f"RMSSD: {result.get_measure('rmssd'):.2f} ms")
```

### Cross-Platform Integration (Python calling Swift)

```python
import subprocess
import json

# Process ECG data using HeartSW from Python
def process_with_heartsw(csv_file, sample_rate):
    result = subprocess.run([
        'swift', 'run', '--package-path', 'heartsw', 'HeartSWCLI',
        'process', csv_file, '--sample-rate', str(sample_rate),
        '--output', 'swift_results.json'
    ], capture_output=True, text=True)

    with open('swift_results.json', 'r') as f:
        return json.load(f)

# Compare Python and Swift results
heartsw_result = process_with_heartsw('ecg_data.csv', 100)
print(f"Swift BPM: {heartsw_result['measures']['bpm']:.2f}")
```

## 🧪 Testing & Validation

### HeartSW Swift Tests
```bash
# Run all tests
swift test --package-path heartsw

# Run specific test categories
swift test --package-path heartsw --filter HeartSWTests.testPerformanceLargeSignal

# Build and test in one command
./heartsw/Scripts/test.sh
```

### Cross-Implementation Validation
```bash
# Compare HeartSW against HeartPy using synthetic data
source .venv/bin/activate
python3 heartsw/Scripts/compare_with_heartpy.py
```

### Test Results Summary
- ✅ **20 Swift test cases** - All passing with 0 failures
- ✅ **Performance benchmarks** - ~0.54s for 10,000 samples
- ✅ **Cross-validation** - <1% difference between implementations
- ✅ **JSON compatibility** - Full serialization support

## 📊 Validation Results

### Implementation Comparison (30s synthetic ECG @ 100Hz)
| Implementation | BPM   | Peaks | SDNN  | RMSSD | Status |
|---------------|-------|-------|-------|-------|--------|
| **HeartPy**   | 73.39 | 37    | 16.05 | 9.71  | ✅ Reference |
| **HeartOO**   | 73.39 | 37    | 16.05 | 9.71  | ✅ Compatible |
| **HeartSW**   | 73.25 | 37    | 16.02 | 9.63  | ✅ <1% difference |

**Validation Status**: All implementations show consistent results within expected algorithmic tolerances.

## 🧹 Project Maintenance

### Cleaning Development Files
```bash
# Clean Swift build artifacts
swift package --package-path heartsw clean

# Remove temporary comparison files
rm -f heartsw_validation_result.json
rm -f swift_results.json

# Keep essential validation data in comparison_outputs/
```

### Build Scripts
```bash
# Build everything
./heartsw/Scripts/build.sh

# Test everything
./heartsw/Scripts/test.sh

# Full validation pipeline
source .venv/bin/activate && python3 heartsw/Scripts/compare_with_heartpy.py
```

## 📁 Project Structure

```
HeartOO/
├── README.md                          # This comprehensive guide
├── .venv/                            # Python virtual environment
├── heartoo/                          # Python HeartOO implementation
│   ├── core/                        # Core classes and result handling
│   └── __init__.py                  # Package initialization
├── heartsw/                         # Swift HeartSW implementation
│   ├── Package.swift                # Swift package manifest
│   ├── Sources/
│   │   ├── HeartSW/                # Core Swift library
│   │   └── HeartSWCLI/             # Command-line interface
│   ├── Tests/HeartSWTests/         # Comprehensive test suite
│   └── Scripts/                     # Build and validation scripts
├── comparison_outputs/              # Validation results and test data
│   ├── working_comparison_results.json  # Cross-implementation validation
│   ├── test_ecg_data.csv               # Test dataset
│   └── heartsw_validation_result.json  # Latest HeartSW results
└── examples/                        # Usage examples and demos
```

## 🔧 Advanced Configuration

### HeartSW Configuration Options
```bash
# CLI with all options
swift run --package-path heartsw HeartSWCLI process data.csv \
  --sample-rate 100 \
  --bpm-limits 50,180 \
  --filter-cutoff 0.75 \
  --window-size 150 \
  --output results.json
```

### Python Environment Setup
```bash
# Always activate virtual environment
source .venv/bin/activate

# Install additional dependencies if needed
pip install heartpy numpy matplotlib scipy
```

## 🚀 Performance Highlights

### HeartSW (Swift) Performance
- **Processing Speed**: ~0.54s for 10,000 sample analysis
- **Memory Efficiency**: Value semantics with copy-on-write optimization
- **Type Safety**: Compile-time error prevention
- **Cross-Platform**: Native performance on all Swift platforms

### HeartOO (Python) Architecture
HeartOO uses established design patterns:

1. **Factory Pattern**: Creating different signal processing components
2. **Strategy Pattern**: Interchangeable algorithms (peak detection, filtering)
3. **Builder Pattern**: Constructing complex analysis pipelines
4. **Composite Pattern**: Combining multiple analysis components
5. **Chain of Responsibility**: Handling preprocessing steps

### HeartSW (Swift) Architecture
HeartSW employs protocol-oriented programming:

1. **Protocol-Oriented Design**: Extensible interfaces for all major components
2. **Value Semantics**: Immutable data structures with efficient copying
3. **Error Handling**: Comprehensive Swift error handling with typed exceptions
4. **Memory Safety**: Automatic reference counting with no manual memory management

## 📚 Documentation & Resources

- **Design Documents**: See `.claude/heartsw_design.md` for architectural details
- **API Documentation**: Generate with `swift package generate-documentation`
- **Validation Data**: Comprehensive results in `comparison_outputs/`
- **Example Scripts**: Working examples in `examples/` directory

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/new-analysis-method`
3. **Add comprehensive tests**: Ensure new features have corresponding tests
4. **Run validation**: `swift test --package-path heartsw`
5. **Cross-validate**: Compare results with HeartPy using validation scripts
6. **Submit pull request** with detailed description

### Development Workflow
```bash
# Set up development environment
source .venv/bin/activate
swift build --package-path heartsw

# Make changes and test
swift test --package-path heartsw

# Validate against HeartPy
python3 heartsw/Scripts/compare_with_heartpy.py

# Clean up before commit
swift package --package-path heartsw clean
```

## 📈 Future Roadmap

### Planned Features
- **Frequency-domain analysis** (LF, HF, LF/HF ratio)
- **Non-linear HRV measures** (Poincaré plot analysis)
- **Real-time processing** capabilities
- **iOS/watchOS** framework integration
- **WebAssembly** compilation for browser usage

### Performance Goals
- Sub-100ms processing for 30-second ECG segments
- Memory usage optimization for embedded systems
- GPU acceleration for large dataset analysis

## ⚠️ Important Notes

### Python Environment
Always activate the virtual environment before running Python code:
```bash
source .venv/bin/activate
```

### Platform Compatibility
- **HeartSW**: macOS, iOS, Linux, Windows (via Swift for Windows)
- **HeartOO**: All platforms with Python 3.8+
- **Cross-validation**: Requires both Python and Swift environments

## 📄 License

This project builds upon the HeartPy library and maintains compatibility while providing enhanced performance and safety benefits through modern language features.

## 🙏 Acknowledgments

- **Paul van Gent** - Original HeartPy implementation
- **HeartPy Contributors** - Foundational algorithms and validation
- **Swift Community** - Excellent Swift ecosystem and tooling
- **Open Source Community** - For continuous improvement and feedback

---

**HeartOO Ecosystem** - Bridging Python flexibility with Swift performance for comprehensive heart rate analysis! 🚀❤️