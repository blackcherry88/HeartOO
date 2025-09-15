"""
Peak detection implementations for HeartOO.
"""

from typing import List, Optional, Dict, Any, Tuple
import numpy as np
from copy import deepcopy

from ..core.signal import HeartRateSignal
from ..core.result import AnalysisResult
from .processor import PeakDetector


class AdaptiveThresholdPeakDetector(PeakDetector):
    """Peak detector using adaptive thresholding."""
    
    def __init__(self, min_bpm: float = 40, max_bpm: float = 180, windowsize: float = 0.75):
        """Initialize adaptive threshold peak detector.
        
        Parameters
        ----------
        min_bpm : float
            Minimum BPM to consider
        max_bpm : float
            Maximum BPM to consider
        windowsize : float
            Size of window for rolling mean in seconds
        """
        super().__init__(min_bpm, max_bpm)
        self.windowsize = windowsize
        
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
        # Calculate rolling mean
        rol_mean = self._calculate_rolling_mean(signal.data, self.windowsize, signal.sample_rate)
        
        # Find best threshold
        best_ma_perc, peaks = self._fit_peaks(signal.data, rol_mean, signal.sample_rate)
        
        return peaks
    
    def _calculate_rolling_mean(self, data: np.ndarray, windowsize: float, sample_rate: float) -> np.ndarray:
        """Calculate rolling mean of signal.
        
        Parameters
        ----------
        data : numpy.ndarray
            Signal data
        windowsize : float
            Window size in seconds
        sample_rate : float
            Sample rate in Hz
            
        Returns
        -------
        numpy.ndarray
            Rolling mean of signal
        """
        # Calculate window size in samples
        window = int(windowsize * sample_rate)
        
        # Pad data for rolling mean calculation
        half_window = window // 2
        padded_data = np.pad(data, half_window, mode='edge')
        
        # Initialize rolling mean array
        rolling_mean = np.zeros(len(data))
        
        # Calculate rolling mean
        for i in range(len(data)):
            rolling_mean[i] = np.mean(padded_data[i:i+window])
            
        return rolling_mean
    
    def _detect_with_threshold(self, data: np.ndarray, rol_mean: np.ndarray, ma_perc: float) -> List[int]:
        """Detect peaks using a specific threshold.
        
        Parameters
        ----------
        data : numpy.ndarray
            Signal data
        rol_mean : numpy.ndarray
            Rolling mean of signal
        ma_perc : float
            Percentage to raise rolling mean
            
        Returns
        -------
        list of int
            Detected peak positions
        """
        # Calculate threshold
        mn = np.mean(rol_mean / 100) * ma_perc
        threshold = rol_mean + mn
        
        # Find positions where signal is above threshold
        peaksx = np.where((data > threshold))[0]
        peaksy = data[peaksx]
        
        # Find edges of continuous segments above threshold
        peakedges = np.concatenate((np.array([0]),
                                    np.where(np.diff(peaksx) > 1)[0],
                                    np.array([len(peaksx)])))
        
        # Find peaks in each segment
        peaklist = []
        for i in range(len(peakedges) - 1):
            segment = peaksx[peakedges[i]:peakedges[i+1]]
            segment_values = peaksy[peakedges[i]:peakedges[i+1]]
            
            if len(segment) > 0:
                max_idx = np.argmax(segment_values)
                peaklist.append(segment[max_idx])
                
        return peaklist
    
    def _fit_peaks(self, data: np.ndarray, rol_mean: np.ndarray, sample_rate: float) -> Tuple[float, List[int]]:
        """Find optimal threshold for peak detection.
        
        Parameters
        ----------
        data : numpy.ndarray
            Signal data
        rol_mean : numpy.ndarray
            Rolling mean of signal
        sample_rate : float
            Sample rate in Hz
            
        Returns
        -------
        tuple
            (best threshold percentage, detected peaks)
        """
        # List of thresholds to try
        ma_perc_list = [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100]
        
        best_rrsd = float('inf')
        best_ma = None
        best_peaks = []
        
        for ma_perc in ma_perc_list:
            # Detect peaks with current threshold
            peaks = self._detect_with_threshold(data, rol_mean, ma_perc)
            
            # Skip if no peaks detected
            if len(peaks) < 2:
                continue
                
            # Calculate RR intervals and BPM
            rr_intervals = (np.diff(peaks) / sample_rate) * 1000.0
            bpm = (len(peaks) / (len(data) / sample_rate)) * 60
            
            # Check if BPM is within acceptable range
            if self.min_bpm <= bpm <= self.max_bpm:
                # Calculate RR interval standard deviation
                rrsd = np.std(rr_intervals)
                
                # Update best if this is better
                if rrsd < best_rrsd:
                    best_rrsd = rrsd
                    best_ma = ma_perc
                    best_peaks = peaks
        
        # If no valid thresholds found, try again with wider BPM range
        if best_ma is None:
            min_bpm_orig = self.min_bpm
            max_bpm_orig = self.max_bpm
            
            try:
                self.min_bpm = 30
                self.max_bpm = 200
                # Try again with the same process but don't recurse further
                for ma_perc in ma_perc_list:
                    # Detect peaks with current threshold
                    peaks = self._detect_with_threshold(data, rol_mean, ma_perc)
                    
                    # Skip if no peaks detected
                    if len(peaks) < 2:
                        continue
                        
                    # Calculate RR intervals and BPM
                    rr_intervals = (np.diff(peaks) / sample_rate) * 1000.0
                    bpm = (len(peaks) / (len(data) / sample_rate)) * 60
                    
                    # Check if BPM is within acceptable range
                    if self.min_bpm <= bpm <= self.max_bpm:
                        # Calculate RR interval standard deviation
                        rrsd = np.std(rr_intervals)
                        
                        # Update best if this is better
                        if rrsd < best_rrsd:
                            best_rrsd = rrsd
                            best_ma = ma_perc
                            best_peaks = peaks
                
                # If still no valid threshold found, use default
                if best_ma is None:
                    best_ma = 20  # Default value from HeartPy
                    best_peaks = self._detect_with_threshold(data, rol_mean, best_ma)
                    
            finally:
                # Restore original BPM range
                self.min_bpm = min_bpm_orig
                self.max_bpm = max_bpm_orig
                
        # Final check if we found any peaks
        if not best_peaks:
            best_ma = 20  # Default value from HeartPy
            best_peaks = self._detect_with_threshold(data, rol_mean, best_ma)
            
        return best_ma, best_peaks
    
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
        result = super().process(signal, result)
        
        # Calculate RR intervals
        if len(signal.peaks) > 1:
            # Check peaks for anomalies
            rr_list = result.get_working_data('RR_list')
            peaks = result.get_working_data('peaklist')
            ybeat = result.get_working_data('ybeat')
            
            # Define RR range as mean +/- 30%, with minimum of 300ms
            mean_rr = np.mean(rr_list)
            thirty_perc = 0.3 * mean_rr
            
            if thirty_perc <= 300:
                upper_threshold = mean_rr + 300
                lower_threshold = mean_rr - 300
            else:
                upper_threshold = mean_rr + thirty_perc
                lower_threshold = mean_rr - thirty_perc
                
            # Identify peaks to exclude based on RR interval
            rem_idx = np.where((rr_list <= lower_threshold) | (rr_list >= upper_threshold))[0] + 1
            
            removed_beats = [peaks[i] for i in rem_idx if i < len(peaks)]
            removed_beats_y = [ybeat[i] for i in rem_idx if i < len(ybeat)]
            
            # Create binary mask for peaks
            binary_peaklist = np.ones(len(peaks))
            for i in rem_idx:
                if i < len(binary_peaklist):
                    binary_peaklist[i] = 0
                    
            # Update result
            result.set_working_data('removed_beats', removed_beats)
            result.set_working_data('removed_beats_y', removed_beats_y)
            result.set_working_data('binary_peaklist', binary_peaklist.tolist())
            
            # Calculate corrected RR intervals
            self._update_rr_intervals(result)
            
        return result
    
    def _update_rr_intervals(self, result: AnalysisResult) -> None:
        """Update RR intervals based on corrected peaks.
        
        Parameters
        ----------
        result : AnalysisResult
            Result to update
        """
        rr_list = result.get_working_data('RR_list', [])
        binary_peaklist = result.get_working_data('binary_peaklist', [])
        
        if len(rr_list) == 0 or len(binary_peaklist) == 0:
            return
            
        # Get RR intervals between valid peaks
        rr_list_cor = [rr_list[i] for i in range(len(rr_list)) 
                       if i < len(binary_peaklist)-1 and 
                       binary_peaklist[i] + binary_peaklist[i+1] == 2]
        
        # Create mask for rejected intervals
        rr_mask = [0 if (i < len(binary_peaklist)-1 and 
                          binary_peaklist[i] + binary_peaklist[i+1] == 2) 
                  else 1 for i in range(len(rr_list))]
        
        # Calculate differences between adjacent RR intervals
        rr_diff = []
        for i in range(len(rr_list_cor) - 1):
            rr_diff.append(abs(rr_list_cor[i] - rr_list_cor[i + 1]))
            
        # Square differences
        rr_sqdiff = [x**2 for x in rr_diff]
        
        # Update result
        result.set_working_data('RR_masklist', rr_mask)
        result.set_working_data('RR_list_cor', rr_list_cor)
        result.set_working_data('RR_diff', rr_diff)
        result.set_working_data('RR_sqdiff', rr_sqdiff)