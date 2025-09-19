"""
Analysis result classes for HeartOO.
"""

from typing import Dict, Any, List, Optional, Union, Tuple
import numpy as np
from copy import deepcopy
import json
from pathlib import Path


class AnalysisResult:
    """Class to store and manage heart rate analysis results."""
    
    def __init__(self):
        """Initialize an empty analysis result."""
        self._measures = {}
        self._working_data = {}
        self._segments = []
        
    @property
    def measures(self) -> Dict[str, Any]:
        """Get all analysis measures.
        
        Returns
        -------
        dict
            All calculated measures
        """
        return self._measures
    
    @property
    def working_data(self) -> Dict[str, Any]:
        """Get all working data.
        
        Returns
        -------
        dict
            All intermediate working data
        """
        return self._working_data
    
    @property
    def segments(self) -> List['AnalysisResult']:
        """Get segment results for segmented analysis.
        
        Returns
        -------
        list of AnalysisResult
            Results for each segment
        """
        return self._segments
        
    def set_measure(self, key: str, value: Any) -> None:
        """Set a specific measure.
        
        Parameters
        ----------
        key : str
            The measure name
        value : any
            The measure value
        """
        self._measures[key] = value
        
    def get_measure(self, key: str, default: Any = None) -> Any:
        """Get a specific measure.
        
        Parameters
        ----------
        key : str
            The measure name
        default : any, optional
            Default value if measure doesn't exist
            
        Returns
        -------
        any
            The measure value or default
        """
        return self._measures.get(key, default)
        
    def set_working_data(self, key: str, value: Any) -> None:
        """Set specific working data.
        
        Parameters
        ----------
        key : str
            The data name
        value : any
            The data value
        """
        self._working_data[key] = value
        
    def get_working_data(self, key: str, default: Any = None) -> Any:
        """Get specific working data.
        
        Parameters
        ----------
        key : str
            The data name
        default : any, optional
            Default value if data doesn't exist
            
        Returns
        -------
        any
            The data value or default
        """
        return self._working_data.get(key, default)
        
    def add_segment(self, segment: 'AnalysisResult') -> None:
        """Add a segment result.
        
        Parameters
        ----------
        segment : AnalysisResult
            The segment result to add
        """
        self._segments.append(segment)
        
    def get_measures_by_category(self, category: str) -> Dict[str, Any]:
        """Get measures by category prefix.
        
        Parameters
        ----------
        category : str
            The category prefix (e.g., 'hrv_' for HRV measures)
            
        Returns
        -------
        dict
            Measures in the specified category
        """
        return {k: v for k, v in self._measures.items() 
                if k.startswith(category)}
                
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary.
        
        Returns
        -------
        dict
            Dictionary containing all measures and working data
        """
        result = {
            'measures': deepcopy(self._measures),
            'working_data': deepcopy(self._working_data)
        }
        
        if self._segments:
            result['segments'] = [s.to_dict() for s in self._segments]
            
        return result
    
    def get_time_series_measures(self) -> Dict[str, Any]:
        """Get time-domain HRV measures.
        
        Returns
        -------
        dict
            Time-domain HRV measures
        """
        return {
            'bpm': self.get_measure('bpm'),
            'ibi': self.get_measure('ibi'),
            'sdnn': self.get_measure('sdnn'),
            'sdsd': self.get_measure('sdsd'),
            'rmssd': self.get_measure('rmssd'),
            'pnn20': self.get_measure('pnn20'),
            'pnn50': self.get_measure('pnn50'),
            'hr_mad': self.get_measure('hr_mad')
        }
    
    def get_frequency_measures(self) -> Dict[str, Any]:
        """Get frequency-domain HRV measures.
        
        Returns
        -------
        dict
            Frequency-domain HRV measures
        """
        return {
            'lf': self.get_measure('lf'),
            'hf': self.get_measure('hf'),
            'lf/hf': self.get_measure('lf/hf'),
            'vlf': self.get_measure('vlf'),
            'p_total': self.get_measure('p_total'),
            'vlf_perc': self.get_measure('vlf_perc'),
            'lf_perc': self.get_measure('lf_perc'),
            'hf_perc': self.get_measure('hf_perc'),
            'lf_nu': self.get_measure('lf_nu'),
            'hf_nu': self.get_measure('hf_nu')
        }
    
    def get_nonlinear_measures(self) -> Dict[str, Any]:
        """Get nonlinear (Poincaré) HRV measures.
        
        Returns
        -------
        dict
            Nonlinear HRV measures
        """
        return {
            'sd1': self.get_measure('sd1'),
            'sd2': self.get_measure('sd2'),
            's': self.get_measure('s'),
            'sd1/sd2': self.get_measure('sd1/sd2')
        }
    
    def get_breathing_measures(self) -> Dict[str, Any]:
        """Get breathing measures.
        
        Returns
        -------
        dict
            Breathing measures
        """
        return {
            'breathingrate': self.get_measure('breathingrate')
        }
    
    def merge_from(self, other: 'AnalysisResult') -> None:
        """Merge data from another AnalysisResult.
        
        Parameters
        ----------
        other : AnalysisResult
            The result to merge from
        """
        # Merge measures
        self._measures.update(other.measures)
        
        # Merge working data
        self._working_data.update(other.working_data)
        
        # Append segments (if any)
        if other.segments:
            self._segments.extend(other.segments)
    
    def save_to_json(self, filepath: Union[str, Path]) -> None:
        """Save analysis result to JSON file.
        
        Parameters
        ----------
        filepath : str or Path
            Path to save the JSON file
        """
        data = self.to_dict()
        # Convert numpy arrays to lists for JSON serialization
        data = self._convert_numpy_for_json(data)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load_from_json(cls, filepath: Union[str, Path]) -> 'AnalysisResult':
        """Load analysis result from JSON file.
        
        Parameters
        ----------
        filepath : str or Path
            Path to the JSON file
            
        Returns
        -------
        AnalysisResult
            Loaded analysis result
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        result = cls()
        result._measures = data.get('measures', {})
        result._working_data = data.get('working_data', {})
        
        # Load segments if present
        if 'segments' in data:
            for segment_data in data['segments']:
                segment = cls()
                segment._measures = segment_data.get('measures', {})
                segment._working_data = segment_data.get('working_data', {})
                result._segments.append(segment)
        
        return result
    
    def compare_with(self, other: 'AnalysisResult', tolerance: float = 1e-6) -> Dict[str, Any]:
        """Compare this result with another result.
        
        Parameters
        ----------
        other : AnalysisResult
            The other result to compare with
        tolerance : float, optional
            Tolerance for numerical comparisons
            
        Returns
        -------
        dict
            Comparison results with differences
        """
        comparison = {
            'measures_diff': {},
            'measures_only_in_self': [],
            'measures_only_in_other': [],
            'identical_measures': [],
            'different_measures': []
        }
        
        # Compare measures
        all_keys = set(self._measures.keys()) | set(other._measures.keys())
        
        for key in all_keys:
            if key not in self._measures:
                comparison['measures_only_in_other'].append(key)
            elif key not in other._measures:
                comparison['measures_only_in_self'].append(key)
            else:
                val1, val2 = self._measures[key], other._measures[key]
                if self._values_equal(val1, val2, tolerance):
                    comparison['identical_measures'].append(key)
                else:
                    comparison['different_measures'].append(key)
                    comparison['measures_diff'][key] = {
                        'self': val1,
                        'other': val2,
                        'diff': self._calculate_diff(val1, val2)
                    }
        
        return comparison
    
    @staticmethod
    def compare_json_files(file1: Union[str, Path], file2: Union[str, Path], tolerance: float = 1e-6) -> Dict[str, Any]:
        """Compare two JSON result files.
        
        Parameters
        ----------
        file1 : str or Path
            Path to first JSON file
        file2 : str or Path
            Path to second JSON file
        tolerance : float, optional
            Tolerance for numerical comparisons
            
        Returns
        -------
        dict
            Comparison results
        """
        result1 = AnalysisResult.load_from_json(file1)
        result2 = AnalysisResult.load_from_json(file2)
        return result1.compare_with(result2, tolerance)
    
    def _convert_numpy_for_json(self, obj: Any) -> Any:
        """Convert numpy arrays to lists for JSON serialization."""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_numpy_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_for_json(item) for item in obj]
        return obj
    
    def _values_equal(self, val1: Any, val2: Any, tolerance: float) -> bool:
        """Check if two values are equal within tolerance."""
        try:
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                return abs(val1 - val2) <= tolerance
            elif isinstance(val1, (list, np.ndarray)) and isinstance(val2, (list, np.ndarray)):
                arr1, arr2 = np.array(val1), np.array(val2)
                return arr1.shape == arr2.shape and np.allclose(arr1, arr2, atol=tolerance)
            else:
                return val1 == val2
        except:
            return val1 == val2
    
    def _calculate_diff(self, val1: Any, val2: Any) -> Any:
        """Calculate difference between two values."""
        try:
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                return val2 - val1
            elif isinstance(val1, (list, np.ndarray)) and isinstance(val2, (list, np.ndarray)):
                return (np.array(val2) - np.array(val1)).tolist()
            else:
                return f"'{val1}' vs '{val2}'"
        except:
            return f"'{val1}' vs '{val2}'"
    
    @classmethod
    def from_heartpy_output(cls, working_data: Dict[str, Any], measures: Dict[str, Any]) -> 'AnalysisResult':
        """Create an AnalysisResult from HeartPy output.
        
        Parameters
        ----------
        working_data : dict
            HeartPy working_data dictionary
        measures : dict
            HeartPy measures dictionary
            
        Returns
        -------
        AnalysisResult
            New AnalysisResult containing the HeartPy data
        """
        result = cls()
        result._measures = deepcopy(measures)
        result._working_data = deepcopy(working_data)
        return result