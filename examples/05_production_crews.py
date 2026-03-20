#!/usr/bin/env python3
"""
🚀 SmithAI Production Crews - Real-World Multi-Agent Workflows

This example demonstrates production-ready agent crews that solve real problems:
1. Code Review Crew - PR review with automated feedback
2. DevOps Crew - CI/CD pipeline automation
3. Content Crew - Research → Write → Edit pipeline

Run with: python examples/05_production_crews.py
"""

import asyncio
import sys
from open_agent import create_crew


# =============================================================================
# CREW 1: Code Review Automation
# =============================================================================

async def run_code_review_crew(code_snippet: str, language: str = "python"):
    """Automated code review with expert feedback."""
    
    print("\n" + "="*60)
    print("🚀 CREW 1: Code Review Automation")
    print("="*60)
    
    crew = create_crew(
        agents_config=[
            {
                "name": "analyzer",
                "role": "Code Analyzer",
                "goal": "Analyze code for bugs, performance issues, and best practices",
                "backstory": """You are a senior code reviewer with 20 years of experience.
                You excel at finding bugs, performance bottlenecks, security vulnerabilities,
                and code quality issues. You know SOLID principles, design patterns,
                and industry best practices for multiple languages."""
            },
            {
                "name": "reviewer",
                "role": "Code Reviewer",
                "goal": "Provide constructive, actionable feedback on code",
                "backstory": """You are a tech lead who provides clear, actionable feedback.
                You balance thoroughness with practicality, focusing on issues that
                matter most for maintainability and performance."""
            },
            {
                "name": "fixer",
                "role": "Code Fixer",
                "goal": "Write improved versions of code with fixes applied",
                "backstory": """You are a senior developer who writes clean, efficient code.
                You apply fixes while maintaining the original intent and functionality."""
            },
        ],
        tasks_config=[
            {
                "description": f"Analyze this {language} code and identify all issues: bugs, performance problems, security vulnerabilities, SOLID violations, and best practice violations. Format your response as a numbered list.\n\nCode:\n```{language}\n{code_snippet}\n```",
                "agent": "analyzer",
                "expected_output": "Detailed list of all code issues with severity levels"
            },
            {
                "description": "Review the issues found and prioritize them. Focus on the top 5 most critical issues that MUST be fixed. Provide specific, actionable recommendations for each.",
                "agent": "reviewer",
                "expected_output": "Prioritized list of top 5 critical issues with recommendations"
            },
            {
                "description": "Based on the feedback, write an improved version of the code that fixes the critical issues. Maintain the original functionality while improving quality.",
                "agent": "fixer",
                "expected_output": "Improved code with fixes explained in comments"
            },
        ],
        process="sequential",
        verbose=True,
    )
    
    results = await crew.kickoff()
    return results


# =============================================================================
# CREW 2: DevOps Automation
# =============================================================================

async def run_devops_crew(task: str):
    """CI/CD and DevOps task automation."""
    
    print("\n" + "="*60)
    print("🚀 CREW 2: DevOps Automation")
    print("="*60)
    
    crew = create_crew(
        agents_config=[
            {
                "name": "architect",
                "role": "Infrastructure Architect",
                "goal": "Design scalable, reliable infrastructure solutions",
                "backstory": """You are a DevOps architect with expertise in Kubernetes, Docker,
                AWS/GCP/Azure, Terraform, and CI/CD pipelines. You design systems that
                are scalable, reliable, and cost-effective."""
            },
            {
                "name": "implementer",
                "role": "DevOps Engineer",
                "goal": "Implement infrastructure as code and automation scripts",
                "backstory": """You are a DevOps engineer who writes production-ready
                Terraform, Docker, Kubernetes, and CI/CD configurations.
                Your code is always production-quality with proper error handling."""
            },
            {
                "name": "doc_writer",
                "role": "Technical Writer",
                "goal": "Document infrastructure and processes clearly",
                "backstory": """You write clear, comprehensive documentation that
                helps teams understand and maintain infrastructure."""
            },
        ],
        tasks_config=[
            {
                "description": f"Analyze this DevOps task and design an architecture solution: {task}\n\nProvide: 1) Architecture diagram (text-based), 2) Technology stack recommendations, 3) Estimated setup complexity",
                "agent": "architect",
                "expected_output": "Architecture design with recommendations"
            },
            {
                "description": "Based on the architecture, implement the infrastructure as code. Write Terraform/Docker/Kubernetes configurations or CI/CD scripts as needed.",
                "agent": "implementer",
                "expected_output": "Production-ready infrastructure code"
            },
            {
                "description": "Create a README with setup instructions, architecture overview, and usage guide for the implemented solution.",
                "agent": "doc_writer",
                "expected_output": "Complete documentation"
            },
        ],
        process="sequential",
        verbose=True,
    )
    
    results = await crew.kickoff()
    return results


# =============================================================================
# CREW 3: Content Pipeline
# =============================================================================

async def run_content_crew(topic: str):
    """Automated content creation pipeline."""
    
    print("\n" + "="*60)
    print("🚀 CREW 3: Content Creation Pipeline")
    print("="*60)
    
    crew = create_crew(
        agents_config=[
            {
                "name": "researcher",
                "role": "Content Researcher",
                "goal": "Research topics thoroughly and gather key information",
                "backstory": """You are a research expert who finds the most relevant,
                accurate, and up-to-date information on any topic. You know how to
                identify credible sources and synthesize key points."""
            },
            {
                "name": "writer",
                "role": "Content Writer",
                "goal": "Create engaging, well-structured content",
                "backstory": """You are an expert content writer who creates engaging,
                SEO-friendly content. You write clear headlines, compelling introductions,
                and actionable conclusions."""
            },
            {
                "name": "editor",
                "role": "Senior Editor",
                "goal": "Polish content to publication quality",
                "backstory": """You are a meticulous editor who ensures content is
                error-free, well-formatted, and ready for publication. You check
                grammar, style, and consistency."""
            },
        ],
        tasks_config=[
            {
                "description": f"Research this topic and gather key information: {topic}\n\nProvide: 1) Overview, 2) 5 key points, 3) Real-world examples, 4) Statistics or data if available",
                "agent": "researcher",
                "expected_output": "Comprehensive research summary"
            },
            {
                "description": "Write a well-structured article based on the research. Include: catchy headline, intro, 3-4 main sections with subheadings, and a conclusion with call-to-action.",
                "agent": "writer",
                "expected_output": "Complete article draft"
            },
            {
                "description": "Edit the article for: grammar, clarity, flow, SEO optimization, and consistency. Add meta description and tags.",
                "agent": "editor",
                "expected_output": "Publication-ready article"
            },
        ],
        process="sequential",
        verbose=True,
    )
    
    results = await crew.kickoff()
    return results


# =============================================================================
# MAIN MENU
# =============================================================================

async def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🚀 SmithAI Production Crews - Real-World Workflows         ║
║                                                              ║
║   Choose a crew to run:                                      ║
║                                                              ║
║   [1] Code Review - Analyze and fix code issues             ║
║   [2] DevOps - Infrastructure automation                     ║
║   [3] Content - Research → Write → Edit pipeline             ║
║   [4] Run all crews (demo mode)                              ║
║   [Q] Quit                                                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    choice = input("Enter choice: ").strip().lower()
    
    if choice == "1":
        code = '''def calculate_total(items):
    total = 0
    for i in items:
        total += i['price'] * i['quantity']
    return total

def process_order(order):
    total = calculate_total(order['items'])
    if total > 1000:
        total = total * 0.9  # 10% discount
    print("Order processed")
    return total'''
        
        results = await run_code_review_crew(code, "python")
        
        print("\n" + "="*60)
        print("📄 FINAL ARTICLE")
        print("="*60)
        for task, result in results.items():
            print(f"\n### {task[:50]}...\n{result}\n")
    
    elif choice == "2":
        results = await run_devops_crew("Set up a production Kubernetes cluster on AWS with auto-scaling, monitoring, and CI/CD")
        
        print("\n" + "="*60)
        print("📄 DEVOPS OUTPUT")
        print("="*60)
        for task, result in results.items():
            print(f"\n### {task[:50]}...\n{result}\n")
    
    elif choice == "3":
        results = await run_content_crew("The future of AI agents in software development")
        
        print("\n" + "="*60)
        print("📄 FINAL ARTICLE")
        print("="*60)
        print(results[list(results.keys())[-1]])
    
    elif choice == "4":
        print("\n🔄 Running demo mode...")
        
        # Quick demo of each crew
        results1 = await run_code_review_crew("x = input(); print(x)", "python")
        print("\n✅ Code review complete!\n")
        
        results2 = await run_content_crew("Why Python is great for AI")
        print("\n✅ Content pipeline complete!\n")
    
    elif choice == "q":
        print("Goodbye!")
        return
    
    else:
        print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())
