#!/usr/bin/env python3
"""
Test script to connect specifically to Docker PostgreSQL
"""

import psycopg2

def test_docker_connection():
    """Test connection to Docker PostgreSQL"""
    print("=== Testing Docker PostgreSQL Connection ===")
    
    # Connection parameters for Docker container
    params = {
        'host': '127.0.0.1',
        'port': 5434,
        'user': 'jesse_user',
        'password': 'jessepwd123',
        'database': 'jesse_db'
    }
    
    print(f"Connecting to: {params['host']}:{params['port']}")
    print(f"Database: {params['database']}")
    print(f"User: {params['user']}")
    
    try:
        conn = psycopg2.connect(**params)
        print("✓ Connection successful!")
        
        cursor = conn.cursor()
        
        # Get version and connection info
        cursor.execute("SELECT version(), current_user, current_database();")
        result = cursor.fetchone()
        print(f"✓ PostgreSQL version: {result[0][:80]}...")
        print(f"✓ Connected as: {result[1]}")
        print(f"✓ Database: {result[2]}")
        
        # Test schema permissions
        cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'public';")
        schema_result = cursor.fetchone()
        print(f"✓ Public schema exists: {schema_result is not None}")
        
        # Check user privileges
        cursor.execute("""
            SELECT 
                grantee, 
                privilege_type 
            FROM information_schema.role_table_grants 
            WHERE grantee = current_user 
            AND table_schema = 'public'
            LIMIT 5;
        """)
        privileges = cursor.fetchall()
        print(f"✓ User privileges on public schema: {len(privileges)} grants found")
        
        # Check if user is superuser
        cursor.execute("SELECT usesuper FROM pg_user WHERE usename = current_user;")
        is_super = cursor.fetchone()
        print(f"✓ User is superuser: {is_super[0] if is_super else 'Unknown'}")
        
        # Try to create a test table
        try:
            cursor.execute("CREATE TABLE test_table_docker (id SERIAL PRIMARY KEY, name VARCHAR(50));")
            print("✓ Table creation successful!")
            
            cursor.execute("DROP TABLE test_table_docker;")
            print("✓ Table deletion successful!")
            
        except Exception as e:
            print(f"✗ Table creation failed: {e}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_docker_connection()
