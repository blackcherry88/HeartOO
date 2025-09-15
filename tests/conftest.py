"""
Pytest configuration for HeartOO tests.
"""

import pytest
import numpy as np
import json
import os
import tempfile
from typing import Dict, Any, List

try:
    import heartpy as hp
    HEARTPY_AVAILABLE = True
except ImportError:
    HEARTPY_AVAILABLE = False
    
import heartoo as ho


# JSON encoder for numpy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


@pytest.fixture
def sample_signal():
    """Generate a sample signal for testing."""
    # Create a synthetic signal with known peaks
    sample_rate = 100.0  # Hz
    duration = 10.0  # seconds
    t = np.linspace(0, duration, int(duration * sample_rate))
    
    # Base signal (sine wave)
    freq = 1.0  # Hz (60 BPM)
    signal = np.sin(2 * np.pi * freq * t)
    
    # Add higher frequency for clear peaks
    signal += 0.5 * np.sin(2 * np.pi * freq * 2 * t)
    
    # Add some noise
    np.random.seed(42)  # For reproducibility
    noise = np.random.normal(0, 0.1, len(t))
    signal += noise
    
    return signal, sample_rate


@pytest.fixture
def heartpy_example_data():
    """Load example data from HeartPy if available."""
    if not HEARTPY_AVAILABLE:
        pytest.skip("HeartPy not installed")
    
    data, timer = hp.load_exampledata(0)
    return data, 100.0  # Example 0 has 100Hz sample rate


@pytest.fixture
def heartpy_comparison_data(heartpy_example_data):
    """Generate comparison data from HeartPy."""
    if not HEARTPY_AVAILABLE:
        pytest.skip("HeartPy not installed")
    
    data, sample_rate = heartpy_example_data
    wd, m = hp.process(data, sample_rate)
    
    # Save to a temp JSON file for later comparison
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        # Convert numpy arrays to lists for JSON serialization
        wd_serializable = {}
        for k, v in wd.items():
            if isinstance(v, np.ndarray):
                wd_serializable[k] = v.tolist()
            elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], np.ndarray):
                wd_serializable[k] = [arr.tolist() for arr in v]
            else:
                wd_serializable[k] = v
        
        m_serializable = {}
        for k, v in m.items():
            if isinstance(v, np.ndarray):
                m_serializable[k] = v.tolist()
            else:
                m_serializable[k] = v
                
        # Use custom encoder for numpy types
        json.dump(
            {"working_data": wd_serializable, "measures": m_serializable}, 
            f, 
            cls=NumpyEncoder
        )
    
    return {"working_data": wd, "measures": m, "file": f.name}


@pytest.fixture
def heartoo_results(heartpy_example_data):
    """Generate HeartOO results for comparison."""
    data, sample_rate = heartpy_example_data
    
    # Create signal
    signal = ho.HeartRateSignal(data, sample_rate)
    
    # Create pipeline
    pipeline = ho.PipelineBuilder.create_standard_pipeline(calc_freq=True)
    
    # Process signal
    result = pipeline.process(signal)
    
    return result