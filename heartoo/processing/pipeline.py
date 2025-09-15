"""
Processing pipeline for HeartOO.
"""

from typing import List, Optional, Dict, Any, Union
from copy import deepcopy

from ..core.signal import HeartRateSignal
from ..core.result import AnalysisResult
from .processor import Processor


class ProcessingPipeline:
    """Class representing a processing pipeline.
    
    A processing pipeline is a sequence of processors that are applied
    to a signal in order.
    """
    
    def __init__(self, processors: Optional[List[Processor]] = None):
        """Initialize a processing pipeline.
        
        Parameters
        ----------
        processors : list of Processor, optional
            Processors to add to the pipeline
        """
        self._processors = [] if processors is None else list(processors)
    
    @property
    def processors(self) -> List[Processor]:
        """Get the processors in the pipeline.
        
        Returns
        -------
        list of Processor
            The processors in the pipeline
        """
        return self._processors
        
    def add_processor(self, processor: Processor) -> 'ProcessingPipeline':
        """Add a processor to the pipeline.
        
        Parameters
        ----------
        processor : Processor
            Processor to add
            
        Returns
        -------
        ProcessingPipeline
            Self for method chaining
        """
        self._processors.append(processor)
        return self
        
    def remove_processor(self, index: int) -> None:
        """Remove a processor from the pipeline.
        
        Parameters
        ----------
        index : int
            Index of processor to remove
            
        Raises
        ------
        IndexError
            If index is out of range
        """
        self._processors.pop(index)
        
    def clear(self) -> None:
        """Remove all processors from the pipeline."""
        self._processors.clear()
        
    def process(self, signal: HeartRateSignal, result: Optional[AnalysisResult] = None) -> AnalysisResult:
        """Process a signal through the pipeline.
        
        Parameters
        ----------
        signal : HeartRateSignal
            Signal to process
        result : AnalysisResult, optional
            Existing result to update
            
        Returns
        -------
        AnalysisResult
            The result of processing
        """
        # Initialize result if not provided
        if result is None:
            result = AnalysisResult()
            
        # Store original signal in working data
        result.set_working_data('hr', signal.data)
        result.set_working_data('sample_rate', signal.sample_rate)
            
        # Process through each processor in sequence
        for processor in self._processors:
            result = processor.process(signal, result)
            
        return result
    
    def __len__(self) -> int:
        """Get the number of processors in the pipeline.
        
        Returns
        -------
        int
            The number of processors
        """
        return len(self._processors)
    
    def __getitem__(self, index: int) -> Processor:
        """Get a processor by index.
        
        Parameters
        ----------
        index : int
            Index of processor
            
        Returns
        -------
        Processor
            The processor at the specified index
            
        Raises
        ------
        IndexError
            If index is out of range
        """
        return self._processors[index]


class SegmentedPipeline(ProcessingPipeline):
    """Processing pipeline for segmented analysis.
    
    This pipeline processes the signal in segments and aggregates the results.
    """
    
    def __init__(self, 
                 processors: Optional[List[Processor]] = None,
                 segment_width: float = 120.0,
                 segment_overlap: float = 0.0,
                 segment_min_size: float = 20.0):
        """Initialize a segmented processing pipeline.
        
        Parameters
        ----------
        processors : list of Processor, optional
            Processors to add to the pipeline
        segment_width : float
            Width of each segment in seconds
        segment_overlap : float
            Overlap between segments as fraction (0 to 1)
        segment_min_size : float
            Minimum size of segment to process in seconds
        """
        super().__init__(processors)
        
        if not 0 <= segment_overlap < 1:
            raise ValueError("Segment overlap must be between 0 and 1")
            
        self.segment_width = segment_width
        self.segment_overlap = segment_overlap
        self.segment_min_size = segment_min_size
        
    def make_windows(self, signal: HeartRateSignal) -> List[tuple]:
        """Create windows for segmented processing.
        
        Parameters
        ----------
        signal : HeartRateSignal
            Signal to segment
            
        Returns
        -------
        list of tuple
            Start and end indices of each segment
        """
        data_len = len(signal)
        sample_rate = signal.sample_rate
        
        window = int(self.segment_width * sample_rate)
        stepsize = int((1 - self.segment_overlap) * window)
        min_size = int(self.segment_min_size * sample_rate)
        
        start = 0
        end = window
        
        slices = []
        while end < data_len:
            slices.append((start, end))
            start += stepsize
            end += stepsize
        
        # Add remaining data if it meets minimum size
        if data_len - start >= min_size:
            slices.append((start, data_len))
            
        return slices
        
    def process(self, signal: HeartRateSignal, result: Optional[AnalysisResult] = None) -> AnalysisResult:
        """Process a signal through the segmented pipeline.
        
        Parameters
        ----------
        signal : HeartRateSignal
            Signal to process
        result : AnalysisResult, optional
            Existing result to update
            
        Returns
        -------
        AnalysisResult
            The result of processing
        """
        if result is None:
            result = AnalysisResult()
            
        # Create segments
        windows = self.make_windows(signal)
        
        # Process each segment
        for start, end in windows:
            # Create segment signal
            segment_signal = HeartRateSignal(
                signal.data[start:end],
                signal.sample_rate,
                deepcopy(signal.metadata)
            )
            
            # Process segment
            segment_result = super().process(segment_signal)
            
            # Add segment indices
            segment_result.set_working_data('segment_indices', (start, end))
            
            # Add to main result
            result.add_segment(segment_result)
            
        # Aggregate segment results
        self._aggregate_segment_results(result)
            
        return result
    
    def _aggregate_segment_results(self, result: AnalysisResult) -> None:
        """Aggregate segment results into main result.
        
        Parameters
        ----------
        result : AnalysisResult
            Result to update with aggregated data
        """
        # Initialize dictionaries for aggregated measures
        aggregated_measures = {}
        
        # Collect measures from all segments
        for segment in result.segments:
            for key, value in segment.measures.items():
                if key not in aggregated_measures:
                    aggregated_measures[key] = []
                aggregated_measures[key].append(value)
                
        # Store aggregated measures in main result
        for key, values in aggregated_measures.items():
            result.set_measure(key, values)
            
        # Store segment indices
        indices = [segment.get_working_data('segment_indices') for segment in result.segments]
        result.set_working_data('segment_indices', indices)