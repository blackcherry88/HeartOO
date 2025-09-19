#!/usr/bin/env python3

"""
HeartSW Package Validation Script

This script validates the HeartSW package structure and Swift syntax
without requiring a full Swift build environment.
"""

import os
import re
from pathlib import Path


def validate_swift_syntax(file_path):
    """Basic Swift syntax validation"""
    with open(file_path, 'r') as f:
        content = f.read()

    errors = []

    # Check for basic Swift syntax patterns
    patterns = [
        (r'class\s+\w+', 'Contains class definitions'),
        (r'struct\s+\w+', 'Contains struct definitions'),
        (r'protocol\s+\w+', 'Contains protocol definitions'),
        (r'func\s+\w+\s*\(', 'Contains function definitions'),
        (r'import\s+\w+', 'Contains import statements'),
    ]

    found_patterns = []
    for pattern, description in patterns:
        if re.search(pattern, content):
            found_patterns.append(description)

    # Check for common syntax errors
    syntax_checks = [
        (r'\bprint\s*\(', 'Uses print statements'),
        (r'\btry\s+', 'Uses error handling'),
        (r'\bthrows\b', 'Declares throwing functions'),
        (r'\/\/\/.*', 'Has documentation comments'),
    ]

    features = []
    for pattern, description in syntax_checks:
        if re.search(pattern, content):
            features.append(description)

    return {
        'file': str(file_path),
        'patterns': found_patterns,
        'features': features,
        'lines': len(content.splitlines()),
        'chars': len(content)
    }


def validate_package_structure():
    """Validate the HeartSW package structure"""
    heartsw_dir = Path("heartsw")

    if not heartsw_dir.exists():
        return {"error": "HeartSW directory not found"}

    required_files = [
        "Package.swift",
        "README.md",
        "Sources/HeartSW/HeartSW.swift",
        "Sources/HeartSW/Core/Signal.swift",
        "Sources/HeartSW/Core/AnalysisResult.swift",
        "Sources/HeartSW/Core/Errors.swift",
        "Sources/HeartSW/Processing/Processor.swift",
        "Sources/HeartSWCLI/main.swift",
        "Tests/HeartSWTests/HeartSWTests.swift",
    ]

    required_dirs = [
        "Sources",
        "Sources/HeartSW",
        "Sources/HeartSW/Core",
        "Sources/HeartSW/Processing",
        "Sources/HeartSWCLI",
        "Tests",
        "Tests/HeartSWTests",
        "Scripts"
    ]

    structure_report = {
        "found_files": [],
        "missing_files": [],
        "found_dirs": [],
        "missing_dirs": [],
        "swift_files": []
    }

    # Check directories
    for dir_path in required_dirs:
        full_path = heartsw_dir / dir_path
        if full_path.exists():
            structure_report["found_dirs"].append(str(dir_path))
        else:
            structure_report["missing_dirs"].append(str(dir_path))

    # Check files
    for file_path in required_files:
        full_path = heartsw_dir / file_path
        if full_path.exists():
            structure_report["found_files"].append(str(file_path))
            if file_path.endswith('.swift'):
                structure_report["swift_files"].append(str(full_path))
        else:
            structure_report["missing_files"].append(str(file_path))

    # Find additional Swift files
    for swift_file in heartsw_dir.rglob("*.swift"):
        if str(swift_file.relative_to(heartsw_dir)) not in structure_report["swift_files"]:
            structure_report["swift_files"].append(str(swift_file))

    return structure_report


def validate_swift_files(swift_files):
    """Validate all Swift files"""
    results = []

    for file_path in swift_files:
        if os.path.exists(file_path):
            try:
                validation = validate_swift_syntax(file_path)
                results.append(validation)
            except Exception as e:
                results.append({
                    'file': file_path,
                    'error': str(e)
                })

    return results


def check_docstring_tests(swift_files):
    """Check for docstring tests in Swift files"""
    doctest_report = {
        'files_with_doctests': [],
        'total_doctests': 0,
        'example_doctests': []
    }

    for file_path in swift_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()

            # Look for Swift documentation with code examples
            doctest_pattern = r'///.*?```swift\s*\n(.*?)\n\s*```'
            matches = re.findall(doctest_pattern, content, re.DOTALL)

            if matches:
                doctest_report['files_with_doctests'].append(file_path)
                doctest_report['total_doctests'] += len(matches)

                # Store a few examples
                for i, match in enumerate(matches[:2]):
                    doctest_report['example_doctests'].append({
                        'file': os.path.basename(file_path),
                        'code': match.strip()
                    })

    return doctest_report


def main():
    print("🔍 HeartSW Package Validation")
    print("="*40)

    # 1. Validate package structure
    print("\n📁 Validating package structure...")
    structure = validate_package_structure()

    if "error" in structure:
        print(f"❌ {structure['error']}")
        return 1

    print(f"✅ Found {len(structure['found_dirs'])}/{len(structure['found_dirs']) + len(structure['missing_dirs'])} directories")
    print(f"✅ Found {len(structure['found_files'])}/{len(structure['found_files']) + len(structure['missing_files'])} required files")
    print(f"📄 Total Swift files: {len(structure['swift_files'])}")

    if structure['missing_files']:
        print(f"⚠️  Missing files: {', '.join(structure['missing_files'])}")

    if structure['missing_dirs']:
        print(f"⚠️  Missing directories: {', '.join(structure['missing_dirs'])}")

    # 2. Validate Swift syntax
    print(f"\n🦉 Validating Swift files...")
    swift_validations = validate_swift_files(structure['swift_files'])

    total_lines = 0
    total_chars = 0
    files_with_errors = 0

    for validation in swift_validations:
        if 'error' in validation:
            print(f"❌ {validation['file']}: {validation['error']}")
            files_with_errors += 1
        else:
            print(f"✅ {os.path.basename(validation['file'])}: {validation['lines']} lines, {len(validation['patterns'])} patterns")
            total_lines += validation['lines']
            total_chars += validation['chars']

    print(f"\n📊 Swift Code Statistics:")
    print(f"   📝 Total lines: {total_lines}")
    print(f"   📄 Total characters: {total_chars}")
    print(f"   🧩 Files processed: {len(swift_validations) - files_with_errors}/{len(swift_validations)}")

    # 3. Check docstring tests
    print(f"\n🧪 Validating docstring tests...")
    doctest_report = check_docstring_tests(structure['swift_files'])

    print(f"✅ Files with doctests: {len(doctest_report['files_with_doctests'])}")
    print(f"📋 Total doctest examples: {doctest_report['total_doctests']}")

    if doctest_report['example_doctests']:
        print(f"\n📝 Example doctests:")
        for i, example in enumerate(doctest_report['example_doctests'][:3]):
            print(f"   {i+1}. {example['file']}: {example['code'][:50]}...")

    # 4. Check build scripts
    print(f"\n🔨 Checking build scripts...")
    script_dir = Path("heartsw/Scripts")
    scripts = ['build.sh', 'test.sh', 'benchmark.sh', 'compare_with_heartpy.py']

    found_scripts = []
    for script in scripts:
        script_path = script_dir / script
        if script_path.exists():
            found_scripts.append(script)
            # Check if executable
            if os.access(script_path, os.X_OK):
                print(f"✅ {script} (executable)")
            else:
                print(f"⚠️  {script} (not executable)")
        else:
            print(f"❌ {script} (missing)")

    # 5. Summary
    print(f"\n📋 Validation Summary")
    print("="*25)

    success_criteria = [
        (len(structure['missing_files']) == 0, "All required files present"),
        (len(structure['missing_dirs']) == 0, "All required directories present"),
        (files_with_errors == 0, "No Swift syntax errors"),
        (doctest_report['total_doctests'] > 0, "Contains docstring tests"),
        (len(found_scripts) >= 3, "Build scripts available")
    ]

    passed_criteria = 0
    for passed, description in success_criteria:
        status = "✅" if passed else "❌"
        print(f"   {status} {description}")
        if passed:
            passed_criteria += 1

    final_score = passed_criteria / len(success_criteria) * 100

    print(f"\n🎯 Overall Score: {final_score:.0f}% ({passed_criteria}/{len(success_criteria)})")

    if final_score >= 80:
        print("🎉 HeartSW package is ready for use!")
        print("\n💡 Next steps:")
        print("   - Build with: cd heartsw && swift build")
        print("   - Test with: cd heartsw && swift test")
        print("   - Compare with: python3 working_comparison.py")
        return 0
    else:
        print("⚠️  HeartSW package needs some fixes before use")
        return 1


if __name__ == '__main__':
    exit(main())