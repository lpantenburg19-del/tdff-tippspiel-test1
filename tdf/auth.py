import hmac
from functools import wraps

from flask import current_app, redirect, session, url_for

from .models import Player


def current_player():
    player_id = session.get("player_id")
    if not player_id:
        return None
    return Player.query.get(player_id)


def player_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_player() is None:
            session.pop("player_id", None)
            return redirect(url_for("player.join"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)

    return wrapped


def check_admin_password(candidate):
    expected = current_app.config["ADMIN_PASSWORD"]
    return hmac.compare_digest(candidate or "", expected)
