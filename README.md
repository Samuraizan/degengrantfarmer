# Degen Grant Farmer (DGF)

An AI-driven system designed to automate the process of discovering and applying for grant opportunities. DGF uses a multi-agent architecture to continuously scan for grants, filter the most promising ones, and generate high-quality applications.

## Features

- **Automated Grant Discovery**: Continuously scans multiple sources for grant opportunities
- **Intelligent Filtering**: Ranks and selects grants based on relevance, amount, deadlines, and effort
- **AI-Powered Applications**: Generates tailored grant applications using advanced language models
- **Configurable & Extensible**: Easy to add new grant sources or customize filtering criteria
- **Robust Error Handling**: Gracefully handles API failures and network issues
- **Comprehensive Logging**: Detailed logs for monitoring and debugging

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/degengrantfarmer.git
cd degengrantfarmer
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up configuration:
```bash
cp config/settings.yaml.example config/settings.yaml
# Edit config/settings.yaml with your settings
```

5. Set environment variables:
```bash
export OPENAI_API_KEY=your_api_key_here
# Add other API keys as needed
```

## Usage

1. Configure your profile in `config/settings.yaml`:
   - Set your organization details
   - Configure grant sources
   - Adjust filtering criteria

2. Run the system:
```bash
python run.py
```

The system will:
1. Collect grants from configured sources
2. Filter and rank them based on your criteria
3. Generate applications for the most promising opportunities
4. Save results in the `data/` directory

## Project Structure

```
degengrantfarmer/
├── agents/                 # Agent implementations
│   ├── scraper_agent.py   # Grant discovery
│   ├── filter_agent.py    # Grant filtering/ranking
│   └── application_agent.py# Application generation
├── config/                 # Configuration files
│   └── settings.yaml      # Main configuration
├── data/                  # Data storage
│   ├── raw/              # Raw grant data
│   ├── processed/        # Filtered grants
│   ├── applications/     # Generated applications
│   └── logs/            # System logs
├── tests/                # Test suite
├── requirements.txt      # Python dependencies
└── run.py               # Main execution script
```

## Configuration

The system is configured through `config/settings.yaml`. Key settings include:

- **Scraper Configuration**: Define grant sources and update frequencies
- **Filter Configuration**: Set scoring weights and thresholds
- **Application Configuration**: Configure AI parameters and templates
- **User Profile**: Your organization's details used in applications

See `config/settings.yaml` for detailed configuration options.

## Development

### Running Tests

```bash
pytest tests/
```

### Adding a New Grant Source

1. Add source configuration in `config/settings.yaml`
2. Implement scraping logic in `agents/scraper_agent.py`
3. Add tests in `tests/test_scraper_agent.py`

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Future Enhancements

- Decentralized governance integration
- Smart contract-based grant applications
- Community-driven development
- Enhanced AI capabilities
- Web dashboard
- Mobile notifications

## Support

- Create an issue for bug reports or feature requests
- Join our community Discord for discussions

## Acknowledgments

- Built with [AutoGen](https://github.com/microsoft/autogen) and [LangChain](https://github.com/hwchase17/langchain)
- Inspired by the need for efficient grant discovery and application

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

Error Handling: Built-in retry logic for failed requests.

Logging & Monitoring: Uses loguru for logging, with future support for ELK Stack.

📜 License

This project is open-source under the MIT License. Feel free to contribute!

🔗 Links

📑 Documentation: [Coming Soon]

