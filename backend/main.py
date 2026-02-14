from fastapi import FastAPI, HTTPException, Depends, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import httpx
import json
import os
import re
from typing import List, Optional
from datetime import timedelta

from database import engine, get_db, Base
from models import User, ChatSession, ChatMessage, UserMemory
from arch_service import ArchPackageService
from memory_service import MemoryExtractor
from web_search_service import WebSearchService
from auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    decode_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Arch Linux Assistant API")

# Seed database on startup
@app.on_event("startup")
async def startup_event():
    """Seed database with test user on application startup."""
    from seed_database import seed_database
    await seed_database()
security = HTTPBearer()
arch_service = ArchPackageService()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/chat")
ARCH_SYSTEM_PROMPT = """You are Archy, a specialized Arch Linux assistant. 

**ABSOLUTE RULES - ZERO TOLERANCE:**
- You ONLY help with Arch Linux and Linux-related technical topics
- You will IMMEDIATELY REFUSE and STOP responding to:
  * Personal advice (relationships, mental health, life problems)
  * Inappropriate, illegal, or harmful content
  * Any topic not related to Arch Linux, Linux systems, or computing
  * General advice unrelated to technology
  
**CRITICAL: When refusing, you MUST:**
1. Say: "I'm Archy, specialized in Arch Linux support only. I cannot help with that topic."
2. STOP IMMEDIATELY - DO NOT offer alternatives
3. DO NOT suggest "general advice" or "tips"
4. DO NOT continue the conversation on that topic
5. Simply ask: "Do you have any Arch Linux questions I can help with?"

**Your ONLY Expertise:**
- Arch Linux package management (pacman, AUR helpers)
- System configuration and troubleshooting
- Installation, boot issues, drivers
- Systemd services and system administration
- Desktop environments and window managers
- Arch Wiki best practices
- Linux commands and shell scripting
- Hardware compatibility

**Response Style (for ARCH topics ONLY):**
- Keep responses concise (2-4 sentences or 1 code block max)
- Provide the most essential information first
- End EVERY response with a follow-up question like:
  * "Would you like me to explain this in more detail?"
  * "Would you like to see advanced options?"
  * "Need help with the next step?"
  * "Want me to show related commands?"
- Use markdown formatting with code blocks for commands
- Be friendly and encouraging about ARCH LINUX topics only

**REMEMBER: If it's not about Arch Linux or Linux systems, REFUSE and STOP. No exceptions.**"""


# Pydantic Models
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    model: str = "llama3.2"
    session_id: Optional[int] = None


# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


# Auth Endpoints
@app.post("/api/auth/register", response_model=Token)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(new_user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/auth/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "created_at": current_user.created_at
    }


@app.get("/")
async def root():
    return {"status": "ok", "message": "Arch Linux Assistant API"}


@app.get("/health")
async def health_check():
    """Check if Ollama is running"""
    try:
        ollama_base_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/chat").replace("/api/chat", "")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ollama_base_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                return {"status": "healthy", "ollama": "connected"}
            return {"status": "unhealthy", "ollama": "error"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ollama not available: {str(e)}")


# Chat Session Endpoints
@app.get("/api/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all chat sessions for the current user"""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc()).all()
    
    return [{
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "message_count": len(session.messages)
    } for session in sessions]


@app.post("/api/sessions")
async def create_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session"""
    new_session = ChatSession(
        user_id=current_user.id,
        title="New Chat"
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return {
        "id": new_session.id,
        "title": new_session.title,
        "created_at": new_session.created_at.isoformat(),
        "updated_at": new_session.updated_at.isoformat(),
        "message_count": 0
    }


@app.get("/api/sessions/{session_id}")
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific chat session with all messages"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "messages": [{
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat()
        } for msg in session.messages]
    }


@app.put("/api/sessions/{session_id}")
async def update_session(
    session_id: int,
    title: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update chat session title"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    session.title = title
    db.commit()
    
    return {"message": "Session updated successfully"}


@app.delete("/api/sessions/{session_id}")
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    db.delete(session)
    db.commit()
    
    return {"message": "Session deleted successfully"}


async def detect_and_fetch_packages(user_message: str) -> str:
    """Detect package mentions and fetch real-time data from Arch repos"""
    package_context = ""
    
    # Keywords that suggest package queries
    package_keywords = [
        r'\binstall\b', r'\bpacman\b', r'\bpackage\b', r'\bupdate\b',
        r'\bupgrade\b', r'\byay\b', r'\bparu\b', r'\bremove\b',
        r'\bsearch\b', r'\baur\b', r'\bdownload\b'
    ]
    
    # Check if message contains package-related keywords
    has_package_query = any(re.search(pattern, user_message.lower()) for pattern in package_keywords)
    
    if has_package_query:
        # Extract potential package names (words that could be packages)
        # Match words that are likely package names (lowercase, may contain hyphens)
        potential_packages = re.findall(r'\b([a-z][a-z0-9\-]{2,})\b', user_message.lower())
        
        # Common words to exclude
        exclude_words = {
            'install', 'package', 'pacman', 'update', 'upgrade', 'remove', 
            'search', 'want', 'need', 'help', 'with', 'the', 'how', 'what',
            'this', 'that', 'from', 'arch', 'linux', 'system', 'repo',
            'repository', 'latest', 'version', 'stable', 'beta'
        }
        
        package_names = [pkg for pkg in potential_packages if pkg not in exclude_words]
        
        if package_names:
            # Search for up to 3 packages to avoid overwhelming context
            searched_packages = []
            for pkg_name in package_names[:3]:
                results = await arch_service.search_packages(pkg_name, limit=1)
                if results:
                    searched_packages.append(results[0])
            
            if searched_packages:
                package_context = "\n\n**REAL-TIME PACKAGE DATA (use this information):**\n"
                for pkg in searched_packages:
                    package_context += f"- **{pkg['name']}** {pkg['version']} ({pkg['repo']}/{pkg['arch']})\n"
                    package_context += f"  {pkg['description']}\n"
                    package_context += f"  Install: `sudo pacman -S {pkg['name']}`\n"
    
    return package_context


@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stream chat responses from Ollama and save to database"""
    
    # Get or create chat session
    if request.session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == request.session_id,
            ChatSession.user_id == current_user.id
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        session_id = session.id
    else:
        # Create new session
        session = ChatSession(
            user_id=current_user.id,
            title="New Chat"  # Will be updated with first message
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        session_id = session.id
    
    # Save user message
    user_message = request.messages[-1]
    db_message = ChatMessage(
        session_id=session_id,
        role=user_message.role,
        content=user_message.content
    )
    db.add(db_message)
    db.commit()
    
    # Update session title if it's the first message
    if session.title == "New Chat":
        title = user_message.content[:50] + ("..." if len(user_message.content) > 50 else "")
        session.title = title
        db.commit()
    
    # Extract memories from user message
    MemoryExtractor.extract_memories(user_message.content, db, current_user.id)
    
    # Get user memories for context
    memory_context = MemoryExtractor.get_user_memories(db, current_user.id)
    
    # Check if we should search the web
    search_query = WebSearchService.should_search(user_message.content)
    search_context = ""
    if search_query:
        # Note: In a real implementation, you could send a status update here
        # For now, the frontend shows "Thinking..." which covers this
        search_context = await WebSearchService.search_arch_info(search_query, max_results=3)
    
    # Detect package queries and fetch real-time data
    package_context = await detect_and_fetch_packages(user_message.content)
    
    # Add system prompt with all contexts
    enhanced_system_prompt = ARCH_SYSTEM_PROMPT + memory_context + search_context + package_context
    messages = request.messages
    if not messages or messages[0].role != "system":
        messages = [Message(role="system", content=enhanced_system_prompt)] + messages
    
    ollama_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
    
    payload = {
        "model": request.model,
        "messages": ollama_messages,
        "stream": True
    }
    
    assistant_content = ""
    
    async def generate():
        nonlocal assistant_content
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", OLLAMA_API_URL, json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        yield f"data: {json.dumps({'error': error_text.decode()})}\n\n"
                        return
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                yield f"data: {json.dumps(data)}\n\n"
                                
                                # Accumulate assistant response
                                if data.get("message", {}).get("content"):
                                    assistant_content += data["message"]["content"]
                                    
                            except json.JSONDecodeError:
                                continue
            
            # Save assistant response to database using a new session
            if assistant_content:
                # Create new DB session for async context
                from database import SessionLocal
                new_db = SessionLocal()
                try:
                    assistant_message = ChatMessage(
                        session_id=session_id,
                        role="assistant",
                        content=assistant_content
                    )
                    new_db.add(assistant_message)
                    new_db.commit()
                finally:
                    new_db.close()
                                
        except httpx.ConnectError:
            yield f"data: {json.dumps({'error': 'Cannot connect to Ollama. Is it running?'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Arch Package Search Endpoint
@app.get("/api/packages/search")
async def search_packages(
    q: str,
    limit: int = 5,
    current_user: User = Depends(get_current_user)
):
    """Search for Arch Linux packages"""
    packages = await arch_service.search_packages(q, limit)
    return {"query": q, "results": packages}


@app.get("/api/packages/{repo}/{arch}/{name}")
async def get_package_details(
    repo: str,
    arch: str,
    name: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific package"""
    package = await arch_service.get_package_details(repo, arch, name)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    return package

# Memory Management Endpoints
@app.get("/api/memory")
async def get_memories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all memories for current user"""
    memories = db.query(UserMemory).filter(
        UserMemory.user_id == current_user.id
    ).all()
    
    return [{
        "id": m.id,
        "category": m.category,
        "key": m.key,
        "value": m.value,
        "confidence": m.confidence,
        "learned_at": m.learned_at.isoformat() if m.learned_at else None
    } for m in memories]


@app.delete("/api/memory/{memory_id}")
async def delete_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific memory"""
    memory = db.query(UserMemory).filter(
        UserMemory.id == memory_id,
        UserMemory.user_id == current_user.id
    ).first()
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    db.delete(memory)
    db.commit()
    return {"message": "Memory deleted"}


@app.put("/api/memory/{memory_id}")
async def update_memory(
    memory_id: int,
    value: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a memory value"""
    memory = db.query(UserMemory).filter(
        UserMemory.id == memory_id,
        UserMemory.user_id == current_user.id
    ).first()
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    memory.value = value
    db.commit()
    return {"message": "Memory updated", "memory": {
        "id": memory.id,
        "category": memory.category,
        "value": memory.value
    }}
