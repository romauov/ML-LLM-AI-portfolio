# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VetRetro is an AI-powered veterinary incident investigation system for livestock disease outbreaks (primarily pigs and poultry). The system combines structured investigation protocols with RAG-based access to specialized veterinary literature.

**Architecture:**
1. **MCP Server** (`mcp-server/`) - RAG server providing veterinary knowledge base access via Model Context Protocol
2. **Agent Workspace** (`agent-workspace/`) - Structured environment for conducting investigations with AI assistance
3. **Web Backend** (planned, `web-backend/`) - FastAPI + Langchain + Open WebUI integration

**Current Status:** MCP server and agent workspace are fully implemented and tested. Web interface is in planning phase (see TODO.md).

## Database Connection

PostgreSQL database with pgvector for semantic search:
- Host: `{{DB_HOST}}`
- Port: `5432`
- Database: `{{DB_NAME}}`
- User: `{{DB_USER}}`
- Password: `{{DB_PASSWORD}}`

**Connection command:**
```bash
PGPASSWORD={{DB_PASSWORD}} psql -h {{DB_HOST}} -U {{DB_USER}} -d {{DB_NAME}}
```

### knowledge_base_chunks Table

Main table for vector search containing 3,451 records:
- `content` (text) - Actual text content
- `embedding` (vector(1536)) - 1536-dimensional embedding for similarity search
- `source_document` (text) - Name of source book
- `page_number` (integer) - Page number in source
- `chunk_number` (integer) - Sequential chunk number
- `chapter_title` (text) - Chapter where content appears
- `keywords` (text[]) - Associated keywords
- `content_type`, `content_name` - Content metadata

**Loaded sources:**
1. Antimicrobial Therapy in Veterinary Medicine, 5th Edition
2. Examination of pharmacokinetic/pharmacodynamic relationships of antimicrobials in pigs
3. Practical guide to broiler health management
4. Болезни свиней (Russian)

## API Configuration

### Embeddings API (VseGPT)
Used for generating embeddings for vector search:
```python
from openai import OpenAI
client = OpenAI(
    api_key=os.getenv("VSEGPT_API_KEY"),
    base_url="https://api.vsegpt.ru/v1",
)
client.embeddings.create(
    model="text-embedding-ada-002",
    input="your text here",
    encoding_format="float"
)
```

Store API key in `.env`:
```
VSEGPT_API_KEY={{VSEGPT_API_KEY}}
```

### LLM API (Local)
For LLM inference through local proxy:
```python
client = OpenAI(
    api_key="{{LLM_API_KEY}}",
    base_url="{{LLM_API_BASE}}"
)
response = client.chat.completions.create(
    model="unsloth/qwen3-30b-a3b-instruct-2507",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

**Important:** Remove proxy environment variables before making API calls:
```python
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
```

## Project Structure

```
VetRetro/
├── mcp-server/                  # MCP server (implemented)
│   ├── src/
│   │   ├── server.py            # Main MCP server (stdio transport)
│   │   ├── server_http.py       # HTTP/SSE transport
│   │   ├── knowledge_base.py    # RAG search with pgvector
│   │   ├── embeddings.py        # VseGPT OpenAI-compatible embeddings
│   │   ├── document_extractor.py # PDF/DOCX extraction with OCR
│   │   └── config.py            # Settings management
│   ├── run_http.py              # Launch HTTP server
│   ├── run_stdio.py             # Launch stdio server
│   └── pyproject.toml
├── agent-workspace/             # Investigation workspace (implemented)
│   ├── AGENTS.md                # Main agent prompt (loaded by Claude Code)
│   ├── QWEN.md                  # Qwen-specific prompt
│   ├── instructions/            # Specialized investigation protocols
│   │   ├── neonatal_diarrhea.md
│   │   ├── respiratory.md
│   │   └── prrs.md
│   ├── templates/               # Investigation file templates
│   ├── examples/                # Example cases
│   ├── test_scenarios/          # Testing scenarios
│   └── investigations/          # Active investigations (not in git)
├── docs/                        # Documentation
│   ├── ТЗ_MVP_прототип.md       # Original MVP spec
│   ├── ТЗ-Web.md                # Web interface spec (Langchain approach)
│   ├── Руководство_*.md         # Investigation guides
│   └── qwen-code-system-prompt.md # Reference prompts
└── TODO.md                      # Development roadmap
```

## MCP Server Tools

The MCP server provides five tools for knowledge base access:

### 1. vet_search
Semantic search across veterinary knowledge base using pgvector cosine similarity.
- **Parameters:** `query` (required), `limit` (1-20, default 5), `offset` (pagination), `source_filter` (optional)
- **Returns:** Ranked chunks with similarity scores, source metadata, page numbers, chapters
- **Example:** Search for "E.coli neonatal diarrhea treatment"

### 2. vet_sources
List all available sources (books) in the knowledge base.
- **No parameters**
- **Returns:** Source names, descriptions, page ranges, chapter counts

### 3. source_info
Get table of contents for a specific source.
- **Parameters:** `source_document` (source name)
- **Returns:** Chapters with page ranges

### 4. get_pages
Retrieve full text from specific page range.
- **Parameters:** `source_document`, `page_start`, `page_end` (optional)
- **Returns:** Sequential page content (useful when search chunks lack context)

### 5. extract_document
Extract text from PDF/DOCX files with OCR support.
- **Parameters:** `file_path` (absolute path)
- **Supports:** PDF (with OCR), DOCX
- **Output:** Saves extracted pages as markdown in `extracted_documents/<filename>/`
- **Use case:** Process lab results, scanned documents, reports with tables/charts

## Vector Search Implementation

Use pgvector cosine similarity search:
```sql
SELECT
    content,
    source_document,
    page_number,
    chapter_title,
    1 - (embedding <=> query_embedding) as similarity_score
FROM knowledge_base_chunks
ORDER BY embedding <=> query_embedding
LIMIT top_k
```

Minimum similarity threshold: 0.5

## Common Development Tasks

### Running MCP Server

**HTTP/SSE transport** (for web integrations):
```bash
cd mcp-server
python run_http.py
# Server runs on http://localhost:8765
```

**stdio transport** (for Claude Desktop):
```bash
cd mcp-server
python run_stdio.py
```

**Install dependencies:**
```bash
cd mcp-server
pip install -e .
# or
pip install -e ".[dev]"  # with dev dependencies
```

### Testing MCP Server

Test individual tools:
```bash
cd mcp-server
python -c "
from src.knowledge_base import get_knowledge_base
kb = get_knowledge_base()
results = await kb.search('E.coli diarrhea', limit=3)
print(results)
"
```

Test document extraction:
```bash
cd mcp-server
python test_extractor.py
```

### Working with Agent Workspace

**Start investigation** (launch Claude Code from investigation folder):
```bash
cd agent-workspace
mkdir investigations/2025-11-07_farm-name_problem-type
cd investigations/2025-11-07_farm-name_problem-type
# Launch Claude Code - AGENTS.md loads automatically
```

**Test scenarios** (pre-built investigation scenarios):
```bash
cd agent-workspace
# See test_scenarios/ for complete test cases
# - neonatal_diarrhea.md
# - post_weaning_diarrhea.md
# - rotavirus_case.md
```

### Investigation File Structure

When agent creates an investigation, the following files are generated:
```
investigations/YYYY-MM-DD_name/
├── STATUS.md                    # Current investigation status
├── 00_incident.md               # Incident description
├── 01_group_card.md             # Animal group card
├── 02_checklist_general.md      # General checklist
├── 03_checklist_specific.md     # Problem-specific checklist
├── 04_clinical_data.md          # Clinical observations
├── 05_lab_results.md            # Laboratory results
├── 06_knowledge_snippets.md     # Citations from knowledge base
├── 07_hypotheses.md             # Ranked hypotheses with evidence
├── 08_conclusions.md            # Final conclusions
└── 09_report.md                 # Complete report
```

Agent proactively uses MCP tools to search knowledge base and cite sources in `06_knowledge_snippets.md`.

## Investigation Protocols

The system supports specialized investigation protocols (see `agent-workspace/instructions/`):

1. **Neonatal Diarrhea** (`instructions/neonatal_diarrhea.md`)
   - Age: 0-15 days
   - Common causes: ETEC E.coli, rotavirus, management issues
   - Systematic approach: Technology → Infection → Treatment → Prevention

2. **Respiratory Problems** (`instructions/respiratory.md`)
   - All age groups (common in growers/finishers)
   - Common causes: Mycoplasma, PRRS, Streptococcus, environmental
   - Approach: Production data → Field check → Clinical/Lab → Treatment → Root causes

3. **PRRS** (`instructions/prrs.md`)
   - Reproductive + respiratory signs
   - Systematic status determination
   - Monitoring and control planning

**Agent behavior:** Agent automatically detects problem type from initial description and loads appropriate protocol from `instructions/`.

## Testing & Examples

**Completed investigations** (examples in `agent-workspace/investigations/`):
- `ivanovka_neonatal_diarrhea_20251103/` - ETEC case with ROI analysis
- `rassvet_weaning_diarrhea_20251103/` - Multi-factorial post-weaning case
- `dubki_respiratory_20251105/` - Mycoplasma + secondary E.coli

**Testing with different LLMs:**
- Claude Sonnet 4.5: Excellent results (10/10)
- Qwen 3 70B: Good results (9/10)

**Evaluation criteria:**
- Completeness (all files created)
- Proactivity (autonomous knowledge base searches)
- Clinical reasoning (multi-factorial analysis)
- Practicality (specific doses, ROI calculations)

## Environment Variables

Required in `.env`:
```
# Database
DB_HOST={{DB_HOST}}
DB_PORT=5432
DB_NAME={{DB_NAME}}
DB_USER={{DB_USER}}
DB_PASSWORD={{DB_PASSWORD}}

# Embeddings API
VSEGPT_API_KEY={{VSEGPT_API_KEY}}
OPENAI_API_BASE=https://api.vsegpt.ru/v1

# LLM API (optional)
LLM_API_BASE={{LLM_API_BASE}}
LLM_API_KEY={{LLM_API_KEY}}
```

## Key Architecture Decisions

### Why MCP (Model Context Protocol)?
- **Separation of concerns:** Knowledge base operations isolated from agent logic
- **Reusability:** Same MCP server works with Claude Code, web UI, or other clients
- **Standardization:** MCP is an emerging standard for LLM-tool integration

### Why Two Agent Prompts (AGENTS.md + QWEN.md)?
- `AGENTS.md`: Optimized for Claude (used in Claude Code)
- `QWEN.md`: Optimized for Qwen models (different prompting style)
- Both follow same investigation workflow but with model-specific instructions

### Why Markdown Files for Investigations?
- **Human-readable:** Veterinarians can read/edit files directly
- **Version control:** Easy to track changes in git
- **Async-friendly:** Investigation can pause/resume over days/weeks
- **Portable:** No database dependency for investigation data

## Development Principles

1. **Evidence-based:** All recommendations must cite knowledge base sources or explicitly note when based on general knowledge
2. **Systematic approach:** Follow structured protocols (technology → infection → treatment)
3. **Multi-factorial analysis:** Recognize that problems often have multiple contributing factors
4. **Practical output:** Provide specific doses, ROI calculations, actionable checklists
5. **Async workflow:** Support investigations spanning days/weeks (waiting for lab results)

## Important Constraints

**For agent operation:**
- Use ONLY facts from incident description, group card, knowledge base, and lab results
- Never fabricate data or make unsupported assumptions
- If information is insufficient, explicitly state what's missing and ask specific questions
- All hypotheses must cite evidence (clinical findings + knowledge base sources)
- Maintain structured file organization (00-09 numbered files)
- Update STATUS.md after each session

**For development:**
- Never commit API keys or sensitive credentials
- Keep investigations/ directory out of git (in .gitignore)
- MCP server requires proxy variables to be unset (see config.py)
- **Documentation language:** All code comments, docstrings, and README files must be in Russian (Русский язык для всей документации)

## Planned Web Interface (TODO.md)

The next development phase involves creating a web UI using:
- **Backend:** FastAPI + Langchain + LangServe (port 8000)
- **Frontend:** Open WebUI (or other OpenAI-compatible chat UI)
- **Architecture:** 2 servers total (vetretro MCP + FastAPI backend)

**Key approach (from docs/ТЗ-Web.md):**
- Langchain AgentExecutor with OpenRouter LLM
- Langchain Tools wrapping MCP tools + file operations
- Investigation Manager for file operations (no separate MCP-filesystem server)
- LangServe automatically creates OpenAI-compatible `/v1/chat/completions` endpoint
- Agent uses same AGENTS.md prompt adapted for Langchain format

**Progress tracked in:** TODO.md (71 tasks across 9 phases)
