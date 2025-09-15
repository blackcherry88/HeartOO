"""
Compare HeartOO and HeartPy using different example datasets.
"""

import numpy as np
import matplotlib.pyplot as plt
import os

try:
    import heartpy as hp
    HEARTPY_AVAILABLE = True
except ImportError:
    HEARTPY_AVAILABLE = False
    print("HeartPy not available, only showing HeartOO results")

import heartoo as ho


def process_and_compare(example_num, output_dir='comparison_outputs'):
    """Process an example dataset with both HeartPy and HeartOO and compare results.
    
    Parameters
    ----------
    example_num : int
        Example number (0, 1, or 2)
    output_dir : str
        Directory to save output plots
    
    Returns
    -------
    dict
        Comparison results
    """
    if not HEARTPY_AVAILABLE:
        print(f"HeartPy not available, cannot load example {example_num}")
        return None
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"\n=== Processing Example {example_num} ===")
    
    # Load the example data
    data, timer = hp.load_exampledata(example_num)
    
    # Get the sample rate based on the example number
    if example_num == 0:
        sample_rate = 100.0  # Example 0 is 100Hz
        data_type = "ECG"
    elif example_num == 1:
        sample_rate = hp.get_samplerate_mstimer(timer)
        data_type = "PPG"
    else:
        sample_rate = hp.get_samplerate_datetime(timer, timeformat='%Y-%m-%d %H:%M:%S.%f')
        data_type = "ECG"
        
    print(f"Data loaded: {len(data)} points at {sample_rate:.2f} Hz ({data_type} signal)")
    
    # Process with HeartPy
    print("\n--- HeartPy Results ---")
    try:
        wd_hp, m_hp = hp.process(data, sample_rate, calc_freq=True)
        print(f"Heart Rate: {m_hp['bpm']:.2f} BPM")
        print(f"SDNN: {m_hp['sdnn']:.2f} ms")
        print(f"RMSSD: {m_hp['rmssd']:.2f} ms")
        if 'lf/hf' in m_hp:
            print(f"LF/HF Ratio: {m_hp['lf/hf']:.2f}")
        print(f"Peaks detected: {len(wd_hp['peaklist'])}")
        
        # Plot with HeartPy
        hp.plotter(wd_hp, m_hp, title=f"HeartPy Results - Example {example_num} ({data_type})")
        plt.savefig(f"{output_dir}/heartpy_example{example_num}.png")
        plt.close()
        
        # Also plot Poincaré
        try:
            hp.plot_poincare(wd_hp, m_hp, title=f"HeartPy Poincaré - Example {example_num}")
            plt.savefig(f"{output_dir}/heartpy_poincare_example{example_num}.png")
            plt.close()
        except:
            print("Could not create HeartPy Poincaré plot")
            
        hp_success = True
    except Exception as e:
        print(f"Error processing with HeartPy: {str(e)}")
        hp_success = False
        wd_hp, m_hp = {}, {}
    
    # Process with HeartOO using compatibility API
    print("\n--- HeartOO Compatibility API Results ---")
    try:
        wd_ho, m_ho = ho.process(data, sample_rate, calc_freq=True)
        print(f"Heart Rate: {m_ho['bpm']:.2f} BPM")
        print(f"SDNN: {m_ho['sdnn']:.2f} ms")
        print(f"RMSSD: {m_ho['rmssd']:.2f} ms")
        if 'lf/hf' in m_ho:
            print(f"LF/HF Ratio: {m_ho['lf/hf']:.2f}")
        print(f"Peaks detected: {len(wd_ho['peaklist'])}")
        
        ho_success = True
    except Exception as e:
        print(f"Error processing with HeartOO compatibility API: {str(e)}")
        ho_success = False
        wd_ho, m_ho = {}, {}
    
    # Process with HeartOO using OO API
    print("\n--- HeartOO Object-Oriented API Results ---")
    try:
        # Create signal and pipeline
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
                           title=f"HeartOO Results - Example {example_num} ({data_type})",
                           show=False)
        fig.savefig(f"{output_dir}/heartoo_example{example_num}.png")
        plt.close()
        
        # Plot Poincaré
        fig = ho.plot_poincare(result.get_working_data('RR_list_cor'),
                              sd1=result.get_measure('sd1'),
                              sd2=result.get_measure('sd2'),
                              title=f"HeartOO Poincaré - Example {example_num}",
                              show=False)
        fig.savefig(f"{output_dir}/heartoo_poincare_example{example_num}.png")
        plt.close()
        
        oo_success = True
    except Exception as e:
        print(f"Error processing with HeartOO OO API: {str(e)}")
        oo_success = False
        result = None
    
    # Compare results if both libraries were successful
    if hp_success and ho_success:
        print("\n--- Comparison ---")
        # Compare key measures
        bpm_diff = abs(m_hp['bpm'] - m_ho['bpm'])
        sdnn_diff = abs(m_hp['sdnn'] - m_ho['sdnn'])
        rmssd_diff = abs(m_hp['rmssd'] - m_ho['rmssd'])
        
        print(f"BPM difference: {bpm_diff:.4f}")
        print(f"SDNN difference: {sdnn_diff:.4f}")
        print(f"RMSSD difference: {rmssd_diff:.4f}")
        
        if 'lf/hf' in m_hp and 'lf/hf' in m_ho:
            lf_hf_diff = abs(m_hp['lf/hf'] - m_ho['lf/hf'])
            print(f"LF/HF difference: {lf_hf_diff:.4f}")
        
        peak_count_diff = abs(len(wd_hp['peaklist']) - len(wd_ho['peaklist']))
        print(f"Peak count difference: {peak_count_diff}")
        
        # Summary
        print("\nSummary:")
        match_threshold = 0.01  # 1% tolerance
        
        if (bpm_diff / m_hp['bpm'] < match_threshold and 
            sdnn_diff / m_hp['sdnn'] < match_threshold and 
            rmssd_diff / m_hp['rmssd'] < match_threshold and
            peak_count_diff == 0):
            print("✅ Results match within 1% tolerance")
        else:
            print("❌ Results differ by more than 1%")
    
    print(f"\nPlots saved to {output_dir}/ directory")
    
    # Return comparison data
    return {
        'example': example_num,
        'data_type': data_type,
        'sample_rate': sample_rate,
        'heartpy': m_hp if hp_success else None,
        'heartoo_compat': m_ho if ho_success else None,
        'heartoo_oo': result.measures if oo_success else None
    }


def compare_all_examples():
    """Compare all example datasets."""
    
    if not HEARTPY_AVAILABLE:
        print("HeartPy not available, cannot load examples")
        return
    
    results = []
    for i in range(3):  # Examples 0, 1, 2
        results.append(process_and_compare(i))
    
    # Print summary table
    print("\n=== Summary Table ===")
    print(f"{'Example':8} | {'Type':4} | {'HeartPy BPM':12} | {'HeartOO BPM':12} | {'Match':5}")
    print("-" * 50)
    
    for r in results:
        if r is None or r['heartpy'] is None or r['heartoo_compat'] is None:
            match = "N/A"
            hp_bpm = "N/A"
            ho_bpm = "N/A"
        else:
            hp_bpm = f"{r['heartpy']['bpm']:.2f}"
            ho_bpm = f"{r['heartoo_compat']['bpm']:.2f}"
            match = "✅" if abs(r['heartpy']['bpm'] - r['heartoo_compat']['bpm']) < 0.01 else "❌"
            
        print(f"{r['example']:8} | {r['data_type']:4} | {hp_bpm:12} | {ho_bpm:12} | {match:5}")


if __name__ == "__main__":
    compare_all_examples()