import json, pathlib
from json import JSONDecodeError        # ← добавили

DATA_PATH = pathlib.Path("data") / "state.json"
DATA_PATH.parent.mkdir(exist_ok=True, parents=True)

# ---------- low-level I/O ----------
def _load() -> dict:
    """
    Безопасно читаем JSON-файл.
    Если файла нет или он битый → возвращаем чистую структуру,
    чтобы бот не падал.
    """
    if not DATA_PATH.exists():
        return {"users": {}, "payments": {}}
    try:
        with DATA_PATH.open() as f:
            return json.load(f)
    except JSONDecodeError:
        return {"users": {}, "payments": {}}

def _save(data: dict):
    with DATA_PATH.open("w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- public API ----------
def add_user(chat_id: int, name: str, username: str | None, role: str = "member"):
    """Добавляет юзера, если его ещё нет"""
    data = _load()
    uid = str(chat_id)
    if uid not in data["users"]:
        data["users"][uid] = {"name": name, "username": username, "role": role}
        _save(data)

def list_users() -> dict:
    return _load()["users"]

def list_members(admin_id: int) -> dict:
    """Только участники, без администратора"""
    return {uid: info for uid, info in list_users().items() if int(uid) != admin_id}

def set_paid(chat_id: int, month: str):
    data = _load()
    data["payments"].setdefault(month, {})[str(chat_id)] = True
    _save(data)

def unpaid(month: str, admin_id: int):
    """ID тех, кто не оплатил (без админа)"""
    d = _load()
    users = list_members(admin_id)
    paid = d["payments"].get(month, {})
    return [int(uid) for uid in users if uid not in paid]
