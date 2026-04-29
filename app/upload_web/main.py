from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from flask import Flask, jsonify

from upload_web.config import Config


def _load_dotenv_if_present() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    # app/.env next to package upload_web
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.is_file():
        load_dotenv(env_path)


def _ensure_inbox_writable(inbox_dir: str) -> None:
    if not os.path.isdir(inbox_dir):
        print(f"ERROR: INBOX_DIR is not a directory: {inbox_dir}", file=sys.stderr)
        sys.exit(1)
    if not os.access(inbox_dir, os.W_OK):
        print(f"ERROR: INBOX_DIR is not writable: {inbox_dir}", file=sys.stderr)
        sys.exit(1)


def create_app() -> Flask:
    _load_dotenv_if_present()
    cfg = Config.from_env()
    if not cfg.upload_web_password:
        print(
            "ERROR: UPLOAD_WEB_PASSWORD must be set (e.g. in environment or app/.env)",
            file=sys.stderr,
        )
        sys.exit(1)

    _ensure_inbox_writable(cfg.inbox_dir)

    root = Path(__file__).resolve().parent
    app = Flask(
        __name__,
        template_folder=str(root / "templates"),
        static_folder=str(root / "static"),
    )
    app.config["MAX_CONTENT_LENGTH"] = cfg.max_upload_bytes
    app.config["UPLOAD_WEB"] = cfg

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    from upload_web.routes.health import bp as health_bp
    from upload_web.routes.upload import bp as upload_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(upload_bp)

    @app.errorhandler(413)
    def too_large(_e):
        return jsonify(ok=False, error="payload_too_large"), 413

    return app


def main() -> None:
    app = create_app()
    cfg: Config = app.config["UPLOAD_WEB"]
    app.run(host="0.0.0.0", port=cfg.port, threaded=True, debug=False)


if __name__ == "__main__":
    main()
