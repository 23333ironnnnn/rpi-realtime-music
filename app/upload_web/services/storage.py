from __future__ import annotations

import os
import time
import uuid
from pathlib import Path

from werkzeug.datastructures import FileStorage


def is_probably_mp3_header(head: bytes) -> bool:
    if len(head) < 2:
        return False
    if head.startswith(b"ID3"):
        return True
    # MPEG-1 Layer 3 frame sync
    if head[0] == 0xFF and head[1] in (0xFB, 0xFA, 0xF3, 0xF2):
        return True
    return False


class UploadError(Exception):
    code: str

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def save_mp3_atomic(
    file_storage: FileStorage,
    inbox_dir: str,
    max_bytes: int,
) -> tuple[str, int]:
    """
    Stream upload to inbox_dir/<ts>_<uuid>.mp3 via *.part then rename.
    Returns (basename, size).
    """
    name = file_storage.filename or ""
    if Path(name).suffix.lower() != ".mp3":
        raise UploadError("invalid_extension", "Only .mp3 files are allowed")

    stream = file_storage.stream
    try:
        stream.seek(0)
    except OSError:
        pass
    head = stream.read(4)
    try:
        stream.seek(0)
    except OSError:
        pass

    if not is_probably_mp3_header(head):
        raise UploadError("not_mp3", "File does not look like MP3")

    ts = int(time.time() * 1000)
    uid = uuid.uuid4().hex
    final_name = f"{ts}_{uid}.mp3"
    inbox = Path(inbox_dir)
    part_path = inbox / f"{final_name}.part"
    final_path = inbox / final_name

    total = 0
    chunk_size = 64 * 1024
    try:
        with open(part_path, "wb") as out:
            while True:
                chunk = stream.read(chunk_size)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise UploadError("too_large", "File too large")
                out.write(chunk)
        os.rename(part_path, final_path)
    except UploadError:
        part_path.unlink(missing_ok=True)
        raise
    except OSError:
        part_path.unlink(missing_ok=True)
        raise

    return final_name, total
