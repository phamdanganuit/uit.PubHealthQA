#!/usr/bin/env python3
"""
Script để tạo SECRET_KEY an toàn cho ứng dụng UIT@PubHealthQA
"""

import secrets
import string

def generate_secret_key(length=32):
    """Tạo SECRET_KEY ngẫu nhiên và an toàn"""
    return secrets.token_urlsafe(length)

def generate_alternative_key(length=50):
    """Tạo SECRET_KEY thay thế với ký tự alphanumeric"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    print("🔐 SECRET_KEY Generator cho UIT@PubHealthQA")
    print("=" * 50)
    
    # Tạo SECRET_KEY chính
    secret_key = generate_secret_key()
    print(f"SECRET_KEY (URL-safe): {secret_key}")
    
    # Tạo SECRET_KEY thay thế
    alt_key = generate_alternative_key()
    print(f"SECRET_KEY (Alternative): {alt_key}")
    
    print("\n📋 Để sử dụng:")
    print("1. Copy SECRET_KEY ở trên")
    print("2. Paste vào Azure App Service → Configuration → Application Settings")
    print("3. Hoặc thêm vào file .env local:")
    print(f"   SECRET_KEY={secret_key}")
    
    print("\n⚠️  Lưu ý:")
    print("- Không share SECRET_KEY này với ai")
    print("- Mỗi environment nên có SECRET_KEY khác nhau")
    print("- SECRET_KEY phải dài ít nhất 32 ký tự")