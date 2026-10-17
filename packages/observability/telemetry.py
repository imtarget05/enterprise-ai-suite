"""
Observability & Telemetry Module for Langfuse Cloud and OpenTelemetry.
"""

from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional


class TelemetryTracker:
    def __init__(self, public_key: Optional[str] = None, secret_key: Optional[str] = None, host: str = "https://cloud.langfuse.com"):
        self.public_key = public_key
        self.secret_key = secret_key
        self.host = host
        self._langfuse = None

        if self.public_key and self.secret_key:
            try:
                from langfuse import Langfuse
                self._langfuse = Langfuse(public_key=self.public_key, secret_key=self.secret_key, host=self.host)
            except Exception:
                pass

    @contextmanager
    def trace_span(self, name: str, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> Generator[Dict[str, Any], None, None]:
        span_data = {"name": name, "user_id": user_id, "metadata": metadata or {}, "status": "SUCCESS"}
        try:
            yield span_data
        except Exception as e:
            span_data["status"] = "ERROR"
            span_data["error"] = str(e)
            raise
        finally:
            if self._langfuse:
                try:
                    trace = self._langfuse.trace(name=name, user_id=user_id, metadata=span_data["metadata"])
                    trace.span(name=name, metadata=span_data)
                except Exception:
                    pass


telemetry = TelemetryTracker()
