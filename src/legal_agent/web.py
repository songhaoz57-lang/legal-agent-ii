# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from legal_agent.agent import ask_legal_agent, build_agent
from legal_agent.config import get_settings
from legal_agent.contract_review import review_contract, format_review
from legal_agent.auth import (
    create_user, authenticate, get_user_from_request,
    create_token, mark_user_paid, is_user_paid, get_user_by_email,
)
from legal_agent.contract_generator import list_templates, generate_contract
from legal_agent.payment import (
    create_checkout_session,
    verify_stripe_session,
    verify_webhook_signature,
    handle_checkout_completed,
    is_session_paid,
)

load_dotenv(override=True)

app = FastAPI(title="Legal Agent - ii Contract Review")

SRC_DIR = Path(__file__).resolve().parent


def _read_upload(file: UploadFile) -> str:
    suffix = Path(file.filename or "").suffix.lower()
    content = file.file.read()
    if suffix == ".docx":
        from docx import Document
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            doc = Document(tmp_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return chr(10).join(paragraphs)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    else:
        return content.decode("utf-8", errors="ignore")


@app.post("/api/review")
async def api_review(file: UploadFile = File(...)):
    text = _read_upload(file)
    result = review_contract(text)
    report = format_review(result)
    return {
        "filename": file.filename,
        "score": result.overall_score,
        "risks": [
            {
                "clause_type": r.clause_type,
                "risk_level": r.risk_level,
                "found_text": r.found_text,
                "suggestion": r.suggestion,
            }
            for r in result.risks
        ],
        "missing_clauses": result.missing_clauses,
        "report": report,
    }


@app.post("/api/ask")
async def api_ask(question: str = Form(...), jurisdiction: str = Form("cn")):
    answer = await ask_legal_agent(question=question, jurisdiction=jurisdiction)
    return {"answer": answer}


@app.get("/api/sources")
async def api_sources():
    settings = get_settings()
    from legal_agent.retrieval import load_sources
    items = []
    for p, heading, _ in load_sources(settings.source_dir):
        items.append({
            "file": str(p.relative_to(settings.source_dir)),
            "heading": heading,
        })
    return {"sources": items}


@app.get("/api/source/{file_path:path}")
async def api_source(file_path: str):
    settings = get_settings()
    p = Path(settings.source_dir) / file_path
    if not p.exists():
        return {"error": "Not found"}
    return {"content": p.read_text(encoding="utf-8", errors="ignore")}


@app.post("/api/payment/create-checkout")
async def api_create_checkout():
    result = create_checkout_session()
    if result is None:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@app.post("/api/payment/verify/{session_id}")
async def api_verify_payment(session_id: str):
    if is_session_paid(session_id):
        return {"paid": True}
    result = verify_stripe_session(session_id)
    if result is None:
        raise HTTPException(status_code=400, detail="Invalid session")
    return result


@app.get("/api/payment/check/{session_id}")
async def api_check_access(session_id: str):
    return {"paid": is_session_paid(session_id)}


@app.post("/api/stripe-webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    if verify_webhook_signature(payload, sig):
        import json
        event = json.loads(payload)
        if event.get("type") == "checkout.session.completed":
            handle_checkout_completed(event.get("data", {}).get("object", {}))
        return {"received": True}
    raise HTTPException(status_code=400, detail="Invalid signature")


# ── Auth routes ──

@app.post("/api/auth/register")
async def api_register(data: dict):
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    name = data.get("name", "").strip()
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    user = create_user(email, password, name)
    if user is None:
        raise HTTPException(status_code=409, detail="Email already registered")
    token = create_token(user["id"], user["email"])
    return {"token": token, "user": {"id": user["id"], "email": user["email"], "name": user["name"], "is_paid": bool(user["is_paid"])}}


@app.post("/api/auth/login")
async def api_login(data: dict):
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    user = authenticate(email, password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(user["id"], user["email"])
    return {"token": token, "user": {"id": user["id"], "email": user["email"], "name": user["name"], "is_paid": bool(user["is_paid"])}}


@app.get("/api/auth/me")
async def api_me(request: Request):
    auth = request.headers.get("authorization", "")
    user = get_user_from_request(auth)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"user": {"id": user["id"], "email": user["email"], "name": user["name"], "is_paid": bool(user["is_paid"])}}

# ── Contract generator ──

@app.get("/api/templates")
async def api_templates():
    return {"templates": list_templates()}


@app.post("/api/contract/generate")
async def api_generate(data: dict):
    template_id = data.get("template_id", "")
    fields = data.get("fields", {})
    result = generate_contract(template_id, fields)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/api/debug-env")
async def api_debug_env():
    return {
        "openai_key_set": bool(os.environ.get("OPENAI_API_KEY")),
        "openai_base_url": os.environ.get("OPENAI_BASE_URL", "NOT SET"),
        "model": os.environ.get("LEGAL_AGENT_MODEL", "NOT SET"),
    }


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = SRC_DIR / "templates" / "index.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>Legal Agent</h1><p>Frontend not found.</p>"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("legal_agent.web:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8765)))
