"""
Generate comparison data between HeartPy and HeartOO.

This script loads example data from HeartPy, processes it with both
HeartPy and HeartOO, and saves the results to JSON files for comparison.
"""

import os
import json
import numpy as np
import argparse
from typing import Dict, Any

try:
    import heartpy as hp
    HEARTPY_AVAILABLE = True
except ImportError:
    HEARTPY_AVAILABLE = False
    print("WARNING: HeartPy not installed, can only generate HeartOO data")

import heartoo as ho


def save_to_json(data: Dict[str, Any], filename: str) -> None:
    """Save data to JSON file.
    
    Parameters
    ----------
    data : dict
        Data to save
    filename : str
        Output filename
    """
    # Convert numpy arrays to lists
    serializable_data = {}
    
    for key, value in data.items():
        if isinstance(value, dict):
            serializable_data[key] = {}
            for k, v in value.items():
                if isinstance(v, np.ndarray):
                    serializable_data[key][k] = v.tolist()
                elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], np.ndarray):
                    serializable_data[key][k] = [arr.tolist() for arr in v]
                else:
                    serializable_data[key][k] = v
        else:
            if isinstance(value, np.ndarray):
                serializable_data[key] = value.tolist()
            else:
                serializable_data[key] = value
    
    with open(filename, 'w') as f:
        json.dump(serializable_data, f, indent=2)
    
    print(f"Data saved to {filename}")


def generate_heartpy_data(example_num: int, output_dir: str) -> None:
    """Generate data using HeartPy.
    
    Parameters
    ----------
    example_num : int
        Example number (0, 1, 2)
    output_dir : str
        Output directory
    """
    if not HEARTPY_AVAILABLE:
        print("HeartPy not installed, skipping HeartPy data generation")
        return
    
    # Load example data
    data, timer = hp.load_exampledata(example_num)
    
    # Get sample rate
    if example_num == 0:
        sample_rate = 100.0  # Example 0 is sampled at 100Hz
    elif example_num == 1:
        sample_rate = hp.get_samplerate_mstimer(timer)
    else:
        sample_rate = hp.get_samplerate_datetime(timer, timeformat='%Y-%m-%d %H:%M:%S.%f')
    
    # Process with HeartPy
    wd, m = hp.process(data, sample_rate, calc_freq=True)
    
    # Save results
    output_file = os.path.join(output_dir, f"heartpy_example{example_num}.json")
    save_to_json({
        "data": data,
        "sample_rate": sample_rate,
        "working_data": wd,
        "measures": m
    }, output_file)
    
    # Also process segmentwise
    try:
        wd_seg, m_seg = hp.process_segmentwise(data, sample_rate, segment_width=60, segment_overlap=0.5)
        
        output_file = os.path.join(output_dir, f"heartpy_example{example_num}_segmentwise.json")
        save_to_json({
            "data": data,
            "sample_rate": sample_rate,
            "working_data": wd_seg,
            "measures": m_seg
        }, output_file)
    except Exception as e:
        print(f"Error generating segmentwise data: {str(e)}")


def generate_heartoo_data(example_num: int, output_dir: str) -> None:
    """Generate data using HeartOO.
    
    Parameters
    ----------
    example_num : int
        Example number (0, 1, 2)
    output_dir : str
        Output directory
    """
    if not HEARTPY_AVAILABLE:
        print("HeartPy not installed, cannot load example data")
        return
    
    # Load example data from HeartPy
    data, timer = hp.load_exampledata(example_num)
    
    # Get sample rate
    if example_num == 0:
        sample_rate = 100.0  # Example 0 is sampled at 100Hz
    elif example_num == 1:
        sample_rate = hp.get_samplerate_mstimer(timer)
    else:
        sample_rate = hp.get_samplerate_datetime(timer, timeformat='%Y-%m-%d %H:%M:%S.%f')
    
    # Process with HeartOO compatibility function
    wd, m = ho.compatibility.process(data, sample_rate, calc_freq=True)
    
    # Save results
    output_file = os.path.join(output_dir, f"heartoo_example{example_num}.json")
    save_to_json({
        "data": data,
        "sample_rate": sample_rate,
        "working_data": wd,
        "measures": m
    }, output_file)
    
    # Also process using OO API
    signal = ho.HeartRateSignal(data, sample_rate)
    pipeline = ho.PipelineBuilder.create_standard_pipeline(calc_freq=True)
    result = pipeline.process(signal)
    
    # Save OO API results
    output_file = os.path.join(output_dir, f"heartoo_oo_example{example_num}.json")
    save_to_json({
        "data": data,
        "sample_rate": sample_rate,
        "working_data": result.working_data,
        "measures": result.measures
    }, output_file)
    
    # Also process segmentwise
    try:
        wd_seg, m_seg = ho.compatibility.process_segmentwise(
            data, sample_rate, segment_width=60, segment_overlap=0.5
        )
        
        output_file = os.path.join(output_dir, f"heartoo_example{example_num}_segmentwise.json")
        save_to_json({
            "data": data,
            "sample_rate": sample_rate,
            "working_data": wd_seg,
            "measures": m_seg
        }, output_file)
    except Exception as e:
        print(f"Error generating segmentwise data: {str(e)}")


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description='Generate comparison data')
    parser.add_argument('--output-dir', type=str, default='comparison_data',
                        help='Output directory for comparison data')
    parser.add_argument('--examples', type=str, default='0,1,2',
                        help='Example numbers to generate data for (comma-separated)')
    parser.add_argument('--library', type=str, default='both',
                        help='Library to generate data for (heartpy, heartoo, both)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Parse example numbers
    example_nums = [int(x.strip()) for x in args.examples.split(',')]
    
    # Generate data for each example
    for example_num in example_nums:
        if example_num not in [0, 1, 2]:
            print(f"Invalid example number: {example_num}")
            continue
        
        print(f"Generating data for example {example_num}")
        
        if args.library.lower() in ['heartpy', 'both']:
            generate_heartpy_data(example_num, args.output_dir)
        
        if args.library.lower() in ['heartoo', 'both']:
            generate_heartoo_data(example_num, args.output_dir)


if __name__ == '__main__':
    main()