"""
Database seeding script for creating test user and sample data.
Runs automatically on backend startup.
"""
import asyncio
from datetime import datetime
from sqlalchemy import select
from database import get_db, engine, Base
from models import User, ChatSession, ChatMessage, UserMemory
import bcrypt

async def seed_database():
    """Create test user and sample data for tournament judges."""
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Check if test user already exists
        result = db.execute(select(User).where(User.email == "judge@devto.com"))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("✅ Test user already exists - skipping seed")
            return
        
        print("🌱 Seeding database with test user...")
        
        # Create test user
        hashed_password = bcrypt.hashpw("ArchyDemo2024!".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        test_user = User(
            username="judge",
            email="judge@devto.com",
            password_hash=hashed_password
        )
        db.add(test_user)
        db.flush()  # Get user ID
        
        # Create sample chat session
        chat_session = ChatSession(
            user_id=test_user.id,
            title="Memory System Demo"
        )
        db.add(chat_session)
        db.flush()  # Get session ID
        
        # Add sample messages demonstrating memory feature
        messages = [
            ChatMessage(
                session_id=chat_session.id,
                role="user",
                content="Hi Archy! I use yay as my AUR helper and I prefer limine bootloader.",
                timestamp=datetime.utcnow()
            ),
            ChatMessage(
                session_id=chat_session.id,
                role="assistant",
                content="Great! I'll remember that you use yay and limine. Those are excellent choices - yay is fast and user-friendly, and limine is a modern, feature-rich bootloader.\n\nWould you like help with:\n- Installing packages from the AUR with yay?\n- Configuring limine for your system?\n- Exploring other system customizations?",
                timestamp=datetime.utcnow()
            ),
            ChatMessage(
                session_id=chat_session.id,
                role="user",
                content="Can you help me update my system?",
                timestamp=datetime.utcnow()
            ),
            ChatMessage(
                session_id=chat_session.id,
                role="assistant",
                content="Sure! Since you use yay, you can update both official repos and AUR packages in one command:\n\n```bash\nyay -Syu\n```\n\nThis will sync package databases and update all packages. Want to see what would update first without installing? Use `yay -Syu --devel --timeupdate`.",
                timestamp=datetime.utcnow()
            )
        ]
        
        for msg in messages:
            db.add(msg)
        
        # Add sample memories to demonstrate memory system
        memories = [
            UserMemory(
                user_id=test_user.id,
                category="aur_helper",
                key="preferred_aur_helper",
                value="yay",
                confidence=0.95,
                learned_at=datetime.utcnow()
            ),
            UserMemory(
                user_id=test_user.id,
                category="bootloader",
                key="bootloader",
                value="limine",
                confidence=0.95,
                learned_at=datetime.utcnow()
            )
        ]
        
        for memory in memories:
            db.add(memory)
        
        # Commit all changes
        db.commit()
        
        print("✅ Test user created successfully!")
        print("   Email: judge@devto.com")
        print("   Password: ArchyDemo2024!")
        print("   Sample chat and memories added")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
