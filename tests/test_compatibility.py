"""
Tests for HeartPy compatibility functions.
"""

import pytest
import numpy as np
import os
import json
from typing import Dict, Any

try:
    import heartpy as hp
    HEARTPY_AVAILABLE = True
except ImportError:
    HEARTPY_AVAILABLE = False

import heartoo as ho
from heartoo.compatibility import process, process_segmentwise, process_rr


@pytest.mark.skipif(not HEARTPY_AVAILABLE, reason="HeartPy not installed")
class TestCompatibility:
    """Tests for HeartPy compatibility functions."""
    
    def test_process_basic(self, sample_signal):
        """Test basic process function."""
        signal, sample_rate = sample_signal
        
        # Process with HeartOO
        wd, m = process(signal, sample_rate)
        
        # Check output types
        assert isinstance(wd, dict)
        assert isinstance(m, dict)
        
        # Check basic measures
        assert "peaklist" in wd
        assert "binary_peaklist" in wd
        assert "RR_list" in wd
        assert "RR_list_cor" in wd
        
        assert "bpm" in m
        assert "ibi" in m
        assert "sdnn" in m
        assert "rmssd" in m
    
    def test_process_vs_heartpy(self, heartpy_example_data, heartpy_comparison_data):
        """Test process function compared to HeartPy."""
        data, sample_rate = heartpy_example_data
        hp_data = heartpy_comparison_data
        
        # Process with HeartOO
        wd, m = process(data, sample_rate, calc_freq=True)
        
        # Check basic measures match HeartPy
        assert abs(m["bpm"] - hp_data["measures"]["bpm"]) < 1.0
        assert abs(m["sdnn"] - hp_data["measures"]["sdnn"]) < 5.0
        assert abs(m["rmssd"] - hp_data["measures"]["rmssd"]) < 5.0
        
        # Check frequency measures
        assert "lf" in m
        assert "hf" in m
        assert "lf/hf" in m
        
        # Check peak counts are similar
        assert abs(len(wd["peaklist"]) - len(hp_data["working_data"]["peaklist"])) <= 2
    
    def test_process_options(self, sample_signal):
        """Test process function options."""
        signal, sample_rate = sample_signal
        
        # Test with frequency domain analysis
        wd1, m1 = process(signal, sample_rate, calc_freq=True)
        assert "lf" in m1
        assert "hf" in m1
        
        # Test without frequency domain analysis
        wd2, m2 = process(signal, sample_rate, calc_freq=False)
        assert "lf" not in m2
        assert "hf" not in m2
        
        # Test with different BPM limits
        wd3, m3 = process(signal, sample_rate, bpmmin=50, bpmmax=150)
        
        # Should still detect peaks with reasonable settings
        assert len(wd3["peaklist"]) > 0
    
    @pytest.mark.skipif(True, reason="Segmentwise processing not fully implemented yet")
    def test_process_segmentwise(self, heartpy_example_data):
        """Test segmentwise processing."""
        data, sample_rate = heartpy_example_data
        
        # Process with segmentwise
        wd, m = process_segmentwise(data, sample_rate, segment_width=10, segment_overlap=0.5)
        
        # Check results
        assert isinstance(wd, dict)
        assert isinstance(m, dict)
        
        # Check that we have segment data
        assert "segment_indices" in wd
        
        # Check that measures are lists
        assert isinstance(m["bpm"], list)
        assert len(m["bpm"]) > 1
    
    def test_process_rr(self):
        """Test RR interval processing."""
        # Create synthetic RR intervals
        rr_list = [1000, 900, 1100, 950, 1050, 1000, 950]  # in ms
        
        # Process with HeartOO
        wd, m = process_rr(rr_list, calc_freq=True)
        
        # Check basic results
        assert isinstance(wd, dict)
        assert isinstance(m, dict)
        
        # Check measures
        assert "bpm" in m
        assert "ibi" in m
        assert "sdnn" in m
        assert "rmssd" in m
        
        # Check frequency measures
        assert "lf" in m
        assert "hf" in m
        assert "lf/hf" in m
        
        # Check calculated values
        assert abs(m["bpm"] - 60000 / np.mean(rr_list)) < 0.1
        assert abs(m["ibi"] - np.mean(rr_list)) < 0.1