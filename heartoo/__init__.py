"""
HeartOO - Object-oriented heart rate analysis toolkit
====================================================

HeartOO is a Python heart rate analysis toolkit that provides a modern
object-oriented implementation of heart rate variability analysis algorithms.
It's based on the original HeartPy library but designed with clean object-oriented
principles and patterns.

The package provides tools to analyze heart rate data including:
- Signal loading and preprocessing
- Peak detection
- Time domain analysis
- Frequency domain analysis
- Nonlinear (Poincaré) analysis
- Breathing rate estimation
- Visualization utilities

For more information, see the full documentation.
"""

from ._version import __version__

# Import core components
from .core.signal import Signal, HeartRateSignal
from .core.result import AnalysisResult

# Import processors
from .processing.processor import Processor
from .processing.pipeline import ProcessingPipeline
from .processing.builder import PipelineBuilder

# Import HeartPy compatibility functions
from .compatibility import process, process_segmentwise, process_rr

# Import utilities
from .utils.data import get_data, load_exampledata
from .utils.visualization import plot_signal, plot_poincare

__all__ = [
    # Version
    "__version__",
    
    # Core
    "Signal", "HeartRateSignal", "AnalysisResult",
    
    # Processing
    "Processor", "ProcessingPipeline", "PipelineBuilder",
    
    # Compatibility
    "process", "process_segmentwise", "process_rr",
    
    # Utilities
    "get_data", "load_exampledata", "plot_signal", "plot_poincare"
]