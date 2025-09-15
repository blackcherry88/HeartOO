"""
Example script for analyzing a PPG signal using HeartOO.

This is a Python script version of the Jupyter notebook example from HeartPy:
'Analysing_a_PPG_signal.ipynb'
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
    """Analyze a PPG signal using HeartOO."""
    print("HeartOO PPG Signal Analysis Example")
    print("===================================")
    
    # Load PPG data from HeartPy
    if not HEARTPY_AVAILABLE:
        print("HeartPy not available, cannot load example data.")
        return
    
    print("Loading PPG example data...")
    data, timer = hp.load_exampledata(1)
    sample_rate = hp.get_samplerate_mstimer(timer)
    print(f"Loaded {len(data)} data points at {sample_rate:.2f} Hz")
    
    # 1. Object-Oriented Approach
    print("\n1. Object-Oriented Approach")
    print("--------------------------")
    
    # Create HeartRateSignal
    print("Creating HeartRateSignal...")
    ppg_signal = ho.HeartRateSignal(data, sample_rate)
    
    # Create processing pipeline
    print("Building processing pipeline...")
    builder = ho.PipelineBuilder()
    
    # Configure pipeline
    pipeline = builder \
        .with_filter('butterworth', cutoff=0.05, filtertype='highpass') \
        .with_peak_detector('adaptive', min_bpm=40, max_bpm=180) \
        .with_time_domain_analyzer() \
        .with_frequency_domain_analyzer(method='welch') \
        .with_nonlinear_analyzer() \
        .with_breathing_analyzer() \
        .build()
    
    # Process signal
    print("Processing signal...")
    result = pipeline.process(ppg_signal)
    
    # Get results
    print("\nResults:")
    print(f"Heart Rate: {result.get_measure('bpm'):.2f} BPM")
    print(f"IBI: {result.get_measure('ibi'):.2f} ms")
    print(f"SDNN: {result.get_measure('sdnn'):.2f} ms")
    print(f"RMSSD: {result.get_measure('rmssd'):.2f} ms")
    print(f"pNN20: {result.get_measure('pnn20')*100:.2f}%")
    print(f"pNN50: {result.get_measure('pnn50')*100:.2f}%")
    
    print("\nFrequency Domain Measures:")
    print(f"LF: {result.get_measure('lf'):.2f}")
    print(f"HF: {result.get_measure('hf'):.2f}")
    print(f"LF/HF Ratio: {result.get_measure('lf/hf'):.2f}")
    
    print("\nNonlinear Measures:")
    print(f"SD1: {result.get_measure('sd1'):.2f} ms")
    print(f"SD2: {result.get_measure('sd2'):.2f} ms")
    print(f"SD1/SD2 Ratio: {result.get_measure('sd1/sd2'):.2f}")
    
    print("\nBreathing Rate:")
    print(f"Breathing Rate: {result.get_measure('breathingrate'):.3f} Hz "
          f"({result.get_measure('breathingrate')*60:.2f} breaths/min)")
    
    # Plot results
    print("\nGenerating plots...")
    
    # Plot signal with detected peaks
    fig = ho.plot_signal(ppg_signal.data, ppg_signal.sample_rate,
                       peaks=result.get_working_data('peaklist'),
                       rejected_peaks=result.get_working_data('removed_beats', []),
                       title="PPG Signal with Detected Peaks",
                       show=False)
    fig.savefig("examples/ppg_signal_peaks.png")
    plt.close()
    
    # Plot Poincaré
    fig = ho.plot_poincare(result.get_working_data('RR_list_cor'),
                          sd1=result.get_measure('sd1'),
                          sd2=result.get_measure('sd2'),
                          title="HeartOO Poincaré Plot for PPG Signal",
                          show=False)
    fig.savefig("examples/ppg_poincare.png")
    plt.close()
    
    # 2. HeartPy-Compatible API
    print("\n2. HeartPy-Compatible API")
    print("------------------------")
    
    # Process with HeartOO using HeartPy-compatible API
    wd, m = ho.process(data, sample_rate, calc_freq=True)
    
    print("\nResults using compatibility API:")
    print(f"Heart Rate: {m['bpm']:.2f} BPM")
    print(f"SDNN: {m['sdnn']:.2f} ms")
    print(f"RMSSD: {m['rmssd']:.2f} ms")
    print(f"LF/HF Ratio: {m['lf/hf']:.2f}")
    
    print("\nPlots saved to examples/ directory")
    
    # 3. Compare with Original HeartPy (if available)
    if HEARTPY_AVAILABLE:
        print("\n3. Comparison with HeartPy")
        print("------------------------")
        
        # Process with HeartPy
        wd_hp, m_hp = hp.process(data, sample_rate, calc_freq=True)
        
        print("\nHeartPy Results:")
        print(f"Heart Rate: {m_hp['bpm']:.2f} BPM")
        print(f"SDNN: {m_hp['sdnn']:.2f} ms")
        print(f"RMSSD: {m_hp['rmssd']:.2f} ms")
        print(f"LF/HF Ratio: {m_hp['lf/hf']:.2f}")
        
        print("\nComparison:")
        print(f"BPM Difference: {abs(m_hp['bpm'] - m['bpm']):.4f}")
        print(f"SDNN Difference: {abs(m_hp['sdnn'] - m['sdnn']):.4f}")
        print(f"RMSSD Difference: {abs(m_hp['rmssd'] - m['rmssd']):.4f}")
        print(f"LF/HF Difference: {abs(m_hp['lf/hf'] - m['lf/hf']):.4f}")


if __name__ == "__main__":
    analyze_ppg_signal()