#!/usr/bin/env python3
"""SmithAI Skill Workspace - Create, Test, and Publish Skills.

A complete workspace for developers to:
1. Create new skills with handlers
2. Test skills locally
3. Publish to registry
4. Share with the community
"""

import asyncio
import sys
import os
import json
import tempfile
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "/Users/himand/open-agent/src")


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   ████████╗██╗  ██╗███████╗    ███████╗██╗  ██╗██╗████████╗██╗   ██╗ ║
║   ╚══██╔══╝██║  ██║██╔════╝    ██╔════╝██║ ██╔╝██║╚══██╔══╝╚██╗ ██╔╝ ║
║      ██║   ███████║█████╗      ███████╗█████╔╝ ██║   ██║    ╚████╔╝  ║
║      ██║   ██╔══██║██╔══╝      ╚════██║██╔═██╗ ██║   ██║     ╚██╔╝   ║
║      ██║   ██║  ██║███████╗    ███████║██║  ██╗██║   ██║      ██║    ║
║      ╚═╝   ╚═╝  ╚═╝╚══════╝    ╚══════╝╚═╝  ╚═╝╚═╝   ╚═╝      ╚═╝    ║
║                                                                          ║
║   S K I L L   W O R K S P A C E   -   v 4 . 0 . 0                  ║
║                                                                          ║
║   Create • Test • Publish • Share                                      ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
""")


@dataclass
class HandlerTemplate:
    name: str
    description: str
    parameters: List[Dict[str, str]]
    code_template: str
    is_async: bool = False


@dataclass
class SkillProject:
    name: str
    version: str
    description: str
    author: str
    category: str
    tags: List[str] = field(default_factory=list)
    handlers: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    license: str = "MIT"
    repository: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class SkillCreator:
    """Interactive skill creator."""
    
    def __init__(self):
        self.project: Optional[SkillProject] = None
        self.templates = self._get_handler_templates()
    
    def _get_handler_templates(self) -> Dict[str, HandlerTemplate]:
        return {
            "calculator": HandlerTemplate(
                name="calculate",
                description="Perform a calculation",
                parameters=[
                    {"name": "expression", "type": "str", "description": "Math expression"}
                ],
                code_template='''
def calculate(expression: str) -> str:
    """Perform a calculation."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"
''',
            ),
            "text_processor": HandlerTemplate(
                name="process_text",
                description="Process text input",
                parameters=[
                    {"name": "text", "type": "str", "description": "Input text"}
                ],
                code_template='''
def process_text(text: str) -> dict:
    """Process text and return analysis."""
    words = text.split()
    return {
        "word_count": len(words),
        "char_count": len(text),
        "uppercase": text.upper(),
        "lowercase": text.lower(),
    }
''',
            ),
            "data_transformer": HandlerTemplate(
                name="transform",
                description="Transform data between formats",
                parameters=[
                    {"name": "data", "type": "str", "description": "Data to transform"},
                    {"name": "format", "type": "str", "description": "Target format"}
                ],
                code_template='''
def transform(data: str, format: str = "json") -> str:
    """Transform data to specified format."""
    if format == "json":
        return json.dumps({"data": data})
    elif format == "xml":
        return f"<root><data>{data}</data></root>"
    else:
        return data
''',
            ),
            "api_caller": HandlerTemplate(
                name="fetch",
                description="Fetch data from API",
                parameters=[
                    {"name": "url", "type": "str", "description": "API URL"},
                    {"name": "method", "type": "str", "description": "HTTP method"}
                ],
                code_template='''
async def fetch(url: str, method: str = "GET") -> dict:
    """Fetch data from an API."""
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url)
        return {"status": response.status_code, "data": response.text}
''',
                is_async=True,
            ),
            "file_processor": HandlerTemplate(
                name="process_file",
                description="Process a file",
                parameters=[
                    {"name": "path", "type": "str", "description": "File path"},
                    {"name": "operation", "type": "str", "description": "Operation to perform"}
                ],
                code_template='''
def process_file(path: str, operation: str = "read") -> str:
    """Process a file."""
    if operation == "read":
        with open(path, "r") as f:
            return f.read()
    elif operation == "exists":
        return str(os.path.exists(path))
    else:
        return f"Unknown operation: {operation}"
''',
            ),
            "database": HandlerTemplate(
                name="query",
                description="Query a database",
                parameters=[
                    {"name": "query", "type": "str", "description": "SQL query"},
                    {"name": "connection", "type": "str", "description": "Connection string"}
                ],
                code_template='''
async def query(query: str, connection: str = "") -> list:
    """Execute a database query."""
    # Example using sqlite
    import sqlite3
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results
''',
                is_async=True,
            ),
        }
    
    def create_new_skill(self) -> SkillProject:
        """Create a new skill project interactively."""
        print("\n" + "="*60)
        print(" CREATE NEW SKILL")
        print("="*60)
        
        # Get basic info
        name = input("\n  Skill name (e.g., my_awesome_skill): ").strip()
        while not name or " " in name:
            print("  ❌ Name cannot be empty or contain spaces")
            name = input("  Skill name: ").strip()
        
        version = input("  Version [1.0.0]: ").strip() or "1.0.0"
        description = input("  Description: ").strip()
        author = input("  Author name: ").strip()
        
        # Category selection
        print("\n  Categories:")
        categories = [
            "agent", "tool", "integration", "memory", 
            "reasoning", "browser", "data", "utility", "custom"
        ]
        for i, cat in enumerate(categories, 1):
            print(f"    {i}. {cat}")
        
        cat_idx = input("  Select category [1]: ").strip()
        try:
            cat_idx = int(cat_idx) - 1
            category = categories[max(0, min(cat_idx, len(categories)-1))]
        except:
            category = "tool"
        
        # Tags
        tags_input = input("  Tags (comma separated): ").strip()
        tags = [t.strip() for t in tags_input.split(",") if t.strip()]
        
        # License
        license = input("  License [MIT]: ").strip() or "MIT"
        
        self.project = SkillProject(
            name=name,
            version=version,
            description=description,
            author=author,
            category=category,
            tags=tags,
            license=license,
        )
        
        print(f"\n  ✅ Created project: {name}")
        return self.project
    
    def add_handler_interactive(self) -> None:
        """Add a handler to the current project."""
        if not self.project:
            print("❌ No project created. Run create_new_skill() first.")
            return
        
        print("\n" + "-"*60)
        print(" ADD HANDLER")
        print("-"*60)
        
        # Show templates
        print("\n  Handler Templates:")
        for i, (name, tmpl) in enumerate(self.templates.items(), 1):
            print(f"    {i}. {tmpl.name} ({tmpl.description})")
            print(f"       Async: {'Yes' if tmpl.is_async else 'No'}")
        
        print(f"    {len(self.templates)+1}. Custom (write your own)")
        
        sel = input("\n  Select template [1]: ").strip()
        try:
            idx = int(sel) - 1
        except:
            idx = 0
        
        if idx == len(self.templates):
            # Custom handler
            name = input("  Handler name: ").strip()
            desc = input("  Description: ").strip()
            code = input("  Code (multiline, end with ---):\n  ")
            while "---" not in code:
                code += "\n" + input("  ")
            code = code.split("---")[0].strip()
            is_async = "async def" in code
        else:
            tmpl = list(self.templates.values())[idx]
            name = tmpl.name
            desc = tmpl.description
            code = tmpl.code_template.strip()
            is_async = tmpl.is_async
        
        handler = {
            "name": name,
            "description": desc,
            "code": code,
            "is_async": is_async,
            "parameters": self.templates.get(name, HandlerTemplate("", "", [], "")).parameters if idx < len(self.templates) else [],
        }
        
        self.project.handlers.append(handler)
        self.project.updated_at = datetime.now()
        
        print(f"\n  ✅ Added handler: {name}")
    
    def remove_handler(self, name: str) -> bool:
        """Remove a handler by name."""
        if not self.project:
            return False
        
        self.project.handlers = [h for h in self.project.handlers if h["name"] != name]
        self.project.updated_at = datetime.now()
        return True
    
    def list_handlers(self) -> List[str]:
        """List all handlers in the project."""
        if not self.project:
            return []
        return [h["name"] for h in self.project.handlers]
    
    def generate_skill_code(self) -> str:
        """Generate Python code for the skill."""
        if not self.project:
            return ""
        
        handlers_code = []
        for h in self.project.handlers:
            handlers_code.append(f'''
    def {h["name"]}({h["name"]}_params: dict) -> Any:
        """{h["description"]}"""
        {h["code"].replace("def ", "def ").replace("async def ", "async def ")}
''')
        
        code = f'''"""
{self.project.name} - {self.project.description}
Version: {self.project.version}
Author: {self.project.author}
Category: {self.project.category}
Tags: {", ".join(self.project.tags)}
Generated by SmithAI Skill Workspace
"""

import json
from typing import Any, Dict

{chr(10).join(h.replace("def ", "def _handler_").replace("async def", "async def _async_handler_") for h in handlers_code if "def " in h)}

def get_handlers() -> Dict[str, dict]:
    """Return all handlers for this skill."""
    return {{
        {chr(10).join(f'"{h["name"]}": {{"description": "{h["description"]}", "async": {str(h["is_async"]).lower()}}}' + ("," if i < len(self.project.handlers) - 1 else "") for i, h in enumerate(self.project.handlers))}
    }}
'''
        return code
    
    def export_to_file(self, path: str) -> bool:
        """Export skill project to JSON file."""
        if not self.project:
            return False
        
        data = asdict(self.project)
        data["generated_code"] = self.generate_skill_code()
        
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        
        return True
    
    def import_from_file(self, path: str) -> bool:
        """Import skill project from JSON file."""
        try:
            with open(path) as f:
                data = json.load(f)
            
            self.project = SkillProject(
                name=data["name"],
                version=data["version"],
                description=data["description"],
                author=data["author"],
                category=data["category"],
                tags=data.get("tags", []),
                handlers=data.get("handlers", []),
                dependencies=data.get("dependencies", []),
                license=data.get("license", "MIT"),
                repository=data.get("repository", ""),
            )
            return True
        except Exception as e:
            print(f"Error importing: {e}")
            return False


class SkillTester:
    """Test skills before publishing."""
    
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
    
    def create_test_environment(self) -> dict:
        """Create a safe test environment."""
        return {
            "json": __import__("json"),
            "os": __import__("os"),
            "time": __import__("time"),
            "math": __import__("math"),
            "random": __import__("random"),
            "re": __import__("re"),
            "datetime": __import__("datetime"),
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "type": type,
            "len": len,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "open": open,
            "print": print,
        }
    
    async def test_handler(
        self, 
        code: str, 
        handler_name: str, 
        params: Dict[str, Any],
        is_async: bool = False
    ) -> Dict[str, Any]:
        """Test a handler with given parameters."""
        result = {
            "handler": handler_name,
            "params": params,
            "success": False,
            "output": None,
            "error": None,
            "duration_ms": 0,
        }
        
        start = datetime.now()
        
        try:
            # Clean the code - remove type annotations for execution
            import re
            # Step 1: Remove return type annotations first (def f() -> type -> def f())
            clean_code = re.sub(r'\)\s*->\s*\w+\s*:', '):', code)
            # Step 2: Remove type annotations with no default (param: type, or param: type)
            clean_code = re.sub(r'(\w+)\s*:\s*\w+(?=\s*[,)=])', r'\1', clean_code)
            # Step 3: Remove type annotations with default (param: type = value)
            clean_code = re.sub(r'(\w+)\s*:\s*\w+\s*=\s*', r'\1 = ', clean_code)
            # Step 4: For async def inside exec, convert to sync for testing
            if clean_code.strip().startswith('async def'):
                clean_code = clean_code.replace('async def', 'def', 1)
                is_async = False  # Force sync testing
            
            # Create namespace with safe builtins
            namespace = self.create_test_environment()
            namespace["__builtins__"] = {}
            
            # Execute handler code
            exec(compile(clean_code, "<string>", "exec"), namespace)
            
            # Find and call handler - look for the exact function name
            handler = None
            for key in namespace:
                if key == handler_name or key == f"_{handler_name}":
                    handler = namespace[key]
                    break
            
            if handler and callable(handler):
                # For non-async handlers, wrap in async
                if not is_async:
                    result["output"] = handler(**params)
                else:
                    result["output"] = await handler(**params)
                
                result["success"] = True
            else:
                result["error"] = f"Handler '{handler_name}' not found in code"
        
        except Exception as e:
            result["error"] = str(e)
        
        result["duration_ms"] = (datetime.now() - start).total_seconds() * 1000
        self.test_results.append(result)
        
        return result
    
    async def run_suite(
        self, 
        handlers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Run test suite for all handlers."""
        results = []
        
        for handler in handlers:
            # Generate test cases based on parameters
            test_cases = self._generate_test_cases(handler)
            
            for params in test_cases:
                result = await self.test_handler(
                    code=handler["code"],
                    handler_name=handler["name"],
                    params=params,
                    is_async=handler.get("is_async", False)
                )
                results.append(result)
        
        return results
    
    def _generate_test_cases(self, handler: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate test cases based on handler parameters."""
        test_cases = []
        
        # Try to get parameters from handler metadata
        params = handler.get("parameters", [])
        
        # If no parameters in metadata, extract from code
        if not params:
            import re
            code = handler.get("code", "")
            
            # Extract parameter names from function definition
            param_pattern = r'def\s+\w+\s*\(([^)]*)\)'
            match = re.search(param_pattern, code)
            
            if match:
                param_str = match.group(1)
                param_names = []
                
                # Split by comma and process each parameter
                for p in param_str.split(','):
                    p = p.strip()
                    # Remove type annotations first: "location: str" -> "location"
                    p_clean = re.sub(r'(\w+)\s*:\s*.*', r'\1', p)
                    # Then extract name from default value: "units = 'celsius'" -> "units"
                    if '=' in p_clean:
                        p_clean = p_clean.split('=')[0].strip()
                    
                    if p_clean and p_clean not in ('self', 'cls'):
                        param_names.append(p_clean)
                
                # Create test case with all parameters
                if param_names:
                    test_case = {}
                    for pname in param_names:
                        # Provide smart defaults based on name and default value
                        # Check if original had a numeric default
                        original = [p.strip() for p in param_str.split(',')]
                        has_numeric_default = any(
                            '=' in p and any(c.isdigit() for c in p.split('=')[1])
                            for p in original if p.split(':')[0].strip() == pname
                        )
                        
                        if 'location' in pname.lower():
                            test_case[pname] = "San Francisco"
                        elif 'url' in pname.lower():
                            test_case[pname] = "https://example.com"
                        elif 'name' in pname.lower():
                            test_case[pname] = "test"
                        elif 'count' in pname.lower() or 'num' in pname.lower() or 'days' in pname.lower():
                            test_case[pname] = 5
                        elif has_numeric_default:
                            test_case[pname] = 5
                        else:
                            test_case[pname] = "test_value"
                    
                    test_cases.append(test_case)
                    return test_cases
        
        # Generate basic test cases
        for param in params:
            pname = param.get("name", "value")
            ptype = param.get("type", "str")
            
            if ptype == "str":
                test_cases.append({pname: "test data"})
                test_cases.append({pname: ""})
            elif ptype == "int":
                test_cases.append({pname: 42})
            elif ptype == "float":
                test_cases.append({pname: 3.14})
            elif ptype == "bool":
                test_cases.append({pname: True})
                test_cases.append({pname: False})
        
        if not test_cases:
            test_cases.append({})
        
        return test_cases
    
    def generate_report(self) -> str:
        """Generate a test report."""
        if not self.test_results:
            return "No tests run yet."
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed
        
        lines = [
            "=" * 60,
            " TEST REPORT",
            "=" * 60,
            f"  Total: {total}",
            f"  Passed: {passed}",
            f"  Failed: {failed}",
            f"  Success Rate: {passed/total*100:.1f}%",
            "",
            " DETAILED RESULTS:",
            "-" * 60,
        ]
        
        for result in self.test_results:
            status = "✓" if result["success"] else "✗"
            lines.append(f"  {status} {result['handler']}({result['params']})")
            lines.append(f"     Duration: {result['duration_ms']:.2f}ms")
            if result["success"]:
                lines.append(f"     Output: {str(result['output'])[:50]}...")
            else:
                lines.append(f"     Error: {result['error']}")
            lines.append("")
        
        return "\n".join(lines)


class SkillPublisher:
    """Publish skills to registry."""
    
    def __init__(self):
        self.registry_url = "https://registry.smithai.dev"
        self.api_key = os.getenv("SMITHAI_API_KEY", "")
    
    async def validate_skill(self, project: SkillProject) -> List[str]:
        """Validate a skill before publishing."""
        errors = []
        
        # Check required fields
        if not project.name:
            errors.append("Name is required")
        if not project.version:
            errors.append("Version is required")
        if not project.description:
            errors.append("Description is required")
        if not project.author:
            errors.append("Author is required")
        
        # Check version format
        import re
        if not re.match(r"^\d+\.\d+\.\d+$", project.version):
            errors.append("Version must be in format X.Y.Z")
        
        # Check handlers
        if not project.handlers:
            errors.append("At least one handler is required")
        
        for handler in project.handlers:
            if not handler.get("name"):
                errors.append("Handler name is required")
            if not handler.get("code"):
                errors.append("Handler code is required")
        
        return errors
    
    async def publish(self, project: SkillProject) -> Dict[str, Any]:
        """Publish a skill to the registry."""
        # Validate
        errors = await self.validate_skill(project)
        if errors:
            return {
                "success": False,
                "errors": errors,
            }
        
        # Create package
        package = {
            "name": project.name,
            "version": project.version,
            "description": project.description,
            "author": project.author,
            "category": project.category,
            "tags": project.tags,
            "license": project.license,
            "repository": project.repository,
            "handlers": [
                {
                    "name": h["name"],
                    "description": h["description"],
                    "is_async": h.get("is_async", False),
                }
                for h in project.handlers
            ],
            "published_at": datetime.now().isoformat(),
            "downloads": 0,
            "rating": 0.0,
        }
        
        # In production, this would upload to a server
        # For now, save locally
        save_path = Path.home() / ".smithai" / "published" / f"{project.name}.json"
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, "w") as f:
            json.dump(package, f, indent=2)
        
        return {
            "success": True,
            "package": package,
            "registry_url": f"{self.registry_url}/{project.name}",
            "local_path": str(save_path),
        }
    
    async def unpublish(self, name: str) -> bool:
        """Unpublish a skill."""
        save_path = Path.home() / ".smithai" / "published" / f"{name}.json"
        if save_path.exists():
            save_path.unlink()
            return True
        return False
    
    def list_published(self) -> List[str]:
        """List all published skills."""
        published_dir = Path.home() / ".smithai" / "published"
        if not published_dir.exists():
            return []
        
        return [p.stem for p in published_dir.glob("*.json")]


class SkillWorkspace:
    """Main workspace controller."""
    
    def __init__(self):
        self.creator = SkillCreator()
        self.tester = SkillTester()
        self.publisher = SkillPublisher()
    
    def run_interactive(self):
        """Run interactive workspace."""
        print_banner()
        
        while True:
            print("\n" + "="*60)
            print(" SKILL WORKSPACE")
            print("="*60)
            print("""
  1. Create New Skill
  2. Open Existing Skill
  3. Add Handler
  4. Remove Handler
  5. List Handlers
  6. Generate Code
  7. Test Skill
  8. Publish Skill
  9. View Published
  10. Export Skill
  11. Import Skill
  12. Run Skill Handler
  0. Exit
""")
            
            choice = input("  Select option: ").strip()
            
            if choice == "1":
                self.creator.create_new_skill()
            elif choice == "2":
                path = input("  Enter path to skill file: ").strip()
                if self.creator.import_from_file(path):
                    print(f"  ✅ Imported: {self.creator.project.name}")
            elif choice == "3":
                self.creator.add_handler_interactive()
            elif choice == "4":
                handlers = self.creator.list_handlers()
                if handlers:
                    print("  Handlers:", ", ".join(handlers))
                    name = input("  Enter handler name to remove: ").strip()
                    if self.creator.remove_handler(name):
                        print(f"  ✅ Removed: {name}")
            elif choice == "5":
                handlers = self.creator.list_handlers()
                if handlers:
                    print("  Handlers:")
                    for h in handlers:
                        print(f"    - {h}")
                else:
                    print("  No handlers defined")
            elif choice == "6":
                code = self.creator.generate_skill_code()
                if code:
                    print("\n  Generated Code:")
                    print("-"*40)
                    print(code[:1000] + "..." if len(code) > 1000 else code)
            elif choice == "7":
                if self.creator.project and self.creator.project.handlers:
                    print("\n  Running tests...")
                    results = asyncio.run(
                        self.tester.run_suite(self.creator.project.handlers)
                    )
                    print(self.tester.generate_report())
            elif choice == "8":
                if self.creator.project:
                    result = asyncio.run(
                        self.publisher.publish(self.creator.project)
                    )
                    if result["success"]:
                        print(f"  ✅ Published: {result['registry_url']}")
                        print(f"     Local: {result['local_path']}")
                    else:
                        print("  ❌ Validation errors:")
                        for e in result["errors"]:
                            print(f"     - {e}")
            elif choice == "9":
                published = self.publisher.list_published()
                if published:
                    print("  Published skills:")
                    for p in published:
                        print(f"    - {p}")
                else:
                    print("  No published skills")
            elif choice == "10":
                if self.creator.project:
                    path = input("  Export path: ").strip()
                    if self.creator.export_to_file(path):
                        print(f"  ✅ Exported to: {path}")
            elif choice == "11":
                path = input("  Import path: ").strip()
                if self.creator.import_from_file(path):
                    print(f"  ✅ Imported: {self.creator.project.name}")
            elif choice == "12":
                if self.creator.project and self.creator.project.handlers:
                    print("  Handlers:", ", ".join(self.creator.list_handlers()))
                    name = input("  Handler name: ").strip()
                    params_input = input("  Parameters (JSON): ").strip()
                    try:
                        params = json.loads(params_input) if params_input else {}
                    except:
                        params = {}
                    
                    for h in self.creator.project.handlers:
                        if h["name"] == name:
                            result = asyncio.run(
                                self.tester.test_handler(
                                    h["code"], name, params, h.get("is_async", False)
                                )
                            )
                            print(f"\n  Result: {result['output']}")
                            if result["error"]:
                                print(f"  Error: {result['error']}")
                            break
            elif choice == "0":
                print("\n  Goodbye!")
                break


def quick_create_skill(
    name: str,
    description: str,
    author: str,
    category: str = "tool",
    handlers: List[Dict[str, Any]] = None
) -> SkillProject:
    """Quickly create a skill without interaction."""
    project = SkillProject(
        name=name,
        version="1.0.0",
        description=description,
        author=author,
        category=category,
    )
    
    if handlers:
        project.handlers = handlers
    
    return project


async def demo_workspace():
    """Demonstrate the skill workspace."""
    print_banner()
    
    workspace = SkillWorkspace()
    
    print("\n" + "="*60)
    print(" DEMO: Creating a Weather Skill")
    print("="*60)
    
    # Create skill
    workspace.creator.project = SkillProject(
        name="weather_api",
        version="1.0.0",
        description="Get weather information for any location",
        author="Demo Author",
        category="tool",
        tags=["weather", "api", "utility"],
    )
    
    print(f"\n  Created: {workspace.creator.project.name}")
    
    # Add handler
    workspace.creator.project.handlers = [
        {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "code": '''
def get_weather(location: str, units: str = "celsius") -> dict:
    """Get weather for a location."""
    return {
        "location": location,
        "temperature": 22 if units == "celsius" else 72,
        "condition": "sunny",
        "humidity": 45,
    }
''',
            "is_async": False,
        },
        {
            "name": "get_forecast",
            "description": "Get weather forecast",
            "code": '''
async def get_forecast(location: str, days: int = 7) -> list:
    results = []
    for i in range(1, days + 1):
        results.append({"day": i, "temp": 20 + i, "condition": "cloudy"})
    return results
''',
            "is_async": True,
        },
    ]
    
    print(f"  Added {len(workspace.creator.project.handlers)} handlers")
    
    # Test handlers
    print("\n  Testing handlers...")
    test_results = await workspace.tester.run_suite(workspace.creator.project.handlers)
    
    passed = sum(1 for r in test_results if r["success"])
    print(f"  Tests: {passed}/{len(test_results)} passed")
    
    for result in test_results:
        if result["success"]:
            print(f"    ✓ {result['handler']}: {str(result['output'])[:50]}")
        else:
            print(f"    ✗ {result['handler']}: {result['error']}")
    
    # Publish
    print("\n  Publishing...")
    pub_result = await workspace.publisher.publish(workspace.creator.project)
    if pub_result["success"]:
        print(f"  ✅ Published!")
        print(f"     Package: {pub_result['local_path']}")
    else:
        print("  ❌ Errors:", pub_result["errors"])
    
    # Generate code
    print("\n  Generated Code Preview:")
    print("-"*40)
    code = workspace.creator.generate_skill_code()
    print(code[:500] + "...")
    
    return workspace.creator.project


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SmithAI Skill Workspace")
    parser.add_argument("--demo", action="store_true", help="Run demo")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    args = parser.parse_args()
    
    if args.demo:
        asyncio.run(demo_workspace())
    elif args.interactive:
        workspace = SkillWorkspace()
        workspace.run_interactive()
    else:
        print("Usage:")
        print("  python skill_workspace.py --demo        # Run demo")
        print("  python skill_workspace.py --interactive # Interactive mode")
