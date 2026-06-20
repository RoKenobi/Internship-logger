# NTU Internship Logger

A Python-based CLI tool designed to track daily robotics and AI engineering tasks, bugs, and solutions. It dynamically queries for missing context and automatically appends the data to local markdown files for academic reporting.

## Features

* Interactive terminal UI powered by the `rich` library.
* AI-driven prompt completion to ensure all technical blockers and academic learnings are recorded.
* Outputs directly into structured Markdown files.

## Installation

Clone the repository to your local machine:

    git clone https://github.com/YOUR_GITHUB_USERNAME/ntu-internship-logger.git
    cd ntu-internship-logger

## Setup

1. Install the required Python dependencies:

    pip install rich python-dotenv anthropic

2. Create a `.env` file in the root directory and add your API token:

    AWS_BEARER_TOKEN_BEDROCK="your_actual_token_here"

## Usage

Run the logger at the end of your shift:

    python3 logger.py

The script will prompt you for a brain dump, ask context-aware clarifying questions, and save the formatted output directly to your active log files.
