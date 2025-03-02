"""
Service for interacting with Vinted API through the vinted_scraper wrapper.
"""
from vinted_scraper import VintedWrapper

from config.settings import VINTED_BASE_URL, DEFAULT_USER_AGENT


class VintedService:
    """Service class for fetching items from Vinted."""

    def __init__(self, base_url=VINTED_BASE_URL, user_agent=DEFAULT_USER_AGENT):
        """
        Initialize the Vinted service.

        Args:
            base_url: The base URL for Vinted (default: https://www.vinted.it)
            user_agent: The user agent to use for requests
        """
        self.wrapper = VintedWrapper(base_url, agent=user_agent)

    def search_items(self, search_text, max_items=5):
        """
        Search for items on Vinted.

        Args:
            search_text: The text to search for
            max_items: Maximum number of items to return

        Returns:
            A list of detailed item information
        """
        # Set search parameters
        params = {
            "search_text": search_text
        }

        # Perform the search
        search_results = self.wrapper.search(params)

        # Check if items were found
        if not search_results.get("items"):
            print("No items found!")
            return []

        # Limit the number of items to process
        items = search_results["items"][:max_items]

        # Fetch detailed information for each item
        detailed_items = []
        for item in items:
            item_id = item["id"]
            item_details = self.wrapper.item(item_id)
            detailed_items.append(item_details)

        return detailed_items

    def get_item_url(self, item_url):
        """
        Get the full URL for an item.

        Args:
            item_url: The item URL from the API

        Returns:
            The full URL to the item on Vinted
        """
        if item_url and not item_url.startswith('http'):
            return f"https://www.vinted.it{item_url}"
        return item_url