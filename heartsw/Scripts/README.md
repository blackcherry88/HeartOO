# HeartSW Scripts Directory

This directory contains validation and comparison scripts for the HeartSW library.

## Scripts

### `compare_with_heartpy_datasets.py`

**Purpose:** Comprehensive comparison between HeartSW and HeartPy using real ECG datasets.

**Usage:**
```bash
cd heartsw
source ../.venv/bin/activate  # Activate Python environment
python Scripts/compare_with_heartpy_datasets.py
```

**Features:**
- Tests all three standard datasets (data1.csv, data2.csv, data3.csv)
- Handles different CSV formats (single column, timer-based, datetime-based)
- Calculates sample rates from timer/datetime information
- Compares peak detection accuracy
- Analyzes HRV measure differences
- Generates detailed JSON comparison results
- Produces summary statistics

**Output:**
- Console output with real-time progress and results
- `comparison_results_datasets.json` - Detailed comparison data
- `comparison_report.md` - Human-readable analysis report

### `comparison_report.md`

**Purpose:** Detailed analysis report of HeartSW vs HeartPy comparison results.

**Content:**
- Executive summary of test results
- Peak detection comparison tables
- HRV measure analysis
- Algorithm difference identification
- Recommendations for improvements
- Technical implementation notes

## Dataset Information

The scripts use three standard datasets from the HeartOO project:

1. **data1.csv** - Single column heart rate data (2,483 points, 100Hz)
2. **data2.csv** - Timer + heart rate columns (15,000 points, 117Hz)
3. **data3.csv** - Datetime + heart rate columns (68,476 points, 100.42Hz)

## Dependencies

- Python 3.12+ with virtual environment activated
- HeartPy library (from heartrate_analysis_python)
- NumPy for data processing
- Swift toolchain for HeartSW CLI
- HeartSW package built and functional

## Key Findings

The comparison revealed:
- ✅ HeartSW successfully processes all dataset formats
- ⚠️  Peak detection differences (~20-25% fewer peaks detected)
- ❌ HRV calculations show significant unit/formula differences
- 📊 Framework architecture is solid, algorithms need refinement

## Running the Tests

1. Ensure you're in the `heartsw` directory
2. Activate the Python virtual environment: `source ../.venv/bin/activate`
3. Run the comparison: `python Scripts/compare_with_heartpy_datasets.py`
4. Review results in generated JSON and Markdown files

The scripts automatically handle:
- Temporary file creation and cleanup
- Error handling and reporting
- Cross-platform path management
- JSON serialization compatibility

## Troubleshooting

If you encounter issues:

1. **Import errors:** Ensure virtual environment is activated
2. **Swift build failures:** Run `swift build` in heartsw directory first
3. **Missing datasets:** Verify data files exist in `../data/` directory
4. **Permission errors:** Check file system permissions for temp file creation

For detailed debugging, the script includes verbose output showing HeartSW CLI interactions and intermediate results.