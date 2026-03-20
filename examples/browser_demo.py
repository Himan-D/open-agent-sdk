#!/usr/bin/env python3
"""
🚀 SmithAI - Complete Browser Automation Example

Demonstrates full browser automation with DOM manipulation, forms, scraping, and more.

Features:
- Navigate, click, fill forms
- Screenshot, PDF generation
- JavaScript execution
- Web scraping
- Multi-step workflows
"""

import asyncio
from open_agent.automation.browser import BrowserTool, WebScraperTool, FormFillerTool

async def demo_navigation():
    """Demo: Basic navigation and content extraction."""
    print("\n" + "="*60)
    print("🌐 Demo 1: Navigation & Content Extraction")
    print("="*60)
    
    browser = BrowserTool()
    
    print("\n[1] Navigating to example.com...")
    result = await browser.execute("navigate:https://example.com")
    print(f"    {result.output}")
    
    print("\n[2] Getting page title...")
    result = await browser.execute("title")
    print(f"    Title: {result}")
    
    print("\n[3] Getting H1 text...")
    result = await browser.execute("text:h1")
    print(f"    H1: {result}")
    
    print("\n[4] Taking screenshot...")
    result = await browser.execute("screenshot:example.png")
    print(f"    {result}")
    
    await browser.close()
    print("\n✅ Navigation demo complete!")


async def demo_form_filling():
    """Demo: Form filling and submission."""
    print("\n" + "="*60)
    print("📝 Demo 2: Form Filling")
    print("="*60)
    
    browser = BrowserTool()
    
    # Example with httpbin (test form)
    print("\n[1] Navigating to test form...")
    await browser.execute("navigate:https://httpbin.org/forms/post")
    
    print("\n[2] Filling form fields...")
    await browser.execute("fill:input[name=\"custname\"]|John Doe")
    await browser.execute("fill:input[name=\"custtel\"]|1234567890")
    await browser.execute("fill:input[name=\"custemail\"]|john@example.com")
    
    print("\n[3] Taking screenshot of filled form...")
    result = await browser.execute("screenshot:form.png")
    print(f"    {result}")
    
    print("\n[4] Evaluating with JavaScript...")
    result = await browser.execute('evaluate:document.querySelector("form").innerHTML.substring(0, 200)')
    print(f"    Form HTML: {result.output[:100]}...")
    
    await browser.close()
    print("\n✅ Form demo complete!")


async def demo_web_scraping():
    """Demo: Web scraping with selectors."""
    print("\n" + "="*60)
    print("🕷️ Demo 3: Web Scraping")
    print("="*60)
    
    scraper = WebScraperTool()
    
    print("\n[1] Scraping example.com...")
    result = await scraper.execute("https://example.com|h1,p,a")
    print(f"    Results: {result.output[:300]}...")
    
    print("\n[2] Scraping Wikipedia...")
    result = await scraper.execute("https://en.wikipedia.org/wiki/Python_(programming_language)|h1,h2,.mw-parser-output p")
    print(f"    Results: {result.output[:200]}...")
    
    print("\n✅ Scraping demo complete!")


async def demo_javascript():
    """Demo: JavaScript execution."""
    print("\n" + "="*60)
    print("⚡ Demo 4: JavaScript Execution")
    print("="*60)
    
    browser = BrowserTool()
    
    print("\n[1] Navigating...")
    await browser.execute("navigate:https://example.com")
    
    print("\n[2] Getting page info via JS...")
    js = '''
    ({
        title: document.title,
        url: window.location.href,
        h1: document.querySelector("h1")?.textContent,
        links: document.querySelectorAll("a").length
    })
    '''
    result = await browser.execute(f"evaluate:{js}")
    print(f"    Page info: {result.output}")
    
    print("\n[3] Modifying page content...")
    await browser.execute('evaluate:document.body.innerHTML = "<h1>Modified by SmithAI!</h1>"')
    result = await browser.execute("text:h1")
    print(f"    New H1: {result}")
    
    await browser.close()
    print("\n✅ JavaScript demo complete!")


async def demo_multi_step():
    """Demo: Multi-step workflow."""
    print("\n" + "="*60)
    print("🔄 Demo 5: Multi-Step Workflow")
    print("="*60)
    
    browser = BrowserTool()
    
    steps = [
        ("Navigate", "navigate:https://httpbin.org/html"),
        ("Wait", "wait:2"),
        ("Get content", "content"),
        ("Take screenshot", "screenshot:httpbin.png"),
    ]
    
    for name, cmd in steps:
        print(f"\n[{name}] Executing: {cmd[:40]}...")
        result = await browser.execute(cmd)
        if "content" not in cmd:
            print(f"    Result: {str(result)[:80]}")
        else:
            print(f"    Content length: {len(result.output)} chars")
    
    await browser.close()
    print("\n✅ Multi-step demo complete!")


async def demo_element_interaction():
    """Demo: Element interaction."""
    print("\n" + "="*60)
    print("🖱️ Demo 6: Element Interaction")
    print("="*60)
    
    browser = BrowserTool()
    
    print("\n[1] Navigate to test page...")
    await browser.execute("navigate:https://httpbin.org/forms/post")
    
    print("\n[2] Check element exists...")
    result = await browser.execute("exists:input[name=\"custname\"]")
    print(f"    Input exists: {result}")
    
    print("\n[3] Fill and check value...")
    await browser.execute("fill:input[name=\"custname\"]|Test User")
    await browser.execute("evaluate:document.querySelector('input[name=\"custname\"]').value")
    result = await browser.execute("attribute:input[name=\"custname\"]|value")
    print(f"    Value: {result}")
    
    print("\n[4] Count form elements...")
    result = await browser.execute("count:input")
    print(f"    Input count: {result}")
    
    await browser.close()
    print("\n✅ Interaction demo complete!")


async def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🚀 SmithAI - Browser Automation Demo                       ║
║                                                              ║
║   Features:                                                  ║
║   🌐 Navigation & content extraction                        ║
║   📝 Form filling & submission                             ║
║   🕷️ Web scraping with selectors                           ║
║   ⚡ JavaScript execution                                   ║
║   🔄 Multi-step workflows                                  ║
║   🖱️ Element interaction (click, hover, etc.)              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    await demo_navigation()
    await demo_form_filling()
    await demo_web_scraping()
    await demo_javascript()
    await demo_multi_step()
    await demo_element_interaction()
    
    print("\n" + "="*60)
    print("🎉 ALL BROWSER AUTOMATION DEMOS COMPLETE!")
    print("="*60)
    print("""
Next steps:
1. Try running: python examples/browser_demo.py
2. Create agents that use browser tools
3. Build multi-agent workflows with browser automation
""")


if __name__ == "__main__":
    asyncio.run(main())
