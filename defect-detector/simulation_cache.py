"""Disk-backed cache for simulation results with TTL expiration."""
import hashlib
import json
import os
import pickle
import time
from typing import Any, Optional

import numpy as np

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.simulation_cache')
DEFAULT_TTL_SECONDS = 3600  # 1 hour


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def _path_for(key: str) -> str:
    return os.path.join(CACHE_DIR, f'{key}.pkl')


def _hash_part(hasher, part: Any) -> None:
    if isinstance(part, np.ndarray):
        hasher.update(b'ndarray')
        hasher.update(str(part.shape).encode())
        hasher.update(str(part.dtype).encode())
        hasher.update(np.ascontiguousarray(part).tobytes())
    elif isinstance(part, (list, tuple)):
        hasher.update(b'seq')
        hasher.update(json.dumps(part, sort_keys=True, default=str).encode())
    elif isinstance(part, dict):
        hasher.update(b'dict')
        hasher.update(json.dumps(part, sort_keys=True, default=str).encode())
    else:
        hasher.update(b'scalar')
        hasher.update(str(part).encode())
    hasher.update(b'|')


def make_key(*parts: Any) -> str:
    """Build a stable SHA256 cache key from arbitrary inputs."""
    hasher = hashlib.sha256()
    for part in parts:
        _hash_part(hasher, part)
    return hasher.hexdigest()


def get(key: str, ttl: float = DEFAULT_TTL_SECONDS) -> Optional[Any]:
    """Return cached value for key, or None if missing/expired/corrupt."""
    path = _path_for(key)
    if not os.path.exists(path):
        return None
    age = time.time() - os.path.getmtime(path)
    if age > ttl:
        try:
            os.remove(path)
        except OSError:
            pass
        return None
    try:
        with open(path, 'rb') as f:
            return pickle.load(f)
    except (pickle.PickleError, EOFError, OSError):
        return None


def set(key: str, value: Any) -> None:
    """Persist value under key (atomic write via tmp + rename)."""
    _ensure_cache_dir()
    path = _path_for(key)
    tmp = path + '.tmp'
    with open(tmp, 'wb') as f:
        pickle.dump(value, f)
    os.replace(tmp, path)
