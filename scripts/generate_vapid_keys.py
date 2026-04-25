#!/usr/bin/env python
"""Generate VAPID keys for web push notifications."""
import sys
import base64

try:
    from pywebpush import generate_vapid_keys
except ImportError:
    print("Error: pywebpush not installed")
    print("Install with: pip install pywebpush")
    sys.exit(1)

vapid_keys = generate_vapid_keys()

print("\n" + "=" * 60)
print("VAPID Keys for Web Push Notifications")
print("=" * 60)
print("\nAdd these to your .env file:\n")
print(f"VAPID_PUBLIC_KEY={vapid_keys['public_key'].decode('utf-8')}")
print(f"VAPID_PRIVATE_KEY={vapid_keys['private_key'].decode('utf-8')}")
print(f"VAPID_EMAIL=admin@flowos.local\n")
print("=" * 60)
print("\nAlso add to frontend .env:\n")
print(f"REACT_APP_VAPID_PUBLIC_KEY={vapid_keys['public_key'].decode('utf-8')}\n")
print("=" * 60)
