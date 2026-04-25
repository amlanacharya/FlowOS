from abc import ABC, abstractmethod
from typing import Optional


class BaseNotificationProvider(ABC):
    """Abstract base class for notification providers."""

    @abstractmethod
    async def send(
        self,
        to_phone: str,
        template_name: str,
        params: dict,
    ) -> str:
        """
        Send a notification to a phone number.

        Args:
            to_phone: Phone number in E.164 format (e.g., +91XXXXXXXXXX)
            template_name: Name of the template to use (e.g., 'subscription_expiry_reminder')
            params: Dictionary of template parameters

        Returns:
            Provider's message reference ID

        Raises:
            Exception: If sending fails
        """
        ...
