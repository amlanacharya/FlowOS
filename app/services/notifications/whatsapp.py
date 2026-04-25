import os
from typing import Optional

import httpx

from .base import BaseNotificationProvider


class WhatsAppProvider(BaseNotificationProvider):
    """WhatsApp notification provider using Meta Cloud API."""

    def __init__(self):
        self.token = os.environ.get("WHATSAPP_TOKEN", "")
        self.phone_id = os.environ.get("WHATSAPP_PHONE_ID", "")
        self.api_url = "https://graph.facebook.com/v18.0"

    async def send(
        self,
        to_phone: str,
        template_name: str,
        params: dict,
    ) -> str:
        """
        Send WhatsApp message using Meta Cloud API.

        Args:
            to_phone: Phone number in E.164 format
            template_name: WhatsApp template name
            params: Template parameters for body text substitution

        Returns:
            Message ID from WhatsApp API
        """
        if not self.token or not self.phone_id:
            raise ValueError("WHATSAPP_TOKEN and WHATSAPP_PHONE_ID environment variables required")

        # Build template parameters
        template_params = [{"type": "text", "text": str(v)} for v in params.values()]

        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en_US"},
                "components": [{"type": "body", "parameters": template_params}],
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/{self.phone_id}/messages",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
            )

            if not response.is_success:
                raise Exception(f"WhatsApp API error: {response.status_code} - {response.text}")

            data = response.json()
            return data["messages"][0]["id"]
