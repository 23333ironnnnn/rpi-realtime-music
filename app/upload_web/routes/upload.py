from __future__ import annotations

import logging

from flask import Blueprint, current_app, jsonify, render_template, request

from upload_web.auth import require_basic
from upload_web.services.storage import UploadError, save_mp3_atomic

log = logging.getLogger(__name__)

bp = Blueprint("upload", __name__)


@bp.route("/")
@require_basic
def index():
    return render_template("index.html")


@bp.route("/upload", methods=["POST"])
@require_basic
def upload():
    cfg = current_app.config["UPLOAD_WEB"]
    f = request.files.get("file")
    if not f:
        log.info("upload_no_file ip=%s", request.remote_addr)
        return jsonify(ok=False, error="no_file"), 400

    try:
        basename, size = save_mp3_atomic(f, cfg.inbox_dir, cfg.max_upload_bytes)
    except UploadError as e:
        log.info(
            "upload_rejected code=%s ip=%s",
            e.code,
            request.remote_addr,
        )
        status = 413 if e.code == "too_large" else 400
        return jsonify(ok=False, error=e.code), status

    log.info(
        "upload_ok ip=%s saved=%s bytes=%s",
        request.remote_addr,
        basename,
        size,
    )

    body: dict = {"ok": True, "path": basename, "size": size}
    if cfg.run_pipeline_on_upload:
        from upload_web.services.pipeline_runner import spawn_run_pipeline

        spawned = spawn_run_pipeline(
            cfg.run_pipeline_script,
            cfg.run_pipeline_spawn_log or None,
        )
        body["pipeline_spawned"] = spawned

    return jsonify(body), 200
