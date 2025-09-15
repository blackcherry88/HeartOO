"""
Visualization utilities for HeartOO.
"""

from typing import Optional, List, Dict, Any, Union, Tuple
import numpy as np
import warnings

try:
    import matplotlib.pyplot as plt
    import matplotlib as mpl
except ImportError:
    warnings.warn("Matplotlib not found. Visualization functions will not work.")


def plot_signal(signal: np.ndarray, sample_rate: float, title: str = "Heart Rate Signal",
                figsize: Tuple[int, int] = (12, 4), peaks: Optional[List[int]] = None,
                rejected_peaks: Optional[List[int]] = None,
                show: bool = True) -> Optional[plt.Figure]:
    """Plot a heart rate signal with detected peaks.
    
    Parameters
    ----------
    signal : numpy.ndarray
        Heart rate signal data
    sample_rate : float
        Sample rate of the signal in Hz
    title : str
        Title for the plot
    figsize : tuple of int
        Figure size (width, height) in inches
    peaks : list of int, optional
        Indices of detected peaks
    rejected_peaks : list of int, optional
        Indices of rejected peaks
    show : bool
        Whether to show the plot
        
    Returns
    -------
    matplotlib.figure.Figure or None
        Figure object if show=False, None otherwise
    """
    try:
        # Create figure
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
        
        # Plot the signal
        time = np.arange(0, len(signal) / sample_rate, 1 / sample_rate)
        ax.plot(time, signal, label="Signal", color='blue', alpha=0.7)
        
        # Plot detected peaks
        if peaks is not None and len(peaks) > 0:
            ax.scatter(np.array(peaks) / sample_rate, signal[peaks],
                      color='green', label="Detected Peaks", zorder=3)
        
        # Plot rejected peaks
        if rejected_peaks is not None and len(rejected_peaks) > 0:
            ax.scatter(np.array(rejected_peaks) / sample_rate, signal[rejected_peaks],
                      color='red', label="Rejected Peaks", zorder=3)
        
        # Add labels and legend
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Amplitude")
        ax.set_title(title)
        ax.legend(loc="upper right")
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        
        if show:
            plt.show()
            return None
        else:
            return fig
    except Exception as e:
        warnings.warn(f"Error plotting signal: {str(e)}")
        return None


def plot_poincare(rr_intervals: np.ndarray, sd1: Optional[float] = None, sd2: Optional[float] = None,
                 title: str = "Poincaré Plot", figsize: Tuple[int, int] = (6, 6),
                 show: bool = True) -> Optional[plt.Figure]:
    """Create a Poincaré plot from RR intervals.
    
    Parameters
    ----------
    rr_intervals : numpy.ndarray
        Array of RR intervals in ms
    sd1 : float, optional
        SD1 value to plot ellipse
    sd2 : float, optional
        SD2 value to plot ellipse
    title : str
        Title for the plot
    figsize : tuple of int
        Figure size (width, height) in inches
    show : bool
        Whether to show the plot
        
    Returns
    -------
    matplotlib.figure.Figure or None
        Figure object if show=False, None otherwise
    """
    try:
        # Need at least 2 intervals
        if len(rr_intervals) < 2:
            warnings.warn("Not enough RR intervals for Poincaré plot")
            return None
        
        # Create figure
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, aspect='equal')
        
        # Create vectors of adjacent RR intervals
        x_plus = rr_intervals[:-1]  # RR(n)
        x_minus = rr_intervals[1:]  # RR(n+1)
        
        # Plot the points
        ax.scatter(x_plus, x_minus, color='blue', alpha=0.7, s=20)
        
        # Draw identity line
        min_val = min(np.min(x_plus), np.min(x_minus))
        max_val = max(np.max(x_plus), np.max(x_minus))
        ax.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5)
        
        # Draw ellipse if SD1 and SD2 are provided
        if sd1 is not None and sd2 is not None:
            from matplotlib.patches import Ellipse
            mean_rr = np.mean(rr_intervals)
            
            # Create ellipse centered at mean RR
            ellipse = Ellipse((mean_rr, mean_rr), 2 * sd2, 2 * sd1,
                             angle=-45, fc='none', edgecolor='red', lw=2)
            ax.add_patch(ellipse)
            
            # Annotate SD1 and SD2
            ax.annotate(f"SD1: {sd1:.2f} ms", xy=(0.05, 0.95), xycoords='axes fraction',
                       ha='left', va='top')
            ax.annotate(f"SD2: {sd2:.2f} ms", xy=(0.05, 0.9), xycoords='axes fraction',
                       ha='left', va='top')
        
        # Set labels and title
        ax.set_xlabel("RR(n) (ms)")
        ax.set_ylabel("RR(n+1) (ms)")
        ax.set_title(title)
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        
        if show:
            plt.show()
            return None
        else:
            return fig
    except Exception as e:
        warnings.warn(f"Error plotting Poincaré plot: {str(e)}")
        return None


def plot_breathing(breathing_signal: np.ndarray, breathing_rate: float, 
                  sample_rate: float = 1000.0, title: str = "Breathing Signal",
                  figsize: Tuple[int, int] = (12, 4),
                  show: bool = True) -> Optional[plt.Figure]:
    """Plot breathing signal and rate.
    
    Parameters
    ----------
    breathing_signal : numpy.ndarray
        Breathing signal data
    breathing_rate : float
        Breathing rate in Hz
    sample_rate : float
        Sample rate of the breathing signal in Hz
    title : str
        Title for the plot
    figsize : tuple of int
        Figure size (width, height) in inches
    show : bool
        Whether to show the plot
        
    Returns
    -------
    matplotlib.figure.Figure or None
        Figure object if show=False, None otherwise
    """
    try:
        # Create figure
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
        
        # Plot the signal
        time = np.arange(0, len(breathing_signal) / sample_rate, 1 / sample_rate)
        ax.plot(time, breathing_signal, color='blue', alpha=0.7)
        
        # Add breathing rate annotation
        breathing_rate_bpm = breathing_rate * 60
        ax.annotate(f"Breathing rate: {breathing_rate_bpm:.2f} breaths/min",
                   xy=(0.05, 0.95), xycoords='axes fraction',
                   ha='left', va='top')
        
        # Add labels and title
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Amplitude")
        ax.set_title(title)
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        
        if show:
            plt.show()
            return None
        else:
            return fig
    except Exception as e:
        warnings.warn(f"Error plotting breathing signal: {str(e)}")
        return None