import json
import os
from typing import Optional

from .base import BaseNotificationProvider

try:
    from pywebpush import webpush
    PYWEBPUSH_AVAILABLE = True
except ImportError:
    PYWEBPUSH_AVAILABLE = False
    webpush = None


class WebPushProvider(BaseNotificationProvider):
    """Web Push Notification Provider using VAPID protocol."""

    def __init__(self):
        self.vapid_public_key = os.environ.get("VAPID_PUBLIC_KEY")
        self.vapid_private_key = os.environ.get("VAPID_PRIVATE_KEY")
        self.vapid_claims = {
            "sub": os.environ.get("VAPID_EMAIL", "admin@flowos.local")
        }

    async def send(
        self,
        to_phone: str,
        template_name: str,
        params: dict,
    ) -> Optional[str]:
        """
        Send web push notification.

        Args:
            to_phone: Push subscription token (treated as phone for interface compatibility)
            template_name: Message template name
            params: Parameters for message body

        Returns:
            Message ID from push service or subscription endpoint
        """
        if not PYWEBPUSH_AVAILABLE:
            raise RuntimeError("pywebpush not installed. Run: pip install pywebpush")

        if not self.vapid_private_key or not self.vapid_public_key:
            raise ValueError("VAPID keys not configured for web push")

        try:
            subscription_info = json.loads(to_phone)
            message_body = self._render_message(template_name, params)

            webpush(
                subscription_info=subscription_info,
                data=json.dumps({
                    "title": self._get_title(template_name),
                    "body": message_body,
                    "icon": "/icon-192x192.png",
                }),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims,
                timeout=10,
            )

            return subscription_info.get("endpoint", "pushed")
        except json.JSONDecodeError:
            raise ValueError("Invalid push subscription token format")
        except Exception as e:
            raise RuntimeError(f"Web push failed: {str(e)}")

    def _render_message(self, template_name: str, params: dict) -> str:
        """Render message from template."""
        templates = {
            "subscription_renewed": "Your membership has been renewed",
            "payment_confirmed": f"Payment of {params.get('amount', '₹0')} confirmed",
            "trial_expiring": f"Trial expiring in {params.get('days', 3)} days",
            "dues_overdue": f"Outstanding dues: {params.get('amount', '₹0')}",
            "class_enrollment": f"Enrolled in {params.get('class_name', 'class')}",
        }
        return templates.get(template_name, "New notification from FlowOS")

    def _get_title(self, template_name: str) -> str:
        """Get notification title from template."""
        titles = {
            "subscription_renewed": "Membership Renewed",
            "payment_confirmed": "Payment Confirmed",
            "trial_expiring": "Trial Expiring Soon",
            "dues_overdue": "Outstanding Dues",
            "class_enrollment": "Class Enrollment",
        }
        return titles.get(template_name, "FlowOS Notification")
