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
        sid = request.query_params.get("sid") or request.query_params.get("sectionId") or request.query_params.get("sectionID")

    # 4. Check Cookie (signed)
    if not sid:
        cookie_val = request.cookies.get(settings.SESSION_COOKIE_NAME)
        if cookie_val:
            sid = sm.decode_cookie(cookie_val)

    if not sid:
        raise HTTPException(status_code=401, detail="Not authenticated")

    data = await sm.get(sid)
    if not data:
        # Try to auto-provision from HRMS
        hrms = request.app.state.hrms
        from app.services.hrms.profile import get_user_profile
        
        # We treat the SID as the primary HRMS session cookie
        res = await get_user_profile(hrms=hrms, hrms_cookies={"_aisSessionId": sid})
        if res.get("ok"):
            info = res.get("basicInfo") or {}
            user = {
                "id": info.get("employeeId"),
                "name": info.get("name"),
                "email": info.get("email"),
                "phone": info.get("phone"),
                "userType": "employee", 
                "department": info.get("department"),
                "designation": info.get("designation"),
                "company": info.get("company"),
            }
            data = {"user": user, "hrms_cookies": {"_aisSessionId": sid}, "history": []}
            await sm.update(sid, data)
            print(f"AUTO-PROVISION | User: {user['name']} (HRMS SID: {sid[:8]}...)")
        else:
            raise HTTPException(status_code=401, detail="Session expired or invalid")

    user = data.get("user") or {}
    print(f"API AUTH | User: {user.get('name')} (ID: {user.get('id')}) | SID: {sid[:8]}...")

    request.state.sid = sid
    return data


async def get_session_from_ws(ws: WebSocket, sm: SessionManager) -> tuple[str, Dict[str, Any]]:
    sid = None

    # 1. Check Query Parameters (standard for WS clients)
    sid = ws.query_params.get("sid") or ws.query_params.get("sectionId") or ws.query_params.get("sectionID")

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
        # Try to auto-provision from HRMS
        hrms = ws.app.state.hrms
        from app.services.hrms.profile import get_user_profile
        
        res = await get_user_profile(hrms=hrms, hrms_cookies={"_aisSessionId": sid})
        if res.get("ok"):
            info = res.get("basicInfo") or {}
            user = {
                "id": info.get("employeeId"),
                "name": info.get("name"),
                "email": info.get("email"),
                "phone": info.get("phone"),
                "userType": "employee", 
                "department": info.get("department"),
                "designation": info.get("designation"),
                "company": info.get("company"),
            }
            data = {"user": user, "hrms_cookies": {"_aisSessionId": sid}, "history": []}
            await sm.update(sid, data)
            print(f"AUTO-PROVISION (WS) | User: {user['name']} (HRMS SID: {sid[:8]}...)")
        else:
            await ws.close(code=4401)
            raise RuntimeError("Session expired or invalid")

    user = data.get("user") or {}
    print(f"WS AUTH  | User: {user.get('name')} (ID: {user.get('id')}) | SID: {sid[:8]}...")

    return sid, data
