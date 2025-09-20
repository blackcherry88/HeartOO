// HeartSW - Swift Heart Rate Analysis
// Peak validation and RR interval outlier detection

import Foundation

/// Peak validator that implements HeartPy's check_peaks functionality
public struct PeakValidator: HeartRateProcessor {
    public typealias InputType = HeartRateSignal
    public typealias OutputType = HeartRateSignal

    public let name = "PeakValidator"

    public var parameters: [String: Any] {
        return [:]
    }

    public init() {}

    /// Process signal and validate peaks using HeartPy's approach
    public func process(_ signal: HeartRateSignal, result: inout AnalysisResult) throws -> HeartRateSignal {
        guard let peaks = signal.peaks else {
            // No peaks to validate, return as-is
            return signal
        }

        // Apply HeartPy's first peak filtering (within 150ms of start)
        var filteredPeaks = peaks
        if !filteredPeaks.isEmpty {
            let firstPeakThreshold = Int((signal.sampleRate / 1000.0) * 150) // 150ms in samples
            if filteredPeaks[0] <= firstPeakThreshold {
                filteredPeaks.removeFirst()
            }
        }

        // Update signal with filtered peaks and recalculate RR intervals
        var updatedSignal = signal
        updatedSignal.setPeaks(filteredPeaks)

        guard let rrIntervals = updatedSignal.rrIntervals else {
            // No RR intervals to validate, return filtered signal
            result.setWorkingData("peaklist", value: filteredPeaks)
            result.setWorkingData("RR_list_cor", value: [Double]())
            result.setWorkingData("RR_masklist", value: [Int]())
            result.setWorkingData("binary_peaklist", value: Array(repeating: true, count: filteredPeaks.count))
            return updatedSignal
        }

        // Apply HeartPy's RR interval outlier detection
        let validationResult = validateRRIntervals(rrIntervals)

        // Create binary mask for valid peaks (HeartPy approach)
        var binaryMask: [Bool] = Array(repeating: true, count: filteredPeaks.count)

        // Mark invalid RR intervals (note: RR intervals are between peaks)
        for invalidIndex in validationResult.removedIndices {
            // RR interval at index i is between peaks[i] and peaks[i+1]
            // So we mark peak[i+1] as invalid
            let peakIndex = invalidIndex + 1
            if peakIndex < binaryMask.count {
                binaryMask[peakIndex] = false
            }
        }

        // HeartPy keeps ALL peaks but flags invalid RR intervals
        // Don't remove peaks, just mark them in the binary mask
        var validatedSignal = signal
        validatedSignal.setPeaks(filteredPeaks)  // Keep all peaks

        // Calculate corrected RR intervals using HeartPy's update_rr logic
        let correctedRRData = calculateCorrectedRRIntervals(
            originalRRIntervals: rrIntervals,
            binaryMask: binaryMask
        )

        // Store validation results in working data (HeartPy format)
        result.setWorkingData("peaklist", value: filteredPeaks)  // All peaks, not just valid ones
        result.setWorkingData("removed_beats", value: validationResult.removedBeats)
        result.setWorkingData("binary_peaklist", value: binaryMask)

        // Only set RR_list_cor if it hasn't been set already by AdaptiveThresholdDetector
        if result.getWorkingData("RR_list_cor", as: [Double].self) == nil {
            result.setWorkingData("RR_list_cor", value: correctedRRData.correctedIntervals)
        }

        result.setWorkingData("RR_masklist", value: correctedRRData.maskList)

        return validatedSignal
    }

    /// HeartPy's RR interval validation approach - exact implementation
    private func validateRRIntervals(_ rrIntervals: [Double]) -> ValidationResult {
        guard !rrIntervals.isEmpty else {
            return ValidationResult(correctedIntervals: [], removedBeats: [], removedIndices: [], maskList: [])
        }

        // Calculate mean RR interval
        let meanRR = rrIntervals.reduce(0, +) / Double(rrIntervals.count)

        // Define RR range as mean +/- 30%, with a minimum of 300ms (HeartPy's approach)
        let thirtyPercent = 0.3 * meanRR
        let upperThreshold = thirtyPercent <= 300 ? meanRR + 300 : meanRR + thirtyPercent
        let lowerThreshold = thirtyPercent <= 300 ? meanRR - 300 : meanRR - thirtyPercent

        // HeartPy: identify peaks to exclude based on RR interval
        // rem_idx = np.where((rr_arr <= lower_threshold) | (rr_arr >= upper_threshold))[0] + 1
        var removedPeakIndices: [Int] = []
        var rrMaskList: [Int] = []

        for (index, interval) in rrIntervals.enumerated() {
            if interval <= lowerThreshold || interval >= upperThreshold {
                // This RR interval is invalid, so mark the second peak of the interval for removal
                removedPeakIndices.append(index + 1)
                rrMaskList.append(1) // 1 = removed/masked
            } else {
                rrMaskList.append(0) // 0 = kept
            }
        }

        return ValidationResult(
            correctedIntervals: [], // Will be calculated separately using HeartPy logic
            removedBeats: removedPeakIndices,
            removedIndices: removedPeakIndices,
            maskList: rrMaskList
        )
    }

    /// Calculate corrected RR intervals using HeartPy's update_rr logic
    private func calculateCorrectedRRIntervals(originalRRIntervals: [Double], binaryMask: [Bool]) -> (correctedIntervals: [Double], maskList: [Int]) {
        guard originalRRIntervals.count > 0 && binaryMask.count > 1 else {
            return ([], [])
        }

        // HeartPy logic: rr_list = np.array([rr_source[i] for i in range(len(rr_source)) if b_peaklist[i] + b_peaklist[i+1] == 2])
        var correctedIntervals: [Double] = []
        var maskList: [Int] = []

        for i in 0..<originalRRIntervals.count {
            let currentPeakValid = binaryMask[i]
            let nextPeakValid = i + 1 < binaryMask.count ? binaryMask[i + 1] : false

            if currentPeakValid && nextPeakValid {
                // Both peaks are valid, so this RR interval is valid
                correctedIntervals.append(originalRRIntervals[i])
                maskList.append(0) // 0 = kept
            } else {
                // At least one peak is invalid, so this RR interval is masked
                maskList.append(1) // 1 = masked
            }
        }

        return (correctedIntervals, maskList)
    }

    /// Result of RR interval validation
    private struct ValidationResult {
        let correctedIntervals: [Double]
        let removedBeats: [Int]
        let removedIndices: [Int]
        let maskList: [Int]
    }
}