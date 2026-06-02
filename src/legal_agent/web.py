# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from legal_agent.agent import ask_legal_agent, build_agent
from legal_agent.config import get_settings
from legal_agent.contract_review import review_contract, format_review
import os

load_dotenv(override=True)

app = FastAPI(title='Legal Agent - 合同审查系统')

SRC_DIR = Path(__file__).resolve().parent


def _read_upload(file: UploadFile) -> str:
    suffix = Path(file.filename or '').suffix.lower()
    content = file.file.read()
    if suffix == '.docx':
        from docx import Document
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            doc = Document(tmp_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return chr(10).join(paragraphs)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    else:
        return content.decode('utf-8', errors='ignore')


@app.post('/api/review')
async def api_review(file: UploadFile = File(...)):
    text = _read_upload(file)
    result = review_contract(text)
    report = format_review(result)
    return {
        'filename': file.filename,
        'score': result.overall_score,
        'risks': [
            {
                'clause_type': r.clause_type,
                'risk_level': r.risk_level,
                'found_text': r.found_text,
                'suggestion': r.suggestion,
            }
            for r in result.risks
        ],
        'missing_clauses': result.missing_clauses,
        'report': report,
    }


@app.post('/api/ask')
async def api_ask(question: str = Form(...), jurisdiction: str = Form('cn')):
    loop = asyncio.get_event_loop()
    answer = await ask_legal_agent(question=question, jurisdiction=jurisdiction)
    return {'answer': answer}


@app.get('/api/sources')
async def api_sources():
    settings = get_settings()
    from legal_agent.retrieval import load_sources
    items = []
    for p, heading, _ in load_sources(settings.source_dir):
        items.append({
            'file': str(p.relative_to(settings.source_dir)),
            'heading': heading,
        })
    return {'sources': items}


@app.get('/', response_class=HTMLResponse)
async def index():
    html_path = SRC_DIR / 'templates' / 'index.html'
    if html_path.exists():
        return html_path.read_text(encoding='utf-8')
    return '<h1>Legal Agent</h1><p>Frontend not found.</p>'


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('legal_agent.web:app', host='0.0.0.0', port=int(os.environ.get('PORT', 8765)))
@app.get("/api/source/{file_path:path}")
async def api_source(file_path: str):
    settings = get_settings()
    p = Path(settings.source_dir) / file_path
    if not p.exists():
        return {"error": "Not found"}
    return {"content": p.read_text(encoding="utf-8", errors="ignore")}


