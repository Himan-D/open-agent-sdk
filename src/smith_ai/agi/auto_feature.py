"""Auto Feature Generator - Generate and implement new features from failures.

This module enables the AGI to:
1. Analyze task failures
2. Research solutions via internet
3. Generate new code/features
4. Test and validate implementations
5. Integrate into codebase safely

Pipeline:
    Task Failure → Analysis → Research → Code Generation → Testing → Integration
"""

from __future__ import annotations

import ast
import asyncio
import json
import os
import re
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class FailureType(str, Enum):
    """Types of task failures."""
    MISSING_DEPENDENCY = "missing_dependency"
    MISSING_FEATURE = "missing_feature"
    API_ERROR = "api_error"
    IMPLEMENTATION = "implementation"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    PERMISSION = "permission"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class FeaturePriority(str, Enum):
    """Priority for feature implementation."""
    CRITICAL = "critical"  # Must have now
    HIGH = "high"         # Important
    MEDIUM = "medium"     # Nice to have
    LOW = "low"           # Can wait


@dataclass
class TaskFailure:
    """Represents a task failure."""
    task_name: str
    error_message: str
    error_type: str
    stack_trace: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task_name,
            "error": self.error_message,
            "type": self.error_type,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
        }


@dataclass
class FeatureRequest:
    """Request for a new feature."""
    name: str
    description: str
    category: str
    priority: FeaturePriority
    failure: Optional[TaskFailure] = None
    research_data: Dict[str, Any] = field(default_factory=dict)
    estimated_complexity: str = "medium"
    related_features: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "priority": self.priority.value,
            "research": self.research_data,
            "complexity": self.estimated_complexity,
        }


@dataclass
class GeneratedCode:
    """Generated code implementation."""
    feature_name: str
    file_path: str
    code: str
    imports: List[str] = field(default_factory=list)
    tests: str = ""
    documentation: str = ""
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature": self.feature_name,
            "file": self.file_path,
            "imports": self.imports,
            "has_tests": bool(self.tests),
            "confidence": self.confidence,
        }


@dataclass
class FeaturePipeline:
    """Complete feature pipeline."""
    request: FeatureRequest
    research: Dict[str, Any]
    implementation: GeneratedCode
    tests_passed: bool = False
    integrated: bool = False
    rollback_available: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request": self.request.to_dict(),
            "implementation": self.implementation.to_dict(),
            "tests_passed": self.tests_passed,
            "integrated": self.integrated,
        }


# =============================================================================
# INTERNET RESEARCH
# =============================================================================

class InternetResearcher:
    """Research solutions via internet search."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self._search_available = self._check_search()
    
    def _check_search(self) -> bool:
        """Check if search is available."""
        try:
            from ddgs import DDGS
            return True
        except ImportError:
            try:
                from duckduckgo_search import DDGS
                return True
            except ImportError:
                if self.verbose:
                    print("[Researcher] ddgs/duckduckgo-search not installed. Run: pip install ddgs")
                return False
    
    def search(
        self,
        query: str,
        max_results: int = 5
    ) -> List[Dict[str, str]]:
        """Search the web for solutions."""
        if not self._search_available:
            return self._fallback_search(query, max_results)
        
        try:
            from ddgs import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", "")[:200],
                    })
            if self.verbose:
                print(f"[Researcher] Found {len(results)} results for: {query}")
            return results
        except Exception:
            try:
                from duckduckgo_search import DDGS
                results = []
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=max_results):
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("href", ""),
                            "snippet": r.get("body", "")[:200],
                        })
                if self.verbose:
                    print(f"[Researcher] Found {len(results)} results for: {query}")
                return results
            except Exception as e:
                if self.verbose:
                    print(f"[Researcher] Search failed: {e}")
                return self._fallback_search(query, max_results)
    
    def _fallback_search(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Fallback when search is not available."""
        return [
            {
                "title": f"Search for: {query}",
                "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                "snippet": "Install duckduckgo-search: pip install duckduckgo-search",
            }
        ]
    
    def fetch_documentation(self, url: str) -> str:
        """Fetch documentation from URL."""
        try:
            import httpx
            response = httpx.get(url, timeout=10)
            if response.status_code == 200:
                return response.text[:5000]
        except Exception as e:
            if self.verbose:
                print(f"[Researcher] Failed to fetch: {e}")
        return ""
    
    def research_error(self, error_message: str) -> Dict[str, Any]:
        """Research how to fix an error."""
        search_query = f"python {error_message} fix solution"
        results = self.search(search_query, max_results=5)
        
        return {
            "error": error_message,
            "search_query": search_query,
            "results": results,
            "analysis": self._analyze_results(results),
        }
    
    def research_feature(
        self,
        feature_name: str,
        category: str
    ) -> Dict[str, Any]:
        """Research how to implement a feature."""
        queries = [
            f"python {feature_name} implementation",
            f"{category} library python best practices",
            f"python {feature_name} example code",
        ]
        
        all_results = []
        for query in queries:
            results = self.search(query, max_results=3)
            all_results.extend(results)
        
        return {
            "feature": feature_name,
            "category": category,
            "results": all_results,
            "best_practices": self._extract_best_practices(all_results),
        }
    
    def _analyze_results(self, results: List[Dict[str, str]]) -> str:
        """Analyze search results to extract key information."""
        if not results:
            return "No results found"
        
        snippets = [r.get("snippet", "") for r in results[:3]]
        return " | ".join(snippets)
    
    def _extract_best_practices(self, results: List[Dict[str, str]]) -> List[str]:
        """Extract best practices from search results."""
        practices = []
        keywords = ["best practice", "recommended", "should", "must", "avoid"]
        
        for r in results:
            snippet = r.get("snippet", "").lower()
            for kw in keywords:
                if kw in snippet:
                    practices.append(r.get("snippet", "")[:100])
        
        return practices[:5]


# =============================================================================
# FAILURE ANALYZER
# =============================================================================

class FailureAnalyzer:
    """Analyze task failures to determine root cause."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.failure_history: List[TaskFailure] = []
    
    def analyze(self, failure: TaskFailure) -> Dict[str, Any]:
        """Analyze a task failure."""
        self.failure_history.append(failure)
        
        # Determine failure type
        failure_type = self._classify_failure(failure)
        
        # Extract key information
        analysis = {
            "failure": failure.to_dict(),
            "type": failure_type.value,
            "root_cause": self._find_root_cause(failure, failure_type),
            "can_retry": self._can_retry(failure_type),
            "feature_needed": self._feature_from_failure(failure, failure_type),
            "suggestions": self._generate_suggestions(failure, failure_type),
        }
        
        if self.verbose:
            print(f"[Analyzer] Failure type: {failure_type.value}")
            print(f"[Analyzer] Root cause: {analysis['root_cause']}")
        
        return analysis
    
    def _classify_failure(self, failure: TaskFailure) -> FailureType:
        """Classify the type of failure."""
        error = failure.error_message.lower()
        error_type = failure.error_type.lower()
        
        if "modulenotfounderror" in error or "importerror" in error:
            return FailureType.MISSING_DEPENDENCY
        elif "attributeerror" in error or "has no attribute" in error:
            return FailureType.MISSING_FEATURE
        elif "apierror" in error or "api" in error:
            return FailureType.API_ERROR
        elif "notimplementederror" in error or "not implemented" in error:
            return FailureType.MISSING_FEATURE
        elif "connectionerror" in error or "timeout" in error or "network" in error:
            return FailureType.NETWORK
        elif "permission denied" in error or "access denied" in error:
            return FailureType.PERMISSION
        elif "configuration" in error or "config" in error:
            return FailureType.CONFIGURATION
        elif "traceback" in failure.stack_trace.lower():
            return FailureType.IMPLEMENTATION
        else:
            return FailureType.UNKNOWN
    
    def _find_root_cause(
        self,
        failure: TaskFailure,
        failure_type: FailureType
    ) -> str:
        """Find the root cause of the failure."""
        error = failure.error_message
        
        if failure_type == FailureType.MISSING_DEPENDENCY:
            match = re.search(r"No module named '(\w+)'", error)
            if match:
                return f"Missing module: {match.group(1)}"
        
        elif failure_type == FailureType.MISSING_FEATURE:
            match = re.search(r"'(\w+)' object has no attribute '(\w+)'", error)
            if match:
                return f"Object {match.group(1)} missing attribute {match.group(2)}"
        
        elif failure_type == FailureType.API_ERROR:
            return "API returned an error - check API key, endpoint, or rate limits"
        
        elif failure_type == FailureType.NETWORK:
            return "Network connectivity issue or service unavailable"
        
        return f"Error: {error[:100]}"
    
    def _can_retry(self, failure_type: FailureType) -> bool:
        """Determine if the task can be retried."""
        retryable = [
            FailureType.NETWORK,
            FailureType.TIMEOUT,
            FailureType.API_ERROR,
        ]
        return failure_type in retryable
    
    def _feature_from_failure(
        self,
        failure: TaskFailure,
        failure_type: FailureType
    ) -> Optional[FeatureRequest]:
        """Convert a failure to a feature request."""
        if failure_type == FailureType.MISSING_FEATURE:
            # Extract what feature is missing
            error = failure.error_message
            match = re.search(r"'(\w+)' object has no attribute '(\w+)'", error)
            if match:
                return FeatureRequest(
                    name=f"add_{match.group(2)}",
                    description=f"Add {match.group(2)} method/attribute",
                    category="feature",
                    priority=FeaturePriority.HIGH,
                    failure=failure,
                )
        
        elif failure_type == FailureType.MISSING_DEPENDENCY:
            match = re.search(r"No module named '(\w+)'", failure.error_message)
            if match:
                return FeatureRequest(
                    name=f"install_{match.group(1)}",
                    description=f"Install and integrate {match.group(1)} module",
                    category="dependency",
                    priority=FeaturePriority.CRITICAL,
                    failure=failure,
                )
        
        elif failure_type == FailureType.IMPLEMENTATION:
            return FeatureRequest(
                name="fix_implementation",
                description=f"Fix: {failure.error_message[:100]}",
                category="bug_fix",
                priority=FeaturePriority.HIGH,
                failure=failure,
            )
        
        return None
    
    def _generate_suggestions(
        self,
        failure: TaskFailure,
        failure_type: FailureType
    ) -> List[str]:
        """Generate suggestions to fix the failure."""
        suggestions = []
        
        if failure_type == FailureType.MISSING_DEPENDENCY:
            suggestions.append("Install required dependency")
            suggestions.append("Add to requirements.txt or pyproject.toml")
        
        elif failure_type == FailureType.MISSING_FEATURE:
            suggestions.append("Implement the missing feature")
            suggestions.append("Check if feature exists in newer version")
        
        elif failure_type == FailureType.API_ERROR:
            suggestions.append("Verify API key and permissions")
            suggestions.append("Check rate limits and quotas")
            suggestions.append("Implement retry with exponential backoff")
        
        elif failure_type == FailureType.NETWORK:
            suggestions.append("Check internet connection")
            suggestions.append("Implement timeout and retry logic")
        
        return suggestions
    
    def get_failure_patterns(self) -> Dict[str, int]:
        """Get patterns from failure history."""
        patterns = {}
        for failure in self.failure_history:
            key = failure.error_type
            patterns[key] = patterns.get(key, 0) + 1
        return patterns


# =============================================================================
# CODE GENERATOR
# =============================================================================

class CodeGenerator:
    """Generate code implementations for features."""
    
    def __init__(self, root_path: str, verbose: bool = True):
        self.root_path = Path(root_path)
        self.verbose = verbose
        self._load_templates()
    
    def _load_templates(self):
        """Load code templates."""
        self.templates = {
            "async_tool": '''async def {name}({params}) -> {return_type}:
    """Auto-generated {name} tool.
    
    {description}
    """
    try:
        {implementation}
        return {return_value}
    except Exception as e:
        if __name__ == "__main__":
            print("Error: " + str(e))
        raise
''',
            "class_tool": '''class {name}:
    """Auto-generated {name} class.
    
    {description}
    """
    
    def __init__(self{init_params}):
        {init_body}
    
    def execute(self{exec_params}) -> {return_type}:
        """Execute {name}."""
        try:
            {implementation}
            return {return_value}
        except Exception as e:
            raise {exception_type}("Error in " + name + ": " + str(e))
''',
            "decorator": '''def {name}({params}):
    """Auto-generated {name} decorator.
    
    {description}
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                {before}
                result = func(*args, **kwargs)
                {after}
                return result
            except Exception as e:
                raise
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator
''',
            "retry_decorator": '''from functools import wraps
import time
import asyncio

def with_retry(max_attempts=3, delay=1, backoff=2):
    """Decorator with retry logic for failed operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (backoff ** attempt)
                        print(f"Retry {attempt + 1}/{max_attempts} after {wait_time}s")
                        time.sleep(wait_time)
            raise last_exception
        return wrapper
    return decorator

def with_retry_async(max_attempts=3, delay=1, backoff=2):
    """Async decorator with retry logic."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (backoff ** attempt)
                        await asyncio.sleep(wait_time)
            raise last_exception
        return wrapper
    return decorator
''',
            "cache_decorator": '''from functools import lru_cache, wraps
import time

def timed_cache(seconds=60, maxsize=128):
    """Cache with TTL (time-to-live)."""
    def decorator(func):
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < seconds:
                    return result
            
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result
        return wrapper
    return decorator
''',
            "rate_limiter": '''import time
from collections import deque
from threading import Lock

class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()
        self.lock = Lock()
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            with self.lock:
                now = time.time()
                # Remove old calls
                while self.calls and now - self.calls[0] > self.time_window:
                    self.calls.popleft()
                
                if len(self.calls) >= self.max_calls:
                    sleep_time = self.time_window - (now - self.calls[0])
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                        now = time.time()
                        while self.calls and now - self.calls[0] > self.time_window:
                            self.calls.popleft()
                
                self.calls.append(now)
            return func(*args, **kwargs)
        return wrapper
''',
        }
    
    def generate(
        self,
        feature_request: FeatureRequest,
        research_data: Dict[str, Any]
    ) -> GeneratedCode:
        """Generate code for a feature request."""
        name = feature_request.name
        description = feature_request.description
        category = feature_request.category
        
        # Select template
        template_key = self._select_template(category, research_data)
        template = self.templates.get(template_key, self.templates["async_tool"])
        
        # Generate implementation
        code = self._generate_from_template(
            template, name, description, research_data
        )
        
        # Generate imports
        imports = self._generate_imports(feature_request, research_data)
        
        # Generate tests
        tests = self._generate_tests(name, description)
        
        # Generate documentation
        documentation = self._generate_docs(name, description)
        
        # Determine file path
        file_path = self._determine_file_path(name, category)
        
        confidence = self._calculate_confidence(feature_request, research_data)
        
        return GeneratedCode(
            feature_name=name,
            file_path=file_path,
            code=code,
            imports=imports,
            tests=tests,
            documentation=documentation,
            confidence=confidence,
        )
    
    def _select_template(
        self,
        category: str,
        research_data: Dict[str, Any]
    ) -> str:
        """Select appropriate template based on category."""
        category_lower = category.lower()
        
        if "retry" in category_lower or "resilience" in category_lower:
            return "retry_decorator"
        elif "cache" in category_lower or "performance" in category_lower:
            return "cache_decorator"
        elif "rate" in category_lower or "limit" in category_lower:
            return "rate_limiter"
        elif "decorator" in category_lower:
            return "decorator"
        elif "class" in category_lower:
            return "class_tool"
        else:
            return "async_tool"
    
    def _generate_from_template(
        self,
        template: str,
        name: str,
        description: str,
        research_data: Dict[str, Any]
    ) -> str:
        """Generate code from template."""
        practices = research_data.get("best_practices", [])
        best_practices = "; ".join(practices[:2]) if practices else "Follow best practices"
        
        if "retry" in name.lower():
            implementation = """last_exception = None
            for i in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if i < max_attempts - 1:
                        await asyncio.sleep(delay * (backoff ** i))
            raise last_exception"""
        elif "cache" in name.lower():
            implementation = """key = str(args) + str(kwargs)
            if key in self._cache:
                return self._cache[key]
            result = func(*args, **kwargs)
            self._cache[key] = result
            return result"""
        else:
            implementation = "# TODO: Implement feature based on research\n            # Best practices: " + best_practices
        
        return template.format(
            name=name,
            params="self, *args, **kwargs" if "class" in template else "*args, **kwargs",
            return_type="Any",
            return_value="None",
            description=description,
            implementation=implementation,
            exception_type="Exception",
            init_params="",
            init_body="pass",
            exec_params="",
            before="# Before hook",
            after="# After hook",
        )
    
    def _generate_imports(
        self,
        feature_request: FeatureRequest,
        research_data: Dict[str, Any]
    ) -> List[str]:
        """Generate required imports."""
        imports = []
        
        # Add common imports
        imports.append("from typing import Any, Optional, Dict, List")
        
        # Add specific imports based on category
        category = feature_request.category.lower()
        if "retry" in category:
            imports.extend(["import time", "import asyncio", "from functools import wraps"])
        elif "cache" in category:
            imports.extend(["from functools import lru_cache", "import time"])
        elif "rate" in category:
            imports.extend(["from collections import deque", "from threading import Lock"])
        
        # Add imports from research
        results = research_data.get("results", [])
        for r in results[:2]:
            snippet = r.get("snippet", "").lower()
            if "import" in snippet:
                # Extract potential import
                match = re.search(r'from (\w+) import', snippet)
                if match:
                    module = match.group(1)
                    if module not in " ".join(imports):
                        imports.append(f"# Consider: from {module} import ...")
        
        return imports
    
    def _generate_tests(self, name: str, description: str) -> str:
        """Generate test code."""
        return f'''
def test_{name}():
    """Test for {name}."""
    # Arrange
    # Act
    # Assert
    pass

def test_{name}_error_handling():
    """Test error handling for {name}."""
    with pytest.raises(Exception):
        pass
'''
    
    def _generate_docs(self, name: str, description: str) -> str:
        """Generate documentation."""
        return f'''
{name}
{'=' * len(name)}

{description}

Usage:
    # TODO: Add usage example

Example:
    # TODO: Add example
'''
    
    def _determine_file_path(self, name: str, category: str) -> str:
        """Determine where to save the generated code."""
        category_lower = category.lower()
        
        if "retry" in category_lower or "resilience" in category_lower:
            return str(self.root_path / "utils" / f"{name}.py")
        elif "cache" in category_lower or "performance" in category_lower:
            return str(self.root_path / "utils" / f"{name}.py")
        elif "rate" in category_lower:
            return str(self.root_path / "utils" / f"{name}.py")
        else:
            return str(self.root_path / "features" / f"{name}.py")
    
    def _calculate_confidence(
        self,
        feature_request: FeatureRequest,
        research_data: Dict[str, Any]
    ) -> float:
        """Calculate confidence in the generated code."""
        confidence = 0.5  # Base confidence
        
        # Increase based on research
        results = research_data.get("results", [])
        confidence += min(len(results) * 0.1, 0.3)
        
        # Increase based on priority
        if feature_request.priority == FeaturePriority.CRITICAL:
            confidence -= 0.1  # Less confident for critical (need more testing)
        elif feature_request.priority == FeaturePriority.LOW:
            confidence += 0.1
        
        return min(max(confidence, 0.0), 1.0)


# =============================================================================
# CODE TESTER
# =============================================================================

class CodeTester:
    """Test generated code safely."""
    
    def __init__(self, root_path: str, verbose: bool = True):
        self.root_path = Path(root_path)
        self.verbose = verbose
        self.test_results: List[Dict[str, Any]] = []
    
    def test_code(
        self,
        code: GeneratedCode,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Test generated code in a sandbox."""
        result = {
            "code": code,
            "syntax_valid": False,
            "imports_valid": False,
            "tests_passed": False,
            "errors": [],
        }
        
        # Test 1: Syntax check
        try:
            compile(code.code, code.file_path, 'exec')
            result["syntax_valid"] = True
            if self.verbose:
                print("[Tester] Syntax: OK")
        except SyntaxError as e:
            result["errors"].append(f"Syntax error: {e}")
            if self.verbose:
                print(f"[Tester] Syntax error: {e}")
        
        # Test 2: Import check
        if result["syntax_valid"]:
            import_test = self._test_imports(code.imports)
            result["imports_valid"] = import_test["success"]
            if not import_test["success"]:
                result["errors"].extend(import_test["missing"])
        
        # Test 3: Run tests if available
        if code.tests and result["syntax_valid"]:
            test_result = self._run_tests(code.tests, timeout)
            result["tests_passed"] = test_result["passed"]
            if not test_result["passed"]:
                result["errors"].extend(test_result["failures"])
        
        # Record result
        self.test_results.append(result)
        
        return result
    
    def _test_imports(self, imports: List[str]) -> Dict[str, Any]:
        """Test if imports are available."""
        missing = []
        for imp in imports:
            if imp.startswith("#"):
                continue
            if imp.startswith("from ") or imp.startswith("import "):
                module = imp.split()[1].split('.')[0]
                try:
                    __import__(module)
                except ImportError:
                    missing.append(f"Missing: {module}")
        
        return {
            "success": len(missing) == 0,
            "missing": missing,
        }
    
    def _run_tests(
        self,
        tests: str,
        timeout: int
    ) -> Dict[str, Any]:
        """Run tests in a subprocess."""
        result = {"passed": False, "failures": []}
        
        try:
            # Write tests to temp file
            import tempfile
            test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
            test_file.write(tests)
            test_file.close()
            
            # Run pytest
            proc = subprocess.run(
                ["python", "-m", "pytest", test_file.name, "-v"],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            
            result["passed"] = proc.returncode == 0
            if not result["passed"]:
                result["failures"].append(proc.stderr)
            
            # Cleanup
            os.unlink(test_file.name)
            
        except subprocess.TimeoutExpired:
            result["failures"].append("Test timeout")
        except Exception as e:
            result["failures"].append(str(e))
        
        return result


# =============================================================================
# FEATURE INTEGRATOR
# =============================================================================

class FeatureIntegrator:
    """Integrate new features into the codebase safely."""
    
    def __init__(self, root_path: str, verbose: bool = True):
        self.root_path = Path(root_path)
        self.verbose = verbose
        self.integrations: List[FeaturePipeline] = []
        self._backup_dir = self.root_path / ".backups"
        self._backup_dir.mkdir(exist_ok=True)
    
    def integrate(
        self,
        pipeline: FeaturePipeline
    ) -> bool:
        """Integrate a feature into the codebase."""
        code = pipeline.implementation
        
        if not pipeline.tests_passed and pipeline.request.priority != FeaturePriority.CRITICAL:
            if self.verbose:
                print("[Integrator] Skipping: tests failed")
            return False
        
        try:
            # Create backup
            self._create_backup(code.file_path)
            
            # Write code
            self._write_code(code)
            
            # Update __init__ if needed
            self._update_exports(code)
            
            # Mark as integrated
            pipeline.integrated = True
            self.integrations.append(pipeline)
            
            if self.verbose:
                print(f"[Integrator] Integrated: {code.feature_name}")
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"[Integrator] Failed: {e}")
            # Rollback
            self._rollback(code.file_path)
            return False
    
    def _create_backup(self, file_path: str):
        """Create a backup of existing file."""
        path = Path(file_path)
        if path.exists():
            backup_name = f"{path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{path.suffix}"
            backup_path = self._backup_dir / backup_name
            backup_path.write_text(path.read_text())
            if self.verbose:
                print(f"[Integrator] Backup created: {backup_path}")
    
    def _write_code(self, code: GeneratedCode):
        """Write generated code to file."""
        path = Path(code.file_path)
        
        # Create directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write imports and code
        content = []
        for imp in code.imports:
            content.append(imp)
        content.append("")
        content.append(code.code)
        
        if code.documentation:
            content.append("")
            content.append(code.documentation)
        
        path.write_text("\n".join(content))
        
        if self.verbose:
            print(f"[Integrator] Written: {path}")
    
    def _update_exports(self, code: GeneratedCode):
        """Update __init__.py exports if needed."""
        path = Path(code.file_path)
        
        # Find __init__.py in same directory
        init_file = path.parent / "__init__.py"
        if not init_file.exists():
            return
        
        content = init_file.read_text()
        
        # Add export if not already there
        export_name = f"{code.feature_name}"
        if export_name not in content:
            content += f"\n__all__ = __all__ + ['{export_name}']\n"
            init_file.write_text(content)
    
    def _rollback(self, file_path: str):
        """Rollback to previous version."""
        path = Path(file_path)
        
        # Find most recent backup
        backups = list(self._backup_dir.glob(f"{path.stem}_*{path.suffix}"))
        if backups:
            latest = max(backups, key=lambda p: p.stat().st_mtime)
            path.write_text(latest.read_text())
            if self.verbose:
                print(f"[Integrator] Rolled back: {path}")
    
    def undo_last(self) -> bool:
        """Undo the last integration."""
        if not self.integrations:
            return False
        
        pipeline = self.integrations.pop()
        code = pipeline.implementation
        
        self._rollback(code.file_path)
        pipeline.integrated = False
        
        if self.verbose:
            print(f"[Integrator] Undid: {code.feature_name}")
        
        return True


# =============================================================================
# AUTO FEATURE GENERATOR - MAIN CLASS
# =============================================================================

class AutoFeatureGenerator:
    """Complete system for generating and integrating new features.
    
    Pipeline:
    1. Task Fails → FailureAnalyzer
    2. Analyze → InternetResearcher
    3. Research → CodeGenerator
    4. Generate → CodeTester
    5. Test → FeatureIntegrator
    
    Usage:
        generator = AutoFeatureGenerator("/path/to/project")
        
        # On task failure
        generator.on_task_failure(failure)
        
        # Or manually request feature
        feature = FeatureRequest(...)
        pipeline = generator.generate_feature(feature)
    """
    
    def __init__(
        self,
        root_path: Optional[str] = None,
        verbose: bool = True,
        auto_integrate: bool = False,
    ):
        self.root_path = Path(root_path or os.getcwd())
        self.verbose = verbose
        self.auto_integrate = auto_integrate
        
        # Components
        self.researcher = InternetResearcher(verbose=verbose)
        self.analyzer = FailureAnalyzer(verbose=verbose)
        self.generator = CodeGenerator(str(self.root_path), verbose=verbose)
        self.tester = CodeTester(str(self.root_path), verbose=verbose)
        self.integrator = FeatureIntegrator(str(self.root_path), verbose=verbose)
        
        # State
        self.pipelines: List[FeaturePipeline] = []
        self.generated_features: List[GeneratedCode] = []
        
        if self.verbose:
            print(f"[AutoFeatureGenerator] Initialized at {self.root_path}")
    
    def on_task_failure(
        self,
        failure: TaskFailure
    ) -> Optional[FeaturePipeline]:
        """Handle a task failure - analyze and generate fix."""
        if self.verbose:
            print(f"\n[AutoFeatureGenerator] Task failed: {failure.task_name}")
            print(f"  Error: {failure.error_message[:100]}")
        
        # Step 1: Analyze failure
        analysis = self.analyzer.analyze(failure)
        
        # Step 2: Check if feature is needed
        feature_request = analysis.get("feature_needed")
        if not feature_request:
            if self.verbose:
                print("[AutoFeatureGenerator] No feature needed")
            return None
        
        # Step 3: Research solution
        research = self.researcher.research_error(failure.error_message)
        feature_request.research_data = research
        
        # Step 4: Generate feature
        pipeline = self.generate_feature(feature_request)
        
        return pipeline
    
    def generate_feature(
        self,
        feature_request: FeatureRequest
    ) -> FeaturePipeline:
        """Generate and optionally integrate a feature."""
        if self.verbose:
            print(f"\n[AutoFeatureGenerator] Generating: {feature_request.name}")
        
        # Research
        research = self.researcher.research_feature(
            feature_request.name,
            feature_request.category
        )
        
        # Generate code
        code = self.generator.generate(feature_request, research)
        self.generated_features.append(code)
        
        if self.verbose:
            print(f"[AutoFeatureGenerator] Generated {len(code.code)} chars of code")
            print(f"  File: {code.file_path}")
            print(f"  Confidence: {code.confidence:.0%}")
        
        # Create pipeline
        pipeline = FeaturePipeline(
            request=feature_request,
            research=research,
            implementation=code,
        )
        
        # Test
        test_result = self.tester.test_code(code)
        pipeline.tests_passed = test_result["syntax_valid"]
        
        if self.verbose:
            print(f"[AutoFeatureGenerator] Tests: {'PASSED' if pipeline.tests_passed else 'FAILED'}")
        
        # Integrate if enabled
        if self.auto_integrate and pipeline.tests_passed:
            success = self.integrator.integrate(pipeline)
            if self.verbose:
                print(f"[AutoFeatureGenerator] Integration: {'SUCCESS' if success else 'FAILED'}")
        
        self.pipelines.append(pipeline)
        return pipeline
    
    def generate_from_description(
        self,
        description: str,
        category: str = "feature",
        priority: FeaturePriority = FeaturePriority.MEDIUM
    ) -> FeaturePipeline:
        """Generate a feature from a description."""
        # Create request from description
        name = self._name_from_description(description)
        
        feature_request = FeatureRequest(
            name=name,
            description=description,
            category=category,
            priority=priority,
        )
        
        return self.generate_feature(feature_request)
    
    def _name_from_description(self, description: str) -> str:
        """Convert description to valid feature name."""
        # Remove special chars, lowercase
        name = re.sub(r'[^a-zA-Z0-9\s]', '', description)
        name = re.sub(r'\s+', '_', name)
        name = name.lower()[:50]
        return f"feature_{name}" if name[0].isdigit() else name
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        return {
            "pipelines_total": len(self.pipelines),
            "pipelines_integrated": sum(1 for p in self.pipelines if p.integrated),
            "features_generated": len(self.generated_features),
            "failures_analyzed": len(self.analyzer.failure_history),
            "failure_patterns": self.analyzer.get_failure_patterns(),
        }
    
    def generate_report(self) -> str:
        """Generate a report of all generated features."""
        lines = [
            "=" * 60,
            "AUTO FEATURE GENERATOR REPORT",
            "=" * 60,
            "",
            f"Status: {len(self.pipelines)} pipelines, {len(self.generated_features)} features",
            "",
        ]
        
        if self.pipelines:
            lines.append("Generated Features:")
            for pipeline in self.pipelines:
                status = "✓" if pipeline.integrated else "○"
                lines.append(f"  {status} {pipeline.implementation.feature_name}")
                lines.append(f"      Priority: {pipeline.request.priority.value}")
                lines.append(f"      Tests: {'PASS' if pipeline.tests_passed else 'FAIL'}")
        
        return "\n".join(lines)


# =============================================================================
# SELF-SUFFICIENT AGI AGENT
# =============================================================================

class SelfSufficientAGI:
    """AGI Agent that can self-improve and add features autonomously.
    
    Capabilities:
    - Self-improve from failures
    - Research solutions online
    - Generate and test code
    - Integrate safely with rollback
    - Never break itself
    """
    
    def __init__(
        self,
        root_path: Optional[str] = None,
        verbose: bool = True,
        auto_improve: bool = True,
        auto_integrate: bool = False,
    ):
        self.root_path = Path(root_path or os.getcwd())
        self.verbose = verbose
        
        # Core components
        from smith_ai.agi.self_improvement import SelfImprovingAgent
        self.self_improver = SelfImprovingAgent(
            root_path=str(self.root_path),
            verbose=verbose,
        )
        self.feature_generator = AutoFeatureGenerator(
            root_path=str(self.root_path),
            verbose=verbose,
            auto_integrate=auto_integrate,
        )
        
        # Execution history
        self.task_history: List[Dict[str, Any]] = []
        
        if self.verbose:
            print(f"[SelfSufficientAGI] Initialized at {self.root_path}")
            print(f"[SelfSufficientAGI] Auto-improve: {auto_improve}")
            print(f"[SelfSufficientAGI] Auto-integrate: {auto_integrate}")
    
    async def execute_task(
        self,
        task_name: str,
        task_func: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a task with automatic failure handling."""
        result = {
            "task": task_name,
            "success": False,
            "result": None,
            "error": None,
            "feature_pipeline": None,
        }
        
        try:
            # Execute task
            if asyncio.iscoroutinefunction(task_func):
                result["result"] = await task_func(*args, **kwargs)
            else:
                result["result"] = task_func(*args, **kwargs)
            result["success"] = True
            
            if self.verbose:
                print(f"[SelfSufficientAGI] Task succeeded: {task_name}")
            
        except Exception as e:
            # Task failed - analyze and potentially fix
            if self.verbose:
                print(f"[SelfSufficientAGI] Task failed: {task_name}")
                print(f"  Error: {e}")
            
            # Create failure record
            failure = TaskFailure(
                task_name=task_name,
                error_message=str(e),
                error_type=type(e).__name__,
                stack_trace=traceback.format_exc(),
            )
            
            # Try to generate and integrate fix
            pipeline = self.feature_generator.on_task_failure(failure)
            result["feature_pipeline"] = pipeline
            
            if pipeline and self.verbose:
                print(f"[SelfSufficientAGI] Feature pipeline created")
        
        # Record in history
        self.task_history.append(result)
        
        return result
    
    def self_improve_cycle(
        self,
        max_improvements: int = 5
    ) -> Dict[str, Any]:
        """Run self-improvement cycle."""
        if self.verbose:
            print("[SelfSufficientAGI] Starting self-improvement cycle...")
        
        # Analyze code
        analysis = self.self_improver.analyze_self()
        
        # Apply improvements
        improvements = self.self_improver.improve(max_improvements=max_improvements)
        
        return {
            "analysis": analysis,
            "improvements": improvements,
            "status": self.get_status(),
        }
    
    def full_self_improvement(
        self,
        max_improvements: int = 10,
        include_features: bool = True
    ) -> Dict[str, Any]:
        """Run complete self-improvement including feature generation."""
        results = {
            "code_improvements": None,
            "features_generated": [],
            "failures_analyzed": len(self.feature_generator.analyzer.failure_history),
        }
        
        # Run code improvements
        results["code_improvements"] = self.self_improve_cycle(max_improvements)
        
        # Generate features from past failures
        if include_features:
            for failure in self.feature_generator.analyzer.failure_history[-5:]:
                analysis = self.feature_generator.analyzer.analyze(failure)
                feature_request = analysis.get("feature_needed")
                if feature_request:
                    pipeline = self.feature_generator.generate_feature(feature_request)
                    results["features_generated"].append(pipeline.to_dict())
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status."""
        return {
            "self_improvement": {
                "issues_found": len(self.self_improver.issues) if hasattr(self.self_improver, 'issues') else 0,
                "improvements_applied": len(self.self_improver.improvement_history) if hasattr(self.self_improver, 'improvement_history') else 0,
            },
            "feature_generator": self.feature_generator.get_status(),
            "task_history": {
                "total": len(self.task_history),
                "successes": sum(1 for t in self.task_history if t["success"]),
                "failures": sum(1 for t in self.task_history if not t["success"]),
            },
        }
    
    def generate_report(self) -> str:
        """Generate full report."""
        return f"""
{'='*60}
SELF-SUFFICIENT AGI REPORT
{'='*60}

Feature Generation:
{self.feature_generator.generate_report()}

Task History:
  Total: {len(self.task_history)}
  Success: {sum(1 for t in self.task_history if t['success'])}
  Failed: {sum(1 for t in self.task_history if not t['success'])}

{'='*60}
"""
