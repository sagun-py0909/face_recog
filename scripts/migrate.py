"""
Migration script to upgrade from v1.0 (Flask) to v2.0 (FastAPI)
This script helps transfer existing data and settings
"""

import os
import sys
from sqlalchemy import create_engine, inspect, text
from database import Base, Person, Attendance, User, SessionLocal
from auth import get_password_hash
from config import get_settings

settings = get_settings()

def check_v1_tables_exist():
    """Check if v1.0 tables exist"""
    try:
        engine = create_engine(settings.database_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"Found tables: {tables}")
        return 'people' in tables or 'attendance' in tables
    except Exception as e:
        print(f"Error checking tables: {e}")
        return False

def migrate_data():
    """Migrate data from v1.0 to v2.0"""
    print("\n" + "=" * 60)
    print("Face Recognition System - Data Migration")
    print("From: v1.0 (Flask) → To: v2.0 (FastAPI)")
    print("=" * 60)
    
    # Check if tables exist
    if not check_v1_tables_exist():
        print("\n✓ No v1.0 data found - this appears to be a fresh installation")
        print("You can proceed with normal setup using init_db.py")
        return
    
    print("\n⚠ WARNING: v1.0 data detected")
    print("This will:")
    print("1. Preserve existing people and attendance records")
    print("2. Add new tables for v2.0 features (users, etc.)")
    print("3. NOT modify or delete existing data")
    
    confirm = input("\nContinue with migration? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Migration cancelled")
        return
    
    try:
        # Create new tables (keeps existing ones)
        print("\n1. Creating new tables...")
        Base.metadata.create_all(bind=create_engine(settings.database_url))
        print("✓ New tables created")
        
        # Check if data already has new columns
        db = SessionLocal()
        
        # Count existing data
        people_count = db.query(Person).count()
        attendance_count = db.query(Attendance).count()
        users_count = db.query(User).count()
        
        print(f"\n2. Current data status:")
        print(f"   - People: {people_count}")
        print(f"   - Attendance records: {attendance_count}")
        print(f"   - Users: {users_count}")
        
        # Create admin user if doesn't exist
        if users_count == 0:
            print("\n3. Creating admin user...")
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                is_active=1,
                is_admin=1
            )
            db.add(admin)
            db.commit()
            print("✓ Admin user created")
            print("   Username: admin")
            print("   Password: admin123")
            print("   ⚠ CHANGE PASSWORD AFTER FIRST LOGIN!")
        else:
            print("\n3. Admin user already exists - skipping")
        
        # Add missing columns if needed (for older schemas)
        print("\n4. Checking schema compatibility...")
        engine = create_engine(settings.database_url)
        inspector = inspect(engine)
        
        # Check people table columns
        people_columns = [col['name'] for col in inspector.get_columns('people')]
        if 'created_at' not in people_columns:
            print("   Adding created_at column to people table...")
            with engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE people ADD COLUMN created_at TIMESTAMP DEFAULT NOW()"
                ))
                conn.execute(text(
                    "ALTER TABLE people ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()"
                ))
                conn.commit()
            print("   ✓ Columns added")
        
        # Check attendance table columns
        attendance_columns = [col['name'] for col in inspector.get_columns('attendance')]
        if 'confidence_score' not in attendance_columns:
            print("   Adding confidence_score column to attendance table...")
            with engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE attendance ADD COLUMN confidence_score FLOAT"
                ))
                conn.commit()
            print("   ✓ Column added")
        
        print("\n✓ Schema updated for v2.0 compatibility")
        
        db.close()
        
        print("\n" + "=" * 60)
        print("✓ Migration Complete!")
        print("=" * 60)
        print("\nYour data has been successfully migrated to v2.0")
        print("\nNext steps:")
        print("1. Start the v2.0 application: python main.py")
        print("2. Login with admin/admin123")
        print("3. Change the admin password")
        print("4. Test face recognition functionality")
        print("\nThe old Flask app (app.py) is preserved for reference")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check database connection settings in .env")
        print("2. Ensure PostgreSQL is running")
        print("3. Check database permissions")
        sys.exit(1)

def backup_database():
    """Create a backup of the database"""
    print("\nCreating database backup...")
    
    try:
        import subprocess
        from datetime import datetime
        
        backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        # Parse database URL
        # Format: postgresql://user:pass@host:port/database
        url = settings.database_url.replace('postgresql://', '')
        parts = url.split('@')
        user_pass = parts[0].split(':')
        host_db = parts[1].split('/')
        
        user = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ''
        host_port = host_db[0].split(':')
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else '5432'
        database = host_db[1]
        
        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = password
        
        # Run pg_dump
        cmd = [
            'pg_dump',
            '-h', host,
            '-p', port,
            '-U', user,
            '-d', database,
            '-f', backup_file
        ]
        
        subprocess.run(cmd, env=env, check=True)
        print(f"✓ Backup created: {backup_file}")
        return backup_file
        
    except Exception as e:
        print(f"⚠ Backup failed: {e}")
        print("Continuing without backup...")
        return None

if __name__ == "__main__":
    print("\nFace Recognition System - Migration Tool")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--backup':
        backup_database()
    elif len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Usage:")
        print("  python migrate.py           - Run migration")
        print("  python migrate.py --backup  - Create database backup")
        print("  python migrate.py --help    - Show this help")
    else:
        # Offer backup option
        print("\nIt's recommended to backup your database before migration.")
        backup = input("Create backup now? (yes/no): ")
        
        if backup.lower() == 'yes':
            backup_database()
        
        # Run migration
        migrate_data()
