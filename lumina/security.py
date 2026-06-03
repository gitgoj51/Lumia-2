"""Local-first security controls.

Lumina is designed to work only with local files. It does not use external
APIs, telemetry, network storage, or secrets. This module offers a lightweight
runtime guard that can block common socket-based network access during analysis.
"""

from __future__ import annotations

import socket
from contextlib import contextmanager
from pathlib import Path
from types import TracebackType
from typing import Iterator


class NetworkAccessBlocked(RuntimeError):
    """Raised when code attempts network access while Lumina is running."""


class LocalFirstGuard:
    """Temporarily blocks common Python socket calls.

    The guard is intentionally small and dependency-free. It reduces accidental
    network use from libraries while keeping Lumina focused on local files.
    """

    def __init__(self) -> None:
        self._original_socket = socket.socket
        self._original_create_connection = socket.create_connection

    def __enter__(self) -> "LocalFirstGuard":
        def blocked_socket(*args: object, **kwargs: object) -> socket.socket:
            raise NetworkAccessBlocked("Network access is disabled by Lumina's local-first guard.")

        def blocked_create_connection(*args: object, **kwargs: object) -> socket.socket:
            raise NetworkAccessBlocked("Network access is disabled by Lumina's local-first guard.")

        socket.socket = blocked_socket  # type: ignore[assignment]
        socket.create_connection = blocked_create_connection  # type: ignore[assignment]
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        socket.socket = self._original_socket
        socket.create_connection = self._original_create_connection


@contextmanager
def enforce_local_first() -> Iterator[None]:
    """Context manager that blocks accidental network activity."""

    with LocalFirstGuard():
        yield


def assert_local_path(path: str | Path) -> Path:
    """Return a normalized local path and reject URL-like inputs."""

    candidate = Path(path)
    text = str(path).lower()
    if text.startswith(("http://", "https://", "ftp://", "s3://", "gs://")):
        raise ValueError("Lumina accepts local filesystem paths only, not URLs.")
    return candidate
