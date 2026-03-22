#!/usr/bin/env python3
"""SmithAI Long-Running Agent - Runs continuously like Claude Code.

Usage:
    python examples/21_agent_daemon.py
    
Features:
    - Runs indefinitely until stopped
    - Processes tasks from queue
    - Self-improves when idle
    - Persists state between tasks
    - Logs all activity
    - Graceful shutdown on Ctrl+C
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from smith_ai.agi.v2 import TrueAGIAgent
from smith_ai.agi.self_improvement import SelfImprovingAgent
from smith_ai.agi.auto_feature import SelfSufficientAGI, TaskFailure


class LongRunningAgent:
    """Agent that runs continuously like Claude Code.
    
    Features:
    - Continuous task processing
    - Self-improvement cycles
    - State persistence
    - Activity logging
    - Graceful shutdown
    """
    
    def __init__(
        self,
        name: str = "SmithAI-Agent",
        workspace: str = None,
        verbose: bool = True,
    ):
        self.name = name
        self.workspace = Path(workspace or os.getcwd())
        self.verbose = verbose
        
        # Core agent
        self.agent = TrueAGIAgent(name=name, role="general", verbose=verbose)
        
        # Self-improvement
        self.self_improver = SelfImprovingAgent(
            root_path=str(self.workspace),
            verbose=False,
        )
        
        # Task queue
        self.task_queue = asyncio.Queue()
        self.results = []
        
        # State
        self.start_time = datetime.now()
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.self_improvements = 0
        
        # Running state
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        # Setup signal handlers
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup graceful shutdown handlers."""
        import signal
        
        def shutdown_handler(signum, frame):
            print("\n[Agent] Received shutdown signal...")
            self._running = False
            self._shutdown_event.set()
        
        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)
    
    async def start(self):
        """Start the long-running agent."""
        self._running = True
        
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🚀 SmithAI Long-Running Agent Started                          ║
║                                                                  ║
║   Name: {self.name:<52} ║
║   Workspace: {str(self.workspace)[:46]:<46} ║
║                                                                  ║
║   Commands:                                                     ║
║   - task <description>  : Queue a task                          ║
║   - improve             : Run self-improvement cycle            ║
║   - status              : Show agent status                     ║
║   - quit                : Exit gracefully                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._process_tasks()),
            asyncio.create_task(self._auto_improve_loop()),
            asyncio.create_task(self._heartbeat()),
            asyncio.create_task(self._interactive_mode()),
        ]
        
        # Wait for shutdown
        await self._shutdown_event.wait()
        
        # Cancel all tasks
        for task in tasks:
            task.cancel()
        
        # Cleanup
        await self._cleanup()
    
    async def _interactive_mode(self):
        """Handle interactive commands."""
        loop = asyncio.get_event_loop()
        
        while self._running:
            try:
                # Read input with timeout
                line = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: input("\n> ")),
                    timeout=1.0
                )
                
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split(None, 1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if cmd == "task":
                    await self.queue_task(args or "Process data")
                    
                elif cmd == "improve":
                    await self.run_self_improvement()
                    
                elif cmd == "status":
                    self._print_status()
                    
                elif cmd in ["quit", "exit", "q"]:
                    print("[Agent] Shutting down...")
                    self._running = False
                    self._shutdown_event.set()
                    
                elif cmd == "help":
                    self._print_help()
                    
                else:
                    await self.queue_task(line)
                    
            except asyncio.TimeoutError:
                continue
            except EOFError:
                break
            except Exception as e:
                if self._running:
                    print(f"[Error] {e}")
    
    async def queue_task(self, description: str):
        """Queue a task for processing."""
        task_id = f"task_{int(time.time())}"
        
        await self.task_queue.put({
            "id": task_id,
            "description": description,
            "timestamp": datetime.now().isoformat(),
        })
        
        print(f"[Agent] Queued task: {description[:50]}...")
    
    async def run_self_improvement(self):
        """Run a self-improvement cycle on demand."""
        print("[Agent] Running self-improvement cycle...")
        
        try:
            analysis = self.self_improver.analyze_self()
            result = self.self_improver.improve(max_improvements=5)
            
            print(f"[Agent] Analysis: {analysis['issues_found']} issues, "
                  f"{analysis['gaps_found']} gaps found")
            print(f"[Agent] Applied {result['applied']} improvements")
            
        except Exception as e:
            print(f"[Agent] Self-improvement error: {e}")
    
    async def _process_tasks(self):
        """Process tasks from the queue."""
        while self._running:
            try:
                # Get task with timeout
                task = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=5.0
                )
                
                print(f"\n[Agent] Processing: {task['description'][:50]}...")
                
                # Execute task
                start = time.time()
                try:
                    # Simulate task execution
                    result = await self._execute_task(task)
                    
                    elapsed = time.time() - start
                    self.tasks_completed += 1
                    
                    print(f"[Agent] ✓ Completed in {elapsed:.1f}s")
                    print(f"[Agent] Result: {str(result)[:100]}...")
                    
                    # Store result
                    self.results.append({
                        "task": task,
                        "result": result,
                        "elapsed": elapsed,
                        "success": True,
                    })
                    
                except Exception as e:
                    elapsed = time.time() - start
                    self.tasks_failed += 1
                    
                    print(f"[Agent] ✗ Failed in {elapsed:.1f}s: {e}")
                    
                    # Create failure and attempt fix
                    failure = TaskFailure(
                        task_name=task["id"],
                        error_message=str(e),
                        error_type=type(e).__name__,
                    )
                    
                    # Record failure for later analysis
                    self.results.append({
                        "task": task,
                        "error": str(e),
                        "elapsed": elapsed,
                        "success": False,
                        "failure": failure.to_dict(),
                    })
                
                self.task_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._running:
                    print(f"[Agent] Task error: {e}")
    
    async def _execute_task(self, task: Dict) -> Dict:
        """Execute a single task using the agent."""
        # Use cognitive agent to process
        result = await self.agent.cognitive.think(
            task["description"],
            goal=f"Complete task: {task['description']}"
        )
        
        return result
    
    async def _auto_improve_loop(self):
        """Periodically run self-improvement."""
        improvement_interval = 300  # Every 5 minutes
        
        while self._running:
            await asyncio.sleep(improvement_interval)
            
            if not self._running:
                break
            
            # Check if we should improve
            if self.tasks_failed > 0 or self.tasks_completed > 10:
                print(f"\n[Agent] Running self-improvement cycle...")
                
                try:
                    # Analyze code
                    analysis = self.self_improver.analyze_self()
                    
                    # Apply improvements (max 3)
                    result = self.self_improver.improve(max_improvements=3)
                    
                    if result["applied"] > 0:
                        self.self_improvements += result["applied"]
                        print(f"[Agent] ✓ Applied {result['applied']} improvements")
                    else:
                        print(f"[Agent] No improvements needed")
                        
                except Exception as e:
                    print(f"[Agent] Self-improvement error: {e}")
    
    async def _heartbeat(self):
        """Periodic status update."""
        while self._running:
            await asyncio.sleep(60)  # Every minute
            
            if self._running and self.verbose:
                uptime = datetime.now() - self.start_time
                hours = int(uptime.total_seconds() // 3600)
                minutes = int((uptime.total_seconds() % 3600) // 60)
                
                queue_size = self.task_queue.qsize()
                
                if queue_size > 0 or self.tasks_completed % 10 == 0:
                    print(f"[Agent] Heartbeat: {hours}h {minutes}m | "
                          f"Completed: {self.tasks_completed} | "
                          f"Failed: {self.tasks_failed} | "
                          f"Queue: {queue_size}")
    
    def _print_status(self):
        """Print current status."""
        uptime = datetime.now() - self.start_time
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  AGENT STATUS                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  Name:       {self.name:<50} ║
║  Uptime:     {hours}h {minutes}m{'':>43} ║
║  Workspace:  {str(self.workspace)[:50]:<50} ║
╠══════════════════════════════════════════════════════════════════╣
║  Tasks Completed:  {self.tasks_completed:<37} ║
║  Tasks Failed:     {self.tasks_failed:<37} ║
║  Self-Improvements: {self.self_improvements:<35} ║
║  Queue Size:      {self.task_queue.qsize():<37} ║
╚══════════════════════════════════════════════════════════════════╝
        """)
    
    def _print_help(self):
        """Print help message."""
        print("""
╔══════════════════════════════════════════════════════════════════╗
║  COMMANDS                                                      ║
╠══════════════════════════════════════════════════════════════════╣
║  task <description>   Queue a new task                         ║
║  <any text>           Queue a task with this description        ║
║  improve              Run self-improvement cycle               ║
║  status               Show agent status                         ║
║  quit / exit / q      Exit gracefully                          ║
║  help                 Show this help                           ║
╚══════════════════════════════════════════════════════════════════╝
        """)
    
    async def _cleanup(self):
        """Cleanup before exit."""
        uptime = datetime.now() - self.start_time
        
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  SHUTDOWN SUMMARY                                              ║
╠══════════════════════════════════════════════════════════════════╣
║  Uptime:        {uptime}{'':>47} ║
║  Tasks Done:    {self.tasks_completed:<50} ║
║  Tasks Failed:  {self.tasks_failed:<50} ║
║  Improvements:  {self.self_improvements:<50} ║
╚══════════════════════════════════════════════════════════════════╝
        """)


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SmithAI Long-Running Agent")
    parser.add_argument("--name", default="SmithAI-Agent", help="Agent name")
    parser.add_argument("--workspace", default=None, help="Working directory")
    parser.add_argument("--quiet", action="store_true", help="Minimize output")
    
    args = parser.parse_args()
    
    agent = LongRunningAgent(
        name=args.name,
        workspace=args.workspace,
        verbose=not args.quiet,
    )
    
    await agent.start()


if __name__ == "__main__":
    asyncio.run(main())
