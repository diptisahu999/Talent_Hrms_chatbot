from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import httpx

from app.config import settings

AUTH_PATH = "/mobile/user/authenticate"


class HRMSClient:
    def __init__(self, http: httpx.AsyncClient) -> None:
        self.http = http
        self.base_url = settings.HRMS_BASE_URL.rstrip("/")

    async def authenticate(
        self,
        *,
        userName: str,
        password: str,
        registrationToken: str,
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, str], int, str, Dict[str, str]]:
        """Never raises on 4xx/5xx. Returns (json_or_none, cookies, status_code, raw_text, headers)."""
        url = f"{self.base_url}{AUTH_PATH}"
        payload = {"userName": userName, "password": password, "registrationToken": registrationToken}

        # Use a fresh client for authentication to ensure we get a clean set of cookies
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.post(
                url,
                data=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "PostmanRuntime/7.0.0",
                },
            )

            raw_text = resp.text
            cookies = dict(resp.cookies)
            headers = dict(resp.headers)
            try:
                data = resp.json()
            except Exception:
                data = None
            return data, cookies, resp.status_code, raw_text, headers

    async def get(
        self,
        path: str,
        *,
        params: Dict[str, Any],
        cookies: Optional[Dict[str, str]] = None,
    ) -> tuple[int, Dict[str, str], str, Optional[dict]]:
        url = f"{self.base_url}{path}"
        # Isolated client per request to prevent cookie leakage
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(
                url,
                params=params,
                cookies=cookies or {},
                headers={"Accept": "application/json", "User-Agent": "PostmanRuntime/7.0.0"},
            )
            raw = resp.text
            headers = dict(resp.headers)
            try:
                js = resp.json()
            except Exception:
                js = None
            return resp.status_code, headers, raw, js

    async def post(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> tuple[int, Dict[str, str], str, Optional[dict]]:
        url = f"{self.base_url}{path}"
        # Isolated client per request to prevent cookie leakage
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.post(
                url,
                params=params or {},
                json=json_body,
                cookies=cookies or {},
                headers={"Accept": "application/json", "User-Agent": "PostmanRuntime/7.0.0"},
            )
            raw = resp.text
            headers = dict(resp.headers)
            try:
                js = resp.json()
            except Exception:
                js = None
            return resp.status_code, headers, raw, js
