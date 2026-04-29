from __future__ import annotations

from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)


@bp.route("/health")
def health():
    # Public (no Basic) for systemd / curl probes; see PRD §11 E4.
    return jsonify(ok=True)
