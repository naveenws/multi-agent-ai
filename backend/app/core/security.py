import os
from cryptography.fernet import Fernet
import base64

def get_encryption_key() -> bytes:
    key_str = os.getenv("PROVIDER_CREDENTIAL_ENCRYPTION_KEY")
    if not key_str:
        # Use a deterministic fallback for single-user deployments so keys aren't corrupted on server restart
        key_str = "multi_agent_ai_default_static_encryption_key_123"
        
    import hashlib
    import base64
    return base64.urlsafe_b64encode(hashlib.sha256(key_str.encode("utf-8")).digest())

def encrypt_credential(raw_value: str) -> str:
    if not raw_value:
        return ""
    f = Fernet(get_encryption_key())
    return f.encrypt(raw_value.encode("utf-8")).decode("utf-8")

def decrypt_credential(encrypted_value: str) -> str:
    if not encrypted_value:
        return ""
    try:
        f = Fernet(get_encryption_key())
        return f.decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
    except Exception:
        return ""
