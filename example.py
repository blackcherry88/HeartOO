"""
HeartOO example comparing with HeartPy
"""

import numpy as np
import matplotlib.pyplot as plt

try:
    import heartpy as hp
    HEARTPY_AVAILABLE = True
except ImportError:
    HEARTPY_AVAILABLE = False
    print("HeartPy not available, only showing HeartOO results")

import heartoo as ho


def run_comparison():
    """Run a comparison between HeartPy and HeartOO."""
    
    print("Loading example data...")
    
    # Load example data from HeartPy or create synthetic data
    if HEARTPY_AVAILABLE:
        data, _ = hp.load_exampledata(0)
        sample_rate = 100.0  # Example 0 has 100Hz sample rate
    else:
        # Create synthetic signal
        sample_rate = 100.0
        duration = 10  # seconds
        t = np.linspace(0, duration, int(duration * sample_rate))
        
        # Base signal (sine wave)
        freq = 1.0  # Hz (60 BPM)
        data = np.sin(2 * np.pi * freq * t)
        
        # Add higher frequency for clear peaks
        data += 0.5 * np.sin(2 * np.pi * freq * 2 * t)
        
        # Add some noise
        np.random.seed(42)  # For reproducibility
        noise = np.random.normal(0, 0.1, len(t))
        data += noise
    
    print(f"Data loaded: {len(data)} points at {sample_rate} Hz")
    
    # Process with HeartPy
    if HEARTPY_AVAILABLE:
        print("\n--- HeartPy Results ---")
        wd_hp, m_hp = hp.process(data, sample_rate, calc_freq=True)
        print(f"Heart Rate: {m_hp['bpm']:.2f} BPM")
        print(f"SDNN: {m_hp['sdnn']:.2f} ms")
        print(f"RMSSD: {m_hp['rmssd']:.2f} ms")
        if 'lf/hf' in m_hp:
            print(f"LF/HF Ratio: {m_hp['lf/hf']:.2f}")
        print(f"Peaks detected: {len(wd_hp['peaklist'])}")
        
        # Plot with HeartPy
        hp.plotter(wd_hp, m_hp, title="HeartPy Results")
        plt.savefig("heartpy_results.png")
        plt.close()
    
    # Process with HeartOO using compatibility API
    print("\n--- HeartOO Compatibility API Results ---")
    wd_ho, m_ho = ho.process(data, sample_rate, calc_freq=True)
    print(f"Heart Rate: {m_ho['bpm']:.2f} BPM")
    print(f"SDNN: {m_ho['sdnn']:.2f} ms")
    print(f"RMSSD: {m_ho['rmssd']:.2f} ms")
    if 'lf/hf' in m_ho:
        print(f"LF/HF Ratio: {m_ho['lf/hf']:.2f}")
    print(f"Peaks detected: {len(wd_ho['peaklist'])}")
    
    # Process with HeartOO using OO API
    print("\n--- HeartOO Object-Oriented API Results ---")
    heart_signal = ho.HeartRateSignal(data, sample_rate)
    pipeline = ho.PipelineBuilder.create_standard_pipeline(calc_freq=True)
    result = pipeline.process(heart_signal)
    
    print(f"Heart Rate: {result.get_measure('bpm'):.2f} BPM")
    print(f"SDNN: {result.get_measure('sdnn'):.2f} ms")
    print(f"RMSSD: {result.get_measure('rmssd'):.2f} ms")
    if result.get_measure('lf/hf') is not None:
        print(f"LF/HF Ratio: {result.get_measure('lf/hf'):.2f}")
    print(f"Peaks detected: {len(result.get_working_data('peaklist'))}")
    
    # Plot with HeartOO
    fig = ho.plot_signal(heart_signal.data, heart_signal.sample_rate,
                       peaks=result.get_working_data('peaklist'),
                       rejected_peaks=result.get_working_data('removed_beats', []),
                       title="HeartOO Results",
                       show=False)
    fig.savefig("heartoo_results.png")
    plt.close()
    
    # Plot Poincaré
    fig = ho.plot_poincare(result.get_working_data('RR_list_cor'),
                          sd1=result.get_measure('sd1'),
                          sd2=result.get_measure('sd2'),
                          title="HeartOO Poincaré Plot",
                          show=False)
    fig.savefig("heartoo_poincare.png")
    plt.close()
    
    print("\nPlots saved to heartpy_results.png, heartoo_results.png, and heartoo_poincare.png")


if __name__ == "__main__":
    run_comparison()