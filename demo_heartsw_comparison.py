#!/usr/bin/env python3

"""
Simple demonstration of HeartSW concept vs HeartPy/HeartOO
Since Swift compilation has environment issues, this creates mock HeartSW results
to demonstrate the JSON comparison functionality.
"""

import sys
import json
import numpy as np
from pathlib import Path

# Add HeartOO to path
sys.path.insert(0, str(Path(__file__).parent / 'heartoo'))

try:
    import heartpy as hp
    from heartoo.compatibility import process as heartoo_process
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

        # Convert numpy arrays to lists for JSON serialization
        result = {
            "measures": {k: float(v) if isinstance(v, (int, float, np.integer, np.floating)) else v
                        for k, v in measures.items()},
            "working_data": {k: (v.tolist() if isinstance(v, np.ndarray) else v)
                           for k, v in working_data.items()
                           if k in ['peaklist', 'ybeat', 'RR_list']}  # Only include serializable data
        }

        return result
    except Exception as e:
        print(f"⚠️  HeartPy processing failed: {e}")
        return {"error": str(e)}


def process_with_heartoo(data, sample_rate):
    """Process data with HeartOO"""
    print("🔄 Processing with HeartOO...")

    try:
        result = heartoo_process(data, sample_rate)
        return result.to_dict()
    except Exception as e:
        print(f"⚠️  HeartOO processing failed: {e}")
        return {"error": str(e)}


def create_mock_heartsw_result(heartpy_result):
    """Create a mock HeartSW result based on HeartPy output for demonstration"""
    print("🦉 Creating mock HeartSW result...")

    if "error" in heartpy_result:
        return {"error": "Mock HeartSW would have similar error"}

    measures = heartpy_result.get("measures", {})
    working_data = heartpy_result.get("working_data", {})

    # Simulate HeartSW results with slight variations (as if from different algorithm)
    mock_measures = {}
    for key, value in measures.items():
        if isinstance(value, (int, float)):
            # Add small random variation to simulate different implementation
            variation = np.random.normal(0, abs(value) * 0.001)  # 0.1% variation
            mock_measures[key] = value + variation
        else:
            mock_measures[key] = value

    # Mock working data with similar structure
    mock_working_data = {}
    for key, value in working_data.items():
        if isinstance(value, list) and key == 'peaklist':
            # Simulate slightly different peak detection
            peaks = np.array(value)
            # Add small variations to peak positions
            variations = np.random.randint(-2, 3, len(peaks))
            mock_peaks = np.maximum(0, peaks + variations).tolist()
            mock_working_data[key] = mock_peaks
        else:
            mock_working_data[key] = value

    return {
        "measures": mock_measures,
        "working_data": mock_working_data,
        "metadata": {
            "implementation": "HeartSW (Swift)",
            "version": "1.0.0",
            "note": "This is a mock result for demonstration"
        }
    }


def compare_measures(measures1, measures2, tolerance=1e-3):
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


def main():
    print("🔄 HeartSW vs HeartPy Comparison Demo")
    print("="*40)

    # Generate test data
    duration = 30.0
    sample_rate = 100.0
    time, data = generate_test_data(duration, sample_rate)

    print(f"📊 Data: {len(data)} samples at {sample_rate}Hz ({len(data)/sample_rate:.1f}s)")

    # Process with HeartPy
    heartpy_result = process_with_heartpy(data, sample_rate)

    # Process with HeartOO
    heartoo_result = process_with_heartoo(data, sample_rate)

    # Create mock HeartSW result
    heartsw_result = create_mock_heartsw_result(heartpy_result)

    # Save results
    output_dir = Path("comparison_outputs")
    output_dir.mkdir(exist_ok=True)

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

    # Compare results
    print("\n📊 Comparison Results:")
    print("="*40)

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
        comparison = compare_measures(heartoo_measures, heartpy_measures)
        print(f"\n🔍 HeartOO vs HeartPy: {comparison['summary']}")
        if comparison['different']:
            print("   Key differences:")
            for key, diff in list(comparison['different'].items())[:3]:
                if isinstance(diff['difference'], (int, float)):
                    print(f"     {key}: {diff['first']:.3f} vs {diff['second']:.3f} (Δ {diff['difference']:+.3f})")

    # Compare HeartSW vs HeartPy
    if heartpy_measures and heartsw_measures:
        comparison = compare_measures(heartsw_measures, heartpy_measures)
        print(f"\n🦉 HeartSW vs HeartPy: {comparison['summary']}")
        if comparison['different']:
            print("   Key differences:")
            for key, diff in list(comparison['different'].items())[:3]:
                if isinstance(diff['difference'], (int, float)):
                    print(f"     {key}: {diff['first']:.3f} vs {diff['second']:.3f} (Δ {diff['difference']:+.3f})")

    # Show sample results
    print(f"\n💓 Sample Results:")
    if heartpy_measures:
        bpm = heartpy_measures.get('bpm', 0)
        sdnn = heartpy_measures.get('sdnn', 0)
        rmssd = heartpy_measures.get('rmssd', 0)
        print(f"   HeartPy - BPM: {bpm:.1f}, SDNN: {sdnn:.1f}, RMSSD: {rmssd:.1f}")

    if heartoo_measures:
        bpm = heartoo_measures.get('bpm', 0)
        sdnn = heartoo_measures.get('sdnn', 0)
        rmssd = heartoo_measures.get('rmssd', 0)
        print(f"   HeartOO - BPM: {bpm:.1f}, SDNN: {sdnn:.1f}, RMSSD: {rmssd:.1f}")

    if heartsw_measures:
        bpm = heartsw_measures.get('bpm', 0)
        sdnn = heartsw_measures.get('sdnn', 0)
        rmssd = heartsw_measures.get('rmssd', 0)
        print(f"   HeartSW - BPM: {bpm:.1f}, SDNN: {sdnn:.1f}, RMSSD: {rmssd:.1f}")

    print(f"\n✅ Demo completed! Results saved to {output_dir}")
    print(f"📋 This demonstrates the JSON comparison system that would work")
    print(f"    with the actual HeartSW Swift implementation when built.")


if __name__ == '__main__':
    main()