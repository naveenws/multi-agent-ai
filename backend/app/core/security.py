import os
from cryptography.fernet import Fernet
import base64

def get_encryption_key() -> bytes:
    key_str = os.getenv("PROVIDER_CREDENTIAL_ENCRYPTION_KEY")
    if not key_str:
        # Generate a temporary one if missing, though in prod it should be set
        # We use a static fallback for development only to prevent crashes, but warn
        key = Fernet.generate_key()
        os.environ["PROVIDER_CREDENTIAL_ENCRYPTION_KEY"] = key.decode("utf-8")
        return key
    
    # Ensure it's 32 url-safe base64-encoded bytes
    if len(key_str) == 44:
        return key_str.encode("utf-8")
        
    # Pad or fix incorrect keys for dev ease
    import hashlib
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
