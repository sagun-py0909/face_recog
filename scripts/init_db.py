"""
Database migration and initialization utilities
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.database import Base, init_db, User, get_db
from app.core.auth import get_password_hash
from app.core.config import get_settings

settings = get_settings()

def create_admin_user():
    """Create initial admin user"""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("Admin user already exists")
            return
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            is_active=1,
            is_admin=1
        )
        
        db.add(admin_user)
        db.commit()
        
        print("=" * 60)
        print("✓ Admin user created successfully")
        print("=" * 60)
        print("Username: admin")
        print("Password: admin123")
        print("Email: admin@example.com")
        print("=" * 60)
        print("⚠ IMPORTANT: Change the password after first login!")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def reset_database():
    """Drop all tables and recreate them"""
    print("⚠ WARNING: This will delete all data!")
    confirm = input("Type 'yes' to continue: ")
    
    if confirm.lower() != 'yes':
        print("Aborted")
        return
    
    try:
        engine = create_engine(settings.database_url)
        
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        
        print("Creating tables...")
        Base.metadata.create_all(bind=engine)
        
        print("✓ Database reset successfully")
        
        # Create admin user
        create_admin_user()
        
    except Exception as e:
        print(f"Error resetting database: {e}")

def init_database():
    """Initialize database tables"""
    try:
        print("Initializing database...")
        init_db()
        print("✓ Database initialized successfully")
        
        # Create admin user if first time
        create_admin_user()
        
    except Exception as e:
        print(f"Error initializing database: {e}")

def check_connection():
    """Test database connection"""
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database connection successful")
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python init_db.py check      - Test database connection")
        print("  python init_db.py init       - Initialize database tables")
        print("  python init_db.py admin      - Create admin user")
        print("  python init_db.py reset      - Reset database (DELETE ALL DATA)")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "check":
        check_connection()
    elif command == "init":
        init_database()
    elif command == "admin":
        create_admin_user()
    elif command == "reset":
        reset_database()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
