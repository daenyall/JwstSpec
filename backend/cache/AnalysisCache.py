import json
import re
from pathlib import Path


class AnalysisCache:
    def __init__(self, cache_dir="./analysis_cache", version="v1"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.version = version

    def get(self, target, bin_width):
        cache_path = self._get_cache_path(target, bin_width)

        if not cache_path.exists():
            return None

        with cache_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def save(self, target, bin_width, data):
        cache_path = self._get_cache_path(target, bin_width)

        with cache_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    def _get_cache_path(self, target, bin_width):
        safe_target = re.sub(r"[^a-zA-Z0-9_-]", "_", target.lower())
        filename = f"{safe_target}_{bin_width}_{self.version}.json"

        return self.cache_dir / filename