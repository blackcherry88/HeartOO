#!/usr/bin/env python3
"""
HeartSW vs HeartPy Comprehensive Comparison Test

This script tests HeartSW against HeartPy using the three standard datasets:
- data.csv: Single column heart rate data
- data2.csv: Timer and heart rate columns
- data3.csv: Datetime and heart rate columns

The script validates that HeartSW produces consistent results with HeartPy
across different data formats and provides detailed comparison metrics.

Usage:
    cd heartsw
    python Scripts/compare_with_heartpy_datasets.py
"""

import sys
import os
import json
import subprocess
import tempfile
from pathlib import Path
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

# Add heartoo to Python path for importing heartpy and result functionality
heartoo_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(heartoo_path))
sys.path.insert(0, str(heartoo_path / "heartrate_analysis_python"))

try:
    import heartpy as hp
    print("✅ Successfully imported HeartPy")
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    print("Please ensure you have activated the virtual environment:")
    print("source .venv/bin/activate")
    sys.exit(1)

class DatasetLoader:
    """Load and preprocess the three standard datasets."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def load_data1(self) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Load data.csv - single column heart rate values."""
        filepath = self.data_dir / "data.csv"
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")

        data = np.genfromtxt(filepath, dtype=np.float64)
        return data, None

    def load_data2(self) -> Tuple[np.ndarray, np.ndarray]:
        """Load data2.csv - timer and heart rate columns."""
        filepath = self.data_dir / "data2.csv"
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")

        # Load with header
        full_data = np.genfromtxt(filepath, delimiter=',', names=True, dtype=None, encoding=None)
        hr_data = full_data['hr'].astype(np.float64)
        timer_data = full_data['timer'].astype(np.float64)
        return hr_data, timer_data

    def load_data3(self) -> Tuple[np.ndarray, np.ndarray]:
        """Load data3.csv - datetime and heart rate columns."""
        filepath = self.data_dir / "data3.csv"
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")

        # Load with header
        full_data = np.genfromtxt(filepath, delimiter=',', names=True, dtype=None, encoding=None)
        hr_data = full_data['hr'].astype(np.float64)
        datetime_data = full_data['datetime']  # Keep as strings for now
        return hr_data, datetime_data

class HeartPyAnalyzer:
    """Run HeartPy analysis and return results."""

    def analyze_data1(self, data: np.ndarray) -> Dict[str, Any]:
        """Analyze data.csv using HeartPy."""
        try:
            # Use default sample rate for single column data
            sample_rate = 100.0

            # Run HeartPy analysis
            working_data, measures = hp.process(data, sample_rate)

            return {
                'measures': measures,
                'working_data': {
                    'peaklist': working_data.get('peaklist', []),
                    'ybeat': working_data.get('ybeat', []),
                    'RR_list': working_data.get('RR_list', []),
                    'sample_rate': sample_rate
                }
            }
        except Exception as e:
            print(f"❌ HeartPy analysis failed for data1: {e}")
            return None

    def analyze_data2(self, hr_data: np.ndarray, timer_data: np.ndarray) -> Dict[str, Any]:
        """Analyze data2.csv using HeartPy with timer information."""
        try:
            # Calculate sample rate from timer data
            sample_rate = hp.get_samplerate_mstimer(timer_data)

            # Run HeartPy analysis
            working_data, measures = hp.process(hr_data, sample_rate)

            return {
                'measures': measures,
                'working_data': {
                    'peaklist': working_data.get('peaklist', []),
                    'ybeat': working_data.get('ybeat', []),
                    'RR_list': working_data.get('RR_list', []),
                    'sample_rate': sample_rate
                },
                'metadata': {
                    'calculated_sample_rate': sample_rate,
                    'timer_range': f"{timer_data[0]:.2f}ms to {timer_data[-1]:.2f}ms"
                }
            }
        except Exception as e:
            print(f"❌ HeartPy analysis failed for data2: {e}")
            return None

    def analyze_data3(self, hr_data: np.ndarray, datetime_data: np.ndarray) -> Dict[str, Any]:
        """Analyze data3.csv using HeartPy with datetime information."""
        try:
            # Calculate sample rate from datetime data
            sample_rate = hp.get_samplerate_datetime(datetime_data, timeformat='%Y-%m-%d %H:%M:%S.%f')

            # Run HeartPy analysis
            working_data, measures = hp.process(hr_data, sample_rate)

            return {
                'measures': measures,
                'working_data': {
                    'peaklist': working_data.get('peaklist', []),
                    'ybeat': working_data.get('ybeat', []),
                    'RR_list': working_data.get('RR_list', []),
                    'sample_rate': sample_rate
                },
                'metadata': {
                    'calculated_sample_rate': sample_rate,
                    'datetime_range': f"{datetime_data[0].decode() if isinstance(datetime_data[0], bytes) else datetime_data[0]} to {datetime_data[-1].decode() if isinstance(datetime_data[-1], bytes) else datetime_data[-1]}"
                }
            }
        except Exception as e:
            print(f"❌ HeartPy analysis failed for data3: {e}")
            return None

class HeartSWAnalyzer:
    """Run HeartSW analysis using the CLI tool."""

    def __init__(self, heartsw_dir: Path):
        self.heartsw_dir = heartsw_dir

    def create_csv_for_heartsw(self, data: np.ndarray, sample_rate: float = 100.0) -> str:
        """Create a temporary CSV file compatible with HeartSW CLI."""
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)

        # Write header
        temp_file.write("time,ecg\n")

        # Write data points with time stamps
        time_step = 1.0 / sample_rate
        for i, value in enumerate(data):
            time = i * time_step
            temp_file.write(f"{time:.4f},{value}\n")

        temp_file.close()
        return temp_file.name

    def analyze_dataset(self, data: np.ndarray, sample_rate: float = 100.0) -> Dict[str, Any]:
        """Analyze data using HeartSW CLI."""
        try:
            # Create temporary CSV file
            temp_csv = self.create_csv_for_heartsw(data, sample_rate)

            # Create temporary JSON output file
            temp_json = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            temp_json.close()

            # Run HeartSW CLI with proper command format and output to file
            result = subprocess.run([
                'swift', 'run', 'HeartSWCLI', 'process', temp_csv,
                '--sample-rate', str(sample_rate),
                '--output', temp_json.name
            ], cwd=self.heartsw_dir, capture_output=True, text=True)

            # Clean up temporary CSV file
            os.unlink(temp_csv)

            if result.returncode != 0:
                print(f"❌ HeartSW CLI failed: {result.stderr}")
                # Clean up temporary JSON file
                try:
                    os.unlink(temp_json.name)
                except:
                    pass
                return None

            # Read JSON result from file
            try:
                with open(temp_json.name, 'r') as f:
                    json_result = json.load(f)
                # Clean up temporary JSON file
                os.unlink(temp_json.name)
                return json_result
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"❌ Failed to read JSON output: {e}")
                # Print stdout for debugging
                print(f"🔍 HeartSW CLI stdout: {result.stdout}")
                # Clean up temporary JSON file
                try:
                    os.unlink(temp_json.name)
                except:
                    pass
                return None

        except Exception as e:
            print(f"❌ HeartSW analysis failed: {e}")
            return None

class ResultComparator:
    """Compare HeartPy and HeartSW results."""

    @staticmethod
    def calculate_percentage_difference(val1: float, val2: float) -> float:
        """Calculate percentage difference between two values."""
        if val1 == 0 and val2 == 0:
            return 0.0
        if val1 == 0:
            return 100.0
        return abs(val1 - val2) / abs(val1) * 100.0

    @staticmethod
    def compare_measures(heartpy_measures: Dict, heartsw_measures: Dict) -> Dict[str, Any]:
        """Compare HRV measures between implementations."""
        comparison = {}

        # Key measures to compare
        key_measures = ['bpm', 'ibi', 'sdnn', 'sdsd', 'rmssd', 'pnn20', 'pnn50']

        for measure in key_measures:
            if measure in heartpy_measures and measure in heartsw_measures:
                hp_val = heartpy_measures[measure]
                hsw_val = heartsw_measures[measure]

                diff = abs(hp_val - hsw_val)
                pct_diff = ResultComparator.calculate_percentage_difference(hp_val, hsw_val)

                comparison[measure] = {
                    'heartpy': hp_val,
                    'heartsw': hsw_val,
                    'difference': diff,
                    'percentage_difference': pct_diff,
                    'within_tolerance': pct_diff <= 5.0  # 5% tolerance
                }

        return comparison

    @staticmethod
    def compare_peaks(heartpy_peaks: List[int], heartsw_peaks: List[int]) -> Dict[str, Any]:
        """Compare detected peaks between implementations."""
        hp_count = len(heartpy_peaks)
        hsw_count = len(heartsw_peaks)

        # Calculate peak position differences if counts match
        position_diffs = []
        if hp_count == hsw_count and hp_count > 0:
            position_diffs = [abs(hp - hsw) for hp, hsw in zip(heartpy_peaks, heartsw_peaks)]
            avg_position_diff = np.mean(position_diffs)
            max_position_diff = max(position_diffs)
        else:
            avg_position_diff = None
            max_position_diff = None

        return {
            'heartpy_count': hp_count,
            'heartsw_count': hsw_count,
            'count_match': hp_count == hsw_count,
            'avg_position_difference': avg_position_diff,
            'max_position_difference': max_position_diff,
            'position_differences': position_diffs[:10]  # Show first 10 for brevity
        }

def main():
    """Main comparison function."""
    print("🔬 HeartSW vs HeartPy Comprehensive Dataset Comparison")
    print("=" * 60)

    # Setup paths relative to script location
    script_dir = Path(__file__).parent
    heartsw_dir = script_dir.parent  # heartsw directory
    data_dir = heartsw_dir.parent / "data"  # HeartOO/data directory

    # Verify directories exist
    if not (heartsw_dir / "Package.swift").exists():
        print(f"❌ HeartSW Package.swift not found at: {heartsw_dir}")
        return 1

    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return 1

    # Initialize analyzers
    loader = DatasetLoader(data_dir)
    heartpy_analyzer = HeartPyAnalyzer()
    heartsw_analyzer = HeartSWAnalyzer(heartsw_dir)

    # Test results storage
    results = {
        'timestamp': datetime.now().isoformat(),
        'datasets': {},
        'summary': {}
    }

    datasets = [
        ('data1', 'Single column heart rate data', loader.load_data1),
        ('data2', 'Timer + heart rate columns', loader.load_data2),
        ('data3', 'Datetime + heart rate columns', loader.load_data3)
    ]

    for dataset_name, description, load_func in datasets:
        print(f"\n📊 Testing {dataset_name}: {description}")
        print("-" * 40)

        try:
            # Load dataset
            if dataset_name == 'data1':
                hr_data, extra_data = load_func()
                sample_rate = 100.0  # Default for data1
            else:
                hr_data, extra_data = load_func()
                # Calculate sample rate for data2 and data3
                if dataset_name == 'data2':
                    sample_rate = hp.get_samplerate_mstimer(extra_data)
                else:  # data3
                    sample_rate = hp.get_samplerate_datetime(extra_data, timeformat='%Y-%m-%d %H:%M:%S.%f')

            print(f"📈 Loaded {len(hr_data)} data points, sample rate: {sample_rate:.2f} Hz")

            # Run HeartPy analysis
            print("🐍 Running HeartPy analysis...")
            if dataset_name == 'data1':
                heartpy_result = heartpy_analyzer.analyze_data1(hr_data)
            elif dataset_name == 'data2':
                heartpy_result = heartpy_analyzer.analyze_data2(hr_data, extra_data)
            else:  # data3
                heartpy_result = heartpy_analyzer.analyze_data3(hr_data, extra_data)

            if not heartpy_result:
                print(f"❌ HeartPy analysis failed for {dataset_name}")
                continue

            # Run HeartSW analysis
            print("🦉 Running HeartSW analysis...")
            heartsw_result = heartsw_analyzer.analyze_dataset(hr_data, sample_rate)

            if not heartsw_result:
                print(f"❌ HeartSW analysis failed for {dataset_name}")
                continue

            # Compare results
            print("🔍 Comparing results...")

            measures_comparison = ResultComparator.compare_measures(
                heartpy_result['measures'],
                heartsw_result['measures']
            )

            peaks_comparison = ResultComparator.compare_peaks(
                heartpy_result['working_data']['peaklist'],
                heartsw_result['workingData']['peaklist']  # HeartSW uses camelCase
            )

            # Store results
            results['datasets'][dataset_name] = {
                'description': description,
                'data_points': len(hr_data),
                'sample_rate': sample_rate,
                'heartpy_result': heartpy_result,
                'heartsw_result': heartsw_result,
                'comparison': {
                    'measures': measures_comparison,
                    'peaks': peaks_comparison
                }
            }

            # Print summary for this dataset
            print(f"✅ Analysis complete for {dataset_name}")
            print(f"   HeartPy peaks: {peaks_comparison['heartpy_count']}")
            print(f"   HeartSW peaks: {peaks_comparison['heartsw_count']}")
            print(f"   Peak count match: {'✅' if peaks_comparison['count_match'] else '❌'}")

            # Show key measure comparisons
            for measure in ['bpm', 'sdnn', 'rmssd']:
                if measure in measures_comparison:
                    comp = measures_comparison[measure]
                    tolerance_icon = '✅' if comp['within_tolerance'] else '❌'
                    print(f"   {measure.upper()}: HeartPy={comp['heartpy']:.2f}, HeartSW={comp['heartsw']:.2f}, "
                          f"diff={comp['percentage_difference']:.2f}% {tolerance_icon}")

        except Exception as e:
            print(f"❌ Error processing {dataset_name}: {e}")
            continue

    # Generate overall summary
    print(f"\n📋 Overall Summary")
    print("=" * 60)

    successful_tests = len(results['datasets'])
    total_tests = len(datasets)

    print(f"Tests completed: {successful_tests}/{total_tests}")

    if successful_tests > 0:
        # Calculate average differences across all datasets
        all_measure_diffs = []
        all_peak_matches = []

        for dataset_result in results['datasets'].values():
            comparison = dataset_result['comparison']

            # Collect measure differences
            for measure_comp in comparison['measures'].values():
                all_measure_diffs.append(measure_comp['percentage_difference'])

            # Collect peak match results
            all_peak_matches.append(comparison['peaks']['count_match'])

        avg_measure_diff = np.mean(all_measure_diffs) if all_measure_diffs else 0
        peak_match_rate = sum(all_peak_matches) / len(all_peak_matches) * 100 if all_peak_matches else 0

        results['summary'] = {
            'successful_tests': successful_tests,
            'total_tests': total_tests,
            'average_measure_difference_percent': avg_measure_diff,
            'peak_detection_match_rate_percent': peak_match_rate,
            'overall_success': avg_measure_diff <= 5.0 and peak_match_rate >= 90.0
        }

        print(f"Average measure difference: {avg_measure_diff:.2f}%")
        print(f"Peak detection match rate: {peak_match_rate:.1f}%")

        if results['summary']['overall_success']:
            print("🎉 Overall result: SUCCESS - HeartSW shows excellent compatibility with HeartPy!")
        else:
            print("⚠️  Overall result: NEEDS ATTENTION - Some differences exceed tolerance")

    # Save detailed results
    output_file = heartsw_dir / "comparison_results_datasets.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Detailed results saved to: {output_file}")
    print("\n🔬 Comparison complete!")

    return 0 if results['summary'].get('overall_success', False) else 1

if __name__ == "__main__":
    sys.exit(main())