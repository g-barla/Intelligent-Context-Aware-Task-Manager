
import json
import os
from datetime import datetime

class Memory:
    PATH = "mcp_memory.json"

    def __init__(self):
        if os.path.exists(self.PATH):
            with open(self.PATH, "r") as f:
                self.data = json.load(f)
        else:
            self.data = {
                "completions_count": 0,
                "user_rules": {
                    "prefer_deadline": True,
                    "prefer_high_priority": True
                },
                "last_updated": datetime.utcnow().isoformat()
            }
            self._save()

    def _save(self):
        self.data["last_updated"] = datetime.utcnow().isoformat()
        with open(self.PATH, "w") as f:
            json.dump(self.data, f, indent=2)

    def record_completion(self):
        self.data["completions_count"] = self.data.get("completions_count", 0) + 1
        self._save()

    def rules(self):
        return self.data.get("user_rules", {})

    def set_rule(self, key, value):
        self.data.setdefault("user_rules", {})[key] = value
        self._save()
