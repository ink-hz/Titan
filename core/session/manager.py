"""
Titan Session Manager — Multi-turn conversation and context management.

Handles conversation history, context window limits, and session persistence.

Usage:
    session = SessionManager()
    sid = session.create()
    session.add_message(sid, "user", "What's the security status?")
    session.add_message(sid, "assistant", "Overall status is stable...")
    history = session.get_history(sid, max_messages=20)
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Message:
    """A single message in a conversation."""
    role: str           # "system", "user", "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)  # tool_calls, components, etc.


@dataclass
class Session:
    """A conversation session with history."""
    id: str
    messages: List[Message] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    context: Dict = field(default_factory=dict)  # Session-level context/state


class SessionManager:
    """
    Manages conversation sessions.

    Features:
    - Create/retrieve sessions
    - Add messages with metadata
    - Context window management (truncate old messages)
    - Session-level state storage
    """

    def __init__(self, max_history: int = 50, session_timeout: int = 3600):
        self._sessions: Dict[str, Session] = {}
        self.max_history = max_history
        self.session_timeout = session_timeout

    def create(self, session_id: str = None) -> str:
        """Create a new session. Returns session ID."""
        sid = session_id or str(uuid.uuid4())
        self._sessions[sid] = Session(id=sid)
        return sid

    def get(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        session = self._sessions.get(session_id)
        if session:
            session.last_active = time.time()
        return session

    def add_message(self, session_id: str, role: str, content: str, metadata: dict = None):
        """Add a message to session history."""
        session = self.get(session_id)
        if not session:
            session = Session(id=session_id)
            self._sessions[session_id] = session

        msg = Message(role=role, content=content, metadata=metadata or {})
        session.messages.append(msg)

        # Trim if exceeding max
        if len(session.messages) > self.max_history:
            # Keep system messages + trim oldest user/assistant messages
            system_msgs = [m for m in session.messages if m.role == "system"]
            other_msgs = [m for m in session.messages if m.role != "system"]
            keep = self.max_history - len(system_msgs)
            session.messages = system_msgs + other_msgs[-keep:]

    def get_history(self, session_id: str, max_messages: int = None) -> List[Dict]:
        """Get message history formatted for LLM API call."""
        session = self.get(session_id)
        if not session:
            return []

        messages = session.messages
        if max_messages:
            # Keep system messages + last N
            system = [m for m in messages if m.role == "system"]
            others = [m for m in messages if m.role != "system"]
            messages = system + others[-(max_messages - len(system)):]

        return [{"role": m.role, "content": m.content} for m in messages]

    def set_context(self, session_id: str, key: str, value):
        """Set session-level context."""
        session = self.get(session_id)
        if session:
            session.context[key] = value

    def get_context(self, session_id: str, key: str, default=None):
        """Get session-level context."""
        session = self.get(session_id)
        return session.context.get(key, default) if session else default

    def cleanup_expired(self):
        """Remove expired sessions."""
        now = time.time()
        expired = [sid for sid, s in self._sessions.items() if now - s.last_active > self.session_timeout]
        for sid in expired:
            del self._sessions[sid]
