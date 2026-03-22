#!/usr/bin/env python3
"""Self-Improvement Demo for SmithAI True AGI.

This demo showcases the self-improving capabilities:
1. SelfAnalyzer - Detect issues in code
2. GapDetector - Find missing features
3. SelfPatcher - Apply fixes
4. ImprovementEngine - Generate improvements
5. SelfImprovingAgent - Autonomous self-improvement

Run:
    python examples/19_self_improvement_demo.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from smith_ai.agi.self_improvement import (
    SelfImprovingAgent,
    SelfAnalyzer,
    GapDetector,
    SelfPatcher,
    ImprovementEngine,
    IssueType,
    IssueSeverity,
    CodeIssue,
    CodeGap,
    Improvement,
)


def demo_analyzer():
    """Demo 1: Self-Analysis - Detect code issues."""
    print("\n" + "="*70)
    print("DEMO 1: Self-Analyzer - Detect Code Issues")
    print("="*70)
    
    # Analyze the smith_ai package
    root = os.path.join(os.path.dirname(__file__), "..", "src", "smith_ai")
    
    analyzer = SelfAnalyzer(root, verbose=False)
    issues = analyzer.analyze_directory()
    
    print(f"\n[1] Analysis Results:")
    print(f"    Total issues found: {len(issues)}")
    
    # Group by severity
    by_severity = analyzer.get_issues_by_severity()
    for severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH, IssueSeverity.MEDIUM]:
        issues_list = by_severity[severity]
        if issues_list:
            print(f"\n    {severity.value.upper()} ({len(issues_list)}):")
            for issue in issues_list[:3]:
                print(f"      - {issue.description}")
                print(f"        [{issue.file_path}:{issue.line_number}]")
    
    print(f"\n[2] Report:")
    print("-" * 50)
    print(analyzer.generate_report()[:500] + "...")
    
    return True


def demo_gap_detector():
    """Demo 2: Gap Detection - Find missing features."""
    print("\n" + "="*70)
    print("DEMO 2: Gap Detector - Find Missing Features")
    print("="*70)
    
    root = os.path.join(os.path.dirname(__file__), "..", "src", "smith_ai")
    
    detector = GapDetector(root, verbose=False)
    gaps = detector.detect_missing_features()
    
    print(f"\n[1] Gap Detection Results:")
    print(f"    Gaps found: {len(gaps)}")
    
    if gaps:
        print(f"\n[2] Detected Gaps:")
        for gap in sorted(gaps, key=lambda x: x.priority, reverse=True)[:5]:
            print(f"    [{gap.priority}/10] {gap.gap_type} ({gap.category})")
            print(f"        {gap.description}")
    else:
        print("\n    No significant gaps detected!")
    
    print(f"\n[3] Report:")
    print("-" * 50)
    print(detector.generate_report())
    
    return True


def demo_improvement_engine():
    """Demo 3: Improvement Engine - Generate improvements."""
    print("\n" + "="*70)
    print("DEMO 3: Improvement Engine - Generate Improvements")
    print("="*70)
    
    root = os.path.join(os.path.dirname(__file__), "..", "src", "smith_ai")
    
    # Get issues and gaps
    analyzer = SelfAnalyzer(root, verbose=False)
    detector = GapDetector(root, verbose=False)
    
    issues = analyzer.analyze_directory()
    gaps = detector.detect_missing_features()
    
    # Generate improvements
    engine = ImprovementEngine(root, verbose=False)
    improvements = engine.generate_improvements(issues, gaps)
    
    print(f"\n[1] Generated {len(improvements)} potential improvements:")
    
    if improvements:
        print(f"\n[2] Top Improvements:")
        for imp in improvements[:5]:
            print(f"    [{imp.improvement_type.value}] {imp.title}")
            print(f"        Confidence: {imp.confidence:.0%}")
            print(f"        Rationale: {imp.rationale[:60]}...")
    
    print(f"\n[3] Report:")
    print("-" * 50)
    print(engine.generate_report()[:500] + "...")
    
    return True


def demo_self_patcher():
    """Demo 4: Self-Patcher - Apply fixes."""
    print("\n" + "="*70)
    print("DEMO 4: Self-Patcher - Apply Fixes")
    print("="*70)
    
    # Create a test file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''"""Test file for patching demo."""

def bad_function():
    """This function has issues."""
    try:
        x = 1 / 0
    except:
        pass
    print("Done")
''')
        test_file = f.name
    
    patcher = SelfPatcher(os.path.dirname(test_file), verbose=True)
    
    print(f"\n[1] Created test file: {test_file}")
    print(f"\n[2] Original code:")
    print("-" * 30)
    print(open(test_file).read())
    
    # Fix the bare except
    success = patcher.apply_fix(
        test_file,
        "except:\n        pass",
        "except Exception as e:\n        print(f'Error: {e}')",
        "Fixed bare except clause"
    )
    
    print(f"\n[3] Applied fix: {success}")
    
    print(f"\n[4] Modified code:")
    print("-" * 30)
    print(open(test_file).read())
    
    # Add import
    patcher.add_import(test_file, "import logging")
    
    print(f"\n[5] Added logging import")
    print("-" * 30)
    print(open(test_file).read()[:200] + "...")
    
    # Cleanup
    os.unlink(test_file)
    os.unlink(test_file + '.bak')
    
    print(f"\n[6] Modifications history:")
    for mod in patcher.get_modifications():
        print(f"    - {mod.change_type}: {mod.description}")
    
    return True


def demo_self_improving_agent():
    """Demo 5: Full Self-Improving Agent."""
    print("\n" + "="*70)
    print("DEMO 5: Self-Improving Agent - Full Cycle")
    print("="*70)
    
    # Use a temp directory for testing
    import tempfile
    test_dir = tempfile.mkdtemp()
    
    # Create test files with issues
    test_file = os.path.join(test_dir, "test_module.py")
    with open(test_file, 'w') as f:
        f.write('''"""Test module with issues."""

def bad_function():
    """Function with issues."""
    try:
        x = 1 / 0
    except:
        pass
    print("Done")
    # TODO: Fix this later
''')
    
    agent = SelfImprovingAgent(root_path=test_dir, verbose=True)
    
    print(f"\n[1] Analyzing test files in: {test_dir}")
    result = agent.analyze_self()
    
    print(f"\n[2] Analysis Results:")
    print(f"    Issues found: {result['issues_found']}")
    print(f"    Gaps found: {result['gaps_found']}")
    print(f"    Improvements possible: {result['improvements_possible']}")
    print(f"    Critical issues: {result['critical_issues']}")
    
    # Show sample issues
    if agent.issues:
        print(f"\n[3] Sample Issues:")
        for issue in agent.issues[:3]:
            print(f"    [{issue.severity.value}] {issue.description}")
            print(f"        → {issue.suggestion}")
    
    # Show improvements
    if agent.improvements:
        print(f"\n[4] Sample Improvements:")
        for imp in agent.improvements[:3]:
            print(f"    [{imp.improvement_type.value}] {imp.title}")
            print(f"        Confidence: {imp.confidence:.0%}")
    
    # Clean up temp directory
    import shutil
    shutil.rmtree(test_dir)
    
    return True


def demo_autonomous_cycle():
    """Demo 6: Autonomous Self-Improvement Cycle."""
    print("\n" + "="*70)
    print("DEMO 6: Autonomous Self-Improvement Cycle")
    print("="*70)
    
    # Use a temp directory for testing
    import tempfile
    test_dir = tempfile.mkdtemp()
    
    # Create test files with issues
    test_file = os.path.join(test_dir, "test_module.py")
    with open(test_file, 'w') as f:
        f.write('''"""Test module with issues."""

def bad_function():
    """Function with issues."""
    try:
        x = 1 / 0
    except:
        pass
    print("Debug: Starting")
    print("Debug: Done")
    # TODO: Fix this later
''')
    
    agent = SelfImprovingAgent(root_path=test_dir, verbose=True)
    
    print(f"\n[1] Running self-improvement cycle on test files...")
    
    # Run full cycle
    result = agent.run_self_improvement_cycle(
        max_improvements=3,
        auto_commit=False
    )
    
    print(f"\n[2] Cycle Results:")
    print(json.dumps(result, indent=2, default=str))
    
    print(f"\n[3] Summary:")
    print(f"    Issues analyzed: {result.get('issues_found', 0)}")
    print(f"    Gaps detected: {result.get('gaps_found', 0)}")
    print(f"    Improvements applied: {result.get('applied', 0)}")
    print(f"    Improvements failed: {result.get('failed', 0)}")
    
    # Show improved file
    improved_content = open(test_file).read()
    print(f"\n[4] Improved test file content:")
    print("-" * 40)
    print(improved_content)
    
    # Clean up
    import shutil
    shutil.rmtree(test_dir)
    
    return True


def main():
    """Run all demos."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🚀 SmithAI Self-Improvement Demo                               ║
║                                                                  ║
║   True AGI can:                                                  ║
║   ✓ Analyze its own code for issues                             ║
║   ✓ Detect gaps in functionality                               ║
║   ✓ Generate improvement suggestions                           ║
║   ✓ Apply fixes autonomously                                   ║
║   ✓ Learn from self-modification                                ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    demos = [
        ("Self-Analyzer", demo_analyzer),
        ("Gap Detector", demo_gap_detector),
        ("Improvement Engine", demo_improvement_engine),
        ("Self-Patcher", demo_self_patcher),
        ("Self-Improving Agent", demo_self_improving_agent),
        ("Autonomous Cycle", demo_autonomous_cycle),
    ]
    
    passed = 0
    for name, demo in demos:
        try:
            result = demo()
            if result:
                passed += 1
                print(f"\n✅ {name} Demo PASSED")
        except Exception as e:
            print(f"\n❌ {name} Demo FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print(f"FINAL RESULT: {passed}/{len(demos)} demos passed")
    print("="*70)
    
    return passed == len(demos)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
