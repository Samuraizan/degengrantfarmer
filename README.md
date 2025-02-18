Degen Grant Farmer

🚀 Introduction

Degen Grant Farmer is an autonomous, AI-powered agentic framework designed to hunt, filter, and apply for Web3 grants. It scrapes blockchain grant programs, categorizes them, and assists in the application process, making it easier for developers, researchers, and founders to secure funding.

🎯 Features

Automated Web3 Grant Discovery: Scrapes data from Ethereum, Solana, Gitcoin, Polygon, Arbitrum, and other funding sources.

Multi-Agent Framework: Uses distinct AI agents to scrape, analyze, and auto-fill applications.

Grant Categorization & Ranking: Sorts grants based on funding size, ecosystem relevance, and deadlines.

Google Sheets / Notion Integration: Stores and updates grant details in real-time.

Application Auto-Fill: Uses AI to generate draft responses tailored to each grant.

Scheduled Updates: Automated weekly scans for new grants.

On-Chain & DAO Compatibility: Future integration with decentralized governance funding.

🛠️ Tech Stack

Component

Technology

Language

Python 3.9+

Scraping

BeautifulSoup, Scrapy

APIs & Automation

Requests, Selenium

Database

SQLite / PostgreSQL / Google Sheets API

AI Agents

OpenAI API, LangChain, AutoGen

Orchestration

Prefect / Airflow

Application Handling

Google Forms API / Notion API

📁 Repository Structure

Degen-Grant-Farmer/
│── agents/                   # AI agents for grant discovery & applications
│   ├── scraper_agent.py       # Scrapes grant websites
│   ├── filter_agent.py        # Categorizes and ranks grants
│   ├── application_agent.py   # Auto-generates application responses
│── data/                      # Storage for fetched and processed grant data
│   ├── grants.json            # Raw scraped data
│   ├── processed_grants.json  # Filtered & ranked grants
│── docs/                      # Documentation and guides
│── config/                    # Configuration settings (API keys, schedules)
│── tests/                     # Unit tests for agents
│── README.md                  # Project overview
│── requirements.txt           # Dependencies list
│── setup.py                   # Installable package setup
│── .github/workflows/ci.yml   # GitHub Actions for automation

🚀 Installation & Usage

1️⃣ Clone the repository

git clone https://github.com/your-username/Degen-Grant-Farmer.git
cd Degen-Grant-Farmer

2️⃣ Install dependencies

pip install -r requirements.txt

3️⃣ Run the scraper agent

python agents/scraper_agent.py

4️⃣ Process & filter grants

python agents/filter_agent.py

5️⃣ Generate application drafts

python agents/application_agent.py

📌 Automation & CI/CD

GitHub Actions: Automates weekly scraping & sheet updates.

Error Handling: Built-in retry logic for failed requests.

Logging & Monitoring: Uses loguru for logging, with future support for ELK Stack.

📖 Future Roadmap

✔ Phase 1: Scraping & API integrations✔ Phase 2: Filtering and ranking system✔ Phase 3: AI-powered auto-filling of applications✔ Phase 4: Multi-agent collaboration for complete automation🚀 Phase 5: On-chain grant verification & smart contract submission

📜 License

This project is open-source under the MIT License. Feel free to contribute!

🔗 Links

📑 Documentation: [Coming Soon]

🛠️ Issues & Features: GitHub Issues

🤝 Join the Community: Discord

💰 Degen Grant Farmer: Because why write grant applications manually when you can let AI do it for you? 🚀

