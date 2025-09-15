"""
Core signal classes for HeartOO.
"""

from typing import Union, Optional, Dict, Any, List, Tuple
import numpy as np
from copy import deepcopy


class Signal:
    """Base class for signal data.
    
    This class represents a time series signal and provides basic operations.
    """
    
    def __init__(self, 
                 data: Union[List, np.ndarray], 
                 sample_rate: float, 
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize a signal object.
        
        Parameters
        ----------
        data : list or numpy.ndarray
            The signal data
        sample_rate : float
            The sample rate of the signal in Hz
        metadata : dict, optional
            Additional metadata about the signal
        """
        # Ensure data is numpy array
        self._data = np.asarray(data)
        
        # Validate sample rate
        if sample_rate <= 0:
            raise ValueError("Sample rate must be positive")
        self._sample_rate = float(sample_rate)
        
        # Initialize metadata
        self._metadata = {} if metadata is None else deepcopy(metadata)
    
    @property
    def data(self) -> np.ndarray:
        """Get the signal data.
        
        Returns
        -------
        numpy.ndarray
            The signal data
        """
        return self._data
    
    @property
    def sample_rate(self) -> float:
        """Get the sample rate of the signal.
        
        Returns
        -------
        float
            The sample rate in Hz
        """
        return self._sample_rate
    
    @property
    def duration(self) -> float:
        """Get the duration of the signal.
        
        Returns
        -------
        float
            The duration in seconds
        """
        return len(self._data) / self._sample_rate
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the signal metadata.
        
        Returns
        -------
        dict
            The signal metadata
        """
        return self._metadata
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value.
        
        Parameters
        ----------
        key : str
            The metadata key
        value : Any
            The metadata value
        """
        self._metadata[key] = value
    
    def get_slice(self, start_sec: float, end_sec: float) -> 'Signal':
        """Get a slice of the signal.
        
        Parameters
        ----------
        start_sec : float
            Start time in seconds
        end_sec : float
            End time in seconds
            
        Returns
        -------
        Signal
            A new signal object containing the slice
            
        Raises
        ------
        ValueError
            If start_sec or end_sec is out of range
        """
        if start_sec < 0 or end_sec > self.duration or start_sec >= end_sec:
            raise ValueError("Invalid time range")
        
        # Convert to samples
        start_idx = int(start_sec * self._sample_rate)
        end_idx = int(end_sec * self._sample_rate)
        
        # Create new signal with sliced data
        return self.__class__(
            data=self._data[start_idx:end_idx], 
            sample_rate=self._sample_rate,
            metadata=deepcopy(self._metadata)
        )
    
    def get_time_axis(self) -> np.ndarray:
        """Get the time axis for the signal.
        
        Returns
        -------
        numpy.ndarray
            The time axis in seconds
        """
        return np.arange(len(self._data)) / self._sample_rate
    
    def __len__(self) -> int:
        """Get the length of the signal in samples.
        
        Returns
        -------
        int
            The number of samples in the signal
        """
        return len(self._data)
    
    def __getitem__(self, key) -> Union[float, np.ndarray]:
        """Get signal data at a specific index or slice.
        
        Parameters
        ----------
        key : int, slice, or array-like
            The index, slice, or array of indices
            
        Returns
        -------
        float or numpy.ndarray
            The signal data at the specified index or slice
        """
        return self._data[key]


class HeartRateSignal(Signal):
    """Class for heart rate signal data.
    
    This class extends the base Signal class with heart rate specific functionality.
    """
    
    def __init__(self, 
                 data: Union[List, np.ndarray], 
                 sample_rate: float, 
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize a heart rate signal object.
        
        Parameters
        ----------
        data : list or numpy.ndarray
            The heart rate signal data
        sample_rate : float
            The sample rate of the signal in Hz
        metadata : dict, optional
            Additional metadata about the signal
        """
        super().__init__(data, sample_rate, metadata)
        
        # Heart rate specific properties
        self._peaks = None
        self._rr_intervals = None
        self._rr_indices = None
    
    @property
    def peaks(self) -> Optional[np.ndarray]:
        """Get the detected peaks in the signal.
        
        Returns
        -------
        numpy.ndarray or None
            The positions of detected peaks (in samples) if available
        """
        return self._peaks
    
    @peaks.setter
    def peaks(self, value: np.ndarray) -> None:
        """Set the detected peaks in the signal.
        
        Parameters
        ----------
        value : numpy.ndarray
            The positions of detected peaks (in samples)
        """
        if value is not None:
            self._peaks = np.asarray(value)
            # Reset derived properties
            self._rr_intervals = None
            self._rr_indices = None
    
    @property
    def rr_intervals(self) -> Optional[np.ndarray]:
        """Get the RR intervals (in milliseconds).
        
        Returns
        -------
        numpy.ndarray or None
            The RR intervals if peaks have been detected
        """
        if self._rr_intervals is None and self._peaks is not None:
            self._calculate_rr_intervals()
        return self._rr_intervals
    
    @property
    def rr_indices(self) -> Optional[List[Tuple[int, int]]]:
        """Get the RR interval indices.
        
        Returns
        -------
        list of tuple or None
            The start and end index of each RR interval if peaks have been detected
        """
        if self._rr_indices is None and self._peaks is not None:
            self._calculate_rr_intervals()
        return self._rr_indices
    
    def _calculate_rr_intervals(self) -> None:
        """Calculate RR intervals from the peaks."""
        if self._peaks is None or len(self._peaks) < 2:
            self._rr_intervals = np.array([])
            self._rr_indices = []
            return
            
        # Calculate intervals in milliseconds
        self._rr_intervals = (np.diff(self._peaks) / self.sample_rate) * 1000.0
        
        # Calculate indices
        self._rr_indices = [(self._peaks[i], self._peaks[i+1]) 
                           for i in range(len(self._peaks) - 1)]
    
    def get_heart_rate(self) -> float:
        """Calculate heart rate (BPM) from peaks.
        
        Returns
        -------
        float
            The heart rate in BPM
            
        Raises
        ------
        ValueError
            If no peaks have been detected
        """
        if self._peaks is None or len(self._peaks) < 2:
            raise ValueError("No peaks detected for heart rate calculation")
        
        # Calculate heart rate from mean RR interval
        return 60000 / np.mean(self.rr_intervals)
    
    def scale_data(self, lower: float = 0, upper: float = 1024) -> 'HeartRateSignal':
        """Scale signal data to a specified range.
        
        Parameters
        ----------
        lower : float
            Lower bound for scaling
        upper : float
            Upper bound for scaling
            
        Returns
        -------
        HeartRateSignal
            A new signal with scaled data
        """
        rng = np.max(self.data) - np.min(self.data)
        minimum = np.min(self.data)
        scaled_data = (upper - lower) * ((self.data - minimum) / rng) + lower
        
        return HeartRateSignal(scaled_data, self.sample_rate, self.metadata)