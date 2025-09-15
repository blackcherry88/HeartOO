"""
Compatibility functions for HeartPy API.
"""

from typing import Dict, Any, List, Tuple, Union, Optional
import numpy as np
import warnings

from .core.signal import HeartRateSignal
from .core.result import AnalysisResult
from .processing.builder import PipelineBuilder


def process(hrdata: Union[List, np.ndarray], sample_rate: float, windowsize: float = 0.75,
            report_time: bool = False, calc_freq: bool = False, freq_method: str = 'welch',
            welch_wsize: float = 240, freq_square: bool = False, interp_clipping: bool = False,
            clipping_scale: bool = False, interp_threshold: int = 1020, hampel_correct: bool = False,
            bpmmin: int = 40, bpmmax: int = 180, reject_segmentwise: bool = False,
            high_precision: bool = False, high_precision_fs: float = 1000.0,
            breathing_method: str = 'welch', clean_rr: bool = False,
            clean_rr_method: str = 'quotient-filter',
            measures: Optional[Dict] = None,
            working_data: Optional[Dict] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Process heart rate data.
    
    Compatibility function that mimics the HeartPy process() function but uses
    the HeartOO object-oriented backend.
    
    Parameters
    ----------
    hrdata : list or array
        Heart rate signal data
    sample_rate : float
        Sample rate of the signal in Hz
    windowsize : float
        Size of the moving average window in seconds
    report_time : bool
        Whether to print processing time
    calc_freq : bool
        Whether to calculate frequency domain measures
    freq_method : str
        Method to use for frequency analysis ('welch', 'fft', 'periodogram')
    welch_wsize : float
        Window size for Welch's method in seconds
    freq_square : bool
        Whether to square the frequency spectrum
    interp_clipping : bool
        Whether to interpolate clipping segments
    clipping_scale : bool
        Whether to scale data before clipping detection
    interp_threshold : int
        Threshold for clipping detection
    hampel_correct : bool
        Whether to apply Hampel filter
    bpmmin : int
        Minimum BPM to consider
    bpmmax : int
        Maximum BPM to consider
    reject_segmentwise : bool
        Whether to reject segments with too many rejected beats
    high_precision : bool
        Whether to use high precision peak detection
    high_precision_fs : float
        Sample rate for high precision interpolation
    breathing_method : str
        Method to use for breathing estimation
    clean_rr : bool
        Whether to clean RR intervals
    clean_rr_method : str
        Method to use for RR interval cleaning
    measures : dict, optional
        Existing measures dictionary to update
    working_data : dict, optional
        Existing working_data dictionary to update
    
    Returns
    -------
    working_data : dict
        Dictionary containing intermediate data
    measures : dict
        Dictionary containing calculated measures
    """
    # Create signal object
    signal = HeartRateSignal(hrdata, sample_rate)
    
    # Create pipeline builder
    builder = PipelineBuilder()
    
    # Add preprocessing steps
    if interp_clipping:
        # TODO: Implement clipping interpolation
        pass
        
    if hampel_correct:
        builder.with_filter('hampel', 10, 'hampel')
        
    # Add peak detection
    builder.with_peak_detector('adaptive', bpmmin, bpmmax)
    
    # Add analyzers
    builder.with_time_domain_analyzer()
    builder.with_nonlinear_analyzer()
    
    if calc_freq:
        builder.with_frequency_domain_analyzer(
            method=freq_method,
            welch_wsize=welch_wsize,
            square_spectrum=freq_square
        )
        
    builder.with_breathing_analyzer(
        method=breathing_method,
        filter_breathing=True,
        bw_cutoff=[0.1, 0.4]
    )
    
    # Build pipeline
    pipeline = builder.build()
    
    # Create result object if needed
    result = None
    if measures is not None or working_data is not None:
        result = AnalysisResult()
        if measures is not None:
            for key, value in measures.items():
                result.set_measure(key, value)
        if working_data is not None:
            for key, value in working_data.items():
                result.set_working_data(key, value)
    
    # Process signal
    import time
    start_time = time.time()
    result = pipeline.process(signal, result)
    end_time = time.time()
    
    if report_time:
        print(f"\nFinished in {end_time - start_time:.8f} sec")
    
    # Return in HeartPy format
    return result.working_data, result.measures


def process_segmentwise(hrdata: Union[List, np.ndarray], sample_rate: float, segment_width: float = 120,
                        segment_overlap: float = 0, segment_min_size: float = 20,
                        replace_outliers: bool = False, outlier_method: str = 'iqr',
                        mode: str = 'full', ignore_badsignalwarning: bool = True,
                        **kwargs) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Process heart rate data in segments.
    
    Compatibility function that mimics the HeartPy process_segmentwise() function
    but uses the HeartOO object-oriented backend.
    
    Parameters
    ----------
    hrdata : list or array
        Heart rate signal data
    sample_rate : float
        Sample rate of the signal in Hz
    segment_width : float
        Width of each segment in seconds
    segment_overlap : float
        Overlap fraction between segments (0 to 1)
    segment_min_size : float
        Minimum size of the last segment in seconds
    replace_outliers : bool
        Whether to replace outliers in the measures
    outlier_method : str
        Method to use for outlier detection ('iqr', 'z-score')
    mode : str
        Processing mode ('full' or 'fast')
    ignore_badsignalwarning : bool
        Whether to ignore bad signal warnings
    **kwargs
        Additional arguments to pass to process()
    
    Returns
    -------
    working_data : dict
        Dictionary containing intermediate data
    measures : dict
        Dictionary containing calculated measures
    """
    # Create signal object
    signal = HeartRateSignal(hrdata, sample_rate)
    
    # Create pipeline builder
    builder = PipelineBuilder()
    
    # Configure for segmented processing
    builder.with_segmenter(
        segment_width=segment_width,
        segment_overlap=segment_overlap,
        segment_min_size=segment_min_size
    )
    
    # Add standard processing steps
    if 'calc_freq' in kwargs and kwargs['calc_freq']:
        builder.with_frequency_domain_analyzer(
            method=kwargs.get('freq_method', 'welch'),
            welch_wsize=kwargs.get('welch_wsize', 240),
            square_spectrum=kwargs.get('freq_square', False)
        )
    
    builder.with_peak_detector(
        'adaptive',
        min_bpm=kwargs.get('bpmmin', 40),
        max_bpm=kwargs.get('bpmmax', 180)
    )
    
    builder.with_time_domain_analyzer()
    builder.with_nonlinear_analyzer()
    builder.with_breathing_analyzer(
        method=kwargs.get('breathing_method', 'welch')
    )
    
    # Build pipeline
    pipeline = builder.build()
    
    # Process signal
    result = pipeline.process(signal)
    
    # Handle outlier replacement if needed
    if replace_outliers:
        # TODO: Implement outlier replacement for measures
        pass
    
    # Return in HeartPy format
    return result.working_data, result.measures


def process_rr(rr_list: List[float], threshold_rr: bool = False, clean_rr: bool = False,
               clean_rr_method: str = 'quotient-filter', calc_freq: bool = False,
               freq_method: str = 'welch', welch_wsize: float = 240, square_spectrum: bool = True,
               breathing_method: str = 'welch', measures: Optional[Dict] = None,
               working_data: Optional[Dict] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Process RR-intervals.
    
    Compatibility function that mimics the HeartPy process_rr() function
    but uses the HeartOO object-oriented backend.
    
    Parameters
    ----------
    rr_list : list
        List of RR-intervals in ms
    threshold_rr : bool
        Whether to apply threshold filtering to RR-intervals
    clean_rr : bool
        Whether to clean RR-intervals
    clean_rr_method : str
        Method to use for RR cleaning
    calc_freq : bool
        Whether to calculate frequency domain measures
    freq_method : str
        Method for frequency analysis
    welch_wsize : float
        Window size for Welch's method
    square_spectrum : bool
        Whether to square the frequency spectrum
    breathing_method : str
        Method to use for breathing estimation
    measures : dict, optional
        Existing measures dictionary to update
    working_data : dict, optional
        Existing working_data dictionary to update
    
    Returns
    -------
    working_data : dict
        Dictionary containing intermediate data
    measures : dict
        Dictionary containing calculated measures
    """
    # Create result object
    result = AnalysisResult()
    
    # Set initial RR data
    result.set_working_data('RR_list', rr_list)
    result.set_working_data('RR_masklist', [0] * len(rr_list))
    
    # Create pipeline builder
    builder = PipelineBuilder()
    
    # Add analyzers
    builder.with_time_domain_analyzer()
    builder.with_nonlinear_analyzer()
    
    if calc_freq:
        builder.with_frequency_domain_analyzer(
            method=freq_method,
            welch_wsize=welch_wsize,
            square_spectrum=square_spectrum
        )
    
    builder.with_breathing_analyzer(
        method=breathing_method
    )
    
    # Build pipeline
    pipeline = builder.build()
    
    # Create a dummy signal
    dummy_signal = HeartRateSignal(
        np.zeros(sum(rr_list)),  # Dummy data
        1000.0  # Sample rate doesn't matter for RR analysis
    )
    
    # Set RR intervals on the signal
    dummy_signal._rr_intervals = np.array(rr_list)
    
    # Process
    if measures is not None:
        for key, value in measures.items():
            result.set_measure(key, value)
            
    if working_data is not None:
        for key, value in working_data.items():
            result.set_working_data(key, value)
    
    result = pipeline.process(dummy_signal, result)
    
    # Return in HeartPy format
    return result.working_data, result.measures