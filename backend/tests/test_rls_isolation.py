"""Integration test cô lập RLS của search_history (Constitution V, SC-004).

Dùng Supabase local: đăng ký 2 user qua GoTrue, mỗi user ghi lịch sử qua PostgREST
(áp RLS theo JWT), rồi khẳng định mỗi user CHỈ đọc được hàng của mình.

Tự bỏ qua khi thiếu SUPABASE_URL/SUPABASE_ANON_KEY (CI/máy không có Supabase vẫn xanh).
"""

import os
import uuid

import httpx
import pytest

SUPABASE_URL = os.environ.get("SUPABASE_URL")
ANON = os.environ.get("SUPABASE_ANON_KEY")

pytestmark = pytest.mark.skipif(
    not (SUPABASE_URL and ANON),
    reason="cần SUPABASE_URL + SUPABASE_ANON_KEY (Supabase local) cho test RLS",
)


async def _signup(client: httpx.AsyncClient, email: str, password: str) -> tuple[str, str]:
    r = await client.post(
        f"{SUPABASE_URL}/auth/v1/signup",
        headers={"apikey": ANON, "Content-Type": "application/json"},
        json={"email": email, "password": password},
    )
    r.raise_for_status()
    body = r.json()
    return body["access_token"], body["user"]["id"]


def _hdr(token: str) -> dict[str, str]:
    return {
        "apikey": ANON,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


@pytest.mark.integration
class TestRlsIsolation:
    async def test_user_cannot_read_others_history(self) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            e1 = f"a_{uuid.uuid4().hex[:8]}@test.local"
            e2 = f"b_{uuid.uuid4().hex[:8]}@test.local"
            tok1, uid1 = await _signup(client, e1, "password123")
            tok2, uid2 = await _signup(client, e2, "password123")

            rest = f"{SUPABASE_URL}/rest/v1/search_history"
            r = await client.post(
                rest, headers=_hdr(tok1), json={"query": "cua user 1", "sources": []}
            )
            r.raise_for_status()
            r = await client.post(
                rest, headers=_hdr(tok2), json={"query": "cua user 2", "sources": []}
            )
            r.raise_for_status()

            # user1 chỉ đọc được hàng của mình (RLS cô lập).
            r = await client.get(f"{rest}?select=query,user_id", headers=_hdr(tok1))
            r.raise_for_status()
            rows = r.json()

            assert rows, "user1 phải thấy lịch sử của chính mình"
            assert all(row["user_id"] == uid1 for row in rows)
            queries = {row["query"] for row in rows}
            assert "cua user 1" in queries
            assert "cua user 2" not in queries  # KHÔNG thấy của user2

            # Chiều ngược lại: user2 cũng chỉ thấy của mình (cô lập đối xứng).
            r = await client.get(f"{rest}?select=query,user_id", headers=_hdr(tok2))
            r.raise_for_status()
            rows2 = r.json()
            assert rows2, "user2 phải thấy lịch sử của chính mình"
            assert all(row["user_id"] == uid2 for row in rows2)
            queries2 = {row["query"] for row in rows2}
            assert "cua user 2" in queries2
            assert "cua user 1" not in queries2
