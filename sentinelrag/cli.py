"""SentinelRAG CLI -- secure enterprise research agent.

Usage:
    python cli.py --user data/users/u102.json --question "What is the Q4 revenue forecast?"
    python cli.py --user data/users/u205.json --question "What is the Q4 revenue forecast?"
    python cli.py --user data/users/u301.json --question "What is the latest Q4 revenue forecast?"
"""

from __future__ import annotations

import argparse
import json

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sentinel.document_store import DocumentStore
from sentinel.models import User
from sentinel.orchestrator import SentinelRAGPipeline

console = Console()


def load_user(path: str) -> User:
    with open(path, "r", encoding="utf-8") as f:
        return User.from_dict(json.load(f))


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="SentinelRAG -- secure enterprise research agent")
    parser.add_argument("--user", required=True, help="Path to a user.json file")
    parser.add_argument("--question", required=True, help="Natural language question")
    parser.add_argument("--documents", default="data/documents.json", help="Path to documents.json")
    args = parser.parse_args()

    user = load_user(args.user)
    store = DocumentStore.from_json_file(args.documents)
    pipeline = SentinelRAGPipeline(store)

    mode = "LIVE (Gemini)" if pipeline.llm_client.enabled else "STUB (no LLM key set)"
    result = pipeline.run(user, args.question)

    console.print(
        Panel(
            f"[bold]{args.question}[/bold]",
            title=f"Query from {user.user_id} ({user.role}/{user.department}, clearance={user.clearance})",
            subtitle=f"answer mode: {mode}",
        )
    )

    stats = result["evidence_firewall"]
    table = Table(title="Evidence Firewall")
    table.add_column("Retrieved")
    table.add_column("Authorized", style="green")
    table.add_column("Blocked", style="red")
    table.add_row(str(stats["retrieved"]), str(stats["authorized"]), str(stats["blocked"]))
    console.print(table)

    console.print(Panel(result["answer"], title="Answer"))

    if result["citations"]:
        cite_str = ", ".join(f"{c['document_id']} v{c['version']}" for c in result["citations"])
        console.print(f"[bold]Citations:[/bold] {cite_str}")
    else:
        console.print("[bold]Citations:[/bold] none")

    if result["conflicts"]:
        console.print(f"[yellow]Unresolved conflicts flagged for:[/yellow] {', '.join(result['conflicts'])}")

    console.print(f"[dim]query_id={result['query_id']} (see audit_log.db for full trace)[/dim]")


if __name__ == "__main__":
    main()
