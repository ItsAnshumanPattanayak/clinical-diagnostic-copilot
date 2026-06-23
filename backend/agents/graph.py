"""
LangGraph Multi-Agent Workflow
===============================
Orchestrates three specialized agents:
1. Vision Agent - Analyzes medical images
2. Research Agent - Retrieves relevant literature
3. Supervisor Agent - Synthesizes final diagnostic report

LangGraph provides:
- Automatic state management
- Conditional routing
- Error recovery
- Execution history
"""

from typing import Dict, Literal
from langgraph.graph import StateGraph, END
from agents.state import AgentState, Message
from vision_module import analyze_medical_image
from rag.knowledge_base import search_medical_literature
import json


# ============================================================================
# AGENT NODE FUNCTIONS
# ============================================================================
# Each function represents one "node" in the graph
# They receive the current state and return updated state

def vision_agent(state: AgentState) -> AgentState:
    """
    Vision Agent: Processes medical images and returns diagnostic predictions.
    
    This agent:
    1. Takes the uploaded image from state
    2. Runs it through the vision classifier
    3. Updates state with predictions
    4. Adds a message explaining what it found
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with vision_results populated
    """
    print("🔬 Vision Agent activated")
    
    try:
        # Extract image data from state
        if not state.get("image_data"):
            raise ValueError("No image data provided")
        
        # Run vision analysis
        vision_results = analyze_medical_image(state["image_data"])
        
        # Format findings into a human-readable message
        primary = vision_results["primary_diagnosis"]
        confidence = vision_results["confidence"]
        
        message_content = (
            f"Vision Analysis Complete:\n"
            f"• Primary Finding: {primary}\n"
            f"• Confidence: {confidence:.1%}\n"
            f"• Review Needed: {'Yes' if vision_results['requires_review'] else 'No'}\n\n"
            f"Top 3 Predictions:\n"
        )
        
        for i, pred in enumerate(vision_results["all_predictions"][:3], 1):
            message_content += (
                f"{i}. {pred['condition']}: {pred['confidence']:.1%} "
                f"({pred['severity']})\n"
            )
        
        # Update state
        return {
            **state,
            "vision_results": vision_results,
            "current_agent": "vision",
            "messages": state.get("messages", []) + [{
                "role": "assistant",
                "content": message_content
            }]
        }
        
    except Exception as e:
        print(f"❌ Vision Agent error: {str(e)}")
        return {
            **state,
            "error": f"Vision analysis failed: {str(e)}",
            "current_agent": "vision"
        }


def research_agent(state: AgentState) -> AgentState:
    """
    Research Agent: Retrieves relevant medical literature.
    
    This agent:
    1. Takes the primary diagnosis from Vision Agent
    2. Searches the knowledge base for relevant studies
    3. Extracts key clinical information
    4. Adds contextualized literature to the state
    
    Args:
        state: Current workflow state (must have vision_results)
        
    Returns:
        Updated state with research_results populated
    """
    print("📚 Research Agent activated")
    
    try:
        # Get diagnosis from vision results
        vision_results = state.get("vision_results")
        if not vision_results:
            raise ValueError("No vision results available for research")
        
        primary_diagnosis = vision_results["primary_diagnosis"]
        
        # Search medical literature
        literature = search_medical_literature(primary_diagnosis, top_k=3)
        
        # Compile research summary
        research_summary = f"Literature Review for: {primary_diagnosis}\n\n"
        
        if literature:
            for i, doc in enumerate(literature, 1):
                research_summary += (
                    f"📄 Reference {i}: {doc['title']}\n"
                    f"   Source: {doc['source']}\n"
                    f"   Relevance: {doc.get('search_score', 0):.2f}\n"
                    f"   Summary: {doc['content'][:200]}...\n\n"
                )
        else:
            research_summary += "No directly relevant literature found in knowledge base.\n"
        
        # Package results
        research_results = {
            "query": primary_diagnosis,
            "documents": literature,
            "summary": research_summary
        }
        
        # Update state
        return {
            **state,
            "research_results": research_results,
            "current_agent": "research",
            "messages": state.get("messages", []) + [{
                "role": "assistant",
                "content": research_summary
            }]
        }
        
    except Exception as e:
        print(f"❌ Research Agent error: {str(e)}")
        return {
            **state,
            "error": f"Research failed: {str(e)}",
            "current_agent": "research"
        }


def supervisor_agent(state: AgentState) -> AgentState:
    """
    Supervisor Agent: Synthesizes final diagnostic report.
    
    This agent:
    1. Reviews vision predictions
    2. Integrates research findings
    3. Generates clinical recommendations
    4. Produces a structured final report
    
    This is where you'd integrate an LLM (GPT-4, Claude) for natural language
    generation. For this demo, we use template-based generation.
    
    Args:
        state: Current workflow state (must have vision and research results)
        
    Returns:
        Updated state with final_report populated
    """
    print("🎯 Supervisor Agent activated")
    
    try:
        vision_results = state.get("vision_results")
        research_results = state.get("research_results")
        
        if not vision_results:
            raise ValueError("No vision results to supervise")
        
        # Extract key information
        primary_dx = vision_results["primary_diagnosis"]
        confidence = vision_results["confidence"]
        requires_review = vision_results["requires_review"]
        
        # Build structured report
        report = "=" * 60 + "\n"
        report += "DIAGNOSTIC COPILOT REPORT\n"
        report += "=" * 60 + "\n\n"
        
        # Section 1: Primary Findings
        report += "PRIMARY ASSESSMENT:\n"
        report += f"  Diagnosis: {primary_dx}\n"
        report += f"  Confidence: {confidence:.1%}\n"
        report += f"  Image Quality: {vision_results.get('image_quality', 'unknown')}\n"
        report += f"  Model Version: {vision_results.get('model_version', 'unknown')}\n\n"
        
        # Section 2: Differential Diagnoses
        report += "DIFFERENTIAL DIAGNOSES:\n"
        for i, pred in enumerate(vision_results["all_predictions"][:4], 1):
            report += (
                f"  {i}. {pred['condition']}: {pred['confidence']:.1%} "
                f"(Severity: {pred['severity']})\n"
            )
        report += "\n"
        
        # Section 3: Clinical Context (from research)
        if research_results and research_results.get("documents"):
            report += "CLINICAL CONTEXT:\n"
            doc = research_results["documents"][0]  # Top result
            report += f"  Based on: {doc['title']}\n"
            report += f"  {doc['content'][:250]}...\n\n"
        
        # Section 4: Recommendations
        report += "RECOMMENDATIONS:\n"
        
        if requires_review:
            report += "  ⚠️  HUMAN REVIEW REQUIRED (Confidence < 75%)\n"
            report += "  • Consult with board-certified ophthalmologist\n"
            report += "  • Consider additional imaging (OCT, fluorescein angiography)\n"
        else:
            report += "  ✓ High confidence prediction\n"
            report += "  • Validate with clinical examination\n"
        
        if primary_dx != "Normal (Healthy)":
            report += "  • Recommend patient follow-up within 2 weeks\n"
            report += "  • Review treatment guidelines\n"
        else:
            report += "  • Continue routine screening schedule\n"
        
        report += "\n"
        
        # Section 5: Disclaimers
        report += "IMPORTANT DISCLAIMERS:\n"
        report += "  • This is an AI-assisted diagnostic tool, NOT a replacement for\n"
        report += "    professional medical judgment.\n"
        report += "  • All findings must be validated by licensed healthcare providers.\n"
        report += "  • Do not make treatment decisions based solely on this report.\n"
        report += "\n" + "=" * 60 + "\n"
        
        # Update state with final report
        return {
            **state,
            "final_report": report,
            "current_agent": "supervisor",
            "messages": state.get("messages", []) + [{
                "role": "assistant",
                "content": f"**Final Diagnostic Report**\n\n{report}"
            }]
        }
        
    except Exception as e:
        print(f"❌ Supervisor Agent error: {str(e)}")
        return {
            **state,
            "error": f"Report generation failed: {str(e)}",
            "current_agent": "supervisor"
        }


# ============================================================================
# ROUTING LOGIC
# ============================================================================

def route_after_vision(state: AgentState) -> Literal["research", "end"]:
    """
    Decide where to go after Vision Agent.
    
    If vision analysis succeeded, go to Research Agent.
    If there was an error, end the workflow.
    
    Args:
        state: Current state
        
    Returns:
        Next node name or "end"
    """
    if state.get("error"):
        print("⚠️  Error detected, terminating workflow")
        return "end"
    
    print("✓ Vision successful, routing to Research Agent")
    return "research"


def route_after_research(state: AgentState) -> Literal["supervisor", "end"]:
    """
    Decide where to go after Research Agent.
    
    Args:
        state: Current state
        
    Returns:
        Next node name or "end"
    """
    if state.get("error"):
        print("⚠️  Error detected, terminating workflow")
        return "end"
    
    print("✓ Research successful, routing to Supervisor Agent")
    return "supervisor"


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def create_diagnostic_graph() -> StateGraph:
    """
    Build the LangGraph workflow.
    
    Graph structure:
        START -> Vision Agent -> Research Agent -> Supervisor Agent -> END
        
    Each arrow can have conditional routing based on state.
    
    Returns:
        Compiled LangGraph workflow
    """
    # Initialize graph with our state schema
    workflow = StateGraph(AgentState)
    
    # Add agent nodes
    workflow.add_node("vision", vision_agent)
    workflow.add_node("research", research_agent)
    workflow.add_node("supervisor", supervisor_agent)
    
    # Define entry point
    workflow.set_entry_point("vision")
    
    # Add conditional edges (routing logic)
    workflow.add_conditional_edges(
        "vision",
        route_after_vision,
        {
            "research": "research",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "research",
        route_after_research,
        {
            "supervisor": "supervisor",
            "end": END
        }
    )
    
    # Supervisor always ends the workflow
    workflow.add_edge("supervisor", END)
    
    # Compile the graph
    compiled_graph = workflow.compile()
    
    print("✓ Diagnostic workflow graph compiled successfully")
    return compiled_graph


# Create singleton graph instance
diagnostic_graph = create_diagnostic_graph()