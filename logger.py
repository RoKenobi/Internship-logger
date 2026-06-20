#!/usr/bin/env python3
"""Interactive internship logging CLI powered by Claude via AWS Bedrock."""

import os
import sys
from datetime import date
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.prompt import Prompt
    from rich.rule import Rule
    from rich.theme import Theme
except ImportError:
    print("ERROR: 'rich' package required. Install with: pip install rich")
    sys.exit(1)

try:
    from anthropic import AnthropicBedrock
except ImportError:
    print("ERROR: 'anthropic' package required. Install with: pip install anthropic")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
BIWEEKLY_LOG = SCRIPT_DIR / "01_Biweekly_Logs.md"
FINAL_REPORT = SCRIPT_DIR / "02_Final_Report_Draft.md"
ENV_PATH = SCRIPT_DIR / ".env"

custom_theme = Theme({
    "info": "cyan",
    "success": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "heading": "bold magenta",
})
console = Console(theme=custom_theme)


def load_env_file():
    if not ENV_PATH.exists():
        console.print(f"[error].env file not found: {ENV_PATH}[/error]")
        sys.exit(1)
    env_vars = {}
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                env_vars[key.strip()] = value.strip().strip("\"'")
    return env_vars


def load_settings():
    env = load_env_file()
    token = env.get("AWS_BEARER_TOKEN_BEDROCK")
    if not token:
        console.print("[error]AWS_BEARER_TOKEN_BEDROCK not found in .env[/error]")
        sys.exit(1)
    region = env.get("AWS_REGION", "us-east-1")
    model = env.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
    return token, region, model


def create_client(token, region):
    os.environ["AWS_BEARER_TOKEN_BEDROCK"] = token
    return AnthropicBedrock(aws_region=region)


def init_biweekly_log():
    if not BIWEEKLY_LOG.exists():
        BIWEEKLY_LOG.write_text(
            "# Biweekly Internship Logs\n\n"
            "> Auto-generated via `logger.py` — Claude-assisted structured reflections.\n\n"
        )


def init_final_report():
    if not FINAL_REPORT.exists():
        FINAL_REPORT.write_text(
            "# Final Report Draft — Technical Insights Repository\n\n"
            "> Running collection of academic-aligned technical insights from internship work.\n\n"
        )


def get_brain_dump():
    console.print(Rule("[heading]Internship Logger[/heading]"))
    console.print(Panel(
        "[info]Paste your daily brain dump below — what you worked on, "
        "challenges faced, solutions found, anything relevant.\n"
        "Type [bold]done[/bold] on its own line when finished.[/info]",
        title="Daily Brain Dump",
        border_style="cyan",
    ))
    lines = []
    while True:
        line = Prompt.ask("[cyan]>[/cyan]", default="")
        if line.strip().lower() == "done":
            break
        if line.strip().lower() == "exit":
            return ""
        lines.append(line)
    return "\n".join(lines).strip()


SYSTEM_PROMPT = """You are an internship logging assistant. The user will provide a brain dump of their daily work.
Your job is to ask clarifying questions ONE AT A TIME to gather structured detail about:
1. Technical tasks and implementations (what was built, tools/frameworks used)
2. Bugs, bottlenecks, and challenges encountered
3. Solutions, outcomes, and connections to academic CS concepts (algorithms, design patterns, theory)

Rules:
- Ask exactly ONE question at a time, then wait for the answer.
- Be specific and context-aware — reference details from the brain dump.
- After 4-6 questions (or when you have enough context), respond with EXACTLY the marker:
  [QUESTIONS_COMPLETE]
  followed by nothing else.
- Keep questions concise and conversational.
- Do NOT generate the final log — just gather information."""

GENERATION_PROMPT = """Based on the full conversation above, generate TWO clearly separated markdown sections.

SECTION 1 — BIWEEKLY LOG ENTRY:
Generate a log entry with this exact structure (no top heading, start directly with the sections):

### Tasks Completed
- (bullet points of technical work done)

### Blockers & Challenges
- (bullet points of issues, bugs, bottlenecks)

### Resolutions & Outcomes
- (bullet points of how things were resolved, results achieved)

### Academic Connections
- (brief links to CS theory, design patterns, algorithms where relevant)

- [ ] Obtain supervisor clearance for confidentiality before submitting

SECTION 2 — FINAL REPORT INSIGHTS:
Generate a section for the final academic report with this structure:

### Technical Insight — [descriptive title]

**Context:** (1-2 sentences on what was being done)

**Technical Detail:** (the core technical insight, implementation detail, or architectural decision)

**Academic Relevance:** (how this connects to CS theory — cite specific concepts, patterns, or algorithms)

---

Separate the two sections with the exact marker line:
===SECTION_SPLIT==="""


def run_conversation(client, model, brain_dump):
    messages = [{"role": "user", "content": f"Here's my brain dump for today:\n\n{brain_dump}"}]

    console.print()
    console.print(Rule("[heading]Clarifying Questions[/heading]"))
    console.print("[info]Claude will ask follow-up questions to structure your log.[/info]\n")

    while True:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        assistant_text = response.content[0].text

        if "[QUESTIONS_COMPLETE]" in assistant_text:
            console.print("[success]Context gathering complete.[/success]\n")
            break

        messages.append({"role": "assistant", "content": assistant_text})
        console.print(Panel(assistant_text, border_style="magenta", title="Claude"))
        while True:
            answer = Prompt.ask("[cyan]Your answer (or 'exit' to quit)[/cyan]")
            if answer.strip():
                break
            console.print("[warning]Please provide a response.[/warning]")
        if answer.strip().lower() == "exit":
            console.print("[warning]Session ended. No logs written.[/warning]")
            return None
        messages.append({"role": "user", "content": answer.strip()})

    console.print(Rule("[heading]Generating Structured Logs[/heading]"))
    messages.append({"role": "user", "content": GENERATION_PROMPT})

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system="You are a technical writing assistant that produces clean, well-structured Markdown.",
        messages=messages,
    )
    return response.content[0].text


def write_logs(generated_text):
    today = date.today().strftime("%B %d, %Y")

    parts = generated_text.split("===SECTION_SPLIT===")
    biweekly_content = parts[0].strip() if len(parts) >= 1 else generated_text.strip()
    report_content = parts[1].strip() if len(parts) >= 2 else ""

    init_biweekly_log()
    with open(BIWEEKLY_LOG, "a") as f:
        f.write(f"\n## {today}\n\n")
        f.write(biweekly_content)
        f.write("\n\n---\n")

    console.print(f"[success]Appended to:[/success] {BIWEEKLY_LOG.name}")

    if report_content:
        init_final_report()
        with open(FINAL_REPORT, "a") as f:
            f.write(f"\n{report_content}\n\n")
        console.print(f"[success]Appended to:[/success] {FINAL_REPORT.name}")


def main():
    token, region, model = load_settings()
    client = create_client(token, region)

    brain_dump = get_brain_dump()
    if not brain_dump:
        console.print("[warning]No input provided. Exiting.[/warning]")
        return

    generated = run_conversation(client, model, brain_dump)
    if not generated:
        return

    write_logs(generated)

    console.print()
    console.print(Panel(
        f"[success]Logs written for {date.today().strftime('%B %d, %Y')}[/success]",
        title="Done",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
