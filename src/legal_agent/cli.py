from __future__ import annotations

import asyncio, sys
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from legal_agent.agent import ask_legal_agent
from legal_agent.config import get_settings
from legal_agent.retrieval import load_sources, build_embedding_index, _embed_and_cache

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

app = typer.Typer(help='Legal assistant agent CLI.')
console = Console(force_terminal=True)

@app.command()
def ask(
    question: str = typer.Argument(..., help='Legal question or document-analysis request.'),
    jurisdiction: str | None = typer.Option(None, '--jurisdiction', '-j', help='Applicable jurisdiction.'),
) -> None:
    load_dotenv()
    settings = get_settings()
    j = jurisdiction or settings.jurisdiction
    a = asyncio.run(ask_legal_agent(question=question, jurisdiction=j))
    console.print(Markdown(a))

@app.command()
def sources() -> None:
    load_dotenv()
    s = get_settings()
    t = Table(title='Legal sources in ' + str(s.source_dir))
    t.add_column('File')
    t.add_column('Heading')
    for p, h, _ in load_sources(s.source_dir):
        t.add_row(str(p.relative_to(s.source_dir)), h)
    console.print(t)

@app.command()
def reindex(force: bool = typer.Option(False, '--force', '-f', help='Force full re-embedding')) -> None:
    load_dotenv()
    s = get_settings()
    async def chk(): return build_embedding_index(s.source_dir, force=force)
    total, needs = asyncio.run(chk())
    if not needs:
        console.print('[green]Index up to date ({} chunks).[/green]'.format(total))
        return
    with console.status('[bold]Embedding {} chunks...[/bold]'.format(total)):
        r = asyncio.run(_embed_and_cache(s.source_dir))
        if r < 0:
            console.print('[red]Embedding failed. Keyword fallback active.[/red]')
        else:
            console.print('[green]Index built: {} chunks.[/green]'.format(r))

def _read_contract(file_path: str) -> str:
    from pathlib import Path as P
    p = P(file_path)
    if not p.exists():
        console.print('[red]File not found: {}[/red]'.format(file_path))
        raise typer.Exit(1)
    suffix = p.suffix.lower()
    if suffix == '.docx':
        try:
            from docx import Document
            doc = Document(str(p))
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return '\n'.join(paragraphs)
        except ImportError:
            console.print('[red]python-docx not installed. Run: pip install python-docx[/red]')
            raise typer.Exit(1)
    else:
        return p.read_text(encoding='utf-8', errors='ignore')

@app.command()
def review(
    file: str = typer.Argument(..., help='Path to contract file (.txt, .md, .docx)'),
) -> None:
    from legal_agent.contract_review import review_contract, format_review
    text = _read_contract(file)
    result = review_contract(text)
    report = format_review(result)
    console.print(Markdown(report))

if __name__ == '__main__':
    app()
