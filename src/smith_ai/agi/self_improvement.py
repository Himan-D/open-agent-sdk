"""Self-Improvement Module for True AGI Agent.

This module enables the AGI to:
1. Analyze its own code for issues
2. Detect gaps in functionality
3. Generate improvements
4. Apply fixes autonomously
5. Learn from self-modification

Core Components:
- SelfAnalyzer: Code analysis and issue detection
- SelfPatcher: Apply fixes to code
- GapDetector: Find missing features
- ImprovementEngine: Generate and evaluate improvements
- SelfImprovingAgent: AGI with self-improvement capabilities
"""

from __future__ import annotations

import ast
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

class IssueSeverity(str, Enum):
    """Severity levels for detected issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueType(str, Enum):
    """Types of issues that can be detected."""
    BUG = "bug"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MISSING_FEATURE = "missing_feature"
    CODE_QUALITY = "code_quality"
    TYPE_SAFETY = "type_safety"
    ERROR_HANDLING = "error_handling"
    DOCUMENTATION = "documentation"
    TEST_COVERAGE = "test_coverage"


class ImprovementType(str, Enum):
    """Types of improvements."""
    REFACTOR = "refactor"
    OPTIMIZE = "optimize"
    SECURE = "secure"
    EXTEND = "extend"
    FIX = "fix"
    DOCUMENT = "document"
    TEST = "test"


@dataclass
class CodeIssue:
    """Represents a detected code issue."""
    issue_type: IssueType
    severity: IssueSeverity
    file_path: str
    line_number: int
    description: str
    suggestion: str
    code_snippet: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.issue_type.value,
            "severity": self.severity.value,
            "file": self.file_path,
            "line": self.line_number,
            "description": self.description,
            "suggestion": self.suggestion,
            "code": self.code_snippet,
        }


@dataclass
class CodeGap:
    """Represents a missing feature or capability."""
    gap_type: str
    category: str
    description: str
    priority: int
    related_files: List[str] = field(default_factory=list)
    suggested_implementation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.gap_type,
            "category": self.category,
            "description": self.description,
            "priority": self.priority,
            "related_files": self.related_files,
            "suggestion": self.suggested_implementation,
        }


@dataclass
class Improvement:
    """Represents a potential improvement."""
    improvement_type: ImprovementType
    title: str
    description: str
    file_path: str
    original_code: str
    improved_code: str
    rationale: str
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.improvement_type.value,
            "title": self.title,
            "description": self.description,
            "file": self.file_path,
            "rationale": self.rationale,
            "confidence": self.confidence,
        }


@dataclass
class SelfModification:
    """Record of a self-modification."""
    timestamp: datetime
    file_path: str
    change_type: str
    description: str
    original_code: str
    new_code: str
    success: bool
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "file": self.file_path,
            "type": self.change_type,
            "description": self.description,
            "success": self.success,
            "error": self.error,
        }


# =============================================================================
# SELF ANALYZER
# =============================================================================

class SelfAnalyzer:
    """Analyzes code to detect issues, bugs, and improvement opportunities."""
    
    def __init__(self, root_path: str, verbose: bool = True):
        self.root_path = Path(root_path)
        self.verbose = verbose
        self.issues: List[CodeIssue] = []
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Setup detection patterns."""
        self.bug_patterns = [
            (r"except\s*:\s*$", IssueSeverity.HIGH, "Bare except clause"),
            (r"except\s+Exception\s*:\s*pass", IssueSeverity.MEDIUM, "Empty exception handler"),
            (r"print\s*\(.*\)", IssueSeverity.LOW, "Debug print statement"),
            (r"# TODO|# FIXME|# XXX", IssueSeverity.LOW, "Unresolved TODO/FIXME"),
            (r"os\.system\s*\(", IssueSeverity.HIGH, "os.system() is a security risk"),
            (r"eval\s*\(", IssueSeverity.HIGH, "eval() is a security risk"),
            (r"exec\s*\(", IssueSeverity.HIGH, "exec() is a security risk"),
        ]
    
    def analyze_file(self, file_path: Path) -> List[CodeIssue]:
        """Analyze a single file for issues."""
        issues = []
        try:
            content = file_path.read_text()
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                for pattern, severity, desc in self.bug_patterns:
                    if re.search(pattern, line):
                        issues.append(CodeIssue(
                            issue_type=IssueType.BUG,
                            severity=severity,
                            file_path=str(file_path),
                            line_number=line_num,
                            description=desc,
                            suggestion=f"Review line: {line.strip()}",
                            code_snippet=line.strip(),
                        ))
            if file_path.suffix == '.py':
                issues.extend(self._ast_analysis(content, str(file_path)))
        except Exception as e:
            if self.verbose:
                print(f"[Analyzer] Error: {e}")
        return issues
    
    def _ast_analysis(self, content: str, file_path: str) -> List[CodeIssue]:
        """Use AST to detect code issues."""
        issues = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = getattr(node, 'end_lineno', 0) - node.lineno
                    if func_lines > 100:
                        issues.append(CodeIssue(
                            issue_type=IssueType.CODE_QUALITY,
                            severity=IssueSeverity.MEDIUM,
                            file_path=file_path,
                            line_number=node.lineno,
                            description=f"Long function '{node.name}' ({func_lines} lines)",
                            suggestion="Consider breaking this function into smaller pieces",
                        ))
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    issues.append(CodeIssue(
                        issue_type=IssueType.ERROR_HANDLING,
                        severity=IssueSeverity.HIGH,
                        file_path=file_path,
                        line_number=node.lineno,
                        description="Bare except clause catches all exceptions",
                        suggestion="Use 'except Exception as e:' instead",
                    ))
        except SyntaxError as e:
            issues.append(CodeIssue(
                issue_type=IssueType.BUG,
                severity=IssueSeverity.CRITICAL,
                file_path=file_path,
                line_number=getattr(e, 'lineno', 0) or 0,
                description=f"Syntax error: {e.msg}",
                suggestion="Fix the syntax error",
            ))
        except Exception as e:
            if self.verbose:
                print(f"[Analyzer] AST error: {e}")
        return issues
    
    def analyze_directory(self, directory: Path = None) -> List[CodeIssue]:
        """Analyze all Python files in a directory."""
        directory = directory or self.root_path
        all_issues = []
        for file_path in directory.rglob("*.py"):
            if any(x in str(file_path) for x in ['venv', '__pycache__', '.git']):
                continue
            issues = self.analyze_file(file_path)
            all_issues.extend(issues)
        self.issues = all_issues
        return all_issues
    
    def get_issues_by_severity(self) -> Dict[IssueSeverity, List[CodeIssue]]:
        """Group issues by severity."""
        grouped = {s: [] for s in IssueSeverity}
        for issue in self.issues:
            grouped[issue.severity].append(issue)
        return grouped
    
    def generate_report(self) -> str:
        """Generate a human-readable report."""
        if not self.issues:
            return "No issues found!"
        by_severity = self.get_issues_by_severity()
        report = ["=" * 60, "SELF-ANALYSIS REPORT", "=" * 60, ""]
        for severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH, IssueSeverity.MEDIUM, IssueSeverity.LOW]:
            issues = by_severity[severity]
            if issues:
                report.append(f"\n{severity.value.upper()} ({len(issues)} issues):")
                for issue in issues[:5]:
                    report.append(f"  [{issue.file_path}:{issue.line_number}]")
                    report.append(f"    {issue.description}")
        return "\n".join(report)


# =============================================================================
# GAP DETECTOR
# =============================================================================

class GapDetector:
    """Detects gaps in functionality and features."""
    
    def __init__(self, root_path: str, verbose: bool = True):
        self.root_path = Path(root_path)
        self.verbose = verbose
        self.gaps: List[CodeGap] = []
    
    def detect_missing_features(self) -> List[CodeGap]:
        """Detect missing features based on patterns."""
        gaps = []
        has_caching = False
        has_retry = False
        has_logging = False
        
        for f in self.root_path.rglob("*.py"):
            if '__pycache__' in str(f):
                continue
            try:
                content = f.read_text().lower()
                if 'cache' in content or 'lru_cache' in content:
                    has_caching = True
                if 'retry' in content:
                    has_retry = True
                if 'logging' in content or 'structlog' in content:
                    has_logging = True
            except:
                pass
        
        if not has_caching:
            gaps.append(CodeGap(
                gap_type="caching",
                category="performance",
                description="No caching implementation found",
                priority=6,
            ))
        if not has_retry:
            gaps.append(CodeGap(
                gap_type="retry_logic",
                category="resilience",
                description="Missing retry logic for failures",
                priority=5,
            ))
        if not has_logging:
            gaps.append(CodeGap(
                gap_type="logging_centralized",
                category="observability",
                description="No centralized logging",
                priority=4,
            ))
        
        self.gaps = gaps
        return gaps
    
    def generate_report(self) -> str:
        """Generate a report of detected gaps."""
        if not self.gaps:
            return "No significant gaps detected!"
        report = ["=" * 60, "GAP DETECTION REPORT", "=" * 60, ""]
        for gap in sorted(self.gaps, key=lambda x: x.priority, reverse=True):
            report.append(f"\n[{gap.priority}/10] {gap.gap_type} ({gap.category})")
            report.append(f"  {gap.description}")
        return "\n".join(report)


# =============================================================================
# SELF PATCHER
# =============================================================================

class SelfPatcher:
    """Applies fixes and improvements to code."""
    
    def __init__(self, root_path: str, verbose: bool = True):
        self.root_path = Path(root_path)
        self.verbose = verbose
        self.modifications: List[SelfModification] = []
    
    def apply_fix(
        self,
        file_path: str,
        old_code: str,
        new_code: str,
        description: str = "Applied fix"
    ) -> bool:
        """Apply a fix to a file."""
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            content = path.read_text()
            if old_code not in content:
                return False
            
            backup_path = path.with_suffix(path.suffix + '.bak')
            backup_path.write_text(content)
            new_content = content.replace(old_code, new_code)
            path.write_text(new_content)
            
            self.modifications.append(SelfModification(
                timestamp=datetime.now(),
                file_path=file_path,
                change_type="fix",
                description=description,
                original_code=old_code[:200],
                new_code=new_code[:200],
                success=True,
            ))
            return True
        except Exception as e:
            self.modifications.append(SelfModification(
                timestamp=datetime.now(),
                file_path=file_path,
                change_type="fix",
                description=description,
                original_code=old_code[:200],
                new_code=new_code[:200],
                success=False,
                error=str(e),
            ))
            return False
    
    def add_import(
        self,
        file_path: str,
        import_statement: str,
    ) -> bool:
        """Add an import to a file."""
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            content = path.read_text()
            if import_statement in content:
                return True
            lines = content.split('\n')
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    insert_idx = i + 1
            lines.insert(insert_idx, import_statement)
            path.write_text('\n'.join(lines))
            self.modifications.append(SelfModification(
                timestamp=datetime.now(),
                file_path=file_path,
                change_type="add_import",
                description=f"Added import: {import_statement}",
                original_code="",
                new_code=import_statement,
                success=True,
            ))
            return True
        except Exception as e:
            return False
    
    def add_function(
        self,
        file_path: str,
        function_code: str,
    ) -> bool:
        """Add a function to a file."""
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            content = path.read_text()
            if function_code in content:
                return True
            content += '\n\n' + function_code
            path.write_text(content)
            self.modifications.append(SelfModification(
                timestamp=datetime.now(),
                file_path=file_path,
                change_type="add_function",
                description="Added function",
                original_code="",
                new_code=function_code[:200],
                success=True,
            ))
            return True
        except Exception as e:
            return False
    
    def undo_last(self) -> bool:
        """Undo the last modification."""
        if not self.modifications:
            return False
        last = self.modifications[-1]
        try:
            path = Path(last.file_path)
            if not path.exists():
                return False
            content = path.read_text()
            if last.new_code in content and last.original_code:
                content = content.replace(last.new_code, last.original_code)
            elif last.new_code in content:
                content = content.replace(last.new_code, '')
            path.write_text(content)
            self.modifications.pop()
            return True
        except:
            return False
    
    def get_modifications(self) -> List[SelfModification]:
        """Get all modifications."""
        return self.modifications


# =============================================================================
# IMPROVEMENT ENGINE
# =============================================================================

class ImprovementEngine:
    """Generates and evaluates code improvements."""
    
    def __init__(self, root_path: str, verbose: bool = True):
        self.root_path = Path(root_path)
        self.verbose = verbose
        self.improvements: List[Improvement] = []
    
    def generate_improvements(
        self,
        issues: List[CodeIssue],
        gaps: List[CodeGap]
    ) -> List[Improvement]:
        """Generate improvements based on issues and gaps."""
        improvements = []
        for issue in issues:
            improvement = self._issue_to_improvement(issue)
            if improvement:
                improvements.append(improvement)
        for gap in gaps:
            improvement = self._gap_to_improvement(gap)
            if improvement:
                improvements.append(improvement)
        self.improvements = improvements
        return improvements
    
    def _issue_to_improvement(self, issue: CodeIssue) -> Optional[Improvement]:
        """Convert an issue to an improvement."""
        if "Bare except" in issue.description:
            return Improvement(
                improvement_type=ImprovementType.FIX,
                title="Add specific exception handling",
                description=f"Fix: {issue.description}",
                file_path=issue.file_path,
                original_code=issue.code_snippet,
                improved_code="except Exception as e:\n    logging.error(f'Error: {e}')",
                rationale="Specific exception handling prevents catching SystemExit",
                confidence=0.8,
            )
        if "print" in issue.description.lower():
            return Improvement(
                improvement_type=ImprovementType.FIX,
                title="Replace print with logging",
                description=f"Fix: {issue.description}",
                file_path=issue.file_path,
                original_code=issue.code_snippet,
                improved_code="import logging\nlogger = logging.getLogger(__name__)",
                rationale="Logging is more configurable and production-ready",
                confidence=0.8,
            )
        return None
    
    def _gap_to_improvement(self, gap: CodeGap) -> Optional[Improvement]:
        """Convert a gap to an improvement."""
        templates = {
            "caching": {
                "code": '''from functools import lru_cache\n\n@lru_cache(maxsize=128)\ndef cached_function(*args, **kwargs):\n    """Cached version."""\n    pass\n''',
                "rationale": "Caching improves performance",
            },
            "retry_logic": {
                "code": '''from tenacity import retry, stop_after_attempt\n\n@retry(stop=stop_after_attempt(3))\ndef retry_function(*args, **kwargs):\n    """Function with retry logic."""\n    pass\n''',
                "rationale": "Retry logic handles transient failures",
            },
        }
        template = templates.get(gap.gap_type)
        if template:
            return Improvement(
                improvement_type=ImprovementType.OPTIMIZE,
                title=f"Implement {gap.gap_type}",
                description=gap.description,
                file_path=str(self.root_path / "utils.py"),
                original_code="",
                improved_code=template["code"],
                rationale=template["rationale"],
                confidence=0.7,
            )
        return None
    
    def apply_improvement(self, improvement: Improvement, patcher: SelfPatcher) -> bool:
        """Apply an improvement using the patcher."""
        if improvement.original_code:
            return patcher.apply_fix(
                improvement.file_path,
                improvement.original_code,
                improvement.improved_code,
                f"Applied: {improvement.title}"
            )
        else:
            return patcher.add_function(
                improvement.file_path,
                improvement.improved_code,
            )
    
    def generate_report(self) -> str:
        """Generate a report of potential improvements."""
        if not self.improvements:
            return "No improvements generated!"
        by_type = {}
        for imp in self.improvements:
            if imp.improvement_type not in by_type:
                by_type[imp.improvement_type] = []
            by_type[imp.improvement_type].append(imp)
        report = ["=" * 60, "IMPROVEMENT REPORT", "=" * 60, ""]
        for imp_type, imps in by_type.items():
            report.append(f"\n{imp_type.value.upper()} ({len(imps)}):")
            for imp in imps[:3]:
                report.append(f"  [{imp.confidence:.0%}] {imp.title}")
        return "\n".join(report)


# =============================================================================
# SELF-IMPROVING AGENT
# =============================================================================

class SelfImprovingAgent:
    """AGI Agent with self-improvement capabilities."""
    
    def __init__(
        self,
        root_path: Optional[str] = None,
        verbose: bool = True,
        auto_improve: bool = False,
    ):
        self.root_path = Path(root_path or os.getcwd())
        self.verbose = verbose
        self.analyzer = SelfAnalyzer(str(self.root_path), verbose=verbose)
        self.gap_detector = GapDetector(str(self.root_path), verbose=verbose)
        self.patcher = SelfPatcher(str(self.root_path), verbose=verbose)
        self.engine = ImprovementEngine(str(self.root_path), verbose=verbose)
        self.issues: List[CodeIssue] = []
        self.gaps: List[CodeGap] = []
        self.improvements: List[Improvement] = []
        self.auto_improve = auto_improve
        self.improvement_history: List[Dict[str, Any]] = []
        if self.verbose:
            print(f"[SelfImprovingAgent] Initialized at {self.root_path}")
    
    def analyze_self(self) -> Dict[str, Any]:
        """Analyze own code for issues and gaps."""
        if self.verbose:
            print("[SelfImprovingAgent] Starting self-analysis...")
        self.issues = self.analyzer.analyze_directory()
        self.gaps = self.gap_detector.detect_missing_features()
        self.improvements = self.engine.generate_improvements(self.issues, self.gaps)
        result = {
            "issues_found": len(self.issues),
            "gaps_found": len(self.gaps),
            "improvements_possible": len(self.improvements),
            "critical_issues": len([i for i in self.issues if i.severity == IssueSeverity.CRITICAL]),
        }
        if self.verbose:
            print(f"[SelfImprovingAgent] Analysis complete:")
            print(f"  - {result['issues_found']} issues found")
            print(f"  - {result['gaps_found']} gaps found")
            print(f"  - {result['improvements_possible']} improvements possible")
        return result
    
    def improve(
        self,
        max_improvements: int = 5,
        min_confidence: float = 0.7,
        severity_threshold: IssueSeverity = IssueSeverity.MEDIUM
    ) -> Dict[str, Any]:
        """Apply improvements autonomously."""
        if not self.improvements:
            self.analyze_self()
        applied = []
        failed = []
        priority_improvements = []
        for imp in self.improvements:
            if imp.confidence < min_confidence:
                continue
            is_high_priority = False
            for issue in self.issues:
                if issue.file_path == imp.file_path and issue.severity >= severity_threshold:
                    is_high_priority = True
                    break
            priority_improvements.append((is_high_priority, imp.confidence, imp))
        priority_improvements.sort(key=lambda x: (x[0], x[1]), reverse=True)
        for _, _, improvement in priority_improvements[:max_improvements]:
            if self.verbose:
                print(f"[SelfImprovingAgent] Applying: {improvement.title}")
            try:
                success = self.engine.apply_improvement(improvement, self.patcher)
                if success:
                    applied.append(improvement)
                    self.improvement_history.append({
                        "timestamp": datetime.now().isoformat(),
                        "improvement": improvement.to_dict(),
                        "status": "applied",
                    })
                else:
                    failed.append(improvement)
            except Exception as e:
                if self.verbose:
                    print(f"[SelfImprovingAgent] Failed: {e}")
                failed.append(improvement)
        return {
            "applied": len(applied),
            "failed": len(failed),
            "total_improvements": len(self.improvements),
        }
    
    def run_self_improvement_cycle(
        self,
        max_improvements: int = 10,
        auto_commit: bool = False
    ) -> Dict[str, Any]:
        """Run a complete self-improvement cycle."""
        if self.verbose:
            print("[SelfImprovingAgent] Starting self-improvement cycle...")
        analysis = self.analyze_self()
        improvement_result = self.improve(max_improvements=max_improvements)
        committed = False
        if auto_commit and improvement_result["applied"] > 0:
            try:
                self._auto_commit()
                committed = True
            except Exception as e:
                if self.verbose:
                    print(f"[SelfImprovingAgent] Auto-commit failed: {e}")
        return {
            **analysis,
            **improvement_result,
            "committed": committed,
            "history": self.improvement_history,
        }
    
    def _auto_commit(self):
        """Auto-commit changes with git."""
        try:
            subprocess.run(["git", "add", "-A"], cwd=self.root_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "feat(self-improvement): Auto-applied improvements"],
                cwd=self.root_path,
                check=True
            )
            if self.verbose:
                print("[SelfImprovingAgent] Changes committed!")
        except Exception as e:
            if self.verbose:
                print(f"[SelfImprovingAgent] Git error: {e}")
            raise
    
    def undo_last_improvement(self) -> bool:
        """Undo the last improvement."""
        return self.patcher.undo_last()
