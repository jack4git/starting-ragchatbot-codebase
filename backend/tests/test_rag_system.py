"""
Test suite for RAG System to identify end-to-end failures
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock, patch
from rag_system import RAGSystem
from config import config
import json


class TestRAGSystemIntegration:
    """Integration tests for RAG system"""
    
    def setup_method(self):
        """Setup RAG system for testing"""
        if not config.ANTHROPIC_API_KEY:
            pytest.skip("No ANTHROPIC_API_KEY available for testing")
        
        try:
            self.rag_system = RAGSystem(config)
            print(f"\n=== RAG SYSTEM SETUP ===")
            print(f"Vector store path: {config.CHROMA_PATH}")
            print(f"Embedding model: {config.EMBEDDING_MODEL}")
            print(f"AI model: {config.ANTHROPIC_MODEL}")
        except Exception as e:
            print(f"Failed to initialize RAG system: {e}")
            pytest.skip(f"Cannot initialize RAG system: {e}")
    
    def test_rag_system_components(self):
        """Test that all RAG system components are properly initialized"""
        print(f"\n=== RAG COMPONENTS TEST ===")
        
        # Check that all components exist
        assert hasattr(self.rag_system, 'document_processor')
        assert hasattr(self.rag_system, 'vector_store')
        assert hasattr(self.rag_system, 'ai_generator')
        assert hasattr(self.rag_system, 'session_manager')
        assert hasattr(self.rag_system, 'tool_manager')
        assert hasattr(self.rag_system, 'search_tool')
        assert hasattr(self.rag_system, 'outline_tool')
        print("✓ All components present")
        
        # Check tool registration
        tools = self.rag_system.tool_manager.get_tool_definitions()
        tool_names = [t['name'] for t in tools]
        print(f"Registered tools: {tool_names}")
        
        assert "search_course_content" in tool_names
        assert "get_course_outline" in tool_names
        print("✓ Tools properly registered")
    
    def test_query_processing_flow(self):
        """Test the complete query processing flow"""
        print(f"\n=== QUERY PROCESSING FLOW TEST ===")
        
        # Test content-related query
        test_query = "What is MCP architecture?"
        test_session_id = "test_session_123"
        
        try:
            result = self.rag_system.query(test_query, test_session_id)
            
            print(f"Query: {test_query}")
            print(f"Result type: {type(result)}")
            print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            if isinstance(result, dict):
                print(f"Answer: {result.get('answer', 'No answer key')[:200]}...")
                print(f"Sources: {result.get('sources', 'No sources key')}")
                print(f"Session ID: {result.get('session_id', 'No session_id key')}")
            else:
                print(f"Unexpected result format: {result}")
                
        except Exception as e:
            print(f"Query processing failed: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
    
    def test_vector_store_data_availability(self):
        """Test if vector store has the expected data"""
        print(f"\n=== VECTOR STORE DATA TEST ===")
        
        try:
            # Check course count
            course_count = self.rag_system.vector_store.get_course_count()
            print(f"Course count: {course_count}")
            
            # Check existing courses
            existing_courses = self.rag_system.vector_store.get_existing_course_titles()
            print(f"Existing courses: {existing_courses}")
            
            # Check course metadata
            all_metadata = self.rag_system.vector_store.get_all_courses_metadata()
            print(f"Metadata count: {len(all_metadata)}")
            
            if all_metadata:
                print(f"Sample metadata keys: {list(all_metadata[0].keys()) if all_metadata else 'None'}")
            
            # Test direct search on vector store
            from vector_store import SearchResults
            search_result = self.rag_system.vector_store.search("MCP")
            print(f"Direct search result - Error: {search_result.error}")
            print(f"Direct search result - Documents count: {len(search_result.documents)}")
            print(f"Direct search result - Is empty: {search_result.is_empty()}")
            
            if search_result.documents:
                print(f"Sample document: {search_result.documents[0][:100]}...")
                print(f"Sample metadata: {search_result.metadata[0] if search_result.metadata else 'No metadata'}")
        
        except Exception as e:
            print(f"Vector store data test failed: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
    
    def test_tool_manager_execution(self):
        """Test tool manager execution directly"""
        print(f"\n=== TOOL MANAGER TEST ===")
        
        try:
            # Test search tool execution
            search_result = self.rag_system.tool_manager.execute_tool(
                "search_course_content",
                query="MCP architecture"
            )
            print(f"Search tool result: {search_result[:200] if search_result else 'None'}...")
            
            # Test outline tool execution
            outline_result = self.rag_system.tool_manager.execute_tool(
                "get_course_outline",
                course_title="MCP"
            )
            print(f"Outline tool result: {outline_result[:200] if outline_result else 'None'}...")
            
        except Exception as e:
            print(f"Tool manager test failed: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
    
    def test_session_management(self):
        """Test session management functionality"""
        print(f"\n=== SESSION MANAGEMENT TEST ===")
        
        try:
            test_session = "test_session_456"
            
            # Add some conversation history
            self.rag_system.session_manager.add_exchange(
                test_session, 
                "What is MCP?", 
                "MCP stands for Model Context Protocol"
            )
            
            # Get history
            history = self.rag_system.session_manager.get_conversation_history(test_session)
            print(f"Session history: {history}")
            
            # Test formatted history
            formatted = self.rag_system.session_manager.get_formatted_history(test_session)
            print(f"Formatted history: {formatted}")
            
        except Exception as e:
            print(f"Session management test failed: {e}")


def run_rag_system_tests():
    """Manually run RAG system tests and capture output"""
    print("="*60)
    print("RUNNING RAG SYSTEM INTEGRATION TESTS")
    print("="*60)
    
    test_class = TestRAGSystemIntegration()
    
    try:
        test_class.setup_method()
        
        # Test components
        test_class.test_rag_system_components()
        print("✓ Components test completed")
        
        # Test vector store data
        test_class.test_vector_store_data_availability()
        print("✓ Vector store data test completed")
        
        # Test tool manager
        test_class.test_tool_manager_execution()
        print("✓ Tool manager test completed")
        
        # Test session management
        test_class.test_session_management()
        print("✓ Session management test completed")
        
        # Test full query processing - this is the most important one
        test_class.test_query_processing_flow()
        print("✓ Query processing test completed")
        
    except Exception as e:
        print(f"RAG system tests failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    run_rag_system_tests()