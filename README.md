# DealSenseAI

DealSenseAI is an intelligent marketplace analyzer designed to identify optimal deals on Vinted. Leveraging **AI-powered analysis**, it evaluates second-hand items based on their condition, pricing, bargain potential and current online value, empowering users to make informed purchasing decisions.  Furthermore, DealSenseAI enhances negotiation strategies by suggesting personalized messages with predicted success probabilities.

**This project was created for educational purposes, specifically to explore AI orchestration, Agentic workflows, and related frameworks. It was built with the assistance of AI code completion. . Feel free to fork and develop it further!**

## 📸 Screenshots & Video

[DealSenseAI Video](src%2FDealSenseAI.mov)

![Command-line-interface.png](src%2FCommand-line-interface.png)

## 🚀 Features

*   **Vinted Marketplace Scraping:** Automatically fetches and analyzes real-time listings from Vinted, using **web scraping** tools.
*   **Online Market Research:** Automatically search online marketplace such as Ebay and Amazon for price comparison enable customizable number of research.
*   **AI-Powered Deal Analysis:** Evaluates items for **bargain potential (0-100)** and provides a **reliability score (0-10)** based on web search integration, showcasing **AI-driven data analysis**.
*   **Market Research Integration:** Compares listings against market averages to identify true bargains, showcasing expertise in **market analysis** and **comparative pricing**.
*   **Smart Message Generation:** Creates personalized negotiation messages with predicted success rates, based on the previous agents output.
*   **Comprehensive HTML Reports:** Generates visually appealing, detailed reports of findings, highlithings key price factors and unique cafracteristics of the insertion demonstrating skills in **data visualization** and **report generation**.

## 📋 Requirements

*   Python 3.8+
*   API keys for AI services (e.g., Serper, Gemini)
*   Internet connection for Vinted scraping

## 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/DealSenseAI.git
cd DealSenseAI

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

## 💻 Usage

Use the command-line interface:
```python
GEMINI_API_KEY="YOUR-GEMINI-API-KEY"
SERPER_API_KEY="YOUR-SERPER.DEV-API-KEY"
```
Use the command-line interface:

```python
python main.py
```

## 🏗️ Architecture

DealSenseAI employs a multi-agent AI system for analyzing Vinted listings, demonstrating **AI agent capabilities**:

*   **Scraper Agent:** Extracts listing data from Vinted search results, using **web scraping techniques**.
*   **Analysis Agent:** Evaluates item condition, price, and market position, employing **AI-powered data analysis**.
*   **Market Search Agent:** Automatically search online marketplace (such as Ebay and Amazon) for price comparison.
*   **Deal Evaluation Agent:** Calculates bargain potential and recommends negotiation strategies based on **Agentic pipeline information** gathering.
*   **Report Generator:** Compiles findings into interactive HTML reports.

## 📊 Example Output

The system generates detailed HTML reports, including:

*   Item details (name, price, condition, location)
*   Bargain potential score (0-100)
*   Reliability score (0-10)
*   Market research, value assessment and key price factors
*   Suggested negotiation messages with predicted success rates
*   Direct links to Vinted listings

![Output-screenshoot.png](src%2FOutput-screenshoot.png)


## 🔍 How It Works

1.  The user provides a search query for desired items.
2.  DealSenseAI scrapes Vinted for matching listings.
3.  Each item undergoes analysis for its true value and bargain potential.
4.  AI generates personalized negotiation messages with predicted success rates.
5.  Results are compiled into an interactive HTML report.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## 🙏 Acknowledgements

*   [CrewAI](https://www.crewai.com/) for the autonomous AI agent framework
*   [Google Gemini](https://ai.google.dev/) for AI analysis capabilities
*   [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/) for HTML report templating
*   The open-source community for various supporting libraries
