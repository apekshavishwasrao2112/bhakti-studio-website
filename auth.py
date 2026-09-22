from functools import wraps

from flask import current_app, jsonify, redirect, request, session, url_for


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin"):
            wants_json = (
                request.path == "/admin-ai-chat"
                or request.accept_mimetypes.best == "application/json"
            )
            if wants_json:
                return jsonify({
                    "success": False,
                    "message": "Admin authentication required.",
                }), 401
            return redirect(url_for("admin_login"))
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            current_app.extensions["csrf"].protect()
        return view(*args, **kwargs)

    wrapped_view._csrf_exempt = True
    return wrapped_view
