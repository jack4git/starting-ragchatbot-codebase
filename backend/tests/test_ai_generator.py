"""
Test suite for AIGenerator to identify tool calling failures
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock, MagicMock, patch
from ai_generator import AIGenerator
from search_tools import ToolManager, CourseSearchTool
from config import config


class MockAnthropicResponse:
    """Mock Anthropic API response"""
    def __init__(self, content_text=None, stop_reason="end_turn", tool_calls=None):
        self.stop_reason = stop_reason
        if tool_calls:
            self.content = tool_calls
        else:
            mock_content = Mock()
            mock_content.text = content_text or "Mock response"
            self.content = [mock_content]


class MockToolUseContent:
    """Mock tool use content block"""
    def __init__(self, name="search_course_content", input_data=None, tool_id="test_id"):
        self.type = "tool_use"
        self.name = name
        self.input = input_data or {"query": "test query"}
        self.id = tool_id


class TestAIGenerator:
    """Test AIGenerator functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        # Skip if no API key available
        if not config.ANTHROPIC_API_KEY:
            pytest.skip("No ANTHROPIC_API_KEY available for testing")
        
        self.ai_generator = AIGenerator(config.ANTHROPIC_API_KEY, config.ANTHROPIC_MODEL)
        
    def test_basic_response_without_tools(self):
        """Test basic response generation without tools"""
        with patch.object(self.ai_generator.client.messages, 'create') as mock_create:
            mock_response = MockAnthropicResponse("Test response without tools")
            mock_create.return_value = mock_response
            
            result = self.ai_generator.generate_response("What is 2+2?")
            
            assert result == "Test response without tools"
            mock_create.assert_called_once()
            
    def test_tool_calling_flow(self):
        """Test the tool calling flow"""
        # Create mock tool manager
        mock_tool_manager = Mock(spec=ToolManager)
        mock_tool_manager.execute_tool.return_value = "Tool execution result"
        
        # Create mock tools list
        mock_tools = [{"name": "search_course_content", "description": "Search content"}]
        
        with patch.object(self.ai_generator.client.messages, 'create') as mock_create:
            # First call returns tool use
            tool_content = MockToolUseContent()
            initial_response = MockAnthropicResponse(
                stop_reason="tool_use",
                tool_calls=[tool_content]
            )
            
            # Second call returns final response
            final_response = MockAnthropicResponse("Final response after tool use")
            
            mock_create.side_effect = [initial_response, final_response]
            
            result = self.ai_generator.generate_response(
                "Search for MCP content",
                tools=mock_tools,
                tool_manager=mock_tool_manager
            )
            
            assert result == "Final response after tool use"
            assert mock_create.call_count == 2
            mock_tool_manager.execute_tool.assert_called_once_with(
                "search_course_content",
                query="test query"
            )


class TestAIGeneratorIntegration:
    """Integration tests for AIGenerator with real tool manager"""
    
    def setup_method(self):
        """Setup with real components"""
        if not config.ANTHROPIC_API_KEY:
            pytest.skip("No ANTHROPIC_API_KEY available for testing")
            
        self.ai_generator = AIGenerator(config.ANTHROPIC_API_KEY, config.ANTHROPIC_MODEL)
        
        # Create real tool manager with mock vector store
        self.mock_vector_store = Mock()
        self.tool_manager = ToolManager()
        self.search_tool = CourseSearchTool(self.mock_vector_store)
        self.tool_manager.register_tool(self.search_tool)
    
    def test_real_tool_execution_flow(self):
        """Test actual tool execution with mocked search results"""
        # Mock the search to return specific results
        from vector_store import SearchResults
        mock_results = SearchResults(
            documents=["Test content about MCP"],
            metadata=[{"course_title": "Test Course", "lesson_number": 1}],
            distances=[0.5],
            error=None
        )
        self.mock_vector_store.search.return_value = mock_results
        
        # Get tool definitions
        tools = self.tool_manager.get_tool_definitions()
        
        print(f"\n=== AI GENERATOR INTEGRATION TEST ===")
        print(f"Available tools: {[t['name'] for t in tools]}")
        
        try:
            # This will make an actual API call to Anthropic
            result = self.ai_generator.generate_response(
                "What does the MCP course teach about architecture?",
                tools=tools,
                tool_manager=self.tool_manager
            )
            
            print(f"AI Response: {result}")
            print(f"Search called: {self.mock_vector_store.search.called}")
            if self.mock_vector_store.search.called:
                print(f"Search call args: {self.mock_vector_store.search.call_args}")
            
        except Exception as e:
            print(f"AI Generator integration test failed: {e}")
            raise


class TestAIGeneratorErrorHandling:
    """Test error handling in AI generator"""
    
    def setup_method(self):
        """Setup test fixtures"""
        if not config.ANTHROPIC_API_KEY:
            pytest.skip("No ANTHROPIC_API_KEY available for testing")
        
        self.ai_generator = AIGenerator(config.ANTHROPIC_API_KEY, config.ANTHROPIC_MODEL)
    
    def test_tool_execution_error_handling(self):
        """Test handling of tool execution errors"""
        # Create mock tool manager that throws errors
        mock_tool_manager = Mock(spec=ToolManager)
        mock_tool_manager.execute_tool.side_effect = Exception("Tool execution failed")
        
        mock_tools = [{"name": "search_course_content", "description": "Search content"}]
        
        with patch.object(self.ai_generator.client.messages, 'create') as mock_create:
            tool_content = MockToolUseContent()
            initial_response = MockAnthropicResponse(
                stop_reason="tool_use",
                tool_calls=[tool_content]
            )
            
            mock_create.return_value = initial_response
            
            # This should handle the tool execution error gracefully
            try:
                result = self.ai_generator.generate_response(
                    "Search for content",
                    tools=mock_tools,
                    tool_manager=mock_tool_manager
                )
                # If no exception, check what the result contains
                print(f"Error handling result: {result}")
            except Exception as e:
                print(f"Tool execution error not handled properly: {e}")
    
    def test_anthropic_api_error_handling(self):
        """Test handling of Anthropic API errors"""
        with patch.object(self.ai_generator.client.messages, 'create') as mock_create:
            mock_create.side_effect = Exception("API rate limit exceeded")
            
            try:
                result = self.ai_generator.generate_response("Test query")
                print(f"API error handled, result: {result}")
            except Exception as e:
                print(f"API error: {e}")
                # This is expected - we want to see how errors propagate


def run_ai_generator_tests():
    """Manually run AI generator tests and capture output"""
    print("="*60)
    print("RUNNING AI GENERATOR TESTS")
    print("="*60)
    
    # Test basic functionality
    print("\n1. Testing basic AI generator functionality...")
    basic_test = TestAIGenerator()
    
    try:
        basic_test.setup_method()
        basic_test.test_basic_response_without_tools()
        print("✓ Basic response test passed")
    except Exception as e:
        print(f"✗ Basic response test failed: {e}")
    
    try:
        basic_test.test_tool_calling_flow()
        print("✓ Tool calling flow test passed")
    except Exception as e:
        print(f"✗ Tool calling flow test failed: {e}")
    
    # Test integration
    print("\n2. Testing AI generator integration...")
    integration_test = TestAIGeneratorIntegration()
    
    try:
        integration_test.setup_method()
        integration_test.test_real_tool_execution_flow()
        print("✓ Integration test completed")
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
    
    # Test error handling
    print("\n3. Testing error handling...")
    error_test = TestAIGeneratorErrorHandling()
    
    try:
        error_test.setup_method()
        error_test.test_tool_execution_error_handling()
        error_test.test_anthropic_api_error_handling()
        print("✓ Error handling tests completed")
    except Exception as e:
        print(f"✗ Error handling tests failed: {e}")


if __name__ == "__main__":
    run_ai_generator_tests()