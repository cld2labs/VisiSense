import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from cachetools import TTLCache


class SessionStore:
    """In-memory session store with TTL for chat sessions."""

    def __init__(self, ttl_minutes: int = 30):
        """Initialize session store with TTL cache."""
        self.ttl_seconds = ttl_minutes * 60
        # maxsize=1000 means we can store up to 1000 sessions
        self.cache: TTLCache = TTLCache(maxsize=1000, ttl=self.ttl_seconds)

    def create_session(self, images: List[bytes], product_data: Optional[Dict] = None) -> str:
        """Create a new session and return session ID."""
        session_id = str(uuid.uuid4())
        self.cache[session_id] = {
            "images": images,
            "product_data": product_data,
            "created_at": datetime.now()
        }
        return session_id

    def update_product_data(self, session_id: str, product_data: Dict) -> bool:
        """Update product analysis data for an existing session."""
        session = self.get_session(session_id)
        if session:
            session["product_data"] = product_data
            self.cache[session_id] = session
            return True
        return False

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve session data by ID."""
        return self.cache.get(session_id)

    def get_images(self, session_id: str) -> Optional[List[bytes]]:
        """Retrieve images from session."""
        session = self.get_session(session_id)
        if session:
            return session.get("images")
        return None

    def get_product_data(self, session_id: str) -> Optional[Dict]:
        """Retrieve product analysis data from session."""
        session = self.get_session(session_id)
        if session:
            return session.get("product_data")
        return None

    def session_exists(self, session_id: str) -> bool:
        """Check if session exists and hasn't expired."""
        return session_id in self.cache

    def cleanup_expired(self):
        """
        Cleanup is automatic with TTLCache.
        This method exists for explicit cleanup if needed.
        """
        # TTLCache handles cleanup automatically
        pass


# Global session store instance
session_store = SessionStore()
