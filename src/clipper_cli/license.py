"""License management for Clipper CLI.

This module handles license key validation and activation.
License keys use HMAC-SHA256 for secure offline validation.

License Key Format: CLIPPER-XXXX-XXXX-XXXX-XXXX
Where each XXXX is a 4-character alphanumeric segment.
"""

import hashlib
import hmac
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


# Secret key for HMAC validation - embedded in executable
# This should be kept secret and NOT shared publicly
_SECRET_KEY = b"ClipperCLI_2024_SecretKey_DoNotShare_v1.0.0"

# License key pattern
LICENSE_PATTERN = re.compile(
    r'^CLIPPER-([A-Z0-9]{4})-([A-Z0-9]{4})-([A-Z0-9]{4})-([A-Z0-9]{4})$'
)


@dataclass
class LicenseInfo:
    """Information about an activated license."""
    key: str
    activated_at: str
    machine_id: str
    
    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "activated_at": self.activated_at,
            "machine_id": self.machine_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "LicenseInfo":
        return cls(
            key=data["key"],
            activated_at=data["activated_at"],
            machine_id=data["machine_id"],
        )
    
    @property
    def masked_key(self) -> str:
        """Return masked version of the key for display."""
        if len(self.key) > 15:
            return self.key[:12] + "****-****"
        return "****-****-****-****"


def _get_machine_id() -> str:
    """Generate a unique machine identifier."""
    import platform
    import uuid
    
    # Combine multiple system identifiers
    components = [
        platform.node(),
        platform.machine(),
        platform.processor(),
        str(uuid.getnode()),  # MAC address
    ]
    
    # Hash the combination
    combined = "|".join(components)
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def _generate_signature(data: str) -> str:
    """Generate HMAC-SHA256 signature for data."""
    return hmac.new(
        _SECRET_KEY,
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:16].upper()


def validate_key_format(key: str) -> bool:
    """Validate that the key matches the expected format."""
    return bool(LICENSE_PATTERN.match(key.upper().strip()))


def validate_license_key(key: str) -> bool:
    """
    Validate a license key using HMAC signature verification.
    
    The key format is: CLIPPER-XXXX-XXXX-XXXX-XXXX
    Where the last segment is a checksum of the first three.
    """
    key = key.upper().strip()
    
    if not validate_key_format(key):
        return False
    
    match = LICENSE_PATTERN.match(key)
    if not match:
        return False
    
    # Extract segments
    seg1, seg2, seg3, checksum = match.groups()
    
    # Verify checksum - last segment should be derived from first three
    data = f"{seg1}-{seg2}-{seg3}"
    expected_checksum = _generate_signature(data)[:4]
    
    return checksum == expected_checksum


def generate_license_key(identifier: str = "") -> str:
    """
    Generate a valid license key.
    
    This function is for the seller/admin to generate keys.
    The identifier can be an email or customer ID for tracking.
    
    Args:
        identifier: Optional identifier (email, customer ID) for key generation
        
    Returns:
        A valid license key in format CLIPPER-XXXX-XXXX-XXXX-XXXX
    """
    import random
    import string
    import time
    
    # Generate random segments with some entropy
    chars = string.ascii_uppercase + string.digits
    
    # Include timestamp and identifier in the randomness
    seed_data = f"{time.time()}-{identifier}-{random.random()}"
    random.seed(hashlib.sha256(seed_data.encode()).hexdigest())
    
    seg1 = ''.join(random.choices(chars, k=4))
    seg2 = ''.join(random.choices(chars, k=4))
    seg3 = ''.join(random.choices(chars, k=4))
    
    # Generate checksum from first three segments
    data = f"{seg1}-{seg2}-{seg3}"
    checksum = _generate_signature(data)[:4]
    
    return f"CLIPPER-{seg1}-{seg2}-{seg3}-{checksum}"


class LicenseManager:
    """Manages license activation and validation."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".clipper-cli"
        self.license_file = self.config_dir / "license.key"
        self._license_info: Optional[LicenseInfo] = None
    
    def _ensure_config_dir(self) -> None:
        """Create config directory if it doesn't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def is_activated(self) -> bool:
        """Check if a valid license is activated."""
        info = self.get_license_info()
        if info is None:
            return False
        
        # Validate the stored key
        return validate_license_key(info.key)
    
    def get_license_info(self) -> Optional[LicenseInfo]:
        """Get the current license information."""
        if self._license_info is not None:
            return self._license_info
        
        if not self.license_file.exists():
            return None
        
        try:
            with open(self.license_file, "r") as f:
                data = json.load(f)
            self._license_info = LicenseInfo.from_dict(data)
            return self._license_info
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            return None
    
    def activate(self, key: str) -> tuple[bool, str]:
        """
        Activate a license key.
        
        Args:
            key: The license key to activate
            
        Returns:
            Tuple of (success, message)
        """
        key = key.upper().strip()
        
        # Validate format
        if not validate_key_format(key):
            return False, "Invalid license key format. Expected: CLIPPER-XXXX-XXXX-XXXX-XXXX"
        
        # Validate signature
        if not validate_license_key(key):
            return False, "Invalid license key. Please check your key and try again."
        
        # Save license
        self._ensure_config_dir()
        
        license_info = LicenseInfo(
            key=key,
            activated_at=datetime.now().isoformat(),
            machine_id=_get_machine_id(),
        )
        
        try:
            with open(self.license_file, "w") as f:
                json.dump(license_info.to_dict(), f, indent=2)
            
            self._license_info = license_info
            return True, "License activated successfully!"
        
        except IOError as e:
            return False, f"Failed to save license: {e}"
    
    def deactivate(self) -> bool:
        """Remove the current license activation."""
        if self.license_file.exists():
            self.license_file.unlink()
        self._license_info = None
        return True
    
    def get_status_display(self) -> str:
        """Get a formatted status string for display."""
        info = self.get_license_info()
        
        if info is None:
            return "❌ Not Activated"
        
        if not validate_license_key(info.key):
            return "⚠️ Invalid License"
        
        return f"✅ Licensed ({info.masked_key})"


# Global instance for easy access
_license_manager: Optional[LicenseManager] = None


def get_license_manager() -> LicenseManager:
    """Get the global license manager instance."""
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager
