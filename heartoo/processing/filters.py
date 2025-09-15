"""
Filter implementations for HeartOO.
"""

from typing import Union, List, Optional
import numpy as np
from scipy.signal import butter, filtfilt

from ..core.signal import HeartRateSignal
from .processor import FilterProcessor


class ButterworthFilter(FilterProcessor):
    """Butterworth filter implementation."""
    
    def __init__(self, cutoff: Union[float, List[float]], filtertype: str = 'lowpass', order: int = 4):
        """Initialize Butterworth filter.
        
        Parameters
        ----------
        cutoff : float or list of float
            Cutoff frequency or frequencies (normalized to Nyquist)
        filtertype : str
            Filter type ('lowpass', 'highpass', 'bandpass', 'bandstop')
        order : int
            Filter order
        """
        super().__init__(cutoff, filtertype)
        self.order = order
        
    def apply_filter(self, signal: HeartRateSignal) -> HeartRateSignal:
        """Apply Butterworth filter to signal.
        
        Parameters
        ----------
        signal : HeartRateSignal
            Signal to filter
            
        Returns
        -------
        HeartRateSignal
            Filtered signal
        """
        nyq = 0.5 * signal.sample_rate
        
        # Normalize cutoff
        if isinstance(self.cutoff, list):
            cutoff_norm = [cf / nyq for cf in self.cutoff]
        else:
            cutoff_norm = self.cutoff / nyq
            
        # Create filter coefficients
        b, a = butter(self.order, cutoff_norm, btype=self.filtertype)
        
        # Apply filter
        filtered_data = filtfilt(b, a, signal.data)
        
        return HeartRateSignal(filtered_data, signal.sample_rate, signal.metadata)


class HampelFilter(FilterProcessor):
    """Hampel filter implementation."""
    
    def __init__(self, window_size: int = 10, threshold: float = 3.0, filtertype: str = 'hampel'):
        """Initialize Hampel filter.
        
        Parameters
        ----------
        window_size : int
            Size of window for median calculation
        threshold : float
            Threshold for outlier detection (in MADs)
        filtertype : str
            Always 'hampel' for compatibility with FilterProcessor interface
        """
        super().__init__(window_size, filtertype)
        self.threshold = threshold
        
    def apply_filter(self, signal: HeartRateSignal) -> HeartRateSignal:
        """Apply Hampel filter to signal.
        
        Parameters
        ----------
        signal : HeartRateSignal
            Signal to filter
            
        Returns
        -------
        HeartRateSignal
            Filtered signal
        """
        data = signal.data.copy()
        window_size = int(self.cutoff)
        half_window = window_size // 2
        n = len(data)
        
        for i in range(n):
            # Define window boundaries
            start = max(0, i - half_window)
            end = min(n, i + half_window + 1)
            
            # Extract window
            window = data[start:end]
            
            # Calculate median and MAD
            median = np.median(window)
            mad = np.median(np.abs(window - median))
            
            # Avoid division by zero
            if mad == 0:
                mad = np.mean(np.abs(window - median)) or 1e-10
                
            # Check if point is an outlier
            if np.abs(data[i] - median) > self.threshold * mad:
                # Replace with median
                data[i] = median
                
        return HeartRateSignal(data, signal.sample_rate, signal.metadata)


class BaselineWanderRemovalFilter(FilterProcessor):
    """Filter to remove baseline wander."""
    
    def __init__(self, cutoff: float = 0.05):
        """Initialize baseline wander removal filter.
        
        Parameters
        ----------
        cutoff : float
            Cutoff frequency for high-pass filter
        """
        super().__init__(cutoff, filtertype='highpass')
        
    def apply_filter(self, signal: HeartRateSignal) -> HeartRateSignal:
        """Apply baseline wander removal filter to signal.
        
        Parameters
        ----------
        signal : HeartRateSignal
            Signal to filter
            
        Returns
        -------
        HeartRateSignal
            Filtered signal
        """
        # Use Butterworth high-pass filter
        butterworth = ButterworthFilter(self.cutoff, 'highpass')
        return butterworth.apply_filter(signal)