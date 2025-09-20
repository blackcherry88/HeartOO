#!/usr/bin/env python3

import sys
import numpy as np
import heartpy as hp
from heartpy.datautils import rolling_mean
from heartpy.peakdetection import detect_peaks

print("🔬 HeartPy Threshold Selection Analysis")
print("=" * 50)

def analyze_heartpy_fit_peaks(data_idx, data_name, sample_rate):
    print(f"\n📊 {data_name} Analysis:")

    # Load data
    data, timer = hp.load_exampledata(data_idx)
    print(f"   Data points: {len(data)}, Sample rate: {sample_rate} Hz")

    # Calculate rolling mean (HeartPy's approach)
    rol_mean = rolling_mean(data, windowsize=0.75, sample_rate=sample_rate)

    # HeartPy's exact threshold list from fit_peaks
    ma_perc_list = [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 150, 200, 300]

    print(f"\n   Testing HeartPy's threshold selection:")
    print(f"   {'Threshold':<10} {'Peaks':<6} {'BPM':<7} {'RRSD':<8} {'Valid'}")
    print(f"   {'-'*10} {'-'*6} {'-'*7} {'-'*8} {'-'*5}")

    rrsd_results = []
    valid_ma = []

    for ma_perc in ma_perc_list:
        try:
            # Use HeartPy's detect_peaks function exactly as fit_peaks does
            working_data = {}
            working_data = detect_peaks(data, rol_mean, ma_perc, sample_rate,
                                        update_dict=True, working_data=working_data)

            peak_count = len(working_data['peaklist'])
            bpm = (peak_count / (len(data) / sample_rate)) * 60

            # Calculate RRSD exactly as HeartPy does
            if len(working_data['RR_list']) > 0:
                rrsd = np.std(working_data['RR_list'])
            else:
                rrsd = np.inf

            rrsd_results.append([rrsd, bpm, ma_perc])

            # HeartPy's validation criteria
            is_valid = (rrsd > 0.1) and (40 <= bpm <= 180)
            if is_valid:
                valid_ma.append([rrsd, ma_perc])

            status = "✅" if is_valid else "❌"
            print(f"   {ma_perc:<10} {peak_count:<6} {bpm:<7.1f} {rrsd:<8.1f} {status}")

        except Exception as e:
            print(f"   {ma_perc:<10} ERROR  {str(e)}")

    # Find HeartPy's choice (minimum RRSD among valid options)
    if len(valid_ma) > 0:
        best_choice = min(valid_ma, key=lambda t: t[0])  # Min RRSD
        best_rrsd, best_threshold = best_choice

        print(f"\n   🎯 HeartPy's Choice:")
        print(f"      Best threshold: {best_threshold}%")
        print(f"      Best RRSD: {best_rrsd:.2f}")

        # Test the best choice
        working_data_final = {}
        working_data_final = detect_peaks(data, rol_mean, best_threshold, sample_rate,
                                          update_dict=True, working_data=working_data_final)

        final_peaks = len(working_data_final['peaklist'])
        final_bpm = (final_peaks / (len(data) / sample_rate)) * 60

        print(f"      Final peaks: {final_peaks}")
        print(f"      Final BPM: {final_bpm:.1f}")

        return best_threshold, final_peaks, final_bpm
    else:
        print(f"   ❌ No valid threshold found!")
        return None, 0, 0

# Test data2.csv
threshold_2, peaks_2, bpm_2 = analyze_heartpy_fit_peaks(1, "data2.csv", 117.0)

# Test data3.csv
threshold_3, peaks_3, bpm_3 = analyze_heartpy_fit_peaks(2, "data3.csv", 100.0)

print(f"\n🎯 SUMMARY:")
print(f"   data2.csv: {threshold_2}% threshold → {peaks_2} peaks, {bpm_2:.1f} BPM")
print(f"   data3.csv: {threshold_3}% threshold → {peaks_3} peaks, {bpm_3:.1f} BPM")

print(f"\n💡 Key Insights:")
print(f"   • HeartPy tests thresholds: {[5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 150, 200, 300]}")
print(f"   • Selection criteria: RRSD > 0.1 AND 40 ≤ BPM ≤ 180")
print(f"   • Optimization goal: Minimize RRSD (standard deviation of RR intervals)")
print(f"   • Different datasets need different thresholds for optimal results")