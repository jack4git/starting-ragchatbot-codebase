"""
Test suite for CourseSearchTool to identify search failures
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock, MagicMock
from search_tools import CourseSearchTool, ToolManager
from vector_store import VectorStore, SearchResults
from config import config


class TestCourseSearchTool:
    """Test CourseSearchTool functionality in isolation"""

    def setup_method(self):
        """Setup test fixtures"""
        # Create a mock vector store
        self.mock_store = Mock(spec=VectorStore)
        self.search_tool = CourseSearchTool(self.mock_store)

    def test_tool_definition(self):
        """Test that tool definition is properly structured"""
        tool_def = self.search_tool.get_tool_definition()

        assert tool_def["name"] == "search_course_content"
        assert "description" in tool_def
        assert "input_schema" in tool_def
        assert tool_def["input_schema"]["properties"]["query"]["type"] == "string"
        assert "query" in tool_def["input_schema"]["required"]

    def test_execute_successful_search(self):
        """Test successful search execution"""
        # Mock successful search results
        mock_results = SearchResults(
            documents=["This is lesson content about MCP architecture"],
            metadata=[{"course_title": "MCP Course", "lesson_number": 1}],
            distances=[0.5],
            error=None,
        )
        self.mock_store.search.return_value = mock_results

        result = self.search_tool.execute("MCP architecture")

        assert result is not None
        assert "MCP Course" in result
        assert "Lesson 1" in result
        assert "This is lesson content about MCP architecture" in result
        self.mock_store.search.assert_called_once_with(
            query="MCP architecture", course_name=None, lesson_number=None
        )

    def test_execute_with_course_filter(self):
        """Test search with course name filter"""
        mock_results = SearchResults(
            documents=["Filtered content"],
            metadata=[{"course_title": "Specific Course", "lesson_number": 2}],
            distances=[0.3],
            error=None,
        )
        self.mock_store.search.return_value = mock_results

        result = self.search_tool.execute("test query", course_name="Specific")

        assert "Specific Course" in result
        self.mock_store.search.assert_called_once_with(
            query="test query", course_name="Specific", lesson_number=None
        )

    def test_execute_with_lesson_filter(self):
        """Test search with lesson number filter"""
        mock_results = SearchResults(
            documents=["Lesson-specific content"],
            metadata=[{"course_title": "Test Course", "lesson_number": 3}],
            distances=[0.4],
            error=None,
        )
        self.mock_store.search.return_value = mock_results

        result = self.search_tool.execute("test query", lesson_number=3)

        assert "Test Course" in result
        assert "Lesson 3" in result
        self.mock_store.search.assert_called_once_with(
            query="test query", course_name=None, lesson_number=3
        )

    def test_execute_search_error(self):
        """Test handling of search errors"""
        error_results = SearchResults.empty("Database connection failed")
        self.mock_store.search.return_value = error_results

        result = self.search_tool.execute("test query")

        assert result == "Database connection failed"

    def test_execute_empty_results(self):
        """Test handling of empty search results"""
        empty_results = SearchResults([], [], [], error=None)
        self.mock_store.search.return_value = empty_results

        result = self.search_tool.execute("nonexistent content")

        assert result == "No relevant content found."

    def test_execute_empty_results_with_filters(self):
        """Test handling of empty results with course/lesson filters"""
        empty_results = SearchResults([], [], [], error=None)
        self.mock_store.search.return_value = empty_results

        result = self.search_tool.execute(
            "test", course_name="Missing Course", lesson_number=999
        )

        expected = "No relevant content found in course 'Missing Course' in lesson 999."
        assert result == expected


class TestCourseSearchToolWithRealVectorStore:
    """Test CourseSearchTool with actual vector store to identify real issues"""

    def setup_method(self):
        """Setup with real vector store"""
        try:
            self.vector_store = VectorStore(
                config.CHROMA_PATH, config.EMBEDDING_MODEL, config.MAX_RESULTS
            )
            self.search_tool = CourseSearchTool(self.vector_store)
        except Exception as e:
            pytest.skip(f"Cannot initialize vector store: {e}")

    def test_real_vector_store_search(self):
        """Test search against actual vector store data"""
        # Test a basic search without filters
        result = self.search_tool.execute("MCP")
        print(f"\n=== REAL VECTOR STORE TEST ===")
        print(f"Search query: 'MCP'")
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(result) if result else 0}")
        print(f"Result content: {result[:200] if result else 'None'}...")

        # This test will help us see what the actual search returns
        assert isinstance(result, str), f"Expected string result, got {type(result)}"

        # If we get an error message, capture it
        if "error" in result.lower() or "not found" in result.lower():
            print(f"SEARCH FAILED: {result}")

    def test_vector_store_state(self):
        """Test the current state of the vector store"""
        print(f"\n=== VECTOR STORE STATE TEST ===")

        # Check if course catalog has data
        try:
            catalog_data = self.vector_store.course_catalog.get()
            print(f"Course catalog IDs: {catalog_data.get('ids', [])}")
            print(f"Course catalog count: {len(catalog_data.get('ids', []))}")
        except Exception as e:
            print(f"Error accessing course catalog: {e}")

        # Check if course content has data
        try:
            # Get a small sample of content
            content_data = self.vector_store.course_content.get(limit=3)
            print(f"Course content count (sample): {len(content_data.get('ids', []))}")
            print(f"Sample content IDs: {content_data.get('ids', [])[:3]}")
            if content_data.get("documents"):
                print(f"Sample document: {content_data['documents'][0][:100]}...")
        except Exception as e:
            print(f"Error accessing course content: {e}")

    def test_course_resolution(self):
        """Test course name resolution directly"""
        print(f"\n=== COURSE RESOLUTION TEST ===")

        try:
            # Test the _resolve_course_name method directly
            resolved = self.vector_store._resolve_course_name("MCP")
            print(f"Resolved course name for 'MCP': {resolved}")

            resolved2 = self.vector_store._resolve_course_name("Introduction")
            print(f"Resolved course name for 'Introduction': {resolved2}")

            # Test with exact course title if we know one
            existing_courses = self.vector_store.get_existing_course_titles()
            print(f"Existing courses: {existing_courses}")

            if existing_courses:
                resolved3 = self.vector_store._resolve_course_name(existing_courses[0])
                print(f"Resolved course name for '{existing_courses[0]}': {resolved3}")

        except Exception as e:
            print(f"Error in course resolution test: {e}")


def run_course_search_tests():
    """Manually run the course search tests and capture output"""
    print("=" * 60)
    print("RUNNING COURSE SEARCH TOOL TESTS")
    print("=" * 60)

    # Test with mock vector store
    print("\n1. Testing with mock vector store...")
    test_class = TestCourseSearchTool()
    test_class.setup_method()

    try:
        test_class.test_tool_definition()
        print("✓ Tool definition test passed")
    except Exception as e:
        print(f"✗ Tool definition test failed: {e}")

    try:
        test_class.test_execute_successful_search()
        print("✓ Successful search test passed")
    except Exception as e:
        print(f"✗ Successful search test failed: {e}")

    # Test with real vector store
    print("\n2. Testing with real vector store...")
    real_test_class = TestCourseSearchToolWithRealVectorStore()

    try:
        real_test_class.setup_method()
        real_test_class.test_vector_store_state()
        real_test_class.test_course_resolution()
        real_test_class.test_real_vector_store_search()
    except Exception as e:
        print(f"Real vector store tests failed: {e}")


if __name__ == "__main__":
    run_course_search_tests()
