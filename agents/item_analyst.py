"""
Agent definition for the Item Analyst that evaluates second-hand items.
"""
import json
import os

from crewai import Agent, Task, Crew
from crewai import LLM

from models.item_models import ItemAnalysisResult


def create_item_analyst(llm_instance=None):
    """
    Create and return an Item Analyst agent.

    Args:
        llm_instance: Optional LLM instance to use for the agent

    Returns:
        Agent: The configured Item Analyst agent
    """
    # If no LLM instance is provided, create one using environment variables
    if not llm_instance:
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        llm_instance = LLM(
            model='gemini/gemini-2.0-flash',
            api_key=gemini_api_key
        )

    # Configuration for the agent
    agent_config = {
        "role": "Second-Hand Item Analyst",
        "goal": "Analyze and evaluate second-hand items for bargain potential and value estimation. The score should be on a scale between 0 and 100.",
        "backstory": "You are an experienced analyst who helps buyers identify the most promising second-hand items and estimate their true value."
    }

    # Create and return the agent
    return Agent(
        config=agent_config,
        llm=llm_instance
    )


def create_item_analysis_task(agent, item_data=None):
    """
    Create an item analysis task for the given agent.

    Args:
        agent: The agent that will perform the task
        item_data: Optional item data to analyze

    Returns:
        Task: The configured item analysis task
    """
    # Task configuration with placeholder for item data
    task_config = {
        "description": "Analyze the following second-hand item data and provide a score and recommendations: {item_data}",
        "expected_output": "A comprehensive item analysis with scoring and value estimation. A clear explanation of why you gave that score. The score should be on a scale between 0 and 100."
    }

    # Create and return the task
    return Task(
        config=task_config,
        agent=agent,
        output_pydantic=ItemAnalysisResult
    )


def create_item_analysis_crew(agent, task):
    """
    Create a crew with the given agent and task.

    Args:
        agent: The agent to include in the crew
        task: The task to include in the crew

    Returns:
        Crew: The configured item analysis crew
    """
    return Crew(
        agents=[agent],
        tasks=[task],
        verbose=False
    )


def analyze_item(item_data, llm_instance=None):
    """
    Analyze a single item using the Item Analyst agent.

    Args:
        item_data: The item data to analyze
        llm_instance: Optional LLM instance to use

    Returns:
        The analysis result from the crew
    """
    # Create agent, task, and crew
    analyst = create_item_analyst(llm_instance)
    task = create_item_analysis_task(analyst)
    crew = create_item_analysis_crew(analyst, task)

    # Format the item data for the task
    formatted_data = {"item_data": json.dumps(item_data, indent=2)}

    # Analyze the item and return the result
    return crew.kickoff(formatted_data)