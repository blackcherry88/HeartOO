"""
Tests for core HeartOO components.
"""

import pytest
import numpy as np

from heartoo.core.signal import Signal, HeartRateSignal
from heartoo.core.result import AnalysisResult


class TestSignal:
    """Tests for the Signal class."""
    
    def test_signal_initialization(self):
        """Test Signal initialization."""
        # Create a signal
        data = np.array([1, 2, 3, 4, 5])
        sample_rate = 100.0
        signal = Signal(data, sample_rate)
        
        # Check attributes
        assert np.array_equal(signal.data, data)
        assert signal.sample_rate == sample_rate
        assert signal.duration == len(data) / sample_rate
        assert isinstance(signal.metadata, dict)
        assert len(signal.metadata) == 0
    
    def test_signal_metadata(self):
        """Test Signal metadata operations."""
        signal = Signal([1, 2, 3, 4, 5], 100.0)
        
        # Set metadata
        signal.set_metadata("test_key", "test_value")
        assert signal.metadata["test_key"] == "test_value"
    
    def test_signal_slicing(self):
        """Test Signal slicing."""
        # Create a signal
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        sample_rate = 1.0  # 1 sample per second for easy testing
        signal = Signal(data, sample_rate)
        
        # Slice signal
        sliced = signal.get_slice(2.0, 5.0)
        
        # Check sliced signal
        assert np.array_equal(sliced.data, data[2:5])
        assert sliced.sample_rate == sample_rate
    
    def test_signal_time_axis(self):
        """Test Signal time axis generation."""
        # Create a signal
        data = np.array([1, 2, 3, 4, 5])
        sample_rate = 2.0  # 2 samples per second
        signal = Signal(data, sample_rate)
        
        # Get time axis
        time_axis = signal.get_time_axis()
        
        # Check time axis
        expected = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
        assert np.allclose(time_axis, expected)
    
    def test_signal_length(self):
        """Test Signal length."""
        data = [1, 2, 3, 4, 5]
        signal = Signal(data, 100.0)
        assert len(signal) == len(data)
    
    def test_signal_indexing(self):
        """Test Signal indexing."""
        data = np.array([1, 2, 3, 4, 5])
        signal = Signal(data, 100.0)
        
        # Test single indexing
        assert signal[0] == data[0]
        assert signal[-1] == data[-1]
        
        # Test slice indexing
        assert np.array_equal(signal[1:4], data[1:4])
    
    def test_invalid_sample_rate(self):
        """Test invalid sample rate handling."""
        with pytest.raises(ValueError):
            Signal([1, 2, 3], 0)
        
        with pytest.raises(ValueError):
            Signal([1, 2, 3], -1)


class TestHeartRateSignal:
    """Tests for the HeartRateSignal class."""
    
    def test_heart_rate_signal_initialization(self):
        """Test HeartRateSignal initialization."""
        data = np.array([1, 2, 3, 4, 5])
        sample_rate = 100.0
        signal = HeartRateSignal(data, sample_rate)
        
        # Check attributes
        assert np.array_equal(signal.data, data)
        assert signal.sample_rate == sample_rate
        assert signal.peaks is None
        assert signal.rr_intervals is None
        assert signal.rr_indices is None
    
    def test_set_peaks(self):
        """Test setting peaks."""
        signal = HeartRateSignal([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 100.0)
        
        # Set peaks
        peaks = np.array([1, 3, 5, 7, 9])
        signal.peaks = peaks
        
        # Check peaks
        assert np.array_equal(signal.peaks, peaks)
    
    def test_rr_intervals_calculation(self):
        """Test RR intervals calculation."""
        signal = HeartRateSignal([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 100.0)
        
        # Set peaks
        signal.peaks = np.array([1, 3, 5, 7, 9])
        
        # Check RR intervals
        expected_rr = np.array([2, 2, 2, 2]) * (1000.0 / 100.0)  # in ms
        assert np.array_equal(signal.rr_intervals, expected_rr)
        
        # Check RR indices
        expected_indices = [(1, 3), (3, 5), (5, 7), (7, 9)]
        assert signal.rr_indices == expected_indices
    
    def test_heart_rate_calculation(self):
        """Test heart rate calculation."""
        signal = HeartRateSignal([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 100.0)
        
        # Set peaks with known timing
        signal.peaks = np.array([0, 100, 200, 300])  # 100 samples apart at 100Hz = 1 sec = 60 BPM
        
        # Check heart rate
        assert signal.get_heart_rate() == 60.0
    
    def test_scale_data(self):
        """Test scaling data."""
        data = np.array([1, 2, 3, 4, 5])
        signal = HeartRateSignal(data, 100.0)
        
        # Scale data
        scaled = signal.scale_data(0, 10)
        
        # Check scaled data
        expected = np.array([0, 2.5, 5.0, 7.5, 10.0])
        assert np.array_equal(scaled.data, expected)


class TestAnalysisResult:
    """Tests for the AnalysisResult class."""
    
    def test_analysis_result_initialization(self):
        """Test AnalysisResult initialization."""
        result = AnalysisResult()
        
        # Check attributes
        assert isinstance(result.measures, dict)
        assert len(result.measures) == 0
        assert isinstance(result.working_data, dict)
        assert len(result.working_data) == 0
        assert isinstance(result.segments, list)
        assert len(result.segments) == 0
    
    def test_measures(self):
        """Test measure operations."""
        result = AnalysisResult()
        
        # Set measure
        result.set_measure("bpm", 60.0)
        
        # Get measure
        assert result.get_measure("bpm") == 60.0
        
        # Get non-existent measure
        assert result.get_measure("non_existent") is None
        
        # Get non-existent measure with default
        assert result.get_measure("non_existent", 0) == 0
    
    def test_working_data(self):
        """Test working data operations."""
        result = AnalysisResult()
        
        # Set working data
        result.set_working_data("peaks", [1, 2, 3])
        
        # Get working data
        assert result.get_working_data("peaks") == [1, 2, 3]
        
        # Get non-existent working data
        assert result.get_working_data("non_existent") is None
        
        # Get non-existent working data with default
        assert result.get_working_data("non_existent", []) == []
    
    def test_segments(self):
        """Test segment operations."""
        result = AnalysisResult()
        
        # Create segment
        segment = AnalysisResult()
        segment.set_measure("bpm", 60.0)
        
        # Add segment
        result.add_segment(segment)
        
        # Check segment
        assert len(result.segments) == 1
        assert result.segments[0].get_measure("bpm") == 60.0
    
    def test_get_measures_by_category(self):
        """Test getting measures by category."""
        result = AnalysisResult()
        
        # Set measures
        result.set_measure("hrv_sdnn", 50.0)
        result.set_measure("hrv_rmssd", 30.0)
        result.set_measure("bpm", 60.0)
        
        # Get HRV measures
        hrv_measures = result.get_measures_by_category("hrv_")
        
        # Check HRV measures
        assert len(hrv_measures) == 2
        assert hrv_measures["hrv_sdnn"] == 50.0
        assert hrv_measures["hrv_rmssd"] == 30.0
    
    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = AnalysisResult()
        
        # Set measures and working data
        result.set_measure("bpm", 60.0)
        result.set_working_data("peaks", [1, 2, 3])
        
        # Convert to dict
        result_dict = result.to_dict()
        
        # Check dict
        assert "measures" in result_dict
        assert "working_data" in result_dict
        assert result_dict["measures"]["bpm"] == 60.0
        assert result_dict["working_data"]["peaks"] == [1, 2, 3]
    
    def test_get_time_series_measures(self):
        """Test getting time series measures."""
        result = AnalysisResult()
        
        # Set time series measures
        result.set_measure("bpm", 60.0)
        result.set_measure("ibi", 1000.0)
        result.set_measure("sdnn", 50.0)
        
        # Get time series measures
        ts_measures = result.get_time_series_measures()
        
        # Check time series measures
        assert ts_measures["bpm"] == 60.0
        assert ts_measures["ibi"] == 1000.0
        assert ts_measures["sdnn"] == 50.0
    
    def test_merge_from(self):
        """Test merging results."""
        result1 = AnalysisResult()
        result1.set_measure("bpm", 60.0)
        result1.set_working_data("peaks", [1, 2, 3])
        
        result2 = AnalysisResult()
        result2.set_measure("sdnn", 50.0)
        result2.set_working_data("rr_intervals", [1000, 1000])
        
        # Add segment to result2
        segment = AnalysisResult()
        segment.set_measure("bpm", 65.0)
        result2.add_segment(segment)
        
        # Merge result2 into result1
        result1.merge_from(result2)
        
        # Check merged result
        assert result1.get_measure("bpm") == 60.0  # Original value preserved
        assert result1.get_measure("sdnn") == 50.0  # Added from result2
        assert result1.get_working_data("peaks") == [1, 2, 3]  # Original value preserved
        assert result1.get_working_data("rr_intervals") == [1000, 1000]  # Added from result2
        assert len(result1.segments) == 1  # Segment added
        assert result1.segments[0].get_measure("bpm") == 65.0  # Segment value preserved
    
    def test_from_heartpy_output(self):
        """Test creating result from HeartPy output."""
        # Create HeartPy-like output
        wd = {"peaks": [1, 2, 3], "rr_intervals": [1000, 1000]}
        m = {"bpm": 60.0, "sdnn": 50.0}
        
        # Create result from HeartPy output
        result = AnalysisResult.from_heartpy_output(wd, m)
        
        # Check result
        assert result.get_measure("bpm") == 60.0
        assert result.get_measure("sdnn") == 50.0
        assert result.get_working_data("peaks") == [1, 2, 3]
        assert result.get_working_data("rr_intervals") == [1000, 1000]