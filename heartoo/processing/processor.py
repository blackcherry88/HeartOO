"""
Processor interface and base implementations for HeartOO.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union

from ..core.signal import HeartRateSignal
from ..core.result import AnalysisResult


class Processor(ABC):
    """Base interface for signal processors."""
    
    @abstractmethod
    def process(self, signal: HeartRateSignal, result: Optional[AnalysisResult] = None) -> AnalysisResult:
        """Process the signal and return results.
        
        Parameters
        ----------
        signal : HeartRateSignal
            The signal to process
        result : AnalysisResult, optional
            Existing result to update
            
        Returns
        -------
        AnalysisResult
            The updated or new result
        """
        pass


class FilterProcessor(Processor):
    """Base class for signal filter processors."""
    
    def __init__(self, cutoff: Union[float, List[float]], filtertype: str = 'lowpass'):
        """Initialize filter processor.
        
        Parameters
        ----------
        cutoff : float or list of float
            Cutoff frequency or frequencies for the filter
        filtertype : str
            Type of filter (lowpass, highpass, bandpass, bandstop)
        """
        self.cutoff = cutoff
        self.filtertype = filtertype
        
    @abstractmethod
    def apply_filter(self, signal: HeartRateSignal) -> HeartRateSignal:
        """Apply filter to signal.
        
        Parameters
        ----------
        signal : HeartRateSignal
            Signal to filter
            
        Returns
        -------
        HeartRateSignal
            Filtered signal
        """
        pass
        
    def process(self, signal: HeartRateSignal, result: Optional[AnalysisResult] = None) -> AnalysisResult:
        """Apply filter to signal and update result.
        
        Parameters
        ----------
        signal : HeartRateSignal
            Signal to filter
        result : AnalysisResult, optional
            Existing result to update
            
        Returns
        -------
        AnalysisResult
            Updated result
        """
        if result is None:
            result = AnalysisResult()
        
        # Apply filter
        filtered_signal = self.apply_filter(signal)
        
        # Update working data
        result.set_working_data('filtered_signal', filtered_signal.data)
        
        return result


class PeakDetector(Processor):
    """Base class for peak detection processors."""
    
    def __init__(self, min_bpm: float = 40, max_bpm: float = 180):
        """Initialize peak detector.
        
        Parameters
        ----------
        min_bpm : float
            Minimum BPM to consider
        max_bpm : float
            Maximum BPM to consider
        """
        self.min_bpm = min_bpm
        self.max_bpm = max_bpm
        
    @abstractmethod
    def detect_peaks(self, signal: HeartRateSignal) -> List[int]:
        """Detect peaks in the signal.
        
        Parameters
        ----------
        signal : HeartRateSignal
            Signal to analyze
            
        Returns
        -------
        list of int
            Peak positions (in samples)
        """
        pass
        
    def process(self, signal: HeartRateSignal, result: Optional[AnalysisResult] = None) -> AnalysisResult:
        """Detect peaks and update result.
        
        Parameters
        ----------
        signal : HeartRateSignal
            Signal to analyze
        result : AnalysisResult, optional
            Existing result to update
            
        Returns
        -------
        AnalysisResult
            Updated result with peak information
        """
        if result is None:
            result = AnalysisResult()
            
        # Get filtered signal if available
        data = result.get_working_data('filtered_signal', signal.data)
        
        # Create temporary signal for peak detection
        temp_signal = HeartRateSignal(data, signal.sample_rate, signal.metadata)
        
        # Detect peaks
        peaks = self.detect_peaks(temp_signal)
        
        # Update signal
        signal.peaks = peaks
        
        # Update result
        result.set_working_data('peaklist', peaks)
        result.set_working_data('ybeat', [signal.data[p] for p in peaks])
        
        # Calculate RR intervals
        if signal.rr_intervals is not None:
            result.set_working_data('RR_list', signal.rr_intervals)
            result.set_working_data('RR_indices', signal.rr_indices)
        
        return result


class HRVAnalyzer(Processor):
    """Base class for HRV analysis processors."""
    
    @abstractmethod
    def calculate_measures(self, signal: HeartRateSignal, rr_intervals: List[float]) -> Dict[str, Any]:
        """Calculate HRV measures.
        
        Parameters
        ----------
        signal : HeartRateSignal
            Signal to analyze
        rr_intervals : list of float
            RR intervals in milliseconds
            
        Returns
        -------
        dict
            Calculated measures
        """
        pass
        
    def process(self, signal: HeartRateSignal, result: Optional[AnalysisResult] = None) -> AnalysisResult:
        """Calculate HRV measures and update result.
        
        Parameters
        ----------
        signal : HeartRateSignal
            Signal to analyze
        result : AnalysisResult, optional
            Existing result to update
            
        Returns
        -------
        AnalysisResult
            Updated result with HRV measures
        """
        if result is None:
            result = AnalysisResult()
            
        # Get RR intervals
        rr_intervals = result.get_working_data('RR_list_cor', signal.rr_intervals)
        
        if rr_intervals is None or len(rr_intervals) < 2:
            return result
            
        # Calculate measures
        measures = self.calculate_measures(signal, rr_intervals)
        
        # Update result
        for key, value in measures.items():
            result.set_measure(key, value)
            
        return result