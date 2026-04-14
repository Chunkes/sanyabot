import json
import os
import shutil
import asyncio
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "data.json"))
SEED_PATH = os.path.join(os.path.dirname(__file__), "data_seed.json")
_lock = asyncio.Lock()


def _load_db():
    if not os.path.exists(DB_PATH):
        return {"next_id": 1, "applications": {}}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_db(db):
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


async def init_db():
    async with _lock:
        db_dir = os.path.dirname(DB_PATH)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        if not os.path.exists(DB_PATH):
            if os.path.exists(SEED_PATH):
                shutil.copy(SEED_PATH, DB_PATH)
            else:
                _save_db({"next_id": 1, "applications": {}})


async def save_application(user_id, username, name, instagram, source, reason, vibe):
    async with _lock:
        db = _load_db()
        app_id = db["next_id"]
        db["applications"][str(app_id)] = {
            "id": app_id,
            "user_id": user_id,
            "username": username,
            "name": name,
            "instagram": instagram,
            "source": source,
            "reason": reason,
            "vibe": vibe,
            "status": "pending",
            "admin_comment": None,
            "created_at": datetime.now().isoformat(),
        }
        db["next_id"] = app_id + 1
        _save_db(db)
        return app_id


async def get_application(app_id):
    async with _lock:
        db = _load_db()
        return db["applications"].get(str(app_id))


async def update_status(app_id, status):
    async with _lock:
        db = _load_db()
        key = str(app_id)
        if key in db["applications"]:
            db["applications"][key]["status"] = status
            _save_db(db)


async def has_application(user_id):
    async with _lock:
        db = _load_db()
        for app in db["applications"].values():
            if app["user_id"] == user_id:
                return app["status"]
        return None


async def add_manual_application(user_id, username, name, instagram, source, reason, vibe, comment):
    async with _lock:
        db = _load_db()
        app_id = db["next_id"]
        db["applications"][str(app_id)] = {
            "id": app_id,
            "user_id": user_id,
            "username": username,
            "name": name,
            "instagram": instagram,
            "source": source,
            "reason": reason,
            "vibe": vibe,
            "status": "manual",
            "admin_comment": comment,
            "created_at": datetime.now().isoformat(),
        }
        db["next_id"] = app_id + 1
        _save_db(db)
        return app_id


async def delete_application(app_id):
    async with _lock:
        db = _load_db()
        key = str(app_id)
        if key in db["applications"]:
            removed = db["applications"].pop(key)
            _save_db(db)
            return removed
        return None


async def get_all_applications():
    async with _lock:
        db = _load_db()
        return list(db["applications"].values())


async def get_all_user_ids():
    async with _lock:
        db = _load_db()
        ids = set()
        for app in db["applications"].values():
            if app.get("status") not in ("approved", "manual"):
                continue
            if app["user_id"] and app["user_id"] != 0:
                ids.add(app["user_id"])
        return list(ids)


async def search_applications(query):
    async with _lock:
        db = _load_db()
        q = query.lower()
        results = []
        for app in db["applications"].values():
            searchable = " ".join(
                str(v) for v in app.values() if v is not None
            ).lower()
            if q in searchable:
                results.append(app)
        return results
