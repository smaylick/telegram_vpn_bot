import json
import pathlib
from json import JSONDecodeError

from app.config import DEFAULT_PRICE, DEFAULT_PAYMENT_INFO

# Resolve relative to the package directory so the path is the same whether
# the bot is run as `python -m app.main` from the repo root or from inside the
# container at /app.
DATA_PATH = pathlib.Path(__file__).resolve().parent / "data" / "state.json"
DATA_PATH.parent.mkdir(exist_ok=True, parents=True)

# Legacy CWD-relative path used by previous versions of the bot. Used only for
# one-time migration on startup if no file exists at DATA_PATH.
_LEGACY_PATH = pathlib.Path("data") / "state.json"


def _empty_state() -> dict:
    return {
        "users": {},
        "payments": {},
        "settings": {
            "price": DEFAULT_PRICE,
            "payment_info": DEFAULT_PAYMENT_INFO,
        },
    }


def _maybe_migrate_legacy() -> None:
    if DATA_PATH.exists():
        return
    if not _LEGACY_PATH.exists():
        return
    try:
        DATA_PATH.write_text(_LEGACY_PATH.read_text(), encoding="utf-8")
    except OSError:
        pass


def _load() -> dict:
    _maybe_migrate_legacy()
    if not DATA_PATH.exists():
        return _empty_state()
    try:
        with DATA_PATH.open() as f:
            data = json.load(f)
    except JSONDecodeError:
        return _empty_state()

    changed = False
    if "users" not in data:
        data["users"] = {}
        changed = True
    if "payments" not in data:
        data["payments"] = {}
        changed = True
    if "settings" not in data:
        data["settings"] = {
            "price": DEFAULT_PRICE,
            "payment_info": DEFAULT_PAYMENT_INFO,
        }
        changed = True
    else:
        if "price" not in data["settings"]:
            data["settings"]["price"] = DEFAULT_PRICE
            changed = True
        if "payment_info" not in data["settings"]:
            data["settings"]["payment_info"] = DEFAULT_PAYMENT_INFO
            changed = True

    if changed:
        _save(data)
    return data


def _save(data: dict) -> None:
    with DATA_PATH.open("w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_user(chat_id: int, name: str, username: str | None, role: str = "member") -> None:
    data = _load()
    uid = str(chat_id)
    if uid not in data["users"]:
        data["users"][uid] = {"name": name, "username": username, "role": role}
        _save(data)


def update_user_contact(chat_id: int, name: str | None, username: str | None) -> bool:
    """Update name/username of an existing user if values changed.

    Returns True when something was written. No-op if the user is unknown
    or both fields already match.
    """
    data = _load()
    uid = str(chat_id)
    user = data["users"].get(uid)
    if user is None:
        return False

    changed = False
    if name and user.get("name") != name:
        user["name"] = name
        changed = True
    if username and user.get("username") != username:
        user["username"] = username
        changed = True

    if changed:
        _save(data)
    return changed


def remove_user(chat_id: int) -> None:
    data = _load()
    uid = str(chat_id)
    data["users"].pop(uid, None)
    for month in data["payments"]:
        data["payments"][month].pop(uid, None)
    _save(data)


def list_users() -> dict:
    return _load()["users"]


def list_members(admin_id: int) -> dict:
    return {uid: info for uid, info in list_users().items() if int(uid) != admin_id}


def set_paid(chat_id: int, month: str) -> None:
    data = _load()
    data["payments"].setdefault(month, {})[str(chat_id)] = True
    _save(data)


def unpaid(month: str, admin_id: int) -> list[int]:
    data = _load()
    users = list_members(admin_id)
    paid = data["payments"].get(month, {})
    return [int(uid) for uid in users if uid not in paid]


def get_setting(key: str, default: str = "") -> str:
    return _load()["settings"].get(key, default)


def set_setting(key: str, value: str) -> None:
    data = _load()
    data["settings"][key] = value
    _save(data)


def get_price() -> str:
    return get_setting("price", DEFAULT_PRICE)


def get_payment_info() -> str:
    return get_setting("payment_info", DEFAULT_PAYMENT_INFO)
