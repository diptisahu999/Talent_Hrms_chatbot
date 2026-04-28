from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, WebSocket

from app.config import settings
from app.core.session import SessionManager


async def get_session_from_request(request: Request, sm: SessionManager) -> Dict[str, Any]:
    sid = None

    # 1. Check Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        sid = auth_header.replace("Bearer ", "").strip()

    # 2. Check Custom Headers
    if not sid:
        sid = request.headers.get("X-Session-ID") or request.headers.get("X-Section-ID")

    # 3. Check Query Parameters
    if not sid:
        sid = request.query_params.get("sid") or request.query_params.get("sectionId")

    # 4. Check Cookie (signed)
    if not sid:
        cookie_val = request.cookies.get(settings.SESSION_COOKIE_NAME)
        if cookie_val:
            sid = sm.decode_cookie(cookie_val)

    if not sid:
        raise HTTPException(status_code=401, detail="Not authenticated")

    data = await sm.get(sid)
    if not data:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    request.state.sid = sid
    return data


async def get_session_from_ws(ws: WebSocket, sm: SessionManager) -> tuple[str, Dict[str, Any]]:
    sid = None

    # 1. Check Query Parameters (standard for WS clients)
    sid = ws.query_params.get("sid") or ws.query_params.get("sectionId")

    # 2. Check Cookie (signed)
    if not sid:
        cookie_val = ws.cookies.get(settings.SESSION_COOKIE_NAME)
        if cookie_val:
            sid = sm.decode_cookie(cookie_val)

    if not sid:
        await ws.close(code=4401)
        raise RuntimeError("No session identification found")

    data = await sm.get(sid)
    if not data:
        await ws.close(code=4401)
        raise RuntimeError("Session expired or invalid")

    return sid, data
