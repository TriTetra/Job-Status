"""Load company knowledge from knowledge/v1/companies/*.yaml."""

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

import yaml


class CompanyLoader:
    def __init__(self, version: str = "v1"):
        self.base_path = Path(__file__).parent.parent.parent / "knowledge" / version / "companies"

    @lru_cache(maxsize=1)
    def load_all(self) -> Dict[str, dict]:
        companies: Dict[str, dict] = {}

        for yaml_file in self.base_path.glob("*.yaml"):
            if yaml_file.stem.startswith("company_memory_schema"):
                continue

            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            tier = data.get("tier", "unknown")
            shared = data.get("shared", {})

            for name, info in data.get("companies", {}).items():
                merged = {**shared, **info, "tier": tier}
                companies[name] = merged

        return companies

    def get_company(self, name: str) -> Optional[dict]:
        name_lower = name.lower()
        for key, value in self.load_all().items():
            if key.lower() == name_lower:
                return value
        return None

    def get_by_tier(self, tier: str) -> Dict[str, dict]:
        return {n: d for n, d in self.load_all().items() if d.get("tier") == tier}

    def list_all(self) -> List[str]:
        return list(self.load_all().keys())
