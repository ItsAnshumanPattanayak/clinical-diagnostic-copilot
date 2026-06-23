"""
Agent State Definition
======================
Defines the TypedDict structure that flows through the LangGraph workflow.

This is crucial for:
- Type safety across agent transitions
- Tracking conversation history
- Maintaining intermediate results
- Debugging agent behavior
"""

from typing import TypedDict, List, Dict, Optional, Annotated
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """
    The complete state object that gets passed between agents.
    
    Think of this as a shared whiteboard that all agents can read/write to.
    LangGraph automatically manages state transitions.
    
    Attributes:
        messages: Conversation history (chat-style interface)
        image_data: Raw bytes of uploaded medical image
        image_filename: Original filename for reference
        vision_results: Output from Vision Agent (diagnosis predictions)
        research_results: Output from Research Agent (literature context)
        final_report: Output from Supervisor Agent (synthesized recommendation)
        current_agent: Which agent is currently processing
        error: Any error that occurred during processing
    """
    
    # Conversation messages (uses LangChain message format)
    # The add_messages annotation tells LangGraph to append new messages
    # instead of replacing the whole list
    messages: Annotated[List[Dict], add_messages]
    
    # Image data from user upload
    image_data: Optional[bytes]
    image_filename: Optional[str]
    
    # Results from Vision Agent
    vision_results: Optional[Dict]
    
    # Results from Research Agent
    research_results: Optional[Dict]
    
    # Final synthesized report from Supervisor
    final_report: Optional[str]
    
    # Workflow control
    current_agent: Optional[str]
    
    # Error handling
    error: Optional[str]


class Message(TypedDict):
    """
    Individual message structure (follows LangChain convention).
    
    Attributes:
        role: 'user', 'assistant', or 'system'
        content: The actual message text
    """
    role: str  # 'user', 'assistant', or 'system'
    content: str