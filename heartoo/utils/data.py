"""
Data loading utilities for HeartOO.
"""

from typing import Tuple, List, Dict, Any, Union, Optional
import numpy as np
import os
import datetime
import warnings


def get_data(filepath: str, column_name: Optional[str] = None, 
             delim: str = ',', headerlines: int = 1) -> np.ndarray:
    """Load data from file.
    
    Parameters
    ----------
    filepath : str
        Path to the file
    column_name : str, optional
        Name of the column to extract
    delim : str
        Delimiter used in the file
    headerlines : int
        Number of header lines to skip
    
    Returns
    -------
    numpy.ndarray
        Loaded data
    """
    # Check if file exists
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    # Determine file type
    file_ext = os.path.splitext(filepath)[1].lower()
    
    if file_ext == '.csv' or file_ext == '.txt':
        # Load CSV/TXT file
        if column_name is None:
            # If no column specified, load all data
            data = np.genfromtxt(filepath, delimiter=delim, skip_header=headerlines)
            if len(data.shape) > 1 and data.shape[1] == 1:
                # If single column, flatten
                return data.flatten()
            return data
        else:
            # Load specific column
            data = np.genfromtxt(filepath, delimiter=delim, skip_header=headerlines-1, names=True)
            try:
                return data[column_name]
            except:
                # Column not found, show available columns
                available_cols = list(data.dtype.names)
                raise ValueError(f"Column '{column_name}' not found. Available columns: {available_cols}")
    
    elif file_ext == '.mat':
        try:
            from scipy.io import loadmat
            data = loadmat(filepath)
            if column_name is not None:
                if column_name in data:
                    return data[column_name].flatten()
                else:
                    available_cols = [k for k in data.keys() if not k.startswith('__')]
                    raise ValueError(f"Column '{column_name}' not found. Available columns: {available_cols}")
            else:
                # Try to find the data
                keys = [k for k in data.keys() if not k.startswith('__')]
                if len(keys) == 0:
                    raise ValueError("No data found in .mat file")
                elif len(keys) == 1:
                    return data[keys[0]].flatten()
                else:
                    # Multiple data arrays found, use the largest one
                    largest_key = max(keys, key=lambda k: data[k].size)
                    warnings.warn(f"Multiple arrays found, using largest one: '{largest_key}'")
                    return data[largest_key].flatten()
        except ImportError:
            raise ImportError("scipy.io is required to load .mat files")
    
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")


def load_exampledata(example: int = 0) -> Tuple[np.ndarray, Union[List, np.ndarray]]:
    """Load example data included with HeartOO.
    
    Parameters
    ----------
    example : int
        Which example dataset to load (0, 1, 2)
    
    Returns
    -------
    data : numpy.ndarray
        Heart rate signal data
    timer : list or numpy.ndarray
        Timing information for the signal
        
    Raises
    ------
    ValueError
        If example number is not valid
    """
    # Find the data directory
    module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(module_dir, 'data')
    
    # If directory doesn't exist, try to find it in HeartPy
    if not os.path.isdir(data_dir):
        try:
            import heartpy as hp
            # Extract example data from HeartPy
            return hp.load_exampledata(example)
        except ImportError:
            raise ImportError("HeartPy is required to load example data")
    
    # Load the data based on example number
    if example == 0:
        data_file = os.path.join(data_dir, 'example_data.csv')
        if not os.path.isfile(data_file):
            raise FileNotFoundError(f"Example data file not found: {data_file}")
        data = np.genfromtxt(data_file, delimiter=',')
        return data, []
    
    elif example == 1:
        data_file = os.path.join(data_dir, 'data.csv')
        timer_file = os.path.join(data_dir, 'data.log')
        if not os.path.isfile(data_file) or not os.path.isfile(timer_file):
            raise FileNotFoundError(f"Example data files not found in {data_dir}")
        data = np.genfromtxt(data_file, delimiter=',')
        timer = np.genfromtxt(timer_file, delimiter=',')
        return data, timer
    
    elif example == 2:
        data_file = os.path.join(data_dir, 'data2.csv')
        timer_file = os.path.join(data_dir, 'data2.log')
        if not os.path.isfile(data_file) or not os.path.isfile(timer_file):
            raise FileNotFoundError(f"Example data files not found in {data_dir}")
        data = np.genfromtxt(data_file, delimiter=',')
        
        # Load datetime strings
        with open(timer_file, 'r') as f:
            timer = [line.strip() for line in f]
        return data, timer
    
    else:
        raise ValueError(f"Invalid example number: {example}. Choose 0, 1, or 2.")


def get_samplerate_mstimer(timer_data: np.ndarray) -> float:
    """Calculate sample rate from millisecond timer data.
    
    Parameters
    ----------
    timer_data : numpy.ndarray
        Array of timestamps in milliseconds
    
    Returns
    -------
    float
        Sample rate in Hz
    """
    sample_rate = ((len(timer_data) / (timer_data[-1] - timer_data[0])) * 1000)
    return sample_rate


def get_samplerate_datetime(datetimedata: List[str], timeformat: str = '%Y-%m-%d %H:%M:%S.%f') -> float:
    """Calculate sample rate from datetime strings.
    
    Parameters
    ----------
    datetimedata : list of str
        List of datetime strings
    timeformat : str
        Format of the datetime strings
    
    Returns
    -------
    float
        Sample rate in Hz
    """
    datetimedata = np.asarray(datetimedata, dtype='str')
    elapsed = ((datetime.datetime.strptime(datetimedata[-1], timeformat) -
                datetime.datetime.strptime(datetimedata[0], timeformat)).total_seconds())
    sample_rate = len(datetimedata) / elapsed
    return sample_rate