"""Test script for Langchain Tools."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.services.mcp_client import VetRetroMCPClient
from app.services.investigation_manager import InvestigationManager
from app.tools.mcp_tools import create_mcp_tools
from app.tools.investigation_tools import create_investigation_tools
from app.tools.todo_tool import TodoWriteTool, TodoItem


async def test_mcp_tools():
    """Test MCP tools."""
    print("\n=== Testing MCP Tools ===\n")

    # Initialize MCP client
    mcp_client = VetRetroMCPClient(url=settings.VETRETRO_MCP_URL)

    # Create tools
    tools = create_mcp_tools(mcp_client)

    print(f"Created {len(tools)} MCP tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:80]}...")
        print(f"    Args schema: {tool.args_schema.__name__ if tool.args_schema else 'None'}")

    # Verify tool structure
    assert len(tools) == 4, f"Expected 4 tools, got {len(tools)}"
    assert tools[0].name == "vet_search"
    assert tools[1].name == "vet_sources"
    assert tools[2].name == "source_info"
    assert tools[3].name == "get_pages"

    print("\n✓ MCP Tools test completed (structure verified)")


def test_investigation_tools():
    """Test Investigation tools."""
    print("\n=== Testing Investigation Tools ===\n")

    # Initialize Investigation Manager
    investigation_manager = InvestigationManager(
        workspace_path=settings.AGENT_WORKSPACE_DIR
    )

    # Create tools
    tools = create_investigation_tools(investigation_manager)

    print(f"Created {len(tools)} Investigation tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:80]}...")

    # Test CreateInvestigationTool
    print("\n--- Testing create_investigation ---")
    create_tool = tools[0]
    result = create_tool._run(
        farm_name="Test Farm",
        animal_type="piglets",
        problem_type="test-diarrhea",
        description="This is a test investigation for tool testing purposes."
    )
    print(result)

    # Extract investigation_id from result
    import re
    match = re.search(r"investigation: (\S+)", result)
    if match:
        test_investigation_id = match.group(1)
        print(f"\nCreated test investigation: {test_investigation_id}")

        # Test ListFilesTool
        print("\n--- Testing list_files ---")
        list_files_tool = tools[2]
        result = list_files_tool._run(investigation_id=test_investigation_id)
        print(result)

        # Test ReadFileTool
        print("\n--- Testing read_file ---")
        read_file_tool = tools[3]
        result = read_file_tool._run(
            investigation_id=test_investigation_id,
            filename="STATUS.md"
        )
        print(f"Read result length: {len(result)} characters")
        print(f"First 200 chars: {result[:200]}...")

        # Test WriteFileTool
        print("\n--- Testing write_file ---")
        write_file_tool = tools[4]
        result = write_file_tool._run(
            investigation_id=test_investigation_id,
            filename="test_file.md",
            content="# Test File\n\nThis is a test file created by the tool test script."
        )
        print(result)

        # Clean up test investigation
        print(f"\n--- Cleaning up test investigation ---")
        import shutil
        test_path = Path(settings.AGENT_WORKSPACE_DIR) / "investigations" / test_investigation_id
        if test_path.exists():
            shutil.rmtree(test_path)
            print(f"Removed test investigation: {test_investigation_id}")

    print("\n✓ Investigation Tools test completed")


def test_todo_tool():
    """Test Todo tool."""
    print("\n=== Testing Todo Tool ===\n")

    # Create tool
    todo_tool = TodoWriteTool()

    print(f"Tool name: {todo_tool.name}")
    print(f"Tool description length: {len(todo_tool.description)} characters")

    # Test with sample todos
    print("\n--- Testing todo_write ---")
    result = todo_tool._run(
        todos=[
            TodoItem(
                content="Search for E.coli treatments",
                status="completed",
                activeForm="Searching for E.coli treatments"
            ),
            TodoItem(
                content="Create hypothesis file",
                status="in_progress",
                activeForm="Creating hypothesis file"
            ),
            TodoItem(
                content="Review lab results",
                status="pending",
                activeForm="Reviewing lab results"
            ),
        ]
    )
    print(result)

    print("\n✓ Todo Tool test completed")


async def main():
    """Run all tests."""
    print("=" * 70)
    print("VetRetro Langchain Tools Test Suite")
    print("=" * 70)

    try:
        # Test MCP tools
        await test_mcp_tools()

        # Test Investigation tools
        test_investigation_tools()

        # Test Todo tool
        test_todo_tool()

        print("\n" + "=" * 70)
        print("✓ All tests completed successfully!")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
