"""
Service for generating HTML reports from item analysis results.
"""
import datetime
import os

import jinja2


class ReportService:
    """Service class for generating reports from analysis results."""

    def __init__(self, template_dir="./templates", output_dir="./output"):
        """
        Initialize the report service.

        Args:
            template_dir: Directory containing the HTML templates
            output_dir: Directory where the HTML reports will be saved
        """
        self.template_dir = template_dir
        self.output_dir = output_dir
        # Ensure the template and output directories exist
        os.makedirs(template_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

    def generate_html_report(self, search_query, raw_items, analysis_results, market_research=None, deal_messages=None):
        """
        Generate an HTML report with item analysis results.

        Args:
            search_query: The search query used to find items
            raw_items: The raw item data from Vinted
            analysis_results: The analysis results from the AI crew
            market_research: Optional market research results
            deal_messages: Optional deal messages for items

        Returns:
            The filename of the generated report
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vinted_analysis_{timestamp}.html"
        file_path = os.path.join(self.output_dir, filename)

        # Create a dictionary mapping item IDs to their data
        item_data_map = self._create_item_data_map(raw_items)

        # Create a dictionary mapping item IDs to their market research data
        market_research_map = {}
        if market_research:
            for research in market_research:
                if hasattr(research, 'pydantic'):
                    item_id = research.pydantic.item_id
                    market_research_map[item_id] = research.pydantic
                elif isinstance(research, dict) and 'item_id' in research:
                    item_id = research['item_id']
                    market_research_map[item_id] = research

        # Prepare data for the template
        template_data = self._prepare_template_data(
            search_query,
            item_data_map,
            analysis_results,
            market_research_map,
            deal_messages
        )

        try:
            # Load the template from file
            template_loader = jinja2.FileSystemLoader(searchpath=self.template_dir)
            template_env = jinja2.Environment(loader=template_loader)
            template = template_env.get_template("vinted_report_template.html")

            # Render the template with our data
            html_content = template.render(**template_data)

            # Write HTML to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"HTML report generated: {file_path}")
            return file_path

        except Exception as e:
            print(f"Error generating HTML report: {e}")
            # Fallback to a simple HTML report if template loading fails
            return self._generate_fallback_html_report(template_data, file_path)

    def _create_item_data_map(self, raw_items):
        """Create a dictionary mapping item IDs to their data."""
        item_data_map = {}
        for item in raw_items:
            # Extract the item data from the nested structure
            if 'item' in item:
                item_data = item['item']
                item_id = item_data.get('id')
                if item_id:
                    item_data_map[str(item_id)] = item_data
            else:
                # If the item is not nested, use it directly
                item_id = item.get('id')
                if item_id:
                    item_data_map[str(item_id)] = item

        return item_data_map

    def _prepare_template_data(self, search_query, item_data_map, analysis_results, market_research_map=None,
                               deal_messages=None):
        """Prepare data for the HTML template."""
        template_data = {
            'search_query': search_query,
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'date': datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S"),
            'items': []
        }

        # Process each analysis result
        for result in analysis_results:
            # Extract item data from the analysis result
            if hasattr(result, 'pydantic'):
                item_data = result.pydantic
                item_id = item_data.item_id
            elif hasattr(result, 'model_dump'):
                item_data = result
                item_id = item_data.item_id
            else:
                # Skip if we can't extract item data
                continue

            # Get the raw item data
            raw_item_data = item_data_map.get(str(item_id), {})

            # Extract item details
            item_entry = self._extract_item_details(raw_item_data, item_id)

            # Add analysis results
            if hasattr(item_data, 'model_dump'):
                item_dict = item_data.model_dump()
            elif hasattr(item_data, 'dict'):
                # For backward compatibility with Pydantic v1
                item_dict = item_data.dict()
            else:
                item_dict = item_data

            item_entry.update({
                'score': item_dict.get('score', 0),
                'status': item_dict.get('status', 'Unknown'),
                'notes': item_dict.get('notes', ''),
                'pros': item_dict.get('pros', []),
                'cons': item_dict.get('cons', [])
            })

            # Add market research data if available
            market_data = market_research_map.get(str(item_id)) if market_research_map else None
            if market_data:
                if hasattr(market_data, 'model_dump'):
                    market_dict = market_data.model_dump()
                elif hasattr(market_data, 'dict'):
                    # For backward compatibility with Pydantic v1
                    market_dict = market_data.dict()
                else:
                    market_dict = market_data

                item_entry['market_research'] = {
                    'average_price': market_dict.get('average_price', 'N/A'),
                    'price_range': market_dict.get('price_range', [0, 0]),
                    'value_assessment': market_dict.get('value_assessment', 'N/A'),
                    'market_demand': market_dict.get('market_demand', 'N/A'),
                    'confidence_score': market_dict.get('confidence_score', 0),
                    'comparable_items': market_dict.get('comparable_items', []),
                    'price_factors': market_dict.get('price_factors', []),
                    'notes': market_dict.get('notes', '')
                }

            # Add deal message if available
            deal_message = deal_messages.get(str(item_id)) if deal_messages else None
            if deal_message:
                # Extract deal message data properly
                if hasattr(deal_message, 'pydantic'):
                    message_data = deal_message.pydantic
                    item_entry['deal_message'] = {
                        'message': message_data.message,
                        'tone': message_data.tone,
                        'expected_success_rate': message_data.expected_success_rate
                    }
                elif hasattr(deal_message, 'model_dump'):
                    message_dict = deal_message.model_dump()
                    item_entry['deal_message'] = {
                        'message': message_dict.get('message', ''),
                        'tone': message_dict.get('tone', 'friendly'),
                        'expected_success_rate': message_dict.get('expected_success_rate', 0)
                    }
                elif hasattr(deal_message, 'dict'):
                    # For backward compatibility with Pydantic v1
                    message_dict = deal_message.dict()
                    item_entry['deal_message'] = {
                        'message': message_dict.get('message', ''),
                        'tone': message_dict.get('tone', 'friendly'),
                        'expected_success_rate': message_dict.get('expected_success_rate', 0)
                    }
                else:
                    # Fallback for non-Pydantic objects
                    item_entry['deal_message'] = {
                        'message': getattr(deal_message, 'message', ''),
                        'tone': getattr(deal_message, 'tone', 'friendly'),
                        'expected_success_rate': getattr(deal_message, 'expected_success_rate', 0)
                    }

            # Add the item entry to the template data
            template_data['items'].append(item_entry)

        return template_data

    def _extract_item_details(self, item_data, item_id):
        """Extract item details from the raw item data."""
        # Title
        title = item_data.get('title', 'Unknown Item')

        # Handle price information
        price_numeric = item_data.get('price_numeric', item_data.get('original_price_numeric', '?'))
        if isinstance(price_numeric, str) and price_numeric.isdigit():
            price_numeric = float(price_numeric)

        # Get price from nested price object if available
        price_obj = item_data.get('price', {})
        if isinstance(price_obj, dict) and 'amount' in price_obj:
            price = price_obj.get('amount', price_numeric)
        else:
            price = price_numeric

        # Get currency
        currency = item_data.get('currency', '€')

        # Get service fee and total price if available
        service_fee = item_data.get('service_fee', '0')
        total_item_price = item_data.get('total_item_price', price)

        # Get brand information
        brand_dto = item_data.get('brand_dto', {})
        if isinstance(brand_dto, dict) and 'title' in brand_dto:
            brand = brand_dto.get('title', 'Unknown Brand')
        else:
            brand = item_data.get('brand', 'Unknown Brand')

        # Get item condition/status
        status = item_data.get('status', 'Unknown condition')

        # Get item description
        description = item_data.get('description', 'No description available')

        # Get photo URL
        photo_url = self._extract_photo_url(item_data)

        # Get item URL
        item_url = item_data.get('url', '#')
        if item_url and not item_url.startswith('http'):
            item_url = f"https://www.vinted.it{item_url}"

        # Get seller information if available
        user_login = item_data.get('user_login', 'Unknown seller')

        # Get location information
        city = item_data.get('city', 'Unknown location')
        country = item_data.get('country', '')
        location = f"{city}, {country}" if country else city

        return {
            'title': title,
            'price': price,
            'currency': currency,
            'service_fee': service_fee,
            'total_price': total_item_price,
            'brand': brand,
            'status': status,
            'description': description,
            'photo_url': photo_url,
            'item_url': item_url,
            'seller': user_login,
            'location': location
        }

    def _extract_photo_url(self, item_data):
        """Extract the photo URL from the item data."""
        photo_url = None
        # Try to get photos from the photos array
        photos = item_data.get('photos', [])
        if photos and isinstance(photos, list) and len(photos) > 0:
            # Get the first photo object
            photo = photos[0]
            if isinstance(photo, dict):
                # Try different possible photo URL fields
                photo_url = photo.get('full_size_url',
                                      photo.get('url', None))
                # If thumbnails exist and is a dictionary
                thumbnails = photo.get('thumbnails')
                if not photo_url and thumbnails and isinstance(thumbnails, dict):
                    photo_url = thumbnails.get('original')

        # If no photo found, try alternative fields
        if not photo_url:
            photo_url = item_data.get('photo_url', item_data.get('full_size_url',
                                                                 'https://via.placeholder.com/350x250?text=No+Image'))

        return photo_url

    def _generate_fallback_html_report(self, template_data, filename):
        """Generate a simple HTML report as fallback if template loading fails."""
        print("Using fallback HTML report generation")

        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Vinted Item Analysis Results</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                header { background-color: #5D3FD3; color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; }
                h1 { margin: 0; }
                .item-card { background-color: white; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 20px; padding: 15px; position: relative; }
                .item-title { color: #5D3FD3; }
                .high-score { color: green; }
                .medium-score { color: orange; }
                .low-score { color: red; }
                .notes-container { position: relative; }
                .notes-preview { cursor: pointer; max-height: 60px; overflow: hidden; }
                .notes-full { display: none; position: absolute; left: 0; right: 0; background: white; padding: 15px; 
                              border-radius: 8px; border: 1px solid #ddd; box-shadow: 0 5px 15px rgba(0,0,0,0.2); 
                              z-index: 10; max-height: 300px; overflow-y: auto; }
                .notes-container:hover .notes-full { display: block; }
                .market-data { background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-top: 10px; }
                .market-data h4 { margin-top: 0; color: #5D3FD3; }
                .deal-message { background-color: #f0f7ff; padding: 15px; border-radius: 5px; margin-top: 10px; }
                .deal-message h4 { margin-top: 0; color: #5D3FD3; }
                .message-content { background: white; padding: 10px; border-radius: 5px; border: 1px solid #e0e0e0; }
                .copy-button { background-color: #5D3FD3; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer; margin-top: 5px; }
                footer { margin-top: 40px; text-align: center; color: #777; }
            </style>
            <script>
            function copyMessage(button) {
                const messageContent = button.previousElementSibling.textContent;
                navigator.clipboard.writeText(messageContent.trim()).then(() => {
                    const originalText = button.textContent;
                    button.textContent = 'Copied!';
                    button.style.backgroundColor = '#2E7D32';
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.style.backgroundColor = '';
                    }, 2000);
                });
            }
            </script>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>Vinted Item Analysis Results</h1>
                    <div>Search query: "{search_query}" | {timestamp}</div>
                </header>

                <div class="items-container">
        """.format(search_query=template_data['search_query'], timestamp=template_data['timestamp'])

        # Add item cards to HTML
        for item in template_data['items']:
            item_card = f"""
                <div class="item-card">
                    <h3 class="item-title">{item['title']}</h3>
                    <div>Price: {item['price']} {item['currency']}</div>
                    <div>ID: {item['id']} | Brand: {item['brand']}</div>
                    <div>Bargain Score: <span class="{item['score_class']}">{item['score']}/100</span></div>
                    <div class="notes-container">
                        <div class="notes-preview">
                            <strong>Analysis:</strong> {item['notes'][:100]}{'...' if len(item['notes']) > 100 else ''}
                            <small>(hover to see full analysis)</small>
                        </div>
                        <div class="notes-full">
                            <strong>Full Analysis:</strong><br>
                            {item['notes']}
                        </div>
                    </div>
            """

            # Add market research data if available
            if 'market_research' in item:
                market_data = item['market_research']
                item_card += f"""
                    <div class="market-data">
                        <h4>Market Research</h4>
                        <div>Average Price: {market_data['average_price']} {item['currency']}</div>
                        <div>Price Range: {market_data['price_range'][0]} - {market_data['price_range'][1]} {item['currency']}</div>
                        <div>Value Assessment: {market_data['value_assessment']}</div>
                        <div>Market Demand: {market_data['market_demand']}</div>
                        <div>Confidence: {market_data['confidence_score']}/10</div>
                    </div>
                """

            item_card += f"""
                    <div>
                        <a href="{item['item_url']}" target="_blank">View on Vinted</a>
                    </div>
                </div>
            """
            html_content += item_card

        # Close HTML tags
        html_content += """
                </div>
                <footer>
                    <p>Generated on {date} by Vinted Item Analysis Tool</p>
                </footer>
            </div>
        </body>
        </html>
        """.format(date=template_data['date'])

        # Write HTML to file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"Fallback HTML report generated: {filename}")
            return filename
        except Exception as e:
            print(f"Error generating fallback HTML report: {e}")
            return None