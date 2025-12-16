"""
LangGraph Review/Critique Agent with feedback loop.

Flow:
  Generator → Validator → (VALID) → END
                       → (INVALID/PARTIAL) → Generator (with feedback)

Logs:
- {task_id}.log        - System logs
- {task_id}_claude.log - Claude Code stream output
"""

import uuid
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END

from repo_agent.claude import call_claude
from repo_agent.utils.system_logger import logger


class AgentState(TypedDict):
    task_id: str
    query: str
    repo_path: str
    answer: str
    validation: str
    validation_status: str  # VALID, INVALID, PARTIAL
    feedback: str
    iteration: int
    max_iterations: int


def generator_node(state: AgentState) -> dict:
    """Generate answer, incorporating feedback if available."""
    task_id = state["task_id"]
    iteration = state.get("iteration", 1)
    feedback = state.get("feedback", "")
    
    logger.log(task_id, f"Generator: Starting (iteration {iteration})")
    
    if feedback:
        # Regenerate with feedback
        prompt = f"""Previous answer was marked as needing improvement.

Feedback: {feedback}

Original question: {state['query']}

Please provide an improved, complete answer addressing the feedback."""
    else:
        # First generation
        prompt = (f"You are a principle engineer who has expertise in understanding code fast and to answer queries. "
                  f"With your expertise please answer this query: {state['query']}")
    
    answer, duration, _ = call_claude(prompt, state["repo_path"], task_id, f"generator_v{iteration}")
    
    logger.log(task_id, f"Generator: Done ({duration:.1f}s)")
    
    return {"answer": answer}


def validator_node(state: AgentState) -> dict:
    """Validate the answer. Returns status: VALID, INVALID, or PARTIAL."""
    task_id = state["task_id"]
    iteration = state.get("iteration", 1)
    
    logger.log(task_id, f"Validator: Starting (iteration {iteration})")
    
    prompt = f"""You are validating an answer about a codebase.

Question: {state['query']}

Answer to validate:
{state['answer']}

Instructions:
1. Check if the answer correctly addresses the question
2. Verify code references are accurate (if any)
3. Check for completeness

Respond with EXACTLY one of these formats:
- "VALID" - if the answer is correct and complete
- "INVALID: <specific issues>" - if there are factual errors
- "PARTIAL: <what's missing>" - if partially correct but incomplete

Start your response with VALID, INVALID, or PARTIAL."""

    validation, duration, _ = call_claude(prompt, state["repo_path"], task_id, f"validator_v{iteration}")
    
    # Parse validation status
    validation_upper = validation.strip().upper()
    if validation_upper.startswith("VALID"):
        status = "VALID"
        feedback = ""
    elif validation_upper.startswith("INVALID"):
        status = "INVALID"
        feedback = validation
    elif validation_upper.startswith("PARTIAL"):
        status = "PARTIAL"
        feedback = validation
    else:
        # Default to VALID if we can't parse
        status = "VALID"
        feedback = ""
    
    logger.log(task_id, f"Validator: {status} ({duration:.1f}s)")
    
    # Increment iteration only if looping back (not VALID)
    next_iteration = iteration + 1 if status != "VALID" else iteration
    
    return {
        "validation": validation,
        "validation_status": status,
        "feedback": feedback,
        "iteration": next_iteration
    }


def should_continue(state: AgentState) -> Literal["generator", "end"]:
    """Decide whether to regenerate or finish."""
    status = state.get("validation_status", "VALID")
    iteration = state.get("iteration", 1)
    max_iter = state.get("max_iterations", 3)
    
    if status == "VALID":
        return "end"
    elif iteration >= max_iter:
        logger.log(state["task_id"], f"Max iterations ({max_iter}) reached, returning best answer")
        return "end"
    else:
        return "generator"


# Build graph with conditional edge
def create_graph():
    graph = StateGraph(AgentState)
    
    graph.add_node("generator", generator_node)
    graph.add_node("validator", validator_node)
    
    graph.add_edge(START, "generator")
    graph.add_edge("generator", "validator")
    
    # Conditional: loop back if invalid/partial, end if valid
    graph.add_conditional_edges(
        "validator",
        should_continue,
        {
            "generator": "generator",
            "end": END
        }
    )
    
    return graph.compile()


review_critique_graph = create_graph()


def run_review_critique(query: str, repo_path: str, task_id: str = None) -> str:
    """Run the review/critique workflow. Returns just the final answer."""
    if task_id is None:
        task_id = str(uuid.uuid4())[:8]
    
    logger.log(task_id, "Workflow: Started", details={"query": query, "repo": repo_path})
    
    try:
        result = review_critique_graph.invoke({
            "task_id": task_id,
            "query": query,
            "repo_path": repo_path,
            "answer": "",
            "validation": "",
            "validation_status": "",
            "feedback": "",
            "iteration": 1,
            "max_iterations": 3
        })
        
        status = result.get("validation_status", "UNKNOWN")
        iterations = result.get("iteration", 1)
        logger.log(task_id, f"Workflow: Completed ({status} after {iterations} iteration(s))")
        
        return result["answer"]
        
    except Exception as e:
        logger.log(task_id, f"Workflow: Failed - {str(e)}", level="ERROR")
        return f"Error: {str(e)}"
