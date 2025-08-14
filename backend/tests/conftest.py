"""
Pytest configuration and shared fixtures for RAG system tests
"""
import pytest
import tempfile
import shutil
import os
import sys
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
import httpx
from config import Config
from models import Course, Lesson, CourseChunk


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing"""
    config = Mock(spec=Config)
    config.anthropic_api_key = "test_key"
    config.model_name = "claude-3-sonnet-20240229"
    config.embedding_model = "all-MiniLM-L6-v2"
    config.chunk_size = 800
    config.chunk_overlap = 100
    config.db_path = "./test_chroma_db"
    config.max_conversation_history = 2
    return config


@pytest.fixture
def sample_courses():
    """Create sample course data for testing"""
    return [
        Course(
            title="Introduction to Python",
            instructor="Dr. Smith",
            lessons=[
                Lesson(number=0, title="Getting Started", link="https://example.com/lesson0"),
                Lesson(number=1, title="Variables and Data Types", link="https://example.com/lesson1")
            ],
            links=["https://example.com/course1"]
        ),
        Course(
            title="Advanced Data Structures",
            instructor="Prof. Johnson",
            lessons=[
                Lesson(number=0, title="Introduction to Data Structures"),
                Lesson(number=1, title="Arrays and Lists")
            ],
            links=["https://example.com/course2"]
        )
    ]


@pytest.fixture
def sample_chunks():
    """Create sample course chunks for testing"""
    return [
        CourseChunk(
            content="Python is a high-level programming language known for its simplicity.",
            course_title="Introduction to Python",
            lesson_number=0,
            chunk_index=0
        ),
        CourseChunk(
            content="Variables in Python are created by assigning values to them.",
            course_title="Introduction to Python",
            lesson_number=1,
            chunk_index=0
        ),
        CourseChunk(
            content="Data structures are fundamental building blocks in computer science.",
            course_title="Advanced Data Structures",
            lesson_number=0,
            chunk_index=0
        )
    ]


@pytest.fixture
def temp_docs_dir():
    """Create a temporary directory with sample course documents"""
    temp_dir = tempfile.mkdtemp()
    
    # Create sample course file
    course_content = """Course Title: Introduction to Python
Course Link: https://example.com/python-course
Course Instructor: Dr. Smith

Lesson 0: Getting Started
Welcome to Python programming. Python is a versatile language used for web development, data analysis, and more.

Lesson 1: Variables and Data Types
Variables are containers for storing data values. Python has various data types including integers, strings, and lists.
"""
    
    with open(os.path.join(temp_dir, "python_course.txt"), "w") as f:
        f.write(course_content)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store for testing"""
    mock_store = MagicMock()
    mock_store.search_courses.return_value = [
        {"title": "Introduction to Python", "instructor": "Dr. Smith", "match_score": 0.9}
    ]
    mock_store.search_content.return_value = [
        {
            "content": "Python is a high-level programming language",
            "course_title": "Introduction to Python",
            "lesson_number": 0,
            "chunk_index": 0,
            "score": 0.8
        }
    ]
    mock_store.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Introduction to Python", "Advanced Data Structures"]
    }
    return mock_store


@pytest.fixture
def mock_ai_generator():
    """Create a mock AI generator for testing"""
    mock_generator = MagicMock()
    mock_generator.generate_response.return_value = (
        "This is a test response about Python programming.",
        ["Source 1: Introduction to Python, Lesson 0"]
    )
    return mock_generator


@pytest.fixture
def mock_rag_system(mock_config, mock_vector_store, mock_ai_generator):
    """Create a mock RAG system for testing"""
    with patch('rag_system.VectorStore') as mock_vs_class, \
         patch('rag_system.AIGenerator') as mock_ai_class, \
         patch('rag_system.SessionManager') as mock_session_class:
        
        mock_vs_class.return_value = mock_vector_store
        mock_ai_class.return_value = mock_ai_generator
        
        # Mock session manager with unique session IDs
        mock_session_manager = MagicMock()
        import uuid
        mock_session_manager.create_session.side_effect = lambda: f"test-session-{uuid.uuid4().hex[:8]}"
        mock_session_class.return_value = mock_session_manager
        
        from rag_system import RAGSystem
        rag_system = RAGSystem(mock_config)
        rag_system.session_manager = mock_session_manager
        
        # Mock the query method
        rag_system.query = MagicMock(return_value=(
            "Test response about the query",
            ["Source 1", "Source 2"]
        ))
        
        # Mock the get_course_analytics method
        rag_system.get_course_analytics = MagicMock(return_value={
            "total_courses": 2,
            "course_titles": ["Introduction to Python", "Advanced Data Structures"]
        })
        
        return rag_system


@pytest.fixture
def test_client(mock_rag_system):
    """Create a FastAPI test client with mocked dependencies"""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import List, Optional, Union, Dict, Any
    
    # Create a test app without static file mounting to avoid frontend dependency
    test_app = FastAPI(title="Test Course Materials RAG System")
    
    # Add CORS middleware
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Pydantic models (same as in main app)
    class QueryRequest(BaseModel):
        query: str
        session_id: Optional[str] = None

    class QueryResponse(BaseModel):
        answer: str
        sources: List[Union[str, Dict[str, Any]]]
        session_id: str

    class CourseStats(BaseModel):
        total_courses: int
        course_titles: List[str]

    class NewSessionResponse(BaseModel):
        session_id: str
    
    # API endpoints (inline to avoid import issues)
    @test_app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        from fastapi import HTTPException
        
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        session_id = request.session_id or mock_rag_system.session_manager.create_session()
        answer, sources = mock_rag_system.query(request.query, session_id)
        
        return QueryResponse(
            answer=str(answer),
            sources=sources if isinstance(sources, list) else [],
            session_id=session_id
        )

    @test_app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        from fastapi import HTTPException
        try:
            analytics = mock_rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @test_app.post("/api/new-session", response_model=NewSessionResponse)
    async def create_new_session():
        from fastapi import HTTPException
        try:
            session_id = mock_rag_system.session_manager.create_session()
            return NewSessionResponse(session_id=session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @test_app.get("/")
    async def read_root():
        return {"message": "Test RAG System API"}
    
    return TestClient(test_app)


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client for testing"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(text="This is a test response from Claude")
    ]
    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture(autouse=True)
def cleanup_test_db():
    """Automatically cleanup test database after each test"""
    yield
    # Cleanup any test database files
    test_db_path = "./test_chroma_db"
    if os.path.exists(test_db_path):
        shutil.rmtree(test_db_path)