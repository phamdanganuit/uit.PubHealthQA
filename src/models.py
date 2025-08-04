"""
Database models và connection cho ứng dụng PubHealthQA
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List
import pymongo
from pymongo import MongoClient
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt

# MongoDB Connection
MONGODB_URL = "mongodb+srv://an:dangan123@cluster.ju2jwqz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster"
DATABASE_NAME = "pubhealthqa"
USERS_COLLECTION = "users"
CHAT_SESSIONS_COLLECTION = "chat_sessions"

# JWT Settings
SECRET_KEY = "pubhealthqa_secret_key_2025"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    """User model"""
    email: EmailStr
    full_name: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    """User creation model"""
    email: EmailStr
    full_name: str
    password: str

class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str

class Token(BaseModel):
    """Token model"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token data model"""
    email: Optional[str] = None

class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = datetime.utcnow()

class ChatSession(BaseModel):
    """Chat session model"""
    session_id: str
    user_email: str
    title: str
    messages: List[ChatMessage] = []
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    is_active: bool = True

class DatabaseManager:
    """MongoDB database manager"""
    
    def __init__(self):
        self.client = None
        self.db = None
        
    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(MONGODB_URL)
            self.db = self.client[DATABASE_NAME]
            # Test connection
            self.client.admin.command('ping')
            print("Successfully connected to MongoDB!")
            return True
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return False
    
    def get_users_collection(self):
        """Get users collection"""
        if self.db is None:
            self.connect()
        return self.db[USERS_COLLECTION]
    
    def get_chat_sessions_collection(self):
        """Get chat sessions collection"""
        if self.db is None:
            self.connect()
        return self.db[CHAT_SESSIONS_COLLECTION]
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()

# Global database instance
db_manager = DatabaseManager()

# Authentication utilities
def verify_password(plain_password, hashed_password):
    """Verify password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hash password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Verify token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        token_data = TokenData(email=email)
        return token_data
    except JWTError:
        return None

def get_user_by_email(email: str):
    """Get user by email"""
    users_collection = db_manager.get_users_collection()
    user_data = users_collection.find_one({"email": email})
    if user_data:
        return User(**user_data)
    return None

def create_user(user: UserCreate):
    """Create new user"""
    users_collection = db_manager.get_users_collection()
    
    # Check if user already exists
    if get_user_by_email(user.email):
        return None
    
    # Create user
    hashed_password = get_password_hash(user.password)
    user_dict = {
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    
    result = users_collection.insert_one(user_dict)
    if result.inserted_id:
        return User(**user_dict)
    return None

def authenticate_user(email: str, password: str):
    """Authenticate user"""
    user = get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    
    # Update last login
    users_collection = db_manager.get_users_collection()
    users_collection.update_one(
        {"email": email},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    return user

# Chat History Functions
def create_chat_session(user_email: str, title: str = None) -> str:
    """Create new chat session"""
    import uuid
    
    sessions_collection = db_manager.get_chat_sessions_collection()
    
    session_id = str(uuid.uuid4())
    
    # Generate title from first message if not provided
    if not title:
        title = f"Cuộc trò chuyện {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}"
    
    session_dict = {
        "session_id": session_id,
        "user_email": user_email,
        "title": title,
        "messages": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True
    }
    
    result = sessions_collection.insert_one(session_dict)
    if result.inserted_id:
        return session_id
    return None

def get_user_chat_sessions(user_email: str, limit: int = 20):
    """Get user's chat sessions"""
    sessions_collection = db_manager.get_chat_sessions_collection()
    
    sessions = sessions_collection.find(
        {"user_email": user_email, "is_active": True}
    ).sort("updated_at", -1).limit(limit)
    
    return list(sessions)

def get_chat_session(session_id: str, user_email: str):
    """Get specific chat session"""
    sessions_collection = db_manager.get_chat_sessions_collection()
    
    session = sessions_collection.find_one({
        "session_id": session_id,
        "user_email": user_email,
        "is_active": True
    })
    
    return session

def add_message_to_session(session_id: str, user_email: str, role: str, content: str):
    """Add message to chat session"""
    sessions_collection = db_manager.get_chat_sessions_collection()
    
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow()
    }
    
    result = sessions_collection.update_one(
        {"session_id": session_id, "user_email": user_email},
        {
            "$push": {"messages": message},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return result.modified_count > 0

def update_session_title(session_id: str, user_email: str, title: str):
    """Update session title"""
    sessions_collection = db_manager.get_chat_sessions_collection()
    
    result = sessions_collection.update_one(
        {"session_id": session_id, "user_email": user_email},
        {"$set": {"title": title, "updated_at": datetime.utcnow()}}
    )
    
    return result.modified_count > 0

def delete_chat_session(session_id: str, user_email: str):
    """Delete chat session (soft delete)"""
    sessions_collection = db_manager.get_chat_sessions_collection()
    
    result = sessions_collection.update_one(
        {"session_id": session_id, "user_email": user_email},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    return result.modified_count > 0

def generate_session_title_from_message(first_message: str) -> str:
    """Generate session title from first user message"""
    # Truncate and clean the message for title
    title = first_message.strip()
    if len(title) > 50:
        title = title[:47] + "..."
    
    # Remove newlines and extra spaces
    title = " ".join(title.split())
    
    return title if title else f"Cuộc trò chuyện {datetime.utcnow().strftime('%d/%m %H:%M')}" 