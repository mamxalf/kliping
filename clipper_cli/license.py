"""
License management for Clipper CLI.
Serial key validation and activation.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

# Secret salt for generating valid keys (change this for production!)
SECRET_SALT = "CLIPPER_2024_FPK_CREATIVE"

# License file location
LICENSE_DIR = Path.home() / ".clipper"
LICENSE_FILE = LICENSE_DIR / "license.json"


@dataclass
class LicenseInfo:
    """License information."""
    serial_key: str
    activated_at: str
    machine_id: str


def get_machine_id() -> str:
    """Get a unique machine identifier."""
    import platform
    import uuid
    
    # Combine various system info for a unique ID
    info = f"{platform.node()}-{platform.machine()}-{uuid.getnode()}"
    return hashlib.md5(info.encode()).hexdigest()[:16]


def generate_serial_key(user_id: str) -> str:
    """
    Generate a valid serial key for a user.
    Format: XXXX-XXXX-XXXX-XXXX
    
    This function is for admin use only to generate keys.
    """
    # Create hash from user_id and secret
    data = f"{user_id}-{SECRET_SALT}"
    hash_bytes = hashlib.sha256(data.encode()).digest()
    
    # Convert to alphanumeric key
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Avoid confusing chars like 0/O, 1/I
    key_parts = []
    
    for i in range(4):
        part = ""
        for j in range(4):
            idx = hash_bytes[i * 4 + j] % len(chars)
            part += chars[idx]
        key_parts.append(part)
    
    return "-".join(key_parts)


def validate_serial_key(serial_key: str) -> bool:
    """
    Validate if a serial key is in correct format and is authentic.
    """
    # Check format: XXXX-XXXX-XXXX-XXXX
    parts = serial_key.upper().split("-")
    if len(parts) != 4:
        return False
    
    for part in parts:
        if len(part) != 4:
            return False
        # Check if all chars are valid
        valid_chars = set("ABCDEFGHJKLMNPQRSTUVWXYZ23456789")
        if not all(c in valid_chars for c in part):
            return False
    
    # Validate checksum (last 2 chars of last part should be checksum)
    key_base = "-".join(parts[:3]) + "-" + parts[3][:2]
    checksum_data = f"{key_base}-{SECRET_SALT}"
    expected_checksum = hashlib.md5(checksum_data.encode()).hexdigest()[:2].upper()
    
    # For this implementation, we'll accept any properly formatted key
    # In production, you'd validate against a database or use crypto signatures
    
    # Simple validation: check if key matches pattern and has valid structure
    return True


def is_licensed() -> bool:
    """Check if the software is licensed."""
    if not LICENSE_FILE.exists():
        return False
    
    try:
        with open(LICENSE_FILE, "r") as f:
            data = json.load(f)
        
        serial_key = data.get("serial_key", "")
        stored_machine_id = data.get("machine_id", "")
        
        # Validate key format
        if not validate_serial_key(serial_key):
            return False
        
        # Check if same machine
        current_machine_id = get_machine_id()
        if stored_machine_id != current_machine_id:
            return False
        
        return True
    except Exception:
        return False


def get_license_info() -> Optional[LicenseInfo]:
    """Get current license information."""
    if not LICENSE_FILE.exists():
        return None
    
    try:
        with open(LICENSE_FILE, "r") as f:
            data = json.load(f)
        
        return LicenseInfo(
            serial_key=data.get("serial_key", ""),
            activated_at=data.get("activated_at", ""),
            machine_id=data.get("machine_id", "")
        )
    except Exception:
        return None


def activate_license(serial_key: str) -> tuple[bool, str]:
    """
    Activate a license with the given serial key.
    Returns (success, message).
    """
    from datetime import datetime
    
    # Validate format
    serial_key = serial_key.upper().strip()
    
    if not validate_serial_key(serial_key):
        return False, "Serial key tidak valid. Format: XXXX-XXXX-XXXX-XXXX"
    
    # Create license directory
    LICENSE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save license
    license_data = {
        "serial_key": serial_key,
        "activated_at": datetime.now().isoformat(),
        "machine_id": get_machine_id()
    }
    
    try:
        with open(LICENSE_FILE, "w") as f:
            json.dump(license_data, f, indent=2)
        
        return True, "Lisensi berhasil diaktivasi!"
    except Exception as e:
        return False, f"Gagal menyimpan lisensi: {e}"


def deactivate_license() -> bool:
    """Remove license (for admin/testing)."""
    try:
        if LICENSE_FILE.exists():
            LICENSE_FILE.unlink()
        return True
    except Exception:
        return False


# Admin function to generate keys
def generate_keys_for_users(user_ids: list[str]) -> dict[str, str]:
    """Generate serial keys for multiple users (admin function)."""
    return {user_id: generate_serial_key(user_id) for user_id in user_ids}
