# -*- coding: utf-8 -*-
"""Stripe payment integration for legal-agent-ii."""

import os
import json
import time
from pathlib import Path
from typing import Optional

import stripe

PAID_FILE = Path(__file__).resolve().parent.parent.parent / ".paid_users.json"


def _get_stripe_config():
    return {
        "key": os.environ.get("STRIPE_SECRET_KEY", ""),
        "price_id": os.environ.get("STRIPE_PRICE_ID", ""),
        "webhook_secret": os.environ.get("STRIPE_WEBHOOK_SECRET", ""),
        "site_url": os.environ.get("SITE_URL", "http://localhost:8765"),
    }


def _read_paid() -> dict:
    if not PAID_FILE.exists():
        return {}
    try:
        return json.loads(PAID_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write_paid(data: dict) -> None:
    PAID_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def mark_paid(session_id: str, customer_email: str = "") -> None:
    data = _read_paid()
    data[session_id] = {"email": customer_email, "paid_at": int(time.time())}
    _write_paid(data)


def is_session_paid(session_id: str) -> bool:
    return session_id in _read_paid()


def verify_stripe_session(session_id: str) -> Optional[dict]:
    cfg = _get_stripe_config()
    if not cfg["key"]:
        return None
    stripe.api_key = cfg["key"]
    try:
        session = stripe.checkout.sessions.retrieve(session_id)
        if session.payment_status == "paid":
            mark_paid(session_id, session.customer_details.email if session.customer_details else "")
            return {"paid": True, "email": session.customer_details.email if session.customer_details else ""}
        return {"paid": False}
    except stripe.error.StripeError:
        return None


def create_checkout_session() -> Optional[dict]:
    cfg = _get_stripe_config()
    if not cfg["key"] or not cfg["price_id"]:
        return None
    stripe.api_key = cfg["key"]
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": cfg["price_id"], "quantity": 1}],
            mode="subscription" if cfg["price_id"].startswith("price_") else "payment",
            success_url=cfg["site_url"].rstrip("/") + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cfg["site_url"].rstrip("/"),
        )
        return {"url": session.url, "session_id": session.id}
    except stripe.error.StripeError as e:
        return {"error": str(e)}


def verify_webhook_signature(payload: bytes, sig_header: str) -> bool:
    cfg = _get_stripe_config()
    if not cfg["webhook_secret"]:
        return False
    try:
        stripe.Webhook.construct_event(payload, sig_header, cfg["webhook_secret"])
        return True
    except stripe.error.SignatureVerificationError:
        return False


def handle_checkout_completed(session_data: dict) -> None:
    session_id = session_data.get("id", "")
    email = ""
    if session_data.get("customer_details"):
        email = session_data["customer_details"].get("email", "")
    mark_paid(session_id, email)
