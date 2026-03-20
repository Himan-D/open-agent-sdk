#!/usr/bin/env python3
"""
Example 4: Direct LLM Usage - Test your API keys
This example tests all LLM providers directly
"""
import asyncio
import os
from open_agent import LLMFactory, LLMProvider


async def test_nvidia():
    """Test NVIDIA Nemotron."""
    print("\n🟢 Testing NVIDIA Nemotron...")
    
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        print("   ⚠️  NVIDIA_API_KEY not set")
        return None
    
    try:
        llm = LLMFactory.create(
            LLMProvider.NVIDIA,
            api_key=api_key,
            model="nvidia/nemotron-3-super-120b-a12b",
        )
        
        response = await llm.ainvoke([
            {"role": "user", "content": "Say 'NVIDIA works!' in exactly those words."}
        ])
        
        print(f"   ✅ Success: {response[:100]}...")
        return response
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:200]}")
        return None


async def test_openai():
    """Test OpenAI."""
    print("\n🔵 Testing OpenAI...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("   ⚠️  OPENAI_API_KEY not set")
        return None
    
    try:
        llm = LLMFactory.create(
            LLMProvider.OPENAI,
            api_key=api_key,
            model="gpt-4o-mini",
        )
        
        response = await llm.ainvoke([
            {"role": "user", "content": "Say 'OpenAI works!' in exactly those words."}
        ])
        
        print(f"   ✅ Success: {response[:100]}...")
        return response
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:200]}")
        return None


async def test_anthropic():
    """Test Anthropic Claude."""
    print("\n🟡 Testing Anthropic Claude...")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("   ⚠️  ANTHROPIC_API_KEY not set")
        return None
    
    try:
        llm = LLMFactory.create(
            LLMProvider.ANTHROPIC,
            api_key=api_key,
            model="claude-3-5-haiku-20241022",
        )
        
        response = await llm.ainvoke([
            {"role": "user", "content": "Say 'Anthropic works!' in exactly those words."}
        ])
        
        print(f"   ✅ Success: {response[:100]}...")
        return response
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:200]}")
        return None


async def test_google():
    """Test Google Gemini."""
    print("\n🟠 Testing Google Gemini...")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("   ⚠️  GOOGLE_API_KEY not set")
        return None
    
    try:
        llm = LLMFactory.create(
            LLMProvider.GOOGLE,
            api_key=api_key,
            model="gemini-2.0-flash-exp",
        )
        
        response = await llm.ainvoke([
            {"role": "user", "content": "Say 'Google works!' in exactly those words."}
        ])
        
        print(f"   ✅ Success: {response[:100]}...")
        return response
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:200]}")
        return None


async def test_ollama():
    """Test Ollama local."""
    print("\n🟣 Testing Ollama (local)...")
    
    try:
        llm = LLMFactory.create(
            LLMProvider.OLLAMA,
            model="llama3.2",
            base_url="http://localhost:11434",
        )
        
        response = await llm.ainvoke([
            {"role": "user", "content": "Say 'Ollama works!' in exactly those words."}
        ])
        
        print(f"   ✅ Success: {response[:100]}...")
        return response
    except Exception as e:
        print(f"   ⚠️  Ollama not available: {str(e)[:100]}")
        return None


async def main():
    print("=" * 60)
    print("LLM Provider Test Suite")
    print("=" * 60)
    
    print("\nChecking available API keys...")
    print(f"  NVIDIA_API_KEY: {'✅ set' if os.getenv('NVIDIA_API_KEY') else '❌ not set'}")
    print(f"  OPENAI_API_KEY: {'✅ set' if os.getenv('OPENAI_API_KEY') else '❌ not set'}")
    print(f"  ANTHROPIC_API_KEY: {'✅ set' if os.getenv('ANTHROPIC_API_KEY') else '❌ not set'}")
    print(f"  GOOGLE_API_KEY: {'✅ set' if os.getenv('GOOGLE_API_KEY') else '❌ not set'}")
    
    results = {}
    results["nvidia"] = await test_nvidia()
    results["openai"] = await test_openai()
    results["anthropic"] = await test_anthropic()
    results["google"] = await test_google()
    results["ollama"] = await test_ollama()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    working = [k for k, v in results.items() if v]
    print(f"\nWorking providers: {', '.join(working) if working else 'None'}")
    
    if "nvidia" in working:
        print("\n🎯 Recommended: Use NVIDIA for best performance/cost ratio")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
