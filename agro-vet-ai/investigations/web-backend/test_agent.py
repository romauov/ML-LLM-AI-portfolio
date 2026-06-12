"""
Test script for the veterinary investigation agent.

This script tests the agent in different configurations:
1. Simple agent without tools (basic LLM test)
2. Agent with MCP tools (knowledge base access)
3. Full agent with all tools (complete investigation)
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.vet_agent import get_simple_vet_agent, get_vet_agent_executor
from app.services.mcp_client import VetRetroMCPClient
from app.services.investigation_manager import InvestigationManager
from app.config import get_settings

settings = get_settings()


async def test_simple_agent():
    """
    Test 1: Simple agent without tools.

    This tests basic LLM connectivity and prompt template.
    """
    print("\n" + "="*80)
    print("TEST 1: Simple Agent (No Tools)")
    print("="*80)

    try:
        agent = get_simple_vet_agent(verbose=True)

        question = "What are the most common causes of neonatal diarrhea in piglets aged 3-7 days?"

        print(f"\nQuestion: {question}")
        print("\nAgent response:")
        print("-" * 80)

        result = await agent.ainvoke({"input": question})

        print(result["output"])
        print("-" * 80)
        print("\n✅ Test 1 passed: Simple agent works correctly")
        return True

    except Exception as e:
        print(f"\n❌ Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_with_mcp():
    """
    Test 2: Agent with MCP tools for knowledge base access.

    This tests tool calling with vet_search.
    """
    print("\n" + "="*80)
    print("TEST 2: Agent with MCP Tools (Knowledge Base)")
    print("="*80)

    mcp_client = None
    try:
        # Connect to MCP server
        mcp_url = "http://localhost:8765"
        print(f"\nConnecting to MCP server at {mcp_url}...")

        mcp_client = VetRetroMCPClient(mcp_url)
        await mcp_client.connect()

        print("✓ Connected to MCP server")

        # Create agent with MCP tools only
        agent = get_vet_agent_executor(
            mcp_client=mcp_client,
            investigation_manager=None,  # No file operations for this test
            verbose=True,
            max_iterations=10,
        )

        question = "Search the knowledge base for information about E.coli K88 treatment in neonatal piglets. What antibiotics are recommended?"

        print(f"\nQuestion: {question}")
        print("\nAgent response:")
        print("-" * 80)

        result = await agent.ainvoke({"input": question})

        print("\n" + result["output"])
        print("-" * 80)

        # Check intermediate steps for tool calls
        if "intermediate_steps" in result and result["intermediate_steps"]:
            print("\n📋 Tool calls made:")
            for i, (action, observation) in enumerate(result["intermediate_steps"], 1):
                print(f"  {i}. {action.tool}: {action.tool_input}")

        print("\n✅ Test 2 passed: Agent with MCP tools works correctly")
        return True

    except Exception as e:
        print(f"\n❌ Test 2 failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if mcp_client:
            await mcp_client.close()


async def test_full_agent():
    """
    Test 3: Full agent with all tools (MCP + investigation tools).

    This tests complete investigation workflow.
    """
    print("\n" + "="*80)
    print("TEST 3: Full Agent (All Tools)")
    print("="*80)

    mcp_client = None
    try:
        # Connect to MCP server
        mcp_url = "http://localhost:8765"
        print(f"\nConnecting to MCP server at {mcp_url}...")

        mcp_client = VetRetroMCPClient(mcp_url)
        await mcp_client.connect()

        print("✓ Connected to MCP server")

        # Initialize investigation manager
        inv_manager = InvestigationManager(settings.INVESTIGATIONS_DIR)
        print(f"✓ Investigation manager initialized: {settings.INVESTIGATIONS_DIR}")

        # Create full agent
        agent = get_vet_agent_executor(
            mcp_client=mcp_client,
            investigation_manager=inv_manager,
            verbose=True,
            max_iterations=15,
        )

        question = """I have a diarrhea outbreak in piglets 3-7 days old at Ivanovka farm.
About 40% are affected with watery yellow diarrhea and dehydration.
Can you help me investigate this case?"""

        print(f"\nQuestion: {question}")
        print("\nAgent response:")
        print("-" * 80)

        result = await agent.ainvoke({"input": question})

        print("\n" + result["output"])
        print("-" * 80)

        # Check intermediate steps for tool calls
        if "intermediate_steps" in result and result["intermediate_steps"]:
            print("\n📋 Tool calls made:")
            for i, (action, observation) in enumerate(result["intermediate_steps"], 1):
                tool_name = action.tool
                tool_input = action.tool_input
                print(f"  {i}. {tool_name}")
                if isinstance(tool_input, dict):
                    for key, value in tool_input.items():
                        # Truncate long values
                        if isinstance(value, str) and len(value) > 100:
                            value = value[:100] + "..."
                        print(f"      {key}: {value}")

        print("\n✅ Test 3 passed: Full agent works correctly")
        return True

    except Exception as e:
        print(f"\n❌ Test 3 failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if mcp_client:
            await mcp_client.close()


async def main():
    """
    Run all tests sequentially.
    """
    print("\n" + "🧪 "*20)
    print("Veterinary Investigation Agent Test Suite")
    print("🧪 "*20)

    results = []

    # Test 1: Simple agent
    results.append(await test_simple_agent())

    # Test 2: Agent with MCP tools
    print("\n⏸️  Pausing before next test...")
    await asyncio.sleep(2)
    results.append(await test_agent_with_mcp())

    # Test 3: Full agent
    print("\n⏸️  Pausing before next test...")
    await asyncio.sleep(2)
    results.append(await test_full_agent())

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Test 1 (Simple Agent):        {'✅ PASSED' if results[0] else '❌ FAILED'}")
    print(f"Test 2 (MCP Tools):           {'✅ PASSED' if results[1] else '❌ FAILED'}")
    print(f"Test 3 (Full Agent):          {'✅ PASSED' if results[2] else '❌ FAILED'}")
    print(f"\nTotal: {sum(results)}/3 tests passed")
    print("="*80)

    if all(results):
        print("\n🎉 All tests passed! Agent is ready for deployment.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
