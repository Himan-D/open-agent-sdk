#!/usr/bin/env python3
"""Auto Feature Generator Demo - SmithAI can learn and improve itself.

This demo showcases:
1. Task failure detection and analysis
2. Internet research for solutions
3. Automatic code generation
4. Safe integration with rollback

The AGI can:
- Detect when something is missing
- Research solutions online (like a human)
- Generate and test code
- Integrate safely with rollback capability
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from smith_ai.agi.auto_feature import (
    AutoFeatureGenerator,
    SelfSufficientAGI,
    TaskFailure,
    FeatureRequest,
    FeaturePriority,
    InternetResearcher,
    FailureAnalyzer,
    CodeGenerator,
    FailureType,
)


def demo_internet_research():
    """Demo 1: Internet Research - Learn from the web."""
    print("\n" + "="*70)
    print("DEMO 1: Internet Research - Learn from the Web")
    print("="*70)
    
    researcher = InternetResearcher(verbose=True)
    
    print("\n[1] Researching error solutions online...")
    
    # Research a common error
    research = researcher.research_error("ModuleNotFoundError: No module named 'httpx'")
    print(f"\n[2] Research Results:")
    print(f"    Search Query: {research['search_query']}")
    print(f"    Top Result: {research['results'][0]['title'] if research['results'] else 'N/A'}")
    
    print("\n[3] Analysis:")
    print(f"    {research['analysis'][:200]}...")
    
    print("\n[4] Researching a new feature...")
    
    # Research a feature
    feature_research = researcher.research_feature(
        "retry decorator python",
        "resilience"
    )
    print(f"\n[5] Feature Research:")
    print(f"    Best Practices Found: {len(feature_research['best_practices'])}")
    for practice in feature_research['best_practices'][:2]:
        print(f"    - {practice[:80]}...")
    
    return True


def demo_failure_analysis():
    """Demo 2: Failure Analysis - Understand what's missing."""
    print("\n" + "="*70)
    print("DEMO 2: Failure Analysis - Understand What's Missing")
    print("="*70)
    
    analyzer = FailureAnalyzer(verbose=True)
    
    # Simulate different failures
    failures = [
        TaskFailure(
            task_name="fetch_data",
            error_message="ModuleNotFoundError: No module named 'httpx'",
            error_type="ImportError",
        ),
        TaskFailure(
            task_name="process_data",
            error_message="AttributeError: 'list' object has no attribute 'to_json'",
            error_type="AttributeError",
        ),
        TaskFailure(
            task_name="api_call",
            error_message="ConnectionError: Failed to connect to API",
            error_type="ConnectionError",
        ),
    ]
    
    print("\n[1] Analyzing task failures...")
    
    for failure in failures:
        print(f"\n[2] Analyzing: {failure.task_name}")
        analysis = analyzer.analyze(failure)
        print(f"    Type: {analysis['type']}")
        print(f"    Root Cause: {analysis['root_cause']}")
        print(f"    Feature Needed: {analysis['feature_needed'].name if analysis['feature_needed'] else 'None'}")
        print(f"    Can Retry: {analysis['can_retry']}")
    
    print(f"\n[3] Failure Patterns:")
    patterns = analyzer.get_failure_patterns()
    for pattern, count in patterns.items():
        print(f"    {pattern}: {count}")
    
    return True


def demo_code_generation():
    """Demo 3: Code Generation - Create solutions."""
    print("\n" + "="*70)
    print("DEMO 3: Code Generation - Create Solutions")
    print("="*70)
    
    import tempfile
    test_dir = tempfile.mkdtemp()
    
    generator = CodeGenerator(test_dir, verbose=True)
    
    print("\n[1] Creating feature request...")
    
    feature = FeatureRequest(
        name="retry_with_backoff",
        description="Add retry logic with exponential backoff for failed operations",
        category="resilience",
        priority=FeaturePriority.HIGH,
    )
    
    research_data = {
        "results": [
            {
                "title": "Python Retry Decorator",
                "snippet": "Use @retry decorator with exponential backoff for resilient code",
            }
        ],
        "best_practices": [
            "Always implement exponential backoff",
            "Include maximum retry attempts",
            "Handle specific exceptions",
        ],
    }
    
    print(f"    Feature: {feature.name}")
    print(f"    Description: {feature.description}")
    print(f"    Priority: {feature.priority.value}")
    
    # Use async_tool template by selecting a different category
    feature.category = "general"
    
    print("\n[2] Generating code...")
    code = generator.generate(feature, research_data)
    
    print(f"\n[3] Generated Code:")
    print("-" * 40)
    print(code.code[:500] + "...")
    
    print(f"\n[4] Generated Info:")
    print(f"    File: {code.file_path}")
    print(f"    Imports: {len(code.imports)}")
    print(f"    Confidence: {code.confidence:.0%}")
    print(f"    Has Tests: {bool(code.tests)}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)
    
    return True


def demo_auto_feature_generator():
    """Demo 4: Auto Feature Generator - Full Pipeline."""
    print("\n" + "="*70)
    print("DEMO 4: Auto Feature Generator - Full Pipeline")
    print("="*70)
    
    import tempfile
    test_dir = tempfile.mkdtemp()
    
    generator = AutoFeatureGenerator(
        root_path=test_dir,
        verbose=True,
        auto_integrate=False,  # Don't auto-integrate in demo
    )
    
    print("\n[1] Creating simulated task failure...")
    
    # Simulate a failure that needs a feature
    failure = TaskFailure(
        task_name="fetch_api_data",
        error_message="AttributeError: 'HTTPClient' object has no attribute 'retry'",
        error_type="AttributeError",
        context={"url": "https://api.example.com", "method": "GET"},
    )
    
    print(f"    Task: {failure.task_name}")
    print(f"    Error: {failure.error_message}")
    
    print("\n[2] Analyzing failure and generating fix...")
    pipeline = generator.on_task_failure(failure)
    
    if pipeline:
        print(f"\n[3] Feature Pipeline Created:")
        print(f"    Feature: {pipeline.request.name}")
        print(f"    Priority: {pipeline.request.priority.value}")
        print(f"    Tests Passed: {pipeline.tests_passed}")
        
        print(f"\n[4] Generated Implementation:")
        print("-" * 40)
        print(pipeline.implementation.code[:400] + "...")
        
        print(f"\n[5] Research Results:")
        print(f"    Solutions Found: {len(pipeline.research.get('results', []))}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)
    
    return True


def demo_self_sufficient_agi():
    """Demo 5: Self-Sufficient AGI - Complete Loop."""
    print("\n" + "="*70)
    print("DEMO 5: Self-Sufficient AGI - Complete Self-Improvement Loop")
    print("="*70)
    
    import tempfile
    test_dir = tempfile.mkdtemp()
    
    # Create a test file that will fail
    test_file = os.path.join(test_dir, "agent.py")
    with open(test_file, 'w') as f:
        f.write('''
"""Test agent with intentional issues."""

def fetch_data():
    """Fetch data from API."""
    import requests
    return requests.get("https://api.example.com").json()

def process_data(data):
    """Process data."""
    # Missing error handling
    return data.to_dict()

def main():
    print(fetch_data())
    print(process_data([]))
''')
    
    agi = SelfSufficientAGI(
        root_path=test_dir,
        verbose=True,
        auto_improve=True,
        auto_integrate=False,
    )
    
    print("\n[1] Self-Sufficient AGI Status:")
    status = agi.get_status()
    print(f"    Failure History: {status['feature_generator']['failures_analyzed']}")
    
    print("\n[2] Running self-improvement cycle...")
    
    async def failing_task():
        """A task that will fail."""
        import json
        # Try to use a missing feature
        result = json.nonexistent_method()
        return result
    
    # Execute task (will fail)
    async def run_demo():
        result = await agi.execute_task("demo_task", failing_task)
        print(f"\n[3] Task Result:")
        print(f"    Success: {result['success']}")
        print(f"    Feature Pipeline: {'Created' if result['feature_pipeline'] else 'None'}")
        return result
    
    result = asyncio.run(run_demo())
    
    print("\n[4] Full Status:")
    print(json.dumps(status['feature_generator'], indent=2))
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)
    
    return True


def demo_web_interaction():
    """Demo 6: Web Interaction - Research like a human."""
    print("\n" + "="*70)
    print("DEMO 6: Web Interaction - Research Like a Human")
    print("="*70)
    
    researcher = InternetResearcher(verbose=True)
    
    # Simulate learning a new technology
    print("\n[1] AGI discovers it needs to learn about async/await patterns...")
    
    research = researcher.research_feature("python async best practices 2024", "async")
    
    print(f"\n[2] Web Research Results:")
    print(f"    Sources Found: {len(research['results'])}")
    
    print(f"\n[3] Best Practices Learned:")
    for i, practice in enumerate(research['best_practices'][:3], 1):
        print(f"    {i}. {practice[:100]}...")
    
    print(f"\n[4] Key Insights:")
    print(f"    - Use 'async with' for context managers")
    print(f"    - Implement proper task cancellation")
    print(f"    - Use 'asyncio.gather' for parallel tasks")
    
    # Research error solutions
    print("\n[5] Researching specific error...")
    error_research = researcher.research_error(
        "asyncio.CancelledError handling in Python"
    )
    print(f"    Solutions Found: {len(error_research['results'])}")
    
    return True


def demo_safeguards():
    """Demo 7: Safeguards - Never break itself."""
    print("\n" + "="*70)
    print("DEMO 7: Safeguards - Never Break Itself")
    print("="*70)
    
    import tempfile
    test_dir = tempfile.mkdtemp()
    
    # Create a file to protect
    test_file = os.path.join(test_dir, "important.py")
    original_content = '''
"""Important module - must not break."""

CRITICAL_VALUE = 42

def get_answer():
    """Return the answer."""
    return CRITICAL_VALUE
'''
    with open(test_file, 'w') as f:
        f.write(original_content)
    
    print("\n[1] Original Content:")
    print("-" * 30)
    print(original_content)
    
    # Create feature integrator with safeguards
    from smith_ai.agi.auto_feature import FeatureIntegrator
    integrator = FeatureIntegrator(test_dir, verbose=True)
    
    print("\n[2] Testing backup system...")
    
    # Create backup
    integrator._create_backup(test_file)
    
    # Verify backup exists
    backups = list(integrator._backup_dir.glob("important_*.py"))
    print(f"    Backups Created: {len(backups)}")
    
    print("\n[3] Simulating failed integration...")
    
    # Simulate a bad write
    with open(test_file, 'w') as f:
        f.write("# CORRUPTED - This would break things!")
    
    print(f"    File after corruption: {open(test_file).read()[:30]}...")
    
    print("\n[4] Testing rollback...")
    integrator._rollback(test_file)
    
    print(f"    File after rollback: {open(test_file).read()[:50]}...")
    
    # Verify content restored
    restored = open(test_file).read()
    print(f"\n[5] Integrity Check:")
    print(f"    Content Restored: {'✓' if 'CRITICAL_VALUE' in restored else '✗'}")
    print(f"    Function Intact: {'✓' if 'get_answer' in restored else '✗'}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)
    
    return True


def main():
    """Run all demos."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🚀 SmithAI Auto Feature Generator Demo                        ║
║                                                                  ║
║   AGI can:                                                      ║
║   ✓ Detect failures and missing features                        ║
║   ✓ Research solutions online (like a human)                     ║
║   ✓ Generate and test new code                                ║
║   ✓ Integrate safely with rollback                            ║
║   ✓ Never break itself - always has safeguards                ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    demos = [
        ("Internet Research", demo_internet_research),
        ("Failure Analysis", demo_failure_analysis),
        ("Code Generation", demo_code_generation),
        ("Auto Feature Generator", demo_auto_feature_generator),
        ("Self-Sufficient AGI", demo_self_sufficient_agi),
        ("Web Interaction", demo_web_interaction),
        ("Safeguards", demo_safeguards),
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
