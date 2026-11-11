"""
Опциональный Google Sheets лог оплаченных броней.
"""
import asyncio
import base64
import json
import os
from typing import Optional
from loguru import logger

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GS_OK = True
except ImportError:
    GS_OK = False

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
SA_JSON_B64 = os.getenv("GOOGLE_SA_JSON_B64", "")

_sheet = None

def _init() -> None:
    global _sheet
    if _sheet is not None or not GS_OK or not SHEET_ID or not SA_JSON_B64:
        return
    try:
        json_str = base64.b64decode(SA_JSON_B64).decode("utf-8")
        creds_dict = json.loads(json_str)
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        _sheet = client.open_by_key(SHEET_ID).sheet1
        logger.info("Google Sheets подключён: {}", SHEET_ID)
    except Exception as e:
        logger.error("Sheets init failed: {}", e)
        _sheet = None

def is_enabled() -> bool:
    return _sheet is not None

async def log_booking(b: dict) -> None:
    if not _sheet:
        return
    row = [
        b.get("booking_id", ""),
        str(b.get("vk_id", "")),
        b.get("user_name", ""),
        b.get("date", ""),
        b.get("time", ""),
        b.get("package", ""),
        ",".join(b.get("extras", [])),
        b.get("child_name", ""),
        b.get("child_age", ""),
        b.get("address", ""),
        b.get("phone", ""),
        str(b.get("total", "")),
        b.get("promo", "") or "",
        b.get("status", ""),
        b.get("created_at", ""),
        b.get("paid_at", "") or "",
    ]
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: _sheet.append_row(row))
        logger.info("Booking → Sheets: {}", b.get("booking_id"))
    except Exception as e:
        logger.error("Sheets log failed: {}", e)

async def load_paid() -> list[dict]:
    if not _sheet:
        return []
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: _sheet.get_all_records())
    except Exception as e:
        logger.error("Sheets load failed: {}", e)
        return []

_init()
