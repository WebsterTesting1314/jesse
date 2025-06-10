#!/usr/bin/env python3
"""
Test script to check environment variables and database connection
"""

import os
import sys
sys.path.insert(0, '/d/jesse/jesse')

from dotenv import load_dotenv, dotenv_values

# Load environment variables
load_dotenv()
ENV_VALUES = dotenv_values('.env')

print("=== Environment Variables ===")
for key, value in ENV_VALUES.items():
    if 'PASSWORD' in key:
        print(f"{key}: {'*' * len(value)}")
    else:
        print(f"{key}: {value}")

print("\n=== Testing Database Connection ===")
print(f"Connecting to: {ENV_VALUES['POSTGRES_HOST']}:{ENV_VALUES['POSTGRES_PORT']}")
try:
    import psycopg2
    conn = psycopg2.connect(
        host=ENV_VALUES['POSTGRES_HOST'],
        port=int(ENV_VALUES['POSTGRES_PORT']),
        user=ENV_VALUES['POSTGRES_USERNAME'],
        password=ENV_VALUES['POSTGRES_PASSWORD'],
        database=ENV_VALUES['POSTGRES_NAME']
    )
    print("✓ Direct psycopg2 connection successful!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT current_user, current_database(), version();")
    result = cursor.fetchone()
    print(f"✓ Connected as: {result[0]}")
    print(f"✓ Database: {result[1]}")
    print(f"✓ PostgreSQL version: {result[2][:50]}...")
    
    # Test table creation
    cursor.execute("CREATE TABLE IF NOT EXISTS test_permissions (id SERIAL PRIMARY KEY, name VARCHAR(50));")
    cursor.execute("DROP TABLE test_permissions;")
    print("✓ Table creation/deletion test successful!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Database connection failed: {e}")

print("\n=== Testing Jesse Database Module ===")
try:
    # Import Jesse's database module
    from jesse.services.db import database
    from jesse.services.env import ENV_VALUES as JESSE_ENV
    
    print("Jesse ENV_VALUES:")
    for key, value in JESSE_ENV.items():
        if 'POSTGRES' in key:
            if 'PASSWORD' in key:
                print(f"  {key}: {'*' * len(value)}")
            else:
                print(f"  {key}: {value}")
    
    print(f"Database object: {database}")
    print(f"Database is closed: {database.is_closed()}")
    
    if database.is_closed():
        print("Opening database connection...")
        database.open_connection()
        print(f"Database is closed after open: {database.is_closed()}")
    
    if database.db:
        print(f"Database object: {database.db}")
        print(f"Database name: {database.db.database}")
        print(f"Database host: {database.db.host}")
        print(f"Database port: {database.db.port}")
        print(f"Database user: {database.db.user}")
        
except Exception as e:
    print(f"✗ Jesse database module test failed: {e}")
    import traceback
    traceback.print_exc()
