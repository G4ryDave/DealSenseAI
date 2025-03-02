"""
Agent definition for the Deal Message Agent that crafts negotiation messages.
This agent creates personalized messages for marketplace negotiations based on item data and market research.
"""
import json
import os

from crewai import Agent, Task, Crew
from crewai import LLM
from dotenv import load_dotenv

from models.deal_models import DealMessageResult

load_dotenv()

def create_deal_specialist(llm_instance=None):
    """
    Create an agent specialized in crafting deal messages.

    Args:
        llm_instance: Optional LLM instance to use

    Returns:
        Agent: The configured deal message specialist agent
    """
    if not llm_instance:
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        llm_instance = LLM(
            model='gemini/gemini-2.0-flash',
            api_key=gemini_api_key
        )

    agent_config = {
        "role": "Deal Message Specialist",
        "goal": "Craft engaging, platform-appropriate messages for aggressive deal negotiations",
        "backstory": """You are an expert in online marketplace communication and 
        deal-making with a focus on securing the best possible prices. You understand 
        the psychology of online selling and how to craft messages that are effective 
        while still maintaining respect. You know that on platforms like Vinted, 
        a confident tone works well, and sellers often expect negotiation. You're skilled 
        at identifying value gaps and leveraging market data to justify lower offers. 
        You understand how to interpret market confidence metrics to make appropriately 
        aggressive offers without alienating sellers."""
    }

    return Agent(
        config=agent_config,
        llm=llm_instance
    )

def create_deal_message_task(agent, item_data=None, market_data=None):
    """
    Create a deal message task for the given agent.

    Args:
        agent: The agent that will perform the task
        item_data: Optional item data to use for message creation
        market_data: Optional market research data to inform the message

    Returns:
        Task: The configured deal message task
    """
    task_config = {
        "description": """
        Craft a persuasive message for negotiating an aggressive deal on this item: {item_data}
        
        Market research information: {market_data}
        
        Follow these steps:
        1. Analyze the item details (title, price, condition, etc.)
        2. Consider the market research data (average price, deal score, etc.)
        3. Determine an appropriate offer price based on market value and price listed. The price should be 15-25% lower than the current price, depending on market conditions and item condition.
        4. Craft a friendly but confident message of 2-3 sentences using a concise tone (consider you are in the Vinted platform) that:
           - Expresses interest in the item
           - Makes a bold but justifiable offer based on market data
           - Provides a specific justification for the lower offer (condition issues, market comparisons, etc.)
           - Maintains a positive tone while being direct about price expectations
           - Ends with a call to action that creates urgency

        
        """,
        "expected_output": "A persuasive, confident message for negotiating an aggressive deal"
    }

    return Task(
        config=task_config,
        agent=agent,
        output_pydantic=DealMessageResult
    )

def create_deal_message_crew(agent, task):
    """
    Create a crew with the given agent and task.

    Args:
        agent: The agent to include in the crew
        task: The task to include in the crew

    Returns:
        Crew: The configured deal message crew
    """
    return Crew(
        agents=[agent],
        tasks=[task],
        verbose=False
    )

def generate_deal_message(item_data, market_data=None, llm_instance=None):
    """
    Generate a deal message for a single item.

    Args:
        item_data: The item data to use for message creation
        market_data: Optional market research data to inform the message
        llm_instance: Optional LLM instance to use

    Returns:
        The deal message result from the crew
    """
    specialist = create_deal_specialist(llm_instance)
    task = create_deal_message_task(specialist)
    crew = create_deal_message_crew(specialist, task)

    # Format the data for the task
    formatted_data = {
        "item_data": json.dumps(item_data, indent=2),
        "market_data": json.dumps(market_data, indent=2) if market_data else "{}"
    }

    return crew.kickoff(formatted_data)