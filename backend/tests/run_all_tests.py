"""
Master test runner to identify RAG system failures
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_course_search_tool import run_course_search_tests
from test_ai_generator import run_ai_generator_tests
from test_rag_system import run_rag_system_tests


def main():
    """Run all tests to identify failing components"""
    print("*" * 80)
    print("RAG SYSTEM DIAGNOSTIC TEST SUITE")
    print("*" * 80)
    print("This test suite will help identify why content queries are failing.")
    print()

    try:
        # 1. Test CourseSearchTool
        print("STEP 1: Testing CourseSearchTool components...")
        run_course_search_tests()
        print("\n" + "=" * 60 + "\n")

        # 2. Test AI Generator
        print("STEP 2: Testing AI Generator components...")
        run_ai_generator_tests()
        print("\n" + "=" * 60 + "\n")

        # 3. Test RAG System Integration
        print("STEP 3: Testing RAG System integration...")
        run_rag_system_tests()

    except Exception as e:
        print(f"Test suite execution failed: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "*" * 80)
    print("TEST SUITE COMPLETE")
    print("*" * 80)
    print("Review the output above to identify which components are failing.")
    print("Look for:")
    print("- Vector store data availability issues")
    print("- Search result errors")
    print("- Tool execution failures")
    print("- API communication problems")


if __name__ == "__main__":
    main()
