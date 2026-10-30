"""Historial en memoria de los últimos resúmenes generados en la sesión."""
import os
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional

DEFAULT_MAX_HISTORY = 5


def max_history_from_env() -> int:
    try:
        value = int(os.getenv("MAX_HISTORY", DEFAULT_MAX_HISTORY))
    except ValueError:
        return DEFAULT_MAX_HISTORY
    return max(value, 1)


class SessionHistory:
    def __init__(self, max_items: Optional[int] = None):
        self._items = deque(maxlen=max_items or max_history_from_env())

    def add(self, text: str, simulated: bool, audio_simulated: Optional[bool] = None) -> Dict:
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "text": text,
            "simulated": simulated,
            "audio_simulated": audio_simulated,
        }
        self._items.append(entry)
        return entry

    def items(self) -> List[Dict]:
        """Entradas de la más reciente a la más antigua."""
        return list(reversed(self._items))

    def __len__(self) -> int:
        return len(self._items)
