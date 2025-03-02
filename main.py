"""
Main application script for the Vinted Analyzer.
This script orchestrates the entire analysis process.
"""

import argparse
import json
import os
import sys
import time

import colorama
from crewai import Flow
from crewai import LLM
from crewai.flow.flow import listen, start
from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table

from agents.deal_message_agent import create_deal_specialist, create_deal_message_task, create_deal_message_crew
from agents.item_analyst import create_item_analyst, create_item_analysis_task, create_item_analysis_crew
from agents.market_research_agent import create_market_researcher, create_market_research_task, \
    create_market_research_crew
from config.settings import DEFAULT_SEARCH_TEXT, DEFAULT_MAX_ITEMS, VINTED_BASE_URL
from services.report_service import ReportService
from services.vinted_service import VintedService
from utils.browser_utils import open_html_report

# Initialize colorama for cross-platform colored terminal output
colorama.init()


class SecondHandItemAnalysisPipeline(Flow):
    """Flow for analyzing second-hand items from Vinted."""

    def __init__(self, search_text=DEFAULT_SEARCH_TEXT, max_items=DEFAULT_MAX_ITEMS, max_searches=1,
                 search_site="amazon", vinted_base_url=VINTED_BASE_URL):
        """
        Initialize the analysis pipeline.

        Args:
            search_text: The search query to use on Vinted
            max_items: Maximum number of items to analyze
            max_searches: Maximum number of searches to perform per item (default: 1)
            search_site: Site to focus search on (default: "amazon")
            vinted_base_url: Base URL for Vinted (default: https://www.vinted.it)
        """
        super().__init__()
        self.search_text = search_text
        self.max_items = max_items
        self.max_searches = max_searches
        self.search_site = search_site
        self.vinted_base_url = vinted_base_url
        self.results = []
        self.raw_items = []  # Store the raw item data for HTML generation
        self.market_research_results = []  # Store market research results
        self.deal_messages = {}  # Store deal messages for each item
        self.vinted_service = VintedService(base_url=vinted_base_url)
        self.report_service = ReportService()

    @start()
    def fetch_items_from_vinted(self):
        """Fetch items from Vinted using the vinted_scraper."""
        print("1- Fetching items from Vinted")

        # Use the VintedService to search for items
        detailed_items = self.vinted_service.search_items(
            self.search_text,
            self.max_items
        )

        # Store raw item data for later use
        self.raw_items = detailed_items

        return detailed_items

    @listen(fetch_items_from_vinted)
    def research_market_values(self, items):
        """Research market values for each item using the Market Research agent."""
        print(f"2- Researching market values for {len(items)} items")

        market_research_results = []

        # Create agent, task, and crew for market research
        researcher = create_market_researcher(llm)
        task = create_market_research_task(
            researcher,
            max_searches=self.max_searches,
            search_site=self.search_site
        )
        crew = create_market_research_crew(researcher, task)

        for i, item in enumerate(items):
            print(f"  Researching market value for item {i + 1}/{len(items)} (ID: {item.get('id', 'unknown')})")

            # Format the item data for the market research task
            # Convert ID to string to avoid Pydantic validation errors
            if 'id' in item and not isinstance(item['id'], str):
                item_copy = item.copy()
                item_copy['id'] = str(item_copy['id'])
                formatted_data = {"item_data": json.dumps(item_copy, indent=2)}
            else:
                formatted_data = {"item_data": json.dumps(item, indent=2)}

            # Research the current item's market value
            try:
                research_result = crew.kickoff(formatted_data)
                market_research_results.append(research_result)
            except Exception as e:
                print(f"Error researching market value for item {i + 1}: {str(e)}")
                # Create a minimal research result to avoid breaking the pipeline
                minimal_result = {
                    "item_id": str(item.get('id', f"unknown-{i}")),
                    "average_price": 0.0,
                    "price_range": [0.0, 0.0],
                    "comparable_items": [],
                    "value_assessment": "Could not determine due to error",
                    "market_demand": "Unknown",
                    "price_factors": ["Error during research"],
                    "confidence_score": 1,
                    "notes": f"Error during market research: {str(e)}"
                }
                market_research_results.append(minimal_result)

        # Store market research results for later use
        self.market_research_results = market_research_results

        # Return both the original items and their market research results
        return items, market_research_results

    @listen(research_market_values)
    def analyze_items(self, data):
        """
        Analyze each item individually using the AI crew, incorporating market research.

        Args:
            data: Tuple containing (items, market_research_results)
        """
        items, market_research_results = data
        print(f"3- Analyzing {len(items)} items with market research data")

        all_results = []

        # Create agent, task, and crew for item analysis
        analyst = create_item_analyst(llm)
        task = create_item_analysis_task(analyst)
        crew = create_item_analysis_crew(analyst, task)

        for i, (item, research) in enumerate(zip(items, market_research_results)):
            print(f"  Analyzing item {i + 1}/{len(items)} (ID: {item.get('id', 'unknown')})")

            # Combine item data with market research for more informed analysis
            # Use model_dump with exclude_defaults for Pydantic v2 compatibility to remove any unwanted default keys
            enhanced_item_data = {
                "item_data": item,
                "market_research": research if isinstance(research, dict) else
                (research.pydantic.model_dump(exclude_defaults=True) if hasattr(research, 'pydantic') else research)
            }

            # Convert the enhanced data to a JSON string
            formatted_data = {"item_data": json.dumps(enhanced_item_data, indent=2)}

            # Analyze the current item with market research context
            try:
                analysis_result = crew.kickoff(formatted_data)
                all_results.append(analysis_result)
            except Exception as e:
                print(f"Error analyzing item {i + 1}: {str(e)}")
                # Continue with next item

        return all_results

    @listen(analyze_items)
    def generate_deal_messages(self, analysis_results):
        """
        Generate deal messages for each analyzed item.

        Args:
            analysis_results: List of CrewOutput objects containing item analysis results

        Returns:
            The analysis results to pass to the next step
        """
        print("4- Generating deal messages")

        if not analysis_results:
            return analysis_results

        # Create agent, task, and crew for deal message generation
        specialist = create_deal_specialist(llm)
        task = create_deal_message_task(specialist)
        crew = create_deal_message_crew(specialist, task)

        for i, result in enumerate(analysis_results):
            if not hasattr(result, 'pydantic'):
                continue

            item_data = result.pydantic
            item_id = item_data.item_id

            # Find the corresponding raw item data
            raw_item = next((item for item in self.raw_items if str(item.get('id', '')) == str(item_id)), {})

            # Extract price information properly
            price = None
            if 'price' in raw_item:
                if isinstance(raw_item['price'], dict) and 'amount' in raw_item['price']:
                    price = raw_item['price']['amount']
                else:
                    price = raw_item['price']

            # Find the corresponding market research data
            market_research = None
            for research in self.market_research_results:
                research_item_id = None
                if hasattr(research, 'pydantic'):
                    research_item_id = research.pydantic.item_id
                elif isinstance(research, dict) and 'item_id' in research:
                    research_item_id = research['item_id']

                if research_item_id and str(research_item_id) == str(item_id):
                    market_research = research
                    break

            # Extract market research data
            market_data = {}
            if market_research:
                if hasattr(market_research, 'pydantic'):
                    market_data = market_research.pydantic.model_dump(exclude_defaults=True)
                elif hasattr(market_research, 'dict'):
                    market_data = market_research.dict()
                elif hasattr(market_research, 'model_dump'):
                    market_data = market_research.model_dump()
                else:
                    market_data = market_research

            # Prepare item data for deal message generation with all available information
            item_info = {
                'id': item_id,
                'title': item_data.title,
                'price': item_data.price,
                'status': item_data.status,
                'seller_rating': raw_item.get('user_rating', raw_item.get('seller_rating', 'Unknown')),
                'analysis_score': item_data.score,
                'analysis_notes': item_data.notes
            }

            # Generate deal message
            try:
                print(f"  Generating deal message for item {i + 1} (ID: {item_id})")

                # Format the data for the deal message task
                formatted_data = {
                    "item_data": json.dumps(item_info, indent=2),
                    "market_data": json.dumps(market_data, indent=2)
                }

                # Generate the deal message using the crew
                deal_message_result = crew.kickoff(formatted_data)

                if deal_message_result:
                    self.deal_messages[item_id] = deal_message_result
            except Exception as e:
                print(f"Error generating deal message for item {i + 1}: {str(e)}")

        return analysis_results

    @listen(generate_deal_messages)
    def prepare_recommendations(self, analysis_results):
        """
        Prepare recommendations based on the analysis results.

        Args:
            analysis_results: List of CrewOutput objects containing item analysis results

        Returns:
            A formatted string with recommendations
        """
        print("5- Preparing recommendations")

        if not analysis_results:
            return "No analysis results available to prepare recommendations."

        sorted_results = sorted(
            analysis_results,
            key=lambda x: x.pydantic.score if hasattr(x, 'pydantic') else 0,
            reverse=True
        )

        recommendations = "# Recommended Items\n\n"

        for i, result in enumerate(sorted_results[:3], 1):
            if hasattr(result, 'pydantic'):
                item_data = result.pydantic
                recommendations += f"## {i}. Item ID: {item_data.item_id}\n"
                recommendations += f"**Score: {item_data.score}/100**\n\n"
                recommendations += f"{item_data.notes}\n\n"
                recommendations += "---\n\n"

        # Generate HTML report and open it
        try:
            report_file = self.report_service.generate_html_report(
                self.search_text,
                self.raw_items,
                sorted_results,
                market_research=self.market_research_results,
                deal_messages=self.deal_messages
            )
            if report_file:
                open_html_report(report_file)
        except Exception as e:
            print(f"Error generating/opening HTML report: {str(e)}")

        return recommendations


def display_welcome_screen():
    """Display a beautiful welcome screen for the application."""
    console = Console()

    # Clear the screen
    os.system('cls' if os.name == 'nt' else 'clear')

    # Display welcome banner
    console.print(Panel.fit(
        "[bold magenta]DealSenseAI[/bold magenta]\n"
        "[italic]Find the best second-hand deals with AI-powered analysis[/italic]",
        box=box.DOUBLE,
        border_style="magenta",  # Changed to a supported color name
        padding=(1, 4)
    ))

    # Display app description
    console.print("\n[bold cyan]What this tool does:[/bold cyan]")

    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    table.add_column("Step", style="bright_yellow")
    table.add_column("Description", style="white")

    table.add_row("1️⃣", "Searches Vinted for items matching your query")
    table.add_row("2️⃣", "Researches market values for each item")
    table.add_row("3️⃣", "Analyzes each item for potential bargains")
    table.add_row("4️⃣", "Generates deal messages to help you negotiate")
    table.add_row("5️⃣", "Creates an interactive HTML report with all findings")

    console.print(table)
    console.print()


def get_user_preferences():
    """Get user preferences for the search in a beautiful way."""
    console = Console()

    # Get search query
    console.print("\n[bold green]What are you looking for today?[/bold green]")
    console.print("[dim](e.g., iphone, nike shoes, vintage dress)[/dim]")
    search_text = Prompt.ask("Enter search query", default="iphone")

    # Get number of items
    console.print("\n[bold green]How many items would you like to analyze?[/bold green]")
    console.print("[dim](More items = more comprehensive results but takes longer)[/dim]")
    max_items = IntPrompt.ask("Number of items", default=3, show_default=True)

    # Get number of searches per item
    console.print("\n[bold green]How many market searches per item?[/bold green]")
    console.print("[dim](More searches = better price accuracy but takes longer)[/dim]")
    max_searches = IntPrompt.ask("Number of searches", default=1, show_default=True)

    # Get search site preference
    console.print("\n[bold green]Which marketplace should we focus on for price comparison?[/bold green]")
    sites = ["amazon", "ebay", "all"]

    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    table.add_column("Option", style="bright_yellow")
    table.add_column("Site", style="white")

    for i, site in enumerate(sites, 1):
        table.add_row(f"{i}", site)

    console.print(table)
    site_choice = IntPrompt.ask("Enter option number", default=1, show_default=True)
    search_site = sites[site_choice - 1] if 1 <= site_choice <= len(sites) else "amazon"

    return {
        "search_text": search_text,
        "max_items": max_items,
        "max_searches": max_searches,
        "search_site": search_site
    }


def show_progress(message, duration=3):
    """Show a spinner with a message for the given duration."""
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        task = progress.add_task(f"[cyan]{message}...", total=100)
        for _ in range(duration * 10):
            progress.update(task, advance=10 / duration)
            time.sleep(0.1)


def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Vinted Bargain Hunter - Find the best second-hand deals")
    parser.add_argument("--search", type=str, help="Search query")
    parser.add_argument("--items", type=int, help="Maximum number of items to analyze")
    parser.add_argument("--searches", type=int, help="Maximum number of searches per item")
    parser.add_argument("--site", type=str, choices=["amazon", "ebay", "all"], help="Site to focus search on")
    parser.add_argument("--quick", action="store_true",
                        help="Skip the interactive UI and use defaults or provided args")

    args = parser.parse_args()

    # If quick mode is not enabled, show the interactive UI
    if not args.quick:
        display_welcome_screen()
        preferences = get_user_preferences()
    else:
        # Use command line arguments or defaults
        preferences = {
            "search_text": args.search or DEFAULT_SEARCH_TEXT,
            "max_items": args.items or DEFAULT_MAX_ITEMS,
            "max_searches": args.searches or 1,
            "search_site": args.site or "amazon"
        }

    # Show a summary of the search parameters
    console = Console()
    console.print("\n[bold]Search Parameters:[/bold]")
    console.print(f"🔍 Query: [yellow]{preferences['search_text']}[/yellow]")
    console.print(f"📊 Items to analyze: [yellow]{preferences['max_items']}[/yellow]")
    console.print(f"🔄 Searches per item: [yellow]{preferences['max_searches']}[/yellow]")
    console.print(f"🛒 Target marketplace: [yellow]{preferences['search_site']}[/yellow]")

    # Confirm and start
    if not args.quick:
        if not Confirm.ask("\nStart analysis?", default=True):
            console.print("[yellow]Analysis cancelled.[/yellow]")
            return

    # Show a loading animation
    console.print("\n[bold green]Starting analysis...[/bold green]")
    show_progress("Initializing AI agents", 2)

    # Create and run the analysis pipeline
    try:
        flow = SecondHandItemAnalysisPipeline(
            search_text=preferences["search_text"],
            max_items=preferences["max_items"],
            max_searches=preferences["max_searches"],
            search_site=preferences["search_site"]
        )

        # Run the pipeline
        results = flow.kickoff()

        # Show completion message
        console.print("\n[bold green]✅ Analysis complete![/bold green]")
        console.print("[italic]An HTML report has been generated and should open in your browser.[/italic]")

        # Print the text results as well
        console.print("\n[bold]Top Recommendations:[/bold]")
        console.print(Panel(results, border_style="green"))

    except Exception as e:
        console.print(f"\n[bold red]Error during analysis:[/bold red] {str(e)}")
        return 1

    return 0


# Run the application
if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    # Initialize LLM
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    # Initialize the LLM
    llm = LLM(
        model='gemini/gemini-2.0-flash',
        api_key=gemini_api_key
    )

    # Run the main function
    sys.exit(main())
