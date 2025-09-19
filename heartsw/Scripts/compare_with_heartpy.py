#!/usr/bin/env python3

"""
HeartSW vs HeartPy Comparison Script

This script compares the results of HeartSW (Swift) with HeartPy (Python)
using the same input data and saves results in JSON format for analysis.

Usage:
    python3 compare_with_heartpy.py [--data-file ECG_FILE] [--sample-rate RATE]

Requirements:
    - Python virtual environment activated
    - HeartPy installed in the environment
    - HeartOO available in Python path
    - Swift HeartSW package built
"""

import sys
import os
import json
import argparse
import subprocess
import tempfile
from pathlib import Path

# Add HeartOO to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'heartoo'))

try:
    import numpy as np
    import heartpy as hp
    from heartoo.compatibility import process as heartoo_process
    from heartoo.core.result import AnalysisResult
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure to activate the virtual environment:")
    print("   source .venv/bin/activate")
    sys.exit(1)


def generate_test_data(duration=30.0, sample_rate=100.0, heart_rate=70.0):
    """Generate synthetic ECG data for testing"""
    print(f"🎲 Generating {duration}s of synthetic ECG data at {sample_rate}Hz...")

    time = np.linspace(0, duration, int(duration * sample_rate))

    # Create synthetic ECG with QRS complexes
    ecg = np.zeros_like(time)
    heart_period = 60.0 / heart_rate

    for i, t in enumerate(time):
        phase = (t % heart_period) / heart_period

        # QRS complex
        if 0.35 <= phase <= 0.65:
            qrs_phase = (phase - 0.35) / 0.3
            if qrs_phase < 0.3:
                # P wave
                ecg[i] = 0.2 * np.sin(qrs_phase * np.pi / 0.3)
            elif 0.4 <= qrs_phase <= 0.7:
                # QRS complex
                ecg[i] = 3.0 * np.sin((qrs_phase - 0.4) * np.pi / 0.3)
            elif qrs_phase > 0.8:
                # T wave
                ecg[i] = 0.4 * np.sin((qrs_phase - 0.8) * np.pi / 0.2)

        # Add noise
        ecg[i] += np.random.normal(0, 0.05)

    return time, ecg


def process_with_heartpy(data, sample_rate):
    """Process data with HeartPy"""
    print("💓 Processing with HeartPy...")

    try:
        working_data, measures = hp.process(data, sample_rate)

        # Create result object for JSON serialization
        result = AnalysisResult.from_heartpy_output(working_data, measures)

        return result.to_dict()
    except Exception as e:
        print(f"⚠️  HeartPy processing failed: {e}")
        return {"error": str(e)}


def process_with_heartoo(data, sample_rate):
    """Process data with HeartOO"""
    print("🔄 Processing with HeartOO...")

    try:
        # HeartOO returns AnalysisResult object directly
        result = heartoo_process(data, sample_rate)
        return result.to_dict()
    except Exception as e:
        print(f"⚠️  HeartOO processing failed: {e}")
        return {"error": str(e)}


def save_data_for_swift(data, sample_rate, output_file):
    """Save data in CSV format for Swift processing"""
    print(f"💾 Saving data for Swift: {output_file}")

    time_axis = np.arange(len(data)) / sample_rate

    with open(output_file, 'w') as f:
        f.write("time,ecg\n")
        for t, value in zip(time_axis, data):
            f.write(f"{t},{value}\n")


def process_with_heartsw(csv_file, sample_rate):
    """Process data with HeartSW (Swift)"""
    print("🦉 Processing with HeartSW...")

    # Create Swift script to process the data
    swift_script = f"""
import Foundation
@testable import HeartSW

do {{
    // Load data from CSV
    let url = URL(fileURLWithPath: "{csv_file}")
    let result = try HeartSW.processFile(at: url, sampleRate: {sample_rate})

    // Save result as JSON
    let outputURL = URL(fileURLWithPath: "{csv_file.replace('.csv', '_heartsw_result.json')}")
    try result.saveToJSON(at: outputURL)

    print("HeartSW processing completed")
}} catch {{
    print("HeartSW processing failed: \\(error)")
}}
"""

    # Write Swift script to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.swift', delete=False) as f:
        f.write(swift_script)
        script_path = f.name

    try:
        # Change to HeartSW directory and run Swift script
        heartsw_dir = Path(__file__).parent.parent
        result = subprocess.run(
            ['swift', 'run', '-c', 'release', '--skip-build', script_path],
            cwd=heartsw_dir,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            print(f"⚠️  Swift execution failed: {result.stderr}")
            return {"error": result.stderr}

        # Load the JSON result
        json_file = csv_file.replace('.csv', '_heartsw_result.json')
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                return json.load(f)
        else:
            return {"error": "HeartSW result file not found"}

    except subprocess.TimeoutExpired:
        return {"error": "HeartSW processing timed out"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        # Cleanup
        try:
            os.unlink(script_path)
        except:
            pass


def compare_results(heartpy_result, heartoo_result, heartsw_result, output_dir):
    """Compare all three results and generate comparison report"""
    print("📊 Comparing results...")

    # Save individual results
    results = {
        'heartpy': heartpy_result,
        'heartoo': heartoo_result,
        'heartsw': heartsw_result
    }

    for name, result in results.items():
        output_file = output_dir / f"{name}_result.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"📄 Saved {name} results: {output_file}")

    # Generate comparison
    comparison = {
        'timestamp': np.datetime64('now').isoformat(),
        'results': results,
        'comparison': {}
    }

    # Extract measures for comparison
    def extract_measures(result):
        if 'error' in result:
            return {}
        return result.get('measures', {})

    heartpy_measures = extract_measures(heartpy_result)
    heartoo_measures = extract_measures(heartoo_result)
    heartsw_measures = extract_measures(heartsw_result)

    # Compare HeartOO vs HeartPy
    if heartpy_measures and heartoo_measures:
        comparison['comparison']['heartoo_vs_heartpy'] = compare_measures(
            heartoo_measures, heartpy_measures
        )

    # Compare HeartSW vs HeartPy
    if heartpy_measures and heartsw_measures:
        comparison['comparison']['heartsw_vs_heartpy'] = compare_measures(
            heartsw_measures, heartpy_measures
        )

    # Compare HeartSW vs HeartOO
    if heartoo_measures and heartsw_measures:
        comparison['comparison']['heartsw_vs_heartoo'] = compare_measures(
            heartsw_measures, heartoo_measures
        )

    # Save full comparison
    comparison_file = output_dir / 'comparison_report.json'
    with open(comparison_file, 'w') as f:
        json.dump(comparison, f, indent=2)

    print(f"📋 Saved comparison report: {comparison_file}")

    return comparison


def compare_measures(measures1, measures2, tolerance=1e-6):
    """Compare two sets of measures"""
    all_keys = set(measures1.keys()) | set(measures2.keys())

    identical = []
    different = {}
    only_in_first = []
    only_in_second = []

    for key in all_keys:
        if key not in measures1:
            only_in_second.append(key)
        elif key not in measures2:
            only_in_first.append(key)
        else:
            val1, val2 = measures1[key], measures2[key]
            try:
                if abs(float(val1) - float(val2)) <= tolerance:
                    identical.append(key)
                else:
                    different[key] = {
                        'first': float(val1),
                        'second': float(val2),
                        'difference': float(val2) - float(val1)
                    }
            except (ValueError, TypeError):
                if val1 == val2:
                    identical.append(key)
                else:
                    different[key] = {
                        'first': val1,
                        'second': val2,
                        'difference': 'non-numeric'
                    }

    return {
        'identical': sorted(identical),
        'different': different,
        'only_in_first': sorted(only_in_first),
        'only_in_second': sorted(only_in_second),
        'summary': f"{len(identical)} identical, {len(different)} different, "
                  f"{len(only_in_first)} only in first, {len(only_in_second)} only in second"
    }


def print_summary(comparison):
    """Print a human-readable summary"""
    print("\n" + "="*60)
    print("📈 COMPARISON SUMMARY")
    print("="*60)

    for comp_name, comp_data in comparison.get('comparison', {}).items():
        if comp_data:
            print(f"\n🔍 {comp_name.replace('_', ' ').title()}:")
            print(f"   {comp_data['summary']}")

            if comp_data['different']:
                print("   Key differences:")
                for key, diff in list(comp_data['different'].items())[:5]:  # Show first 5
                    if isinstance(diff['difference'], (int, float)):
                        print(f"     {key}: {diff['first']:.3f} vs {diff['second']:.3f} "
                              f"(Δ {diff['difference']:+.3f})")
                    else:
                        print(f"     {key}: {diff['first']} vs {diff['second']}")

    print(f"\n✅ Analysis complete! Check output directory for detailed results.")


def main():
    parser = argparse.ArgumentParser(description='Compare HeartSW with HeartPy/HeartOO')
    parser.add_argument('--data-file', help='ECG data file (CSV format)')
    parser.add_argument('--sample-rate', type=float, default=100.0, help='Sample rate (Hz)')
    parser.add_argument('--duration', type=float, default=30.0,
                       help='Duration for synthetic data (seconds)')
    parser.add_argument('--output-dir', default='comparison_outputs',
                       help='Output directory for results')

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    print("🔄 HeartSW vs HeartPy Comparison")
    print("="*40)

    # Get data
    if args.data_file and os.path.exists(args.data_file):
        print(f"📂 Loading data from: {args.data_file}")
        data = np.loadtxt(args.data_file, delimiter=',', skiprows=1, usecols=1)
        csv_file = args.data_file
    else:
        # Generate synthetic data
        _, data = generate_test_data(args.duration, args.sample_rate)
        csv_file = output_dir / 'synthetic_ecg_data.csv'
        save_data_for_swift(data, args.sample_rate, csv_file)

    print(f"📊 Data: {len(data)} samples at {args.sample_rate}Hz ({len(data)/args.sample_rate:.1f}s)")

    # Process with all three implementations
    heartpy_result = process_with_heartpy(data, args.sample_rate)
    heartoo_result = process_with_heartoo(data, args.sample_rate)
    heartsw_result = process_with_heartsw(str(csv_file), args.sample_rate)

    # Compare and save results
    comparison = compare_results(heartpy_result, heartoo_result, heartsw_result, output_dir)

    # Print summary
    print_summary(comparison)


if __name__ == '__main__':
    main()