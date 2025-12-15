#!/usr/bin/env python3
"""License Key Generator for Clipper CLI.

This is a SELLER-ONLY tool for generating license keys.
DO NOT distribute this file with the application!

Usage:
    python keygen.py generate                      # Generate a single key
    python keygen.py generate --email user@email.com  # Generate key with identifier
    python keygen.py batch --count 10             # Generate 10 keys
    python keygen.py validate CLIPPER-XXXX-XXXX-XXXX-XXXX  # Validate a key
"""

import argparse
import sys
from datetime import datetime


def generate_key(identifier: str = "") -> str:
    """Generate a valid license key."""
    # Import from license module
    from clipper_cli.license import generate_license_key
    return generate_license_key(identifier)


def validate_key(key: str) -> bool:
    """Validate a license key."""
    from clipper_cli.license import validate_license_key, validate_key_format
    
    if not validate_key_format(key):
        return False
    return validate_license_key(key)


def main():
    parser = argparse.ArgumentParser(
        description="Clipper CLI License Key Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python keygen.py generate
    python keygen.py generate --email customer@example.com
    python keygen.py batch --count 5 --output keys.txt
    python keygen.py validate CLIPPER-ABCD-1234-EFGH-5678
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate a single license key")
    gen_parser.add_argument(
        "--email", "-e",
        default="",
        help="Customer email or identifier (optional, for tracking)"
    )
    
    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Generate multiple license keys")
    batch_parser.add_argument(
        "--count", "-c",
        type=int,
        default=10,
        help="Number of keys to generate (default: 10)"
    )
    batch_parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path (optional, prints to stdout if not specified)"
    )
    batch_parser.add_argument(
        "--prefix", "-p",
        default="",
        help="Prefix identifier for batch (e.g., 'PROMO', 'LAUNCH')"
    )
    
    # Validate command
    val_parser = subparsers.add_parser("validate", help="Validate a license key")
    val_parser.add_argument(
        "key",
        help="License key to validate"
    )
    
    args = parser.parse_args()
    
    if args.command == "generate":
        key = generate_key(args.email)
        print(f"\n🔑 Generated License Key:\n")
        print(f"   {key}")
        if args.email:
            print(f"\n   Identifier: {args.email}")
        print()
    
    elif args.command == "batch":
        keys = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"\n🔑 Generating {args.count} license keys...\n")
        
        for i in range(args.count):
            identifier = f"{args.prefix}_{i+1}" if args.prefix else f"batch_{timestamp}_{i+1}"
            key = generate_key(identifier)
            keys.append(key)
            print(f"   {i+1:3d}. {key}")
        
        if args.output:
            with open(args.output, "w") as f:
                f.write(f"# Clipper CLI License Keys\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n")
                f.write(f"# Count: {args.count}\n")
                if args.prefix:
                    f.write(f"# Prefix: {args.prefix}\n")
                f.write(f"#\n")
                for key in keys:
                    f.write(f"{key}\n")
            print(f"\n✅ Keys saved to: {args.output}")
        
        print()
    
    elif args.command == "validate":
        key = args.key.upper().strip()
        
        print(f"\n🔍 Validating: {key}\n")
        
        if validate_key(key):
            print("   ✅ VALID - This is a valid license key\n")
            return 0
        else:
            print("   ❌ INVALID - This key is not valid\n")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
