"""
Pipeline builder for HeartOO.
"""

from typing import Optional, Dict, Any, List, Union, Type
from copy import deepcopy

from ..core.signal import HeartRateSignal
from ..core.result import AnalysisResult
from .processor import Processor, FilterProcessor, PeakDetector, HRVAnalyzer
from .pipeline import ProcessingPipeline, SegmentedPipeline
from .filters import ButterworthFilter, HampelFilter, BaselineWanderRemovalFilter
from .peak_detectors import AdaptiveThresholdPeakDetector
from .analyzers import (
    TimeDomainAnalyzer, 
    FrequencyDomainAnalyzer, 
    NonlinearAnalyzer,
    BreathingAnalyzer
)


class PipelineBuilder:
    """Builder for creating processing pipelines.
    
    This class uses the Builder pattern to create processing pipelines
    with a fluent interface.
    """
    
    def __init__(self):
        """Initialize a pipeline builder."""
        self._processors = []
        self._segment_width = 120.0
        self._segment_overlap = 0.0
        self._segment_min_size = 20.0
        self._segmented = False
        
    def with_filter(self, 
                    filter_type: str,
                    cutoff: Union[float, List[float]],
                    filtertype: str = 'lowpass') -> 'PipelineBuilder':
        """Add a filter to the pipeline.
        
        Parameters
        ----------
        filter_type : str
            Type of filter ('butterworth', 'hampel', 'baseline_wander')
        cutoff : float or list of float
            Cutoff frequency or frequencies for the filter
        filtertype : str
            Type of filter operation (lowpass, highpass, bandpass, bandstop)
            
        Returns
        -------
        PipelineBuilder
            Self for method chaining
            
        Raises
        ------
        ValueError
            If filter_type is not recognized
        """
        if filter_type.lower() == 'butterworth':
            self._processors.append(ButterworthFilter(cutoff, filtertype))
        elif filter_type.lower() == 'hampel':
            self._processors.append(HampelFilter(cutoff, filtertype))
        elif filter_type.lower() == 'baseline_wander':
            self._processors.append(BaselineWanderRemovalFilter())
        else:
            raise ValueError(f"Unknown filter type: {filter_type}")
            
        return self
        
    def with_peak_detector(self, 
                          detector_type: str = 'adaptive',
                          min_bpm: float = 40, 
                          max_bpm: float = 180) -> 'PipelineBuilder':
        """Add a peak detector to the pipeline.
        
        Parameters
        ----------
        detector_type : str
            Type of peak detector ('adaptive')
        min_bpm : float
            Minimum BPM to consider
        max_bpm : float
            Maximum BPM to consider
            
        Returns
        -------
        PipelineBuilder
            Self for method chaining
            
        Raises
        ------
        ValueError
            If detector_type is not recognized
        """
        if detector_type.lower() == 'adaptive':
            self._processors.append(AdaptiveThresholdPeakDetector(min_bpm, max_bpm))
        else:
            raise ValueError(f"Unknown peak detector type: {detector_type}")
            
        return self
        
    def with_time_domain_analyzer(self) -> 'PipelineBuilder':
        """Add a time-domain analyzer to the pipeline.
        
        Returns
        -------
        PipelineBuilder
            Self for method chaining
        """
        self._processors.append(TimeDomainAnalyzer())
        return self
        
    def with_frequency_domain_analyzer(self, 
                                      method: str = 'welch',
                                      welch_wsize: float = 240.0,
                                      square_spectrum: bool = False) -> 'PipelineBuilder':
        """Add a frequency-domain analyzer to the pipeline.
        
        Parameters
        ----------
        method : str
            Method for spectral estimation ('welch', 'fft', 'periodogram')
        welch_wsize : float
            Window size in seconds for Welch's method
        square_spectrum : bool
            Whether to square the spectrum
            
        Returns
        -------
        PipelineBuilder
            Self for method chaining
        """
        self._processors.append(FrequencyDomainAnalyzer(
            method=method,
            welch_wsize=welch_wsize,
            square_spectrum=square_spectrum
        ))
        return self
        
    def with_nonlinear_analyzer(self) -> 'PipelineBuilder':
        """Add a nonlinear (Poincaré) analyzer to the pipeline.
        
        Returns
        -------
        PipelineBuilder
            Self for method chaining
        """
        self._processors.append(NonlinearAnalyzer())
        return self
        
    def with_breathing_analyzer(self, 
                              method: str = 'welch',
                              filter_breathing: bool = True,
                              bw_cutoff: List[float] = [0.1, 0.4]) -> 'PipelineBuilder':
        """Add a breathing analyzer to the pipeline.
        
        Parameters
        ----------
        method : str
            Method for spectral estimation ('welch', 'fft', 'periodogram')
        filter_breathing : bool
            Whether to filter the breathing signal
        bw_cutoff : list of float
            Cutoff frequencies for breathing filter [low, high]
            
        Returns
        -------
        PipelineBuilder
            Self for method chaining
        """
        self._processors.append(BreathingAnalyzer(
            method=method,
            filter_breathing=filter_breathing,
            bw_cutoff=bw_cutoff
        ))
        return self
        
    def with_segmenter(self, 
                      segment_width: float = 120.0,
                      segment_overlap: float = 0.0,
                      segment_min_size: float = 20.0) -> 'PipelineBuilder':
        """Configure the pipeline for segmented processing.
        
        Parameters
        ----------
        segment_width : float
            Width of each segment in seconds
        segment_overlap : float
            Overlap between segments as fraction (0 to 1)
        segment_min_size : float
            Minimum size of segment to process in seconds
            
        Returns
        -------
        PipelineBuilder
            Self for method chaining
        """
        self._segmented = True
        self._segment_width = segment_width
        self._segment_overlap = segment_overlap
        self._segment_min_size = segment_min_size
        return self
        
    def with_custom_processor(self, processor: Processor) -> 'PipelineBuilder':
        """Add a custom processor to the pipeline.
        
        Parameters
        ----------
        processor : Processor
            Custom processor to add
            
        Returns
        -------
        PipelineBuilder
            Self for method chaining
        """
        self._processors.append(processor)
        return self
        
    def build(self) -> ProcessingPipeline:
        """Build the processing pipeline.
        
        Returns
        -------
        ProcessingPipeline
            The constructed processing pipeline
        """
        if self._segmented:
            return SegmentedPipeline(
                processors=self._processors.copy(),
                segment_width=self._segment_width,
                segment_overlap=self._segment_overlap,
                segment_min_size=self._segment_min_size
            )
        else:
            return ProcessingPipeline(self._processors.copy())
    
    @classmethod
    def create_standard_pipeline(cls, calc_freq: bool = False) -> ProcessingPipeline:
        """Create a standard processing pipeline.
        
        Parameters
        ----------
        calc_freq : bool
            Whether to include frequency domain analysis
            
        Returns
        -------
        ProcessingPipeline
            Standard processing pipeline
        """
        builder = cls()
        
        # Add standard processors
        builder.with_peak_detector()
        builder.with_time_domain_analyzer()
        builder.with_nonlinear_analyzer()
        builder.with_breathing_analyzer()
        
        if calc_freq:
            builder.with_frequency_domain_analyzer()
            
        return builder.build()