#!/usr/bin/env python3

import sys
import numpy as np
sys.path.append('/Volumes/workplace/personal/HeartOO/heartrate_analysis_python')
sys.path.append('/Volumes/workplace/personal/HeartOO')

import heartpy as hp
import heartoo as ho

print("🔬 HeartOO vs HeartPy HRV Comparison on data2.csv")
print("=" * 60)

# Load data2.csv using HeartPy's loader
data, timer = hp.load_exampledata(1)  # data2.csv from HeartPy package
sample_rate = 117.0

print(f"📊 Dataset: data2.csv")
print(f"   Data length: {len(data)}")
print(f"   Sample rate: {sample_rate}")

# Process with HeartPy
print(f"\n🔍 HeartPy Processing:")
try:
    wd, m = hp.process(data, sample_rate=sample_rate)

    heartpy_peaks = len(wd['peaklist'])
    heartpy_bpm = m['bpm']
    heartpy_sdnn = m['sdnn']
    heartpy_rmssd = m['rmssd']
    heartpy_pnn50 = m['pnn50']
    heartpy_pnn20 = m['pnn20']

    print(f"   ✅ Peaks detected: {heartpy_peaks}")
    print(f"   ✅ BPM: {heartpy_bpm:.2f}")
    print(f"   ✅ SDNN: {heartpy_sdnn:.1f} ms")
    print(f"   ✅ RMSSD: {heartpy_rmssd:.1f} ms")
    print(f"   ✅ pNN50: {heartpy_pnn50:.1f}%")
    print(f"   ✅ pNN20: {heartpy_pnn20:.1f}%")

    # Show some RR intervals for debugging
    print(f"   📋 First 10 RR intervals: {[f'{x:.1f}' for x in wd['RR_list'][:10]]}")
    print(f"   📋 RR list length: {len(wd['RR_list'])}")
    print(f"   📋 Mean RR: {np.mean(wd['RR_list']):.1f} ms")

except Exception as e:
    print(f"   ❌ HeartPy Error: {e}")
    heartpy_peaks = heartpy_bpm = heartpy_sdnn = heartpy_rmssd = heartpy_pnn50 = heartpy_pnn20 = None
    wd = None

# Process with HeartOO
print(f"\n🔍 HeartOO Processing:")
try:
    # Use HeartOO's process function (HeartPy compatibility)
    wd_heartoo, m_heartoo = ho.process(data, sample_rate=sample_rate)

    heartoo_peaks = len(wd_heartoo['peaklist'])
    heartoo_bpm = m_heartoo['bpm']
    heartoo_sdnn = m_heartoo['sdnn']
    heartoo_rmssd = m_heartoo['rmssd']
    heartoo_pnn50 = m_heartoo['pnn50']
    heartoo_pnn20 = m_heartoo['pnn20']

    print(f"   ✅ Peaks detected: {heartoo_peaks}")
    print(f"   ✅ BPM: {heartoo_bpm:.2f}")
    print(f"   ✅ SDNN: {heartoo_sdnn:.1f} ms")
    print(f"   ✅ RMSSD: {heartoo_rmssd:.1f} ms")
    print(f"   ✅ pNN50: {heartoo_pnn50:.1f}%")
    print(f"   ✅ pNN20: {heartoo_pnn20:.1f}%")

    # Show some RR intervals for debugging
    rr_intervals = wd_heartoo.get('RR_list', [])
    print(f"   📋 First 10 RR intervals: {[f'{x:.1f}' for x in rr_intervals[:10]]}")
    print(f"   📋 RR list length: {len(rr_intervals)}")
    print(f"   📋 Mean RR: {np.mean(rr_intervals):.1f} ms" if rr_intervals else "No RR intervals")

except Exception as e:
    print(f"   ❌ HeartOO Error: {e}")
    import traceback
    traceback.print_exc()
    heartoo_peaks = heartoo_bpm = heartoo_sdnn = heartoo_rmssd = heartoo_pnn50 = heartoo_pnn20 = None

# Detailed Comparison
print(f"\n📊 Detailed HeartOO vs HeartPy Comparison:")

if heartpy_peaks is not None and heartoo_peaks is not None:
    peak_match = heartoo_peaks == heartpy_peaks
    peak_diff_pct = abs(heartoo_peaks - heartpy_peaks) / heartpy_peaks * 100 if heartpy_peaks > 0 else 0

    bpm_diff_pct = abs(heartoo_bpm - heartpy_bpm) / heartpy_bpm * 100 if heartpy_bpm > 0 else 0
    sdnn_diff_pct = abs(heartoo_sdnn - heartpy_sdnn) / heartpy_sdnn * 100 if heartpy_sdnn > 0 else 0
    rmssd_diff_pct = abs(heartoo_rmssd - heartpy_rmssd) / heartpy_rmssd * 100 if heartpy_rmssd > 0 else 0
    pnn50_diff_pct = abs(heartoo_pnn50 - heartpy_pnn50) / heartpy_pnn50 * 100 if heartpy_pnn50 > 0 else 0
    pnn20_diff_pct = abs(heartoo_pnn20 - heartpy_pnn20) / heartpy_pnn20 * 100 if heartpy_pnn20 > 0 else 0

    print(f"   Peak Count:")
    print(f"      HeartPy: {heartpy_peaks}, HeartOO: {heartoo_peaks}")
    print(f"      Match: {'✅ PERFECT' if peak_match else '❌'} ({peak_diff_pct:.1f}% diff)")

    print(f"   BPM:")
    print(f"      HeartPy: {heartpy_bpm:.2f}, HeartOO: {heartoo_bpm:.2f}")
    print(f"      Difference: {bpm_diff_pct:.2f}% {'✅' if bpm_diff_pct < 5 else '⚠️' if bpm_diff_pct < 10 else '❌'}")

    print(f"   SDNN (key measure):")
    print(f"      HeartPy: {heartpy_sdnn:.1f} ms, HeartOO: {heartoo_sdnn:.1f} ms")
    print(f"      Difference: {sdnn_diff_pct:.1f}% {'✅' if sdnn_diff_pct < 5 else '⚠️' if sdnn_diff_pct < 15 else '❌'}")

    print(f"   RMSSD:")
    print(f"      HeartPy: {heartpy_rmssd:.1f} ms, HeartOO: {heartoo_rmssd:.1f} ms")
    print(f"      Difference: {rmssd_diff_pct:.1f}% {'✅' if rmssd_diff_pct < 5 else '⚠️' if rmssd_diff_pct < 15 else '❌'}")

    print(f"   pNN50:")
    print(f"      HeartPy: {heartpy_pnn50:.1f}%, HeartOO: {heartoo_pnn50:.1f}%")
    print(f"      Difference: {pnn50_diff_pct:.1f}% {'✅' if pnn50_diff_pct < 10 else '⚠️' if pnn50_diff_pct < 25 else '❌'}")

    print(f"   pNN20:")
    print(f"      HeartPy: {heartpy_pnn20:.1f}%, HeartOO: {heartoo_pnn20:.1f}%")
    print(f"      Difference: {pnn20_diff_pct:.1f}% {'✅' if pnn20_diff_pct < 10 else '⚠️' if pnn20_diff_pct < 25 else '❌'}")

    # Overall assessment
    print(f"\n🎯 Overall Assessment:")
    if peak_match and bpm_diff_pct < 5 and sdnn_diff_pct < 10 and rmssd_diff_pct < 15:
        print(f"   ✅ EXCELLENT: HeartOO matches HeartPy very closely!")
        print(f"   🎯 HeartOO can serve as ground truth for HeartSW implementation")
    elif peak_match and sdnn_diff_pct < 20:
        print(f"   ⚠️  ACCEPTABLE: HeartOO mostly matches HeartPy with some differences")
        print(f"   🔍 Need to investigate specific differences for ground truth")
    else:
        print(f"   ❌ SIGNIFICANT DIFFERENCES: HeartOO and HeartPy have major discrepancies")
        print(f"   🚨 Need to debug both implementations to establish ground truth")

    # Ground truth recommendation
    if peak_match and sdnn_diff_pct < 15:
        print(f"\n💡 Ground Truth Recommendation:")
        print(f"   📋 Use HeartOO as reference for HeartSW RR/HRV implementation")
        print(f"   🎯 Target values for HeartSW on data2.csv:")
        print(f"      - Peaks: {heartoo_peaks}")
        print(f"      - BPM: {heartoo_bpm:.2f}")
        print(f"      - SDNN: {heartoo_sdnn:.1f} ms")
        print(f"      - RMSSD: {heartoo_rmssd:.1f} ms")
        print(f"      - pNN50: {heartoo_pnn50:.1f}%")
        print(f"      - pNN20: {heartoo_pnn20:.1f}%")

else:
    print(f"   ❌ Could not complete comparison due to processing errors")

print(f"\n📋 Next Steps:")
print(f"   1. If HeartOO matches HeartPy closely → Use HeartOO as ground truth")
print(f"   2. Debug HeartSW RR interval calculation to match HeartOO/HeartPy")
print(f"   3. Create unit tests for RR processing with ground truth values")