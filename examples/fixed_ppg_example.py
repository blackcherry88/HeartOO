"""
Fixed example script for analyzing a PPG signal using HeartOO.
"""

import numpy as np
import matplotlib.pyplot as plt
import os

# Create examples directory if it doesn't exist
os.makedirs('examples', exist_ok=True)

try:
    import heartpy as hp
    HEARTPY_AVAILABLE = True
except ImportError:
    HEARTPY_AVAILABLE = False
    print("HeartPy not available, using only HeartOO")

import heartoo as ho


def analyze_ppg_signal():
    """Analyze a PPG signal using HeartOO with fixed parameters."""
    print("HeartOO PPG Signal Analysis Example (Fixed)")
    print("==========================================")
    
    # Load PPG data from HeartPy
    if not HEARTPY_AVAILABLE:
        print("HeartPy not available, cannot load example data.")
        return
    
    print("Loading PPG example data...")
    data, timer = hp.load_exampledata(1)
    sample_rate = hp.get_samplerate_mstimer(timer)
    print(f"Loaded {len(data)} data points at {sample_rate:.2f} Hz")
    
    # Process with HeartPy for comparison
    print("\n1. HeartPy Results")
    print("----------------")
    wd_hp, m_hp = hp.process(data, sample_rate, calc_freq=True)
    
    print(f"Heart Rate: {m_hp['bpm']:.2f} BPM")
    print(f"SDNN: {m_hp['sdnn']:.2f} ms")
    print(f"RMSSD: {m_hp['rmssd']:.2f} ms")
    print(f"LF/HF Ratio: {m_hp['lf/hf']:.2f}")
    print(f"Peaks detected: {len(wd_hp['peaklist'])}")
    
    # Plot with HeartPy
    hp.plotter(wd_hp, m_hp, title="HeartPy Results")
    plt.savefig("examples/heartpy_ppg.png")
    plt.close()

    # Process with HeartOO compatibility API
    print("\n2. HeartOO Compatibility API Results")
    print("--------------------------------")
    wd_ho, m_ho = ho.process(data, sample_rate, calc_freq=True)
    
    print(f"Heart Rate: {m_ho['bpm']:.2f} BPM")
    print(f"SDNN: {m_ho['sdnn']:.2f} ms")
    print(f"RMSSD: {m_ho['rmssd']:.2f} ms")
    print(f"LF/HF Ratio: {m_ho['lf/hf']:.2f}")
    print(f"Peaks detected: {len(wd_ho['peaklist'])}")
    
    # Process with HeartOO using OO API - Fixed Version
    print("\n3. HeartOO Object-Oriented API Results (Fixed)")
    print("------------------------------------------")
    
    # Create HeartRateSignal
    ppg_signal = ho.HeartRateSignal(data, sample_rate)
    
    # Use PipelineBuilder.create_standard_pipeline() 
    # which has the same defaults as the compatibility API
    pipeline = ho.PipelineBuilder.create_standard_pipeline(calc_freq=True)
    result = pipeline.process(ppg_signal)
    
    # Print results
    print(f"Heart Rate: {result.get_measure('bpm'):.2f} BPM")
    print(f"SDNN: {result.get_measure('sdnn'):.2f} ms")
    print(f"RMSSD: {result.get_measure('rmssd'):.2f} ms")
    if result.get_measure('lf/hf') is not None:
        print(f"LF/HF Ratio: {result.get_measure('lf/hf'):.2f}")
    print(f"Peaks detected: {len(result.get_working_data('peaklist'))}")
    
    # Plot with HeartOO
    fig = ho.plot_signal(ppg_signal.data, ppg_signal.sample_rate,
                       peaks=result.get_working_data('peaklist'),
                       rejected_peaks=result.get_working_data('removed_beats', []),
                       title="HeartOO Results (Fixed)",
                       show=False)
    fig.savefig("examples/fixed_ppg_signal.png")
    plt.close()
    
    print("\nComparison:")
    print(f"BPM Difference (HeartPy vs HeartOO): {abs(m_hp['bpm'] - result.get_measure('bpm')):.4f}")
    print(f"SDNN Difference: {abs(m_hp['sdnn'] - result.get_measure('sdnn')):.4f}")
    print(f"RMSSD Difference: {abs(m_hp['rmssd'] - result.get_measure('rmssd')):.4f}")
    if m_hp['lf/hf'] is not None and result.get_measure('lf/hf') is not None:
        print(f"LF/HF Difference: {abs(m_hp['lf/hf'] - result.get_measure('lf/hf')):.4f}")
    
    print("\nPlots saved to examples/ directory")


if __name__ == "__main__":
    analyze_ppg_signal()