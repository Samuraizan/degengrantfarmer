from setuptools import setup, find_packages

setup(
    name="degengrantfarmer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "autogen-agentchat>=0.2.0",
        "langchain>=0.1.0",
        "openai>=1.0.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "selenium>=4.16.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "pytest>=7.0.0",
        "pandas>=2.0.0",
        "PyYAML>=6.0.0"
    ],
    python_requires=">=3.8",
) 