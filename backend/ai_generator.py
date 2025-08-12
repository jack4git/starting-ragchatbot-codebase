import anthropic
from typing import List, Optional, Dict, Any, Tuple

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""
    
    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to comprehensive search and outline tools for course information.

Tool Usage:  
- **Content Search Tool**: Use for questions about specific course content or detailed educational materials 
- **Outline Tool**: Use for questions about course structure, lesson lists, course overview, or table of contents
- **Sequential tool calling**: You can use tools across multiple rounds (maximum 2 rounds total)
- **Tool chaining**: Use information from previous tool calls to inform subsequent searches
- **Focused searches**: Break complex queries into targeted tool calls when beneficial
- Synthesize tool results into accurate, fact-based responses
- If tool yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without using tools
- **Course content questions**: Use content search tool first, then answer
- **Course outline/structure questions**: Use outline tool to get course title, link, and complete lesson list
- **Complex queries**: Consider using multiple focused searches across rounds
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, tool explanations, or question-type analysis
 - Do not mention "based on the search results" or "based on the outline"
 - Do not explain your tool usage strategy

Sequential Search Strategy:
- Round 1: Broad search to understand available content
- Round 2: Focused search based on Round 1 findings (if needed)
- Always aim to provide comprehensive answers using available information

For outline queries, ensure responses include:
- Course title
- Course link
- Complete lesson list with lesson numbers and titles
- Lesson links when available

All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""
    
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        
        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None,
                         max_rounds: int = 2) -> str:
        """
        Generate AI response with optional tool usage and conversation context.
        
        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            max_rounds: Maximum tool calling rounds (default: 2)
            
        Returns:
            Generated response as string
        """
        
        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history 
            else self.SYSTEM_PROMPT
        )
        
        # Initialize message conversation
        messages = [{"role": "user", "content": query}]
        
        # Sequential tool calling loop
        for round_num in range(max_rounds):
            # Prepare API call parameters
            api_params = {
                **self.base_params,
                "messages": messages,
                "system": system_content
            }
            
            # Add tools if available
            if tools and tool_manager:
                api_params["tools"] = tools
                api_params["tool_choice"] = {"type": "auto"}
            
            try:
                # Get response from Claude
                response = self.client.messages.create(**api_params)
                
                # Check if Claude wants to use tools
                if response.stop_reason == "tool_use" and tool_manager:
                    # Execute tools and accumulate conversation
                    messages, tool_execution_success = self._execute_tools_round(
                        response, messages, tool_manager, round_num + 1
                    )
                    
                    # If tool execution failed, break the loop
                    if not tool_execution_success:
                        break
                        
                    # Continue to next round if under limit
                    continue
                else:
                    # No tool use - return the response
                    return response.content[0].text
                    
            except Exception as e:
                return f"Error in round {round_num + 1}: {str(e)}"
        
        # If we exit the loop, make final call without tools to get response
        return self._get_final_response(messages, system_content)
    
    def _execute_tools_round(self, response, messages: List[Dict], tool_manager, round_num: int) -> Tuple[List[Dict], bool]:
        """
        Execute tools for a single round and accumulate messages.
        
        Args:
            response: Claude response containing tool use
            messages: Current conversation messages
            tool_manager: Tool execution manager
            round_num: Current round number (for logging)
            
        Returns:
            Tuple of (updated_messages, success_flag)
        """
        # Add Claude's tool use response to conversation
        messages.append({"role": "assistant", "content": response.content})
        
        # Execute all tool calls and collect results
        tool_results = []
        execution_success = True
        
        for content_block in response.content:
            if content_block.type == "tool_use":
                try:
                    tool_result = tool_manager.execute_tool(
                        content_block.name, 
                        **content_block.input
                    )
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": tool_result
                    })
                except Exception as e:
                    # Handle tool execution errors gracefully
                    error_msg = f"Tool execution failed in round {round_num}: {str(e)}"
                    tool_results.append({
                        "type": "tool_result", 
                        "tool_use_id": content_block.id,
                        "content": error_msg
                    })
                    execution_success = False
        
        # Add tool results to conversation
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        
        return messages, execution_success
    
    def _get_final_response(self, messages: List[Dict], system_content: str) -> str:
        """
        Get final response without tools after completing all rounds.
        
        Args:
            messages: Complete conversation messages
            system_content: System prompt content
            
        Returns:
            Final response text
        """
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": system_content
            # Note: No tools parameter - forces final response
        }
        
        try:
            final_response = self.client.messages.create(**final_params)
            return final_response.content[0].text
        except Exception as e:
            return f"Error generating final response: {str(e)}"