"""
Analysis implementations for HeartOO.
"""

from typing import List, Dict, Any, Optional, Union, Tuple
import warnings
import numpy as np
from scipy.interpolate import UnivariateSpline, interp1d
from scipy.signal import welch, periodogram

from ..core.signal import HeartRateSignal
from ..core.result import AnalysisResult
from .processor import HRVAnalyzer, Processor


class TimeDomainAnalyzer(HRVAnalyzer):
    """Time-domain HRV analyzer."""
    
    def calculate_measures(self, signal: HeartRateSignal, rr_intervals: List[float]) -> Dict[str, Any]:
        """Calculate time-domain HRV measures.
        
        Parameters
        ----------
        signal : HeartRateSignal
            Signal to analyze
        rr_intervals : list of float
            RR intervals in milliseconds
            
        Returns
        -------
        dict
            Time-domain HRV measures
        """
        measures = {}
        
        # Basic measures
        measures['bpm'] = 60000 / np.mean(rr_intervals)
        measures['ibi'] = np.mean(rr_intervals)
        
        # Variability measures
        measures['sdnn'] = np.std(rr_intervals)
        
        # Calculate RMSSD and related measures
        if len(rr_intervals) > 1:
            # Differences between adjacent RR intervals
            rr_diff = np.abs(np.diff(rr_intervals))
            rr_sqdiff = np.power(rr_diff, 2)
            
            measures['sdsd'] = np.std(rr_diff)
            measures['rmssd'] = np.sqrt(np.mean(rr_sqdiff))
            
            # Calculate pNN20 and pNN50
            nn20 = rr_diff[np.where(rr_diff > 20.0)]
            nn50 = rr_diff[np.where(rr_diff > 50.0)]
            
            try:
                measures['pnn20'] = float(len(nn20)) / float(len(rr_diff))
            except:
                measures['pnn20'] = np.nan
                
            try:
                measures['pnn50'] = float(len(nn50)) / float(len(rr_diff))
            except:
                measures['pnn50'] = np.nan
                
            # Calculate mean absolute deviation
            measures['hr_mad'] = np.mean(np.abs(rr_intervals - np.mean(rr_intervals)))
            
        return measures


class FrequencyDomainAnalyzer(HRVAnalyzer):
    """Frequency-domain HRV analyzer."""
    
    def __init__(self, method: str = 'welch', welch_wsize: float = 240.0, square_spectrum: bool = False):
        """Initialize frequency-domain analyzer.
        
        Parameters
        ----------
        method : str
            Method for spectral estimation ('welch', 'fft', 'periodogram')
        welch_wsize : float
            Window size in seconds for Welch's method
        square_spectrum : bool
            Whether to square the spectrum
        """
        self.method = method
        self.welch_wsize = welch_wsize
        self.square_spectrum = square_spectrum
        
    def calculate_measures(self, signal: HeartRateSignal, rr_intervals: List[float]) -> Dict[str, Any]:
        """Calculate frequency-domain HRV measures.
        
        Parameters
        ----------
        signal : HeartRateSignal
            Signal to analyze
        rr_intervals : list of float
            RR intervals in milliseconds
            
        Returns
        -------
        dict
            Frequency-domain HRV measures
        """
        measures = {}
        working_data = {}
        
        # Check if we have enough data
        if len(rr_intervals) <= 1:
            # Return NaN for all measures if not enough data
            return {
                'vlf': np.nan,
                'lf': np.nan,
                'hf': np.nan,
                'lf/hf': np.nan,
                'p_total': np.nan,
                'vlf_perc': np.nan,
                'lf_perc': np.nan,
                'hf_perc': np.nan,
                'lf_nu': np.nan,
                'hf_nu': np.nan
            }
            
        # Check if signal is short (less than 5 minutes)
        if np.sum(rr_intervals) < 300000:
            warnings.warn('Short signal for frequency analysis. Results may not be reliable.', 
                          UserWarning)
        
        # Aggregate RR-list and interpolate to a uniform sampling rate at 4x resolution
        rr_x = np.cumsum(rr_intervals)
        
        resamp_factor = 4
        datalen = int((len(rr_x) - 1) * resamp_factor)
        rr_x_new = np.linspace(int(rr_x[0]), int(rr_x[-1]), datalen)
        
        if len(rr_x) > 3:  # Need at least 4 points for cubic spline
            # Interpolate RR intervals to uniform sampling
            interpolation_func = UnivariateSpline(rr_x, rr_intervals, k=3)
            rr_interp = interpolation_func(rr_x_new)
            
            # Calculate sampling rate
            dt = np.mean(rr_intervals) / 1000  # in sec
            fs = 1 / dt  # about 1.1 Hz
            fs_new = fs * resamp_factor
            
            # Compute PSD
            if self.method == 'fft':
                frq = np.fft.fftfreq(datalen, d=(1 / fs_new))
                frq = frq[range(int(datalen / 2))]
                Y = np.fft.fft(rr_interp) / datalen
                Y = Y[range(int(datalen / 2))]
                psd = np.power(np.abs(Y), 2)
                
            elif self.method == 'periodogram':
                frq, psd = periodogram(rr_interp, fs=fs_new)
                
            elif self.method == 'welch':
                # Calculate window size
                nperseg = min(int(self.welch_wsize * fs_new), len(rr_x_new))
                frq, psd = welch(rr_interp, fs=fs_new, nperseg=nperseg)
                
            else:
                raise ValueError(f"Unknown method: {self.method}")
                
            # Square spectrum if requested
            if self.square_spectrum:
                psd = np.power(psd, 2)
                
            # Store frequency and PSD
            working_data['frq'] = frq
            working_data['psd'] = psd
            
            # Calculate power in different bands
            df = frq[1] - frq[0]  # frequency resolution
            
            # Standard frequency bands
            vlf_band = (frq >= 0.0033) & (frq < 0.04)
            lf_band = (frq >= 0.04) & (frq < 0.15)
            hf_band = (frq >= 0.15) & (frq < 0.4)
            
            # Calculate absolute power in each band using trapezoidal integration
            measures['vlf'] = np.trapz(psd[vlf_band], dx=df)
            measures['lf'] = np.trapz(psd[lf_band], dx=df)
            measures['hf'] = np.trapz(psd[hf_band], dx=df)
            
            # Calculate total power and LF/HF ratio
            measures['p_total'] = measures['vlf'] + measures['lf'] + measures['hf']
            measures['lf/hf'] = measures['lf'] / measures['hf'] if measures['hf'] > 0 else np.nan
            
            # Calculate relative powers
            if measures['p_total'] > 0:
                perc_factor = 100 / measures['p_total']
                measures['vlf_perc'] = measures['vlf'] * perc_factor
                measures['lf_perc'] = measures['lf'] * perc_factor
                measures['hf_perc'] = measures['hf'] * perc_factor
            else:
                measures['vlf_perc'] = np.nan
                measures['lf_perc'] = np.nan
                measures['hf_perc'] = np.nan
                
            # Calculate normalized units
            lf_hf_sum = measures['lf'] + measures['hf']
            if lf_hf_sum > 0:
                nu_factor = 100 / lf_hf_sum
                measures['lf_nu'] = measures['lf'] * nu_factor
                measures['hf_nu'] = measures['hf'] * nu_factor
            else:
                measures['lf_nu'] = np.nan
                measures['hf_nu'] = np.nan
                
            # Store interpolation data
            working_data['interp_rr_function'] = interpolation_func
            working_data['interp_rr_linspace'] = rr_x_new
        else:
            # Not enough points for interpolation
            measures = {
                'vlf': np.nan,
                'lf': np.nan,
                'hf': np.nan,
                'lf/hf': np.nan,
                'p_total': np.nan,
                'vlf_perc': np.nan,
                'lf_perc': np.nan,
                'hf_perc': np.nan,
                'lf_nu': np.nan,
                'hf_nu': np.nan
            }
            
        return measures


class NonlinearAnalyzer(HRVAnalyzer):
    """Nonlinear (Poincaré) HRV analyzer."""
    
    def calculate_measures(self, signal: HeartRateSignal, rr_intervals: List[float]) -> Dict[str, Any]:
        """Calculate nonlinear HRV measures.
        
        Parameters
        ----------
        signal : HeartRateSignal
            Signal to analyze
        rr_intervals : list of float
            RR intervals in milliseconds
            
        Returns
        -------
        dict
            Nonlinear HRV measures
        """
        measures = {}
        
        if len(rr_intervals) < 2:
            # Need at least 2 points for Poincaré analysis
            return {
                'sd1': np.nan,
                'sd2': np.nan,
                's': np.nan,
                'sd1/sd2': np.nan
            }
            
        # Generate vectors of adjacent RR intervals
        x_plus = rr_intervals[:-1]  # RR(n)
        x_minus = rr_intervals[1:]  # RR(n+1)
        
        # Calculate Poincaré measures
        x_one = (np.array(x_plus) - np.array(x_minus)) / np.sqrt(2)  # Perpendicular to line of identity
        x_two = (np.array(x_plus) + np.array(x_minus)) / np.sqrt(2)  # Along line of identity
        
        sd1 = np.sqrt(np.var(x_one))  # SD perpendicular to identity line
        sd2 = np.sqrt(np.var(x_two))  # SD along identity line
        s = np.pi * sd1 * sd2  # Area of ellipse
        
        measures['sd1'] = sd1
        measures['sd2'] = sd2
        measures['s'] = s
        measures['sd1/sd2'] = sd1 / sd2 if sd2 > 0 else np.nan
        
        return measures


class BreathingAnalyzer(Processor):
    """Breathing rate analyzer."""
    
    def __init__(self, method: str = 'welch', filter_breathing: bool = True, bw_cutoff: List[float] = [0.1, 0.4]):
        """Initialize breathing analyzer.
        
        Parameters
        ----------
        method : str
            Method for spectral estimation ('welch', 'fft', 'periodogram')
        filter_breathing : bool
            Whether to filter the breathing signal
        bw_cutoff : list of float
            Cutoff frequencies for breathing filter [low, high]
        """
        self.method = method
        self.filter_breathing = filter_breathing
        self.bw_cutoff = bw_cutoff
        
    def process(self, signal: HeartRateSignal, result: Optional[AnalysisResult] = None) -> AnalysisResult:
        """Calculate breathing rate and update result.
        
        Parameters
        ----------
        signal : HeartRateSignal
            Signal to analyze
        result : AnalysisResult, optional
            Existing result to update
            
        Returns
        -------
        AnalysisResult
            Updated result with breathing rate
        """
        if result is None:
            result = AnalysisResult()
            
        # Get RR intervals
        rr_intervals = result.get_working_data('RR_list_cor', signal.rr_intervals)
        
        if rr_intervals is None or len(rr_intervals) < 3:
            result.set_measure('breathingrate', np.nan)
            return result
            
        try:
            # Resample RR intervals to 1000Hz
            x = np.linspace(0, len(rr_intervals), len(rr_intervals))
            x_new = np.linspace(0, len(rr_intervals), int(np.sum(rr_intervals)))
            interp = UnivariateSpline(x, rr_intervals, k=3)
            breathing = interp(x_new)
            
            # Filter breathing signal if requested
            if self.filter_breathing:
                # Implement bandpass filter
                from scipy.signal import butter, filtfilt
                nyq = 500.0  # Nyquist frequency (1000Hz / 2)
                low = self.bw_cutoff[0] / nyq
                high = self.bw_cutoff[1] / nyq
                b, a = butter(2, [low, high], btype='band')
                breathing = filtfilt(b, a, breathing)
                
            # Calculate frequency spectrum
            if self.method == 'fft':
                datalen = len(breathing)
                frq = np.fft.fftfreq(datalen, d=0.001)  # 1000Hz
                frq = frq[range(int(datalen / 2))]
                Y = np.fft.fft(breathing) / datalen
                Y = Y[range(int(datalen / 2))]
                psd = np.power(np.abs(Y), 2)
                
            elif self.method == 'welch':
                nperseg = min(30000, len(breathing) // 10) if len(breathing) > 30000 else len(breathing)
                frq, psd = welch(breathing, fs=1000, nperseg=nperseg)
                
            elif self.method == 'periodogram':
                frq, psd = periodogram(breathing, fs=1000.0)
                
            else:
                raise ValueError(f"Unknown method: {self.method}")
                
            # Find max in frequency spectrum (breathing rate)
            breathingrate = frq[np.argmax(psd)]
            
            # Store result
            result.set_measure('breathingrate', breathingrate)
            result.set_working_data('breathing_signal', breathing)
            result.set_working_data('breathing_psd', psd)
            result.set_working_data('breathing_frq', frq)
            
        except Exception as e:
            # If anything goes wrong, set breathing rate to NaN
            result.set_measure('breathingrate', np.nan)
            
        return result