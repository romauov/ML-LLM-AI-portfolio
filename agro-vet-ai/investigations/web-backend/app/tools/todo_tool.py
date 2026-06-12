"""Langchain Tool for todo list management."""

import json
from typing import List, Type, Union
from pydantic import BaseModel, Field, field_validator
from langchain_core.tools import BaseTool


class TodoItem(BaseModel):
    """Single todo item."""

    content: str = Field(..., description="Task description in imperative form")
    status: str = Field(
        ...,
        description="Task status: 'pending', 'in_progress', or 'completed'"
    )
    activeForm: str = Field(
        ...,
        description="Task description in present continuous form (for display during execution)"
    )


class TodoWriteInput(BaseModel):
    """Input schema for TodoWriteTool."""

    todos: Union[List[TodoItem], str] = Field(
        ...,
        description="Complete list of todos with their current statuses"
    )

    @field_validator('todos', mode='before')
    @classmethod
    def parse_todos(cls, v):
        """Parse todos from JSON string if needed."""
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return [TodoItem(**item) for item in parsed]
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                raise ValueError(f"Invalid todos format: {e}")
        return v


TODO_WRITE_DESCRIPTION = """Use this tool to create and manage a structured task list for your current veterinary investigation. This helps you track progress, organize complex investigations, and demonstrate thoroughness to the user.
It also helps the user understand the progress of the investigation and overall progress of their requests.

## When to Use This Tool
Use this tool proactively in these scenarios:

1. Complex multi-step investigations - When an investigation requires 3 or more distinct steps or actions
2. Non-trivial and complex cases - Cases that require careful planning, multiple data sources, or systematic hypothesis evaluation
3. User explicitly requests todo list - When the user directly asks you to use the todo list
4. User provides multiple tasks - When users describe multiple aspects to investigate (e.g., "check clinical signs, review lab results, search for treatments")
5. After receiving new instructions - Immediately capture investigation requirements as todos
6. When you start working on a task - Mark it as in_progress BEFORE beginning work. Ideally you should only have one todo as in_progress at a time
7. After completing a task - Mark it as completed and add any new follow-up tasks discovered during investigation

## When NOT to Use This Tool

Skip using this tool when:
1. There is only a single, straightforward task
2. The task is trivial and tracking it provides no organizational benefit
3. The task can be completed in less than 3 trivial steps
4. The task is purely conversational or informational (e.g., "what is E.coli?")

NOTE that you should not use this tool if there is only one trivial task to do. In this case you are better off just doing the task directly.

## Examples of When to Use the Todo List

<example>
User: I have a diarrhea outbreak in piglets 3-7 days old. Can you help investigate?
Assistant: I'll help investigate this neonatal diarrhea outbreak. Let me create a todo list to track this investigation.
*Creates todo list with the following items:*
1. Review incident details and create investigation
2. Search knowledge base for neonatal diarrhea causes (E.coli, Clostridium, rotavirus)
3. Request group card data (housing, feeding, hygiene practices)
4. Search for ETEC diagnostic criteria and treatment protocols
5. Develop hypothesis ranking with evidence
6. Create treatment and prevention recommendations
*Begins working on the first task*

<reasoning>
The assistant used the todo list because:
1. Investigating a disease outbreak is a multi-step process requiring systematic data collection
2. Multiple knowledge base searches will be needed (causes, diagnostics, treatments)
3. The investigation requires organizing findings into structured files
4. This approach ensures nothing is missed in the investigation
</reasoning>
</example>

<example>
User: We got lab results back. PCR positive for PRRS. What should we do?
Assistant: Let me first read the existing investigation files to see the case background, then I'll update the hypothesis and create an action plan.
*Uses read_file to review incident and existing hypotheses*
Assistant: Based on the PRRS confirmation, let me create a todo list for next steps.
*Creates todo list:*
1. Search knowledge base for PRRS strain types and implications
2. Update hypothesis file with confirmed PRRS diagnosis
3. Search for PRRS treatment and management protocols
4. Create action plan with vaccination, biosecurity, and monitoring measures
5. Update STATUS.md with confirmed diagnosis
*Begins working on the first task*

<reasoning>
The assistant used the todo list because:
1. New lab results require systematic follow-up actions
2. Multiple knowledge base searches needed (strain info, protocols)
3. Several files need updating (hypotheses, status, action plan)
4. This ensures comprehensive response to the confirmed diagnosis
</reasoning>
</example>

## Examples of When NOT to Use the Todo List

<example>
User: What causes diarrhea in piglets?
Assistant: Neonatal diarrhea in piglets has several common causes:

1. **E.coli (ETEC)** - Most common in first week of life
2. **Clostridium perfringens Type C** - Hemorrhagic enteritis, 1-7 days old
3. **Rotavirus** - Typically 7-21 days
4. **Management factors** - Poor hygiene, colostrum intake, environmental stress

Would you like detailed information on any specific cause?

<reasoning>
The assistant did not use the todo list because this is a straightforward informational question. The user is asking for general knowledge, not requesting an investigation or complex task. A direct answer is more appropriate.
</reasoning>
</example>

<example>
User: Can you read the incident file for investigation X?
Assistant: *Uses read_file tool*
Here's the content of the incident file...

<reasoning>
The assistant did not use the todo list because this is a single, simple task (reading one file). There's no need to track progress for such a straightforward request.
</reasoning>
</example>

## Task States and Management

1. **Task States**: Use these states to track progress:
   - pending: Task not yet started
   - in_progress: Currently working on (limit to ONE task at a time)
   - completed: Task finished successfully

   **IMPORTANT**: Task descriptions must have two forms:
   - content: The imperative form describing what needs to be done (e.g., "Search for E.coli treatments", "Update hypothesis file")
   - activeForm: The present continuous form shown during execution (e.g., "Searching for E.coli treatments", "Updating hypothesis file")

2. **Task Management**:
   - Update task status in real-time as you work
   - Mark tasks complete IMMEDIATELY after finishing (don't batch completions)
   - Exactly ONE task must be in_progress at any time (not less, not more)
   - Complete current tasks before starting new ones
   - Remove tasks that are no longer relevant from the list entirely

3. **Task Completion Requirements**:
   - ONLY mark a task as completed when you have FULLY accomplished it
   - If you encounter errors, blockers, or cannot finish, keep the task as in_progress
   - When blocked, create a new task describing what needs to be resolved
   - Never mark a task as completed if:
     - Knowledge base searches returned no useful results
     - File operations failed
     - You couldn't find necessary information
     - The hypothesis evaluation is incomplete

4. **Task Breakdown**:
   - Create specific, actionable items
   - Break complex investigations into smaller, manageable steps
   - Use clear, descriptive task names
   - Always provide both forms:
     - content: "Search for Mycoplasma treatment protocols"
     - activeForm: "Searching for Mycoplasma treatment protocols"

When in doubt, use this tool. Being proactive with task management demonstrates systematic thinking and ensures you complete all investigation requirements successfully.

**For veterinary investigations specifically:**
- Use todos to track evidence gathering from knowledge base
- Track file creation and updates (hypotheses, lab results, conclusions)
- Organize multi-factorial disease investigation steps
- Ensure systematic coverage of Technology → Infection → Treatment workflow
"""


class TodoWriteTool(BaseTool):
    """
    Tool for managing investigation todo lists.

    This tool helps track complex veterinary investigations by maintaining
    a structured task list. Use it proactively for multi-step cases.
    """

    name: str = "todo_write"
    description: str = TODO_WRITE_DESCRIPTION
    args_schema: Type[BaseModel] = TodoWriteInput

    def _run(self, todos: Union[List[TodoItem], str]) -> str:
        """
        Update todo list.

        This is a display-only tool - the actual todo state is managed
        by the Langchain framework. This just returns a confirmation message.
        """
        # Parse todos if string (already validated by pydantic)
        if isinstance(todos, str):
            todos = json.loads(todos)
            todos = [TodoItem(**item) for item in todos]

        # Count tasks by status
        pending = sum(1 for t in todos if t.status == "pending")
        in_progress = sum(1 for t in todos if t.status == "in_progress")
        completed = sum(1 for t in todos if t.status == "completed")

        result = f"Todo list updated:\n"
        result += f"- Completed: {completed}\n"
        result += f"- In Progress: {in_progress}\n"
        result += f"- Pending: {pending}\n"
        result += f"- Total: {len(todos)}\n\n"

        if in_progress > 0:
            in_progress_items = [t for t in todos if t.status == "in_progress"]
            result += "Currently working on:\n"
            for item in in_progress_items:
                result += f"- {item.activeForm}\n"

        return result
