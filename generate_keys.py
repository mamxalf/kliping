#!/usr/bin/env python3
"""
Admin tool for generating serial keys.
Run this script to generate keys for users.

Usage:
    python generate_keys.py user@email.com
    python generate_keys.py user1@email.com user2@email.com user3@email.com
"""
import sys
from clipper_cli.license import generate_serial_key


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_keys.py <user_id> [user_id2] [user_id3] ...")
        print("Example: python generate_keys.py john@example.com")
        sys.exit(1)
    
    user_ids = sys.argv[1:]
    
    print("\n🔑 Generated Serial Keys:")
    print("-" * 50)
    
    for user_id in user_ids:
        key = generate_serial_key(user_id)
        print(f"  {user_id}: {key}")
    
    print("-" * 50)
    print(f"\nTotal: {len(user_ids)} keys generated")


if __name__ == "__main__":
    main()
