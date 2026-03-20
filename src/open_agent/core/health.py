"""Health checks and status monitoring.

Provides system health checks similar to OpenClaw:
- Gateway health
- Model connectivity
- Channel status
- Memory/Skills availability
- Quick fixes for common issues
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time
import structlog

logger = structlog.get_logger(__name__)


class HealthStatus(str, Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str = ""
    latency_ms: float = 0
    details: Dict[str, Any] = field(default_factory=dict)
    fixes: List[str] = field(default_factory=list)


class HealthChecker:
    """System health checker."""

    def __init__(self):
        self._checks: Dict[str, asyncio.Future] = {}

    async def check_gateway(self) -> HealthCheck:
        """Check gateway health."""
        start = time.time()

        try:
            from open_agent.core.gateway import Gateway
            gateway = Gateway()
            latency = (time.time() - start) * 1000
            return HealthCheck(
                name="gateway",
                status=HealthStatus.HEALTHY,
                message="Gateway is ready",
                latency_ms=latency,
            )
        except Exception as e:
            return HealthCheck(
                name="gateway",
                status=HealthStatus.UNHEALTHY,
                message=f"Gateway error: {str(e)}",
                latency_ms=(time.time() - start) * 1000,
                fixes=["Restart gateway", "Check configuration"],
            )

    async def check_nvidia_api(self) -> HealthCheck:
        """Check NVIDIA API connectivity."""
        start = time.time()

        try:
            import os
            api_key = os.environ.get("NVIDIA_API_KEY", "")

            if not api_key:
                return HealthCheck(
                    name="nvidia_api",
                    status=HealthStatus.UNHEALTHY,
                    message="NVIDIA_API_KEY not set",
                    latency_ms=(time.time() - start) * 1000,
                    fixes=["Set NVIDIA_API_KEY in your environment"],
                )

            # Try a simple API call
            from openai import OpenAI
            client = OpenAI(
                api_key=api_key,
                base_url="https://integrate.api.nvidia.com/v1",
            )

            response = client.chat.completions.create(
                model="nvidia/nemotron-3-super-120b-a12b",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
            )

            latency = (time.time() - start) * 1000

            return HealthCheck(
                name="nvidia_api",
                status=HealthStatus.HEALTHY,
                message="NVIDIA API is accessible",
                latency_ms=latency,
                details={"model": "nemotron-3-super-120b-a12b"},
            )

        except Exception as e:
            latency = (time.time() - start) * 1000
            error_msg = str(e)

            fixes = []
            if "401" in error_msg or "Unauthorized" in error_msg:
                fixes.append("Regenerate your NVIDIA API key")
            elif "connection" in error_msg.lower():
                fixes.append("Check your internet connection")
            else:
                fixes.append("Check NVIDIA API status at status.nvidia.com")

            return HealthCheck(
                name="nvidia_api",
                status=HealthStatus.UNHEALTHY,
                message=f"API error: {error_msg[:100]}",
                latency_ms=latency,
                fixes=fixes,
            )

    async def check_openshell(self) -> HealthCheck:
        """Check OpenShell availability."""
        start = time.time()

        try:
            import subprocess
            result = subprocess.run(
                ["openshell", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                return HealthCheck(
                    name="openshell",
                    status=HealthStatus.HEALTHY,
                    message=f"OpenShell available: {result.stdout.strip()}",
                    latency_ms=(time.time() - start) * 1000,
                )
            else:
                return HealthCheck(
                    name="openshell",
                    status=HealthStatus.DEGRADED,
                    message="OpenShell CLI not fully functional",
                    latency_ms=(time.time() - start) * 1000,
                    fixes=["Reinstall OpenShell: curl -LsSf https://..."],
                )

        except FileNotFoundError:
            return HealthCheck(
                name="openshell",
                status=HealthStatus.DEGRADED,
                message="OpenShell CLI not installed",
                latency_ms=(time.time() - start) * 1000,
                fixes=[
                    "Install OpenShell:",
                    "curl -LsSf https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh | sh",
                ],
            )
        except Exception as e:
            return HealthCheck(
                name="openshell",
                status=HealthStatus.UNHEALTHY,
                message=f"OpenShell error: {str(e)}",
                latency_ms=(time.time() - start) * 1000,
            )

    async def check_memory(self) -> HealthCheck:
        """Check memory system."""
        start = time.time()

        try:
            from open_agent.memory.memory import create_memory_store
            store = create_memory_store()
            stats = store.get_stats()

            return HealthCheck(
                name="memory",
                status=HealthStatus.HEALTHY,
                message=f"Memory initialized with {stats['total']} entries",
                latency_ms=(time.time() - start) * 1000,
                details=stats,
            )
        except Exception as e:
            return HealthCheck(
                name="memory",
                status=HealthStatus.DEGRADED,
                message=f"Memory error: {str(e)}",
                latency_ms=(time.time() - start) * 1000,
                fixes=["Check workspace permissions"],
            )

    async def check_skills(self) -> HealthCheck:
        """Check skills system."""
        start = time.time()

        try:
            from open_agent.tools.skills import create_skill_registry
            registry = create_skill_registry()
            stats = registry.get_stats()

            return HealthCheck(
                name="skills",
                status=HealthStatus.HEALTHY,
                message=f"{stats['total']} skills loaded",
                latency_ms=(time.time() - start) * 1000,
                details=stats,
            )
        except Exception as e:
            return HealthCheck(
                name="skills",
                status=HealthStatus.DEGRADED,
                message=f"Skills error: {str(e)}",
                latency_ms=(time.time() - start) * 1000,
            )

    async def check_all(self) -> Dict[str, HealthCheck]:
        """Run all health checks."""
        checks = await asyncio.gather(
            self.check_gateway(),
            self.check_nvidia_api(),
            self.check_openshell(),
            self.check_memory(),
            self.check_skills(),
        )

        results = {}
        for check in checks:
            results[check.name] = check

        return results

    def get_overall_status(self, checks: Dict[str, HealthCheck]) -> HealthStatus:
        """Get overall system status."""
        statuses = [c.status for c in checks.values()]

        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        elif all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN

    def format_report(self, checks: Dict[str, HealthCheck]) -> str:
        """Format health report."""
        overall = self.get_overall_status(checks)

        lines = [
            "=" * 50,
            f"Health Report - {overall.value.upper()}",
            "=" * 50,
            "",
        ]

        for name, check in checks.items():
            status_icon = {
                HealthStatus.HEALTHY: "✓",
                HealthStatus.DEGRADED: "~",
                HealthStatus.UNHEALTHY: "✗",
                HealthStatus.UNKNOWN: "?",
            }.get(check.status, "?")

            lines.append(f"{status_icon} {name}: {check.status.value}")
            if check.message:
                lines.append(f"  {check.message}")
            if check.latency_ms > 0:
                lines.append(f"  Latency: {check.latency_ms:.0f}ms")
            if check.fixes:
                lines.append("  Fixes:")
                for fix in check.fixes:
                    lines.append(f"    - {fix}")
            lines.append("")

        return "\n".join(lines)


def create_health_checker() -> HealthChecker:
    """Create a health checker."""
    return HealthChecker()
