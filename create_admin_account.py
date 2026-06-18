#!/usr/bin/env python3
"""
Admin Account Creation Script
Creates a verified admin account for system management
"""

import sys
import os
from getpass import getpass
from models import create_user, verify_user_email, create_verification_token, get_user_by_email
from init_db import init_db

def create_admin():
    print("\n" + "="*60)
    print("🔐 ADMIN ACCOUNT CREATION SCRIPT")
    print("="*60)
    print("\nThis script creates a verified admin account for your system.")
    print("Make sure MySQL is running before proceeding.\n")
    
    # Initialize database
    print("Initializing database schema...")
    try:
        init_db()
        print("✅ Database initialized successfully\n")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)
    
    # Get input
    print("Enter admin account details:")
    print("-" * 60)
    
    name = input("Admin Full Name: ").strip()
    if not name:
        print("❌ Name cannot be empty")
        sys.exit(1)
    
    email = input("Admin Email: ").strip()
    if not email or '@' not in email:
        print("❌ Valid email required")
        sys.exit(1)
    
    # Check if email already exists
    try:
        existing_user = get_user_by_email(email)
        if existing_user:
            print(f"❌ Email '{email}' is already registered")
            sys.exit(1)
    except:
        pass
    
    password = getpass("Admin Password: ")
    if len(password) < 6:
        print("❌ Password must be at least 6 characters")
        sys.exit(1)
    
    password_confirm = getpass("Confirm Password: ")
    if password != password_confirm:
        print("❌ Passwords do not match")
        sys.exit(1)
    
    # Create admin user
    print("\n" + "-" * 60)
    print("Creating admin account...")
    try:
        user_id = create_user(name, email, password, 'admin')
        print(f"✅ Admin user created with ID: {user_id}")
        
        # Create and immediately verify email token
        token = create_verification_token(user_id)
        if verify_user_email(token):
            print("✅ Email verified automatically")
        
        print("\n" + "="*60)
        print("🎉 ADMIN ACCOUNT CREATED SUCCESSFULLY")
        print("="*60)
        print(f"\nAdmin Account Details:")
        print(f"  Email: {email}")
        print(f"  Name: {name}")
        print(f"  Role: admin")
        print(f"  Status: ✅ Verified and Ready to Use")
        print("\nYou can now login with these credentials:")
        print(f"  Email: {email}")
        print(f"  Password: [your password]")
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"❌ Error creating admin account: {e}")
        sys.exit(1)

if __name__ == '__main__':
    create_admin()
