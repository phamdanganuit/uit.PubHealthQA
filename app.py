"""
Backend FastAPI cho ứng dụng chatbot sức khỏe công cộng sử dụng hệ thống RAG & LLM.
"""

import os
import logging
import time
from datetime import timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Depends, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uuid
import shutil

import groq
from langchain_core.documents import Document

from src.utils.logging_utils import setup_logger
from src.vector_store.faiss_retriever import query_documents, optimize_retrieval
from src.vector_store.faiss_manager import initialize_embedding_model, load_vector_db
from src.models import (
    User, UserCreate, UserLogin, Token, 
    create_user, authenticate_user, verify_token, 
    create_access_token, get_user_by_email, db_manager,
    create_chat_session, get_user_chat_sessions, get_chat_session,
    add_message_to_session, update_session_title, delete_chat_session,
    generate_session_title_from_message,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

load_dotenv()

logger = setup_logger(
    "pubhealth_chatbot",
    log_file=Path("outputs/logs/chatbot.log")
)

app = FastAPI(
    title="PubHealthQA Chatbot",
    description="Chatbot sức khỏe công cộng sử dụng RAG và Groq LLM",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Security
security = HTTPBearer()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    
class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []
    retrieval_time: float = 0
    generation_time: float = 0
    session_id: str

vector_db = None
embeddings = None
groq_client = None

DEFAULT_VECTOR_DB_PATH = "data/gold/db_faiss_phapluat_yte_full_final"
DEFAULT_EMBEDDING_MODEL = "bkai-foundation-models/vietnamese-bi-encoder"
DEFAULT_LLM_MODEL = "llama3-70b-8192"

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    token_data = verify_token(token)
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = get_user_by_email(token_data.email)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# Optional authentication dependency
async def get_current_user_optional(request: Request):
    """Optional dependency to get current user if authenticated"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        token_data = verify_token(token)
        if token_data is None:
            return None
        
        user = get_user_by_email(token_data.email)
        return user
    except:
        return None

@app.on_event("startup")
async def startup_event():
    """Khởi tạo các tài nguyên khi ứng dụng khởi động"""
    global vector_db, embeddings, groq_client
    
    # Connect to MongoDB
    if not db_manager.connect():
        logger.error("Không thể kết nối đến MongoDB!")
        raise ValueError("Không thể kết nối đến MongoDB")
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        logger.error("GROQ_API_KEY không tìm thấy trong biến môi trường!")
        raise ValueError("GROQ_API_KEY không được đặt. Hãy chạy setup_groq_key.py trước!")
    
    groq_client = groq.Client(api_key=groq_api_key)
    logger.info(f"Đã khởi tạo Groq client")
    
    embeddings = initialize_embedding_model(DEFAULT_EMBEDDING_MODEL)
    if not embeddings:
        logger.error(f"Không thể khởi tạo model embedding '{DEFAULT_EMBEDDING_MODEL}'")
        raise ValueError(f"Không thể khởi tạo model embedding: {DEFAULT_EMBEDDING_MODEL}")
    
    vector_db = load_vector_db(DEFAULT_VECTOR_DB_PATH, embeddings)
    if not vector_db:
        logger.error(f"Không thể tải vector database từ {DEFAULT_VECTOR_DB_PATH}")
        raise ValueError(f"Không thể tải vector database: {DEFAULT_VECTOR_DB_PATH}")
    
    logger.info(f"Ứng dụng đã khởi động thành công. Vector database có {vector_db.index.ntotal} vectors.")

@app.get("/")
async def read_root(request: Request):
    """Endpoint chính trả về trang HTML cho giao diện chatbot"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login")
async def login_page(request: Request):
    """Trang đăng nhập"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
async def register_page(request: Request):
    """Trang đăng ký"""
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/api/auth/register", response_model=dict)
async def register(user: UserCreate):
    """API endpoint đăng ký người dùng mới"""
    try:
        # Validate password length
        if len(user.password) < 6:
            raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 6 ký tự")
        
        # Create user
        new_user = create_user(user)
        if not new_user:
            raise HTTPException(status_code=400, detail="Email đã được sử dụng")
        
        logger.info(f"Người dùng mới đăng ký: {user.email}")
        return {"message": "Đăng ký thành công", "email": user.email}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi đăng ký: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Lỗi máy chủ")

@app.post("/api/auth/login", response_model=Token)
async def login(user: UserLogin):
    """API endpoint đăng nhập"""
    try:
        # Authenticate user
        authenticated_user = authenticate_user(user.email, user.password)
        if not authenticated_user:
            raise HTTPException(
                status_code=401, 
                detail="Email hoặc mật khẩu không chính xác"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": authenticated_user.email}, 
            expires_delta=access_token_expires
        )
        
        logger.info(f"Người dùng đăng nhập: {user.email}")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi đăng nhập: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Lỗi máy chủ")

@app.get("/api/auth/me", response_model=dict)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """API endpoint lấy thông tin người dùng hiện tại"""
    return {
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }

@app.post("/api/auth/logout", response_model=dict)
async def logout(current_user: User = Depends(get_current_user)):
    """API endpoint đăng xuất"""
    logger.info(f"Người dùng đăng xuất: {current_user.email}")
    return {"message": "Đăng xuất thành công"}

# Chat History API Endpoints
@app.get("/api/chat/sessions", response_model=list)
async def get_chat_sessions(current_user: User = Depends(get_current_user)):
    """Get user's chat sessions"""
    try:
        sessions = get_user_chat_sessions(current_user.email)
        
        # Format sessions for frontend
        formatted_sessions = []
        for session in sessions:
            formatted_sessions.append({
                "session_id": session["session_id"],
                "title": session["title"],
                "updated_at": session["updated_at"].isoformat(),
                "message_count": len(session.get("messages", []))
            })
        
        return formatted_sessions
        
    except Exception as e:
        logger.error(f"Lỗi khi lấy chat sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Lỗi máy chủ")

@app.get("/api/chat/sessions/{session_id}", response_model=dict)
async def get_session_detail(session_id: str, current_user: User = Depends(get_current_user)):
    """Get specific chat session with messages"""
    try:
        session = get_chat_session(session_id, current_user.email)
        
        if not session:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện")
        
        return {
            "session_id": session["session_id"],
            "title": session["title"],
            "messages": session.get("messages", []),
            "created_at": session["created_at"].isoformat(),
            "updated_at": session["updated_at"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi lấy chi tiết session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Lỗi máy chủ")

@app.post("/api/chat/sessions", response_model=dict)
async def create_new_chat_session(current_user: User = Depends(get_current_user)):
    """Create new chat session"""
    try:
        session_id = create_chat_session(current_user.email)
        
        if not session_id:
            raise HTTPException(status_code=500, detail="Không thể tạo cuộc trò chuyện mới")
        
        return {"session_id": session_id, "message": "Tạo cuộc trò chuyện mới thành công"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi tạo session mới: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Lỗi máy chủ")

@app.put("/api/chat/sessions/{session_id}/title", response_model=dict)
async def update_session_title_endpoint(
    session_id: str, 
    request_data: dict, 
    current_user: User = Depends(get_current_user)
):
    """Update chat session title"""
    try:
        title = request_data.get("title", "").strip()
        
        if not title:
            raise HTTPException(status_code=400, detail="Tiêu đề không được để trống")
        
        success = update_session_title(session_id, current_user.email, title)
        
        if not success:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện")
        
        return {"message": "Cập nhật tiêu đề thành công"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi cập nhật tiêu đề: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Lỗi máy chủ")

@app.delete("/api/chat/sessions/{session_id}", response_model=dict)
async def delete_session_endpoint(session_id: str, current_user: User = Depends(get_current_user)):
    """Delete chat session"""
    try:
        success = delete_chat_session(session_id, current_user.email)
        
        if not success:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện")
        
        return {"message": "Xóa cuộc trò chuyện thành công"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi xóa session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Lỗi máy chủ")

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user_optional)):
    """API endpoint cho chức năng chat"""
    global vector_db, groq_client
    
    if not vector_db or not groq_client:
        raise HTTPException(
            status_code=503, 
            detail="Hệ thống chưa được khởi tạo đầy đủ. Vui lòng thử lại sau."
        )
    
    query = request.message
    session_id = request.session_id
    
    # If user is logged in, handle chat history
    if current_user:
        # Create new session if not provided
        if not session_id:
            title = generate_session_title_from_message(query)
            session_id = create_chat_session(current_user.email, title)
        
        # Add user message to session
        add_message_to_session(session_id, current_user.email, "user", query)
        
        # Get chat history from session
        session_data = get_chat_session(session_id, current_user.email)
        chat_history = []
        if session_data and session_data.get("messages"):
            for msg in session_data["messages"][:-1]:  # Exclude the just-added message
                chat_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
    else:
        # For non-logged in users, use empty history
        chat_history = []
        session_id = "anonymous"
    
    start_time = time.time()
    
    try:
        retrieval_start = time.time()
        docs_with_score = optimize_retrieval(
            vector_db=vector_db,
            query=query,
            k=5,  
            preprocess_query=True
        )
        retrieval_time = time.time() - retrieval_start
        
        context = ""
        sources = []
        
        for i, item in enumerate(docs_with_score):
            if isinstance(item, tuple) and len(item) == 2:
                doc, score = item
                metadata = doc.metadata if hasattr(doc, "metadata") else {}
                
                context += f"[Tài liệu {i+1}] "
                if "title" in metadata:
                    context += f"Nguồn: {metadata.get('title', 'Không rõ nguồn')}"
                if "law_id" in metadata:
                    context += f", Số hiệu: {metadata.get('law_id', '')}"
                context += "\n"
                context += doc.page_content + "\n\n"
                
                source_info = {
                    "id": i + 1,
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "similarity": float(score),
                    "metadata": metadata
                }
                sources.append(source_info)
        
        llm_start = time.time()
        
        # Tạo prompt
        messages = [
            {"role": "system", "content": """Bạn là trợ lý sức khỏe công cộng và pháp luật y tế thông minh, 
nhiệm vụ của bạn là trả lời các câu hỏi dựa trên thông tin y tế và pháp luật chính xác.
Hãy trả lời bằng tiếng Việt, ngắn gọn, dễ hiểu và chính xác.
Dựa vào thông tin được cung cấp, nếu không có thông tin đầy đủ thì hãy nói rõ.
Luôn trích dẫn nguồn thông tin pháp luật chính xác (nếu có) như tên văn bản, điều khoản.
Trình bày câu trả lời theo đoạn văn có cấu trúc tốt, dễ hiểu."""}
        ]
        
        for msg in chat_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role and content:
                messages.append({"role": role, "content": content})
        
        prompt = f"""Người dùng hỏi: {query}

Dưới đây là các tài liệu y tế và pháp luật liên quan giúp bạn trả lời:

{context}

Hãy trả lời câu hỏi của người dùng dựa trên thông tin từ các tài liệu trên. Nếu tài liệu không cung cấp đủ thông tin để trả lời, hãy nói rõ. Luôn trích dẫn nguồn thông tin từ các văn bản pháp luật nếu có (ví dụ: Theo Luật X, Điều Y...).
Trả lời súc tích, dễ hiểu nhưng đầy đủ thông tin quan trọng."""

        messages.append({"role": "user", "content": prompt})
        
        response = groq_client.chat.completions.create(
            model=DEFAULT_LLM_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        answer = response.choices[0].message.content
        generation_time = time.time() - llm_start
        
        # Save assistant response to session if user is logged in
        if current_user and session_id != "anonymous":
            add_message_to_session(session_id, current_user.email, "assistant", answer)
        
        return ChatResponse(
            answer=answer,
            sources=sources[:3],  
            retrieval_time=retrieval_time,
            generation_time=generation_time,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Lỗi khi xử lý câu hỏi: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý câu hỏi: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port) 