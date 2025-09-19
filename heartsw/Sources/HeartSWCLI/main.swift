// HeartSW CLI Tool
// Command-line interface for HeartSW heart rate analysis

import Foundation
import HeartSW

struct CLI {
    static func main() {
        let arguments = CommandLine.arguments

        if arguments.count < 2 {
            printUsage()
            return
        }

        let command = arguments[1]

        switch command {
        case "process":
            handleProcessCommand(Array(arguments.dropFirst(2)))
        case "version":
            print("HeartSW version \(HeartSW.version)")
        case "help", "--help", "-h":
            printUsage()
        default:
            print("Unknown command: \(command)")
            printUsage()
        }
    }

    static func printUsage() {
        print("""
HeartSW - Swift Heart Rate Analysis Tool

Usage:
    heartsw process <file.csv> --sample-rate <rate> [options]
    heartsw version
    heartsw help

Commands:
    process     Analyze heart rate data from CSV file
    version     Show version information
    help        Show this help message

Process Options:
    --sample-rate <rate>     Sample rate in Hz (required)
    --min-bpm <bpm>         Minimum heart rate (default: 40)
    --max-bpm <bpm>         Maximum heart rate (default: 180)
    --output <file.json>    Output file for results (optional)

Example:
    heartsw process ecg_data.csv --sample-rate 100 --output results.json
""")
    }

    static func handleProcessCommand(_ args: [String]) {
        guard args.count >= 3,
              let sampleRateIndex = args.firstIndex(of: "--sample-rate"),
              sampleRateIndex + 1 < args.count else {
            print("❌ Error: Missing required arguments")
            print("Usage: heartsw process <file.csv> --sample-rate <rate>")
            return
        }

        let inputFile = args[0]
        let sampleRateString = args[sampleRateIndex + 1]

        guard let sampleRate = Double(sampleRateString), sampleRate > 0 else {
            print("❌ Error: Invalid sample rate: \(sampleRateString)")
            return
        }

        // Parse optional parameters
        var minBPM = 40.0
        var maxBPM = 180.0
        var outputFile: String?

        var i = 1
        while i < args.count - 1 {
            switch args[i] {
            case "--min-bpm":
                if let value = Double(args[i + 1]) {
                    minBPM = value
                }
                i += 2
            case "--max-bpm":
                if let value = Double(args[i + 1]) {
                    maxBPM = value
                }
                i += 2
            case "--output":
                outputFile = args[i + 1]
                i += 2
            default:
                i += 1
            }
        }

        // Process the file
        do {
            let url = URL(fileURLWithPath: inputFile)
            let result = try HeartSW.processFile(at: url,
                                               sampleRate: sampleRate,
                                               minBPM: minBPM,
                                               maxBPM: maxBPM)

            // Print results to console
            printResults(result)

            // Save to file if specified
            if let outputPath = outputFile {
                let outputURL = URL(fileURLWithPath: outputPath)
                try result.saveToJSON(at: outputURL)
                print("\n💾 Results saved to: \(outputPath)")
            }

        } catch {
            print("❌ Error processing file: \(error)")
        }
    }

    static func printResults(_ result: AnalysisResult) {
        print("\n📊 HeartSW Analysis Results")
        print("=" * 30)

        let measures = result.getAllMeasures()

        if measures.isEmpty {
            print("⚠️  No measures calculated (possibly no peaks detected)")
            return
        }

        // Time domain measures
        if let bpm = result.getMeasure("bpm") {
            print(String(format: "💓 Heart Rate: %.1f BPM", bpm))
        }
        if let ibi = result.getMeasure("ibi") {
            print(String(format: "⏱️  Mean IBI: %.1f ms", ibi))
        }
        if let sdnn = result.getMeasure("sdnn") {
            print(String(format: "📈 SDNN: %.1f ms", sdnn))
        }
        if let rmssd = result.getMeasure("rmssd") {
            print(String(format: "📊 RMSSD: %.1f ms", rmssd))
        }
        if let pnn50 = result.getMeasure("pnn50") {
            print(String(format: "📋 pNN50: %.1f%%", pnn50))
        }

        // Peak information
        if let peaks: [Int] = result.getWorkingData("peaklist", as: [Int].self) {
            print(String(format: "\n🎯 Detected %d peaks", peaks.count))
            if peaks.count >= 2 {
                let duration = Double(peaks.count - 1) * 60.0 / (result.getMeasure("bpm") ?? 60.0)
                print(String(format: "⏰ Analysis duration: %.1f seconds", duration))
            }
        }

        print("\n📋 All measures:")
        for (key, value) in measures.sorted(by: { $0.key < $1.key }) {
            print(String(format: "   %@: %@", key, String(describing: value)))
        }
    }
}

// String formatting helper
extension String {
    static func *(lhs: String, rhs: Int) -> String {
        return String(repeating: lhs, count: rhs)
    }
}

// Custom string interpolation for formatting
extension DefaultStringInterpolation {
    mutating func appendInterpolation<T: CVarArg>(_ value: T, format: String) {
        appendLiteral(String(format: format, value))
    }
}

// Helper for formatted strings
func f(_ value: String) -> String {
    return value
}

// Run the CLI
CLI.main()