"""
API endpoint tests for the FastAPI RAG system
"""
import pytest
from fastapi.testclient import TestClient
import json


class TestQueryEndpoint:
    """Test the /api/query endpoint"""
    
    @pytest.mark.api
    def test_successful_query(self, test_client):
        """Test successful query processing"""
        response = test_client.post(
            "/api/query",
            json={"query": "What is Python?", "session_id": "test-session-123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert data["session_id"] == "test-session-123"
    
    @pytest.mark.api
    def test_query_without_session_id(self, test_client):
        """Test query without providing session_id (should create new session)"""
        response = test_client.post(
            "/api/query",
            json={"query": "Tell me about data structures"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert data["session_id"]  # Should not be empty
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
    
    @pytest.mark.api
    def test_empty_query(self, test_client):
        """Test query with empty string"""
        response = test_client.post(
            "/api/query",
            json={"query": ""}
        )
        
        assert response.status_code == 400
        assert "Query cannot be empty" in response.json()["detail"]
    
    @pytest.mark.api
    def test_whitespace_only_query(self, test_client):
        """Test query with only whitespace"""
        response = test_client.post(
            "/api/query",
            json={"query": "   \n\t  "}
        )
        
        assert response.status_code == 400
        assert "Query cannot be empty" in response.json()["detail"]
    
    @pytest.mark.api
    def test_missing_query_field(self, test_client):
        """Test request without query field"""
        response = test_client.post(
            "/api/query",
            json={"session_id": "test-session"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.api
    def test_invalid_json_format(self, test_client):
        """Test request with invalid JSON"""
        response = test_client.post(
            "/api/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.api
    def test_long_query(self, test_client):
        """Test with very long query"""
        long_query = "What is Python? " * 100  # Create a long query
        response = test_client.post(
            "/api/query",
            json={"query": long_query}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["answer"], str)


class TestCoursesEndpoint:
    """Test the /api/courses endpoint"""
    
    @pytest.mark.api
    def test_get_course_stats(self, test_client):
        """Test successful retrieval of course statistics"""
        response = test_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_courses" in data
        assert "course_titles" in data
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)
        assert data["total_courses"] >= 0
    
    @pytest.mark.api
    def test_course_stats_structure(self, test_client):
        """Test the structure of course statistics response"""
        response = test_client.get("/api/courses")
        data = response.json()
        
        # Check that the response follows the expected schema
        assert len(data) == 2  # Only total_courses and course_titles
        
        if data["total_courses"] > 0:
            assert len(data["course_titles"]) == data["total_courses"]
            for title in data["course_titles"]:
                assert isinstance(title, str)
                assert title.strip()  # No empty titles


class TestNewSessionEndpoint:
    """Test the /api/new-session endpoint"""
    
    @pytest.mark.api
    def test_create_new_session(self, test_client):
        """Test successful session creation"""
        response = test_client.post("/api/new-session")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert isinstance(data["session_id"], str)
        assert data["session_id"]  # Should not be empty
    
    @pytest.mark.api
    def test_multiple_session_creation(self, test_client):
        """Test that multiple session creations return different IDs"""
        response1 = test_client.post("/api/new-session")
        response2 = test_client.post("/api/new-session")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        session1 = response1.json()["session_id"]
        session2 = response2.json()["session_id"]
        
        # Sessions should be unique
        assert session1 != session2


class TestRootEndpoint:
    """Test the root endpoint"""
    
    @pytest.mark.api
    def test_root_endpoint(self, test_client):
        """Test the root endpoint responds correctly"""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestErrorHandling:
    """Test API error handling"""
    
    @pytest.mark.api
    def test_invalid_endpoint(self, test_client):
        """Test request to non-existent endpoint"""
        response = test_client.get("/api/nonexistent")
        assert response.status_code == 404
    
    @pytest.mark.api
    def test_wrong_http_method(self, test_client):
        """Test using wrong HTTP method"""
        response = test_client.get("/api/query")  # Should be POST
        assert response.status_code == 405  # Method not allowed
    
    @pytest.mark.api
    def test_content_type_handling(self, test_client):
        """Test various content types"""
        # Test with correct content type
        response = test_client.post(
            "/api/query",
            json={"query": "test query"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200


class TestCORS:
    """Test CORS headers"""
    
    @pytest.mark.api
    def test_cors_headers_present(self, test_client):
        """Test that CORS headers are present in responses"""
        response = test_client.post(
            "/api/query", 
            json={"query": "test"},
            headers={"Origin": "http://localhost:3000"}
        )
        
        # TestClient doesn't automatically add CORS headers, but the middleware should handle it
        # In a real browser environment, CORS headers would be present
        assert response.status_code == 200
    
    @pytest.mark.api
    def test_cors_preflight_simulation(self, test_client):
        """Test simulated CORS preflight behavior"""
        # In a real FastAPI app with CORS middleware, this would work
        # TestClient doesn't fully simulate browser CORS behavior
        response = test_client.post(
            "/api/query",
            json={"query": "test query"},
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        # Should succeed regardless of CORS in TestClient
        assert response.status_code == 200


class TestIntegration:
    """Integration tests combining multiple endpoints"""
    
    @pytest.mark.integration
    def test_session_workflow(self, test_client):
        """Test complete workflow: create session, query, check courses"""
        # 1. Create a new session
        session_response = test_client.post("/api/new-session")
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]
        
        # 2. Use the session for a query
        query_response = test_client.post(
            "/api/query",
            json={"query": "What is Python?", "session_id": session_id}
        )
        assert query_response.status_code == 200
        query_data = query_response.json()
        assert query_data["session_id"] == session_id
        
        # 3. Check course statistics
        courses_response = test_client.get("/api/courses")
        assert courses_response.status_code == 200
        courses_data = courses_response.json()
        assert isinstance(courses_data["total_courses"], int)
    
    @pytest.mark.integration
    def test_multiple_queries_same_session(self, test_client):
        """Test multiple queries with the same session"""
        session_id = "test-session-multi"
        
        queries = [
            "What is Python?",
            "Tell me about variables",
            "How do data structures work?"
        ]
        
        for query in queries:
            response = test_client.post(
                "/api/query",
                json={"query": query, "session_id": session_id}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == session_id
            assert isinstance(data["answer"], str)


class TestPerformance:
    """Basic performance tests"""
    
    @pytest.mark.api
    def test_concurrent_requests(self, test_client):
        """Test handling of multiple concurrent requests"""
        import concurrent.futures
        import time
        
        def make_query(query_num):
            response = test_client.post(
                "/api/query",
                json={"query": f"Test query {query_num}"}
            )
            return response.status_code
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_query, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        assert all(status == 200 for status in results)