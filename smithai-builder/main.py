#!/usr/bin/env python3
"""
SmithAI App Builder - A Lovable-like AI-powered app builder.
"""

import json
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from smith_ai.agi.v2 import TrueAGIAgent
    AGI_AVAILABLE = True
except ImportError:
    AGI_AVAILABLE = False


@dataclass
class Project:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    prompt: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "draft"
    frontend: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "prompt": self.prompt,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "files": {"frontend": list(self.frontend.keys())},
        }


class CodeGenerator:
    TODO = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{name}</title><script src="https://cdn.tailwindcss.com"></script><script src="https://unpkg.com/react@18/umd/react.development.js"></script><script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script><script src="https://unpkg.com/@babel/standalone/babel.min.js"></script></head><body class="bg-gray-100 min-h-screen"><div id="root"></div><script type="text/babel">function App(){{const [tasks,setTasks]=React.useState([]);const [newTask,setNewTask]=React.useState("");const addTask=()=>{{if(newTask.trim()){{setTasks([...tasks,{{id:Date.now(),text:newTask,done:false}}]);setNewTask("");}}}};const toggleTask=(id)=>{{setTasks(tasks.map(t=>t.id===id?{{...t,done:!t.done}}:t));}};const deleteTask=(id)=>{{setTasks(tasks.filter(t=>t.id!==id));}};return(<div className="max-w-2xl mx-auto p-6"><h1 className="text-4xl font-bold text-center mb-8">{name}</h1><div className="flex gap-2 mb-6"><input type="text" value={{newTask}} onChange={{(e)=>setNewTask(e.target.value)}} onKeyPress={{(e)=>e.key==="Enter"&&addTask()}} placeholder="Add a task..." className="flex-1 px-4 py-2 rounded-lg border"/><button onClick={{addTask}} className="px-6 py-2 bg-blue-600 text-white rounded-lg">Add</button></div><ul className="space-y-3">{{tasks.map(task=>(<li key={{task.id}} className="flex items-center gap-3 p-4 bg-white rounded-lg shadow"><input type="checkbox" checked={{task.done}} onChange={{()=>toggleTask(task.id)}}/><span className={{task.done?"line-through text-gray-500":"text-gray-800"}}>{{task.text}}</span><button onClick={{()=>deleteTask(task.id)}} className="text-red-500 ml-auto">Delete</button></li>))}}</ul><p className="text-center text-gray-500 mt-6">{{tasks.length}} tasks</p></div>);}}ReactDOM.render(<App/>,document.getElementById("root"));</script></body></html>'''
    
    LANDING = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{name}</title><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-white"><nav class="fixed w-full bg-white/90 backdrop-blur-sm z-50 border-b"><div class="max-w-6xl mx-auto px-6 py-4 flex justify-between"><div class="text-2xl font-bold text-indigo-600">{name}</div><div class="flex gap-6"><a href="#features" class="text-gray-600 hover:text-gray-900">Features</a><a href="#" class="text-gray-600 hover:text-gray-900">Pricing</a><a href="#" class="text-gray-600 hover:text-gray-900">Contact</a></div></div></nav><section class="pt-32 pb-20 px-6 text-center"><h1 class="text-5xl font-bold text-gray-900 mb-6">Build Amazing Products</h1><p class="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">The modern platform for creating and launching your next big idea.</p><div class="flex gap-4 justify-center"><button class="px-8 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">Get Started Free</button><button class="px-8 py-3 border border-gray-300 rounded-lg hover:bg-gray-50">Watch Demo</button></div></section><section id="features" class="py-20 px-6 bg-gray-50"><div class="max-w-6xl mx-auto"><h2 class="text-3xl font-bold text-center mb-12">Features</h2><div class="grid md:grid-cols-3 gap-8"><div class="bg-white p-6 rounded-xl shadow-sm"><h3 class="text-xl font-semibold mb-2">Fast</h3><p class="text-gray-600">Lightning fast performance.</p></div><div class="bg-white p-6 rounded-xl shadow-sm"><h3 class="text-xl font-semibold mb-2">Secure</h3><p class="text-gray-600">Enterprise-grade security.</p></div><div class="bg-white p-6 rounded-xl shadow-sm"><h3 class="text-xl font-semibold mb-2">Easy</h3><p class="text-gray-600">Intuitive interface.</p></div></div></div></section><footer class="py-8 px-6 text-center text-gray-500"><p>&copy; 2024 {name}</p></footer></body></html>'''
    
    BLOG = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{name}</title><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-gray-50"><header class="bg-white shadow-sm sticky top-0 z-50"><div class="max-w-4xl mx-auto px-6 py-4 flex justify-between"><h1 class="text-2xl font-bold">{name}</h1><nav class="flex gap-4"><a href="#" class="text-gray-600">Home</a><a href="#" class="text-gray-600">About</a><a href="#" class="text-gray-600">Contact</a></nav></div></header><main class="max-w-4xl mx-auto px-6 py-12"><article class="bg-white rounded-xl shadow-sm overflow-hidden mb-8"><img src="https://picsum.photos/800/400" class="w-full h-48 object-cover"/><div class="p-6"><div class="text-sm text-gray-500 mb-2">December 15, 2024</div><h2 class="text-2xl font-bold mb-4">Getting Started with AI</h2><p class="text-gray-600">Discover how AI is transforming development...</p></div></article><div class="grid md:grid-cols-2 gap-6"><article class="bg-white rounded-xl shadow-sm p-6"><h3 class="text-xl font-bold mb-2">The Future of Web</h3><p class="text-gray-600">Exploring new trends...</p></article><article class="bg-white rounded-xl shadow-sm p-6"><h3 class="text-xl font-bold mb-2">Building with AI</h3><p class="text-gray-600">Leverage AI for faster development...</p></article></div></main><footer class="bg-gray-800 text-white py-8 px-6 mt-12 text-center"><p>&copy; 2024 {name}</p></footer></body></html>'''
    
    def generate(self, prompt: str) -> Project:
        name = " ".join(prompt.split()[:3]).title() or "MyApp"
        p = Project(name=name, description=prompt, prompt=prompt, status="ready")
        pl = prompt.lower()
        if any(w in pl for w in ["todo", "task"]):
            p.frontend["index.html"] = self.TODO.format(name=name)
        elif any(w in pl for w in ["landing", "marketing"]):
            p.frontend["index.html"] = self.LANDING.format(name=name)
        else:
            p.frontend["index.html"] = self.BLOG.format(name=name)
        return p


class AppBuilder:
    def __init__(self):
        self.generator = CodeGenerator()
        self.projects: Dict[str, Project] = {}
        if AGI_AVAILABLE:
            self.agi = TrueAGIAgent(name="SmithAI-Builder", verbose=True)
    
    def create(self, prompt: str) -> Project:
        p = self.generator.generate(prompt)
        self.projects[p.id] = p
        return p
    
    def list(self) -> List[Project]:
        return list(self.projects.values())


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    
    builder = AppBuilder()
    
    try:
        from flask import Flask, jsonify, request
        from flask_cors import CORS
    except ImportError:
        print("Flask not installed. Install: pip install flask flask-cors")
        return
    
    app = Flask(__name__)
    CORS(app)
    
    HTML = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>SmithAI Builder</title><script src="https://cdn.tailwindcss.com"></script><script src="https://unpkg.com/react@18/umd/react.development.js"></script><script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script><script src="https://unpkg.com/@babel/standalone/babel.min.js"></script><style>.g{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%)}}</style></head><body class="bg-gray-900 min-h-screen"><div id="root"></div><script type="text/babel">function App(){{const[v,sV]=React.useState("create");const[p,sP]=React.useState("");const[ps,sPs]=React.useState([]);const[cp,sCp]=React.useState(null);const[load,sL]=React.useState(false);const mk=async()=>{{if(!p.trim())return;sL(true);try{{const r=await fetch("/api/create",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{prompt:p}})}});const d=await r.json();sPs([d.project,...ps]);sCp(d.project);sV("preview");}}catch(e){{console.error(e);}}sL(false);}};React.useEffect(()=>{{fetch("/api/projects").then(r=>r.json()).then(d=>sPs(d.projects)).catch(console.error);}},[]);return(<div class="min-h-screen"><header class="g text-white py-6 px-8"><div class="max-w-7xl mx-auto flex justify-between items-center"><div><h1 class="text-3xl font-bold">SmithAI Builder</h1><p class="text-white/80">Build apps with AI</p></div><div class="flex gap-4"><button onClick={()=>sV("create")} class={{`px-4 py-2 rounded-lg ${v==="create"?"bg-white text-purple-700":"bg-white/20"}`}}>Create</button><button onClick={()=>{fetch("/api/projects").then(r=>r.json()).then(d=>sPs(d.projects)).catch(console.error);sV("projects");}} class={{`px-4 py-2 rounded-lg ${v==="projects"?"bg-white text-purple-700":"bg-white/20"}`}}>Projects</button></div></div></header><main class="max-w-7xl mx-auto p-8">{v==="create"&&(<div class="max-w-3xl mx-auto"><div class="bg-gray-800 rounded-2xl p-8 shadow-xl"><h2 class="text-2xl font-bold text-white mb-6">What do you want to build?</h2><textarea value={{p}} onChange={{(e)=>sP(e.target.value)}} placeholder="Describe your app..." class="w-full h-40 bg-gray-700 text-white rounded-xl p-4 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"/><button onClick={{mk}} disabled={{load||!p.trim()}} class="w-full py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl font-semibold mt-6 hover:opacity-90 disabled:opacity-50">{load?"Building...":"Build App"}</button><div class="mt-8"><p class="text-gray-400 text-sm mb-3">Quick Start</p><div class="flex flex-wrap gap-2">{{["Todo app","Landing page","Blog"].map(t=>(<button key={{t}} onClick={()=>sP(t)} class="px-3 py-1.5 bg-gray-700 text-gray-300 rounded-lg text-sm hover:bg-gray-600">{{t}}</button>))}}</div></div></div>)}工人{v==="projects"&&(<div><h2 class="text-2xl font-bold text-white mb-6">Your Projects</h2><div class="grid md:grid-cols-3 gap-6">{{ps.map(pr=>(<div key={{pr.id}} onClick={()=>{{sCp(pr);sV("preview");}} class="bg-gray-800 rounded-xl p-6 hover:bg-gray-750 cursor-pointer"><h3 class="text-xl font-semibold text-white mb-2">{{pr.name}}</h3><p class="text-gray-400 text-sm line-clamp-2">{{pr.description}}</p><span class="inline-block mt-4 px-2 py-1 bg-green-600 rounded text-xs text-white">{{pr.status}}</span></div>))}}{{ps.length===0&&(<div class="col-span-3 text-center py-12 text-gray-500">No projects yet</div>)}}</div></div>)}工人{v==="preview"&&cp&&(<div class="grid lg:grid-cols-2 gap-8"><div class="bg-gray-800 rounded-xl overflow-hidden"><pre class="p-4 text-green-400 text-sm overflow-auto max-h-[600px]">{{JSON.stringify(cp.files?.frontend||{},null,2)}}</pre></div><div class="bg-white rounded-xl overflow-hidden shadow-xl"><div class="bg-gray-100 px-4 py-3 border-b flex gap-2"><div class="w-3 h-3 rounded-full bg-red-400"></div><div class="w-3 h-3 rounded-full bg-yellow-400"></div><div class="w-3 h-3 rounded-full bg-green-400"></div></div><iframe srcDoc={{cp.frontend?.["index.html"]}} class="w-full h-[600px] border-0"/></div></div>)}</div></main></body></html>'''
    
    @app.route("/")
    def index():
        return HTML
    
    @app.route("/api/create", methods=["POST"])
    def create():
        data = request.json
        p = builder.create(data.get("prompt", ""))
        return jsonify({"project": p.to_dict()})
    
    @app.route("/api/projects")
    def projects():
        return jsonify({"projects": [p.to_dict() for p in builder.list()]})
    
    print(f"\n🚀 SmithAI App Builder\nOpen http://localhost:{args.port}\n")
    app.run(host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
