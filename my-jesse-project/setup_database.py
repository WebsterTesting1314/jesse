#!/usr/bin/env python3
"""
Database setup script for Jesse trading bot.
This script helps create the required PostgreSQL user and database.
"""

import psycopg2
import sys
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def test_connection(host, port, user, password, database=None):
    """Test PostgreSQL connection"""
    try:
        if database:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
        else:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password
            )
        conn.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def create_user_and_database():
    """Create Jesse user and database"""
    print("=== Jesse Database Setup ===")
    print("This script will help you set up PostgreSQL for Jesse.")
    print()
    
    # Get PostgreSQL admin credentials
    print("First, we need to connect as a PostgreSQL admin user.")
    admin_user = input("Enter PostgreSQL admin username (default: postgres): ").strip() or "postgres"
    admin_password = input(f"Enter password for {admin_user}: ").strip()
    
    if not admin_password:
        print("Password is required!")
        return False
    
    # Test admin connection
    print(f"Testing connection as {admin_user}...")
    if not test_connection("127.0.0.1", 5432, admin_user, admin_password):
        print("Failed to connect as admin user!")
        return False
    
    print("✓ Admin connection successful!")
    
    # Connect and create user/database
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            port=5432,
            user=admin_user,
            password=admin_password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname='jesse_user'")
        user_exists = cursor.fetchone()
        
        if not user_exists:
            print("Creating jesse_user...")
            cursor.execute("CREATE USER jesse_user WITH PASSWORD 'jessepwd123'")
            print("✓ User jesse_user created!")
        else:
            print("✓ User jesse_user already exists!")
            # Update password just in case
            cursor.execute("ALTER USER jesse_user WITH PASSWORD 'jessepwd123'")
            print("✓ Password updated for jesse_user!")
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='jesse_db'")
        db_exists = cursor.fetchone()
        
        if not db_exists:
            print("Creating jesse_db database...")
            cursor.execute("CREATE DATABASE jesse_db")
            print("✓ Database jesse_db created!")
        else:
            print("✓ Database jesse_db already exists!")
        
        # Grant privileges
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE jesse_db TO jesse_user")
        print("✓ Privileges granted to jesse_user!")
        
        cursor.close()
        conn.close()
        
        # Test Jesse user connection
        print("Testing connection as jesse_user...")
        if test_connection("127.0.0.1", 5432, "jesse_user", "jessepwd123", "jesse_db"):
            print("✓ Jesse user connection successful!")
            print()
            print("=== Setup Complete! ===")
            print("You can now run Jesse commands.")
            return True
        else:
            print("✗ Jesse user connection failed!")
            return False
            
    except Exception as e:
        print(f"Error during setup: {e}")
        return False

if __name__ == "__main__":
    if create_user_and_database():
        sys.exit(0)
    else:
        sys.exit(1)
