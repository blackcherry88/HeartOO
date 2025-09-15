# HeartOO

HeartOO is an object-oriented heart rate analysis toolkit, inspired by the [HeartPy](https://github.com/paulvangentcom/heartrate_analysis_python) library. It provides the same functionality as HeartPy but with an improved architecture using design patterns and object-oriented principles.

## Features

- **Object-Oriented Design**: Clean and modular codebase with proper encapsulation
- **Extensible Architecture**: Easily extend with new filters, peak detectors, and analyzers
- **Standard HRV Measures**: All standard time-domain, frequency-domain, and nonlinear HRV measures
- **Breathing Rate Estimation**: Estimate breathing rate from heart rate variability
- **Signal Processing**: Various preprocessing tools including filtering and peak detection
- **Compatibility Layer**: Drop-in replacement for HeartPy API

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/heartoo.git
cd heartoo

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e .
```

## Usage

### Basic Example

```python
import heartoo as ho
import matplotlib.pyplot as plt
import numpy as np

# Create a synthetic signal
t = np.linspace(0, 10, 1000)
signal = np.sin(2 * np.pi * 1.0 * t) + 0.5 * np.sin(2 * np.pi * 2.0 * t) + np.random.normal(0, 0.1, 1000)

# Create a HeartRateSignal
heart_signal = ho.HeartRateSignal(signal, sample_rate=100.0)

# Create a processing pipeline
pipeline = ho.PipelineBuilder.create_standard_pipeline(calc_freq=True)

# Process the signal
result = pipeline.process(heart_signal)

# Access results
print(f"Heart Rate: {result.get_measure('bpm'):.2f} BPM")
print(f"SDNN: {result.get_measure('sdnn'):.2f} ms")
print(f"RMSSD: {result.get_measure('rmssd'):.2f} ms")
print(f"LF/HF Ratio: {result.get_measure('lf/hf'):.2f}")

# Plot the signal with detected peaks
ho.plot_signal(heart_signal.data, heart_signal.sample_rate,
              peaks=heart_signal.peaks,
              title="Heart Rate Signal with Detected Peaks")
plt.show()

# Plot Poincaré diagram
ho.plot_poincare(result.get_working_data('RR_list_cor'),
                sd1=result.get_measure('sd1'),
                sd2=result.get_measure('sd2'))
plt.show()
```

### HeartPy Compatibility

```python
import heartoo as ho

# Load data
data = [1.0, 1.2, 1.5, 1.3, 1.0, 0.8, 0.6, 0.5, 0.4, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5]
sample_rate = 100.0  # Hz

# Use HeartPy-compatible API
wd, m = ho.process(data, sample_rate, calc_freq=True)

# Access results
print(f"Heart Rate: {m['bpm']:.2f} BPM")
print(f"SDNN: {m['sdnn']:.2f} ms")
print(f"RMSSD: {m['rmssd']:.2f} ms")
print(f"LF/HF Ratio: {m['lf/hf']:.2f}")
```

## Important Note

Always source the virtual environment before running Python applications:

```bash
source .venv/bin/activate
```

## Design

HeartOO uses several design patterns:

1. **Factory Pattern**: For creating different signal processing components
2. **Strategy Pattern**: For interchangeable algorithms (peak detection, filtering)
3. **Builder Pattern**: For constructing complex analysis pipelines
4. **Composite Pattern**: For combining multiple analysis components
5. **Chain of Responsibility**: For handling preprocessing steps

The core components are:

- `Signal`: Base class representing a time series signal
- `HeartRateSignal`: Specialized signal for heart rate data
- `Processor`: Interface for all signal processors
- `FilterProcessor`, `PeakDetector`, `HRVAnalyzer`: Processor implementations
- `ProcessingPipeline`: Composite of processors
- `PipelineBuilder`: Builder for creating pipelines
- `AnalysisResult`: Container for analysis results

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Paul van Gent for creating the original [HeartPy](https://github.com/paulvangentcom/heartrate_analysis_python) library
- All contributors to HeartPy