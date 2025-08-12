# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Create .env file with API key (required)
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

### Running the Application
```bash
# Quick start (recommended)
chmod +x run.sh
./run.sh

# Manual start
cd backend && uv run uvicorn app:app --reload --port 8000
```

Access:
- Web interface: http://localhost:8000
- API docs: http://localhost:8000/docs

## Architecture Overview

This is a **Retrieval-Augmented Generation (RAG) system** for querying course materials with AI-powered responses.

### Core Flow
1. **Document Processing Pipeline**: Course documents (PDF/DOCX/TXT) → structured parsing → sentence-based chunking with overlap → ChromaDB vector storage
2. **Query Processing**: User query → RAG System → Claude API with tool-calling → semantic search → contextualized response

### Key Components

**RAG System (`rag_system.py`)**
- Main orchestrator coordinating all components
- Manages document ingestion and query processing
- Handles session management and conversation history

**Document Processing (`document_processor.py`)**
- Parses structured course documents with format:
  ```
  Course Title: [title]
  Course Link: [url]
  Course Instructor: [instructor]
  
  Lesson 0: [lesson title]
  [lesson content...]
  ```
- Intelligent sentence-based chunking with configurable overlap
- Context enhancement: chunks prefixed with course/lesson info

**Vector Storage (`vector_store.py`)**
- ChromaDB with dual collections: course metadata + content chunks
- Semantic search with course/lesson filtering
- Smart course name resolution (fuzzy matching)

**AI Integration (`ai_generator.py`)**
- Claude API with tool-calling capability
- Static system prompt optimized for educational content
- Tool execution workflow for search operations

**Search Tools (`search_tools.py`)**
- Tool-based architecture where Claude decides when to search
- Course search tool with semantic matching
- Source tracking for UI display

### Data Models (`models.py`)
- `Course`: title, instructor, lessons, links
- `Lesson`: number, title, optional link
- `CourseChunk`: content, course_title, lesson_number, chunk_index

### Configuration (`config.py`)
- Environment variable loading (.env file required)
- Model settings: Claude Sonnet 4, MiniLM embeddings
- Processing parameters: chunk_size=800, overlap=100
- ChromaDB storage path: "./chroma_db"

### Session Management (`session_manager.py`)
- Conversation history tracking per session
- Configurable history limits (default: 2 exchanges)
- Memory management to prevent context bloat

## Document Structure
Course documents in `docs/` folder are auto-loaded on startup. They must follow the structured format above with course metadata in first 3 lines and lesson markers (`Lesson N: title`).

## Key Architectural Decisions
- **Tool-calling approach**: Claude decides when to search vs. using general knowledge
- **Dual ChromaDB collections**: Separate storage for metadata vs. content
- **Context-aware chunking**: Preserves sentence boundaries while adding lesson/course context
- **Session-based conversations**: Maintains context across queries within a session
- remember that I want .history tracked, and when I say add/commit/push that means everything -- but do ask if you see something that shouldn't be tracked