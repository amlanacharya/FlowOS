from uuid import uuid4

from .base import BaseNotificationProvider


class StubProvider(BaseNotificationProvider):
    """Stub notification provider that logs to stdout. Use for development."""

    async def send(
        self,
        to_phone: str,
        template_name: str,
        params: dict,
    ) -> str:
        """Send notification by logging to stdout."""
        msg_id = f"stub-{uuid4()}"
        print(f"[NOTIFICATION] To: {to_phone} | Template: {template_name} | Params: {params} | MsgID: {msg_id}")
        return msg_id
