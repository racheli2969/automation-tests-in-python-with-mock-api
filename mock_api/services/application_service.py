import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from collections import defaultdict

from ..config.settings import MAX_REQUESTS_PER_MINUTE
# rules for idempotent create:
#     name must be unique after trim + case-fold (e.g., " My-App " conflicts with
# "my-app").
# ● The same Idempotency-Key (for the same token) must return the original response
# (do not create another resource).
# ● Rate limit: Max 5 create attempts per minute per token → 429 Too Many
# Requests + Retry-After (seconds).
# Possible errors: 409 Conflict (name not unique), 429 Too Many Requests
class RateLimiter:
    def __init__(self):
        self._records = defaultdict(list)
    
    def check_rate_limit(self, token: str) -> Tuple[bool, Optional[int]]:
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old records
        self._records[token] = [t for t in self._records[token] if t > minute_ago]
        
        # Check limit
        if len(self._records[token]) >= MAX_REQUESTS_PER_MINUTE:
            retry_after = int((self._records[token][0] - minute_ago).total_seconds())
            return False, max(0, retry_after)
        
        self._records[token].append(now)
        return True, None

class IdempotencyService:
    def __init__(self):
        self._records = defaultdict(dict)
    
    def get_record(self, token: str, key: str):
        return self._records[token].get(key)
    
    def store_record(self, token: str, key: str, response):
        self._records[token][key] = response

class ApplicationService:
    def __init__(self):
        self._applications = {}
    
    @staticmethod
    def normalize_name(name: str) -> str:
        return name.strip().lower()
    
    @staticmethod
    def generate_etag(version: int, data: dict) -> str:
        content = f"{version}:{str(data)}"
        return f'"{hashlib.md5(content.encode()).hexdigest()}"'
    
    #     name must be unique after trim + case-fold (e.g., " My-App " conflicts with
# "my-app")
    def is_name_unique(self, name: str, exclude_id: Optional[str] = None) -> bool:
        normalized_name = self.normalize_name(name)
        return not any(
            app_id != exclude_id and self.normalize_name(app["name"]) == normalized_name
            for app_id, app in self._applications.items()
        )
    
    def get_application(self, app_id: str):
        return self._applications.get(app_id)
    
    def create_application(self, app_id: str, app_data: dict):
        self._applications[app_id] = app_data
        return app_data
    
    def update_application(self, app_id: str, app_data: dict):
        self._applications[app_id] = app_data
        return app_data