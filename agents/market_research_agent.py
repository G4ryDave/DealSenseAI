"""
Agent definition for the Market Research Agent that searches for item market values.
This agent uses SerperDevTool to find pricing information for second-hand items.
"""
import json
import os

from crewai import Agent, Task, Crew
from crewai import LLM
from crewai_tools import SerperDevTool
from dotenv import load_dotenv

from models.market_models import MarketValueResult

load_dotenv()
# Retrieve the SERPER_API_KEY value
serper_api_key = os.getenv('SERPER_API_KEY')
if serper_api_key:
    os.environ["SERPER_API_KEY"] = serper_api_key
else:
    print("Warning: SERPER_API_KEY not found in environment variables")

def calculate_deal_score(listing_price, market_avg_price):
    """
    Calculate a deal score based on price comparison.

    Args:
        listing_price: Current listing price
        market_avg_price: Average market price

    Returns:
        int: Score from 1-100 where:
        80-100: Excellent deal (≤40% of market price)
        60-79: Good deal (41-60% of market price)
        40-59: Fair price (61-90% of market price)
        20-39: Above market (91-120% of market price)
        1-19: Significantly overpriced (>120% of market price)
    """
    price_ratio = (listing_price / market_avg_price) * 100

    if price_ratio <= 40:
        # 80-100 range for excellent deals
        return 100 if price_ratio <= 30 else 80
    elif price_ratio <= 60:
        # 60-79 range for good deals
        return 79 if price_ratio <= 50 else 60
    elif price_ratio <= 90:
        # 40-59 range for fair prices
        return 59 if price_ratio <= 75 else 40
    elif price_ratio <= 120:
        # 20-39 range for above market
        return 39 if price_ratio <= 105 else 20
    else:
        # 1-19 range for significantly overpriced
        return max(1, min(19, int(200 - price_ratio)))

def create_market_researcher(llm_instance=None):
    """
    Create and return a Market Research agent.

    Args:
        llm_instance: Optional LLM instance to use for the agent

    Returns:
        Agent: The configured Market Research agent
    """
    if not llm_instance:
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        llm_instance = LLM(
            model='gemini/gemini-2.0-flash-lite',
            api_key=gemini_api_key
        )

    agent_config = {
        "role": "Market Value Researcher",
        "goal": "Find accurate market values for second-hand items and evaluate deal quality on a scale 0 to 100.",
        "backstory": """You are an expert in determining fair market values for used items. 
        You understand that great deals are typically 40% or less of market value, 
        while items priced above market average should receive low scores."""
    }

    return Agent(
        config=agent_config,
        llm=llm_instance,
        tools=[SerperDevTool()]
    )

def create_market_research_task(agent, item_data=None, max_searches=1, search_site="amazon"):
    """
    Create a market research task for the given agent.

    Args:
        agent: The agent that will perform the task
        item_data: Optional item data to research
        max_searches: Maximum number of searches to perform (default: 1)
        search_site: Site to focus search on (default: "amazon")

    Returns:
        Task: The configured market research task
    """
    task_config = {
        "description": f"""
        Research the current market value for this second-hand item: {{item_data}}

        Follow these steps:
        1. Extract key information like brand, model, specifications, and condition
        2. Search for similar items on {search_site.capitalize()} (limit to {max_searches} search)
        3. Find comparable listings with similar specifications and condition
        4. Calculate the average market price for similar items
        5. Note any factors that might affect the value (rarity, demand, etc.)
        6. Calculate the deal score using these criteria:
           - Score 80-100: Excellent deal (≤40% of market price)
           - Score 60-79: Good deal (41-60% of market price)
           - Score 40-59: Fair price (61-90% of market price)
           - Score 20-39: Above market (91-120% of market price)
           - Score 1-19: Significantly overpriced (>120% of market price)

        Provide a detailed analysis with specific price points and clear scoring justification. The score value should be between 0 and 100.
        """,
        "expected_output": "A comprehensive market value analysis with price comparisons and deal score assessment"
    }

    return Task(
        config=task_config,
        agent=agent,
        output_pydantic=MarketValueResult
    )

def create_market_research_crew(agent, task):
    """
    Create a crew with the given agent and task.

    Args:
        agent: The agent to include in the crew
        task: The task to include in the crew

    Returns:
        Crew: The configured market research crew
    """
    return Crew(
        agents=[agent],
        tasks=[task],
        verbose=False
    )

def research_item_value(item_data, llm_instance=None, max_searches=1, search_site="amazon"):
    """
    Research the market value for a single item.

    Args:
        item_data: The item data to research
        llm_instance: Optional LLM instance to use
        max_searches: Maximum number of searches to perform (default: 1)
        search_site: Site to focus search on (default: "amazon")

    Returns:
        The market research result from the crew
    """
    researcher = create_market_researcher(llm_instance)
    task = create_market_research_task(researcher, max_searches=max_searches, search_site=search_site)
    crew = create_market_research_crew(researcher, task)

    formatted_data = {"item_data": json.dumps(item_data, indent=2)}
    return crew.kickoff(formatted_data)