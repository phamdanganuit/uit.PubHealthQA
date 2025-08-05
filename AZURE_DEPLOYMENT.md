# 🚀 Hướng dẫn Deploy UIT@PubHealthQA lên Azure App Service

## 📋 Yêu cầu trước khi deploy

- ✅ Azure Student account
- ✅ MongoDB đã được setup (đã hoàn thành)
- ✅ GROQ API Key: (bạn đã có sẵn - sẽ cấu hình trong Azure Portal)

## 🔧 Bước 1: Chuẩn bị dự án

### 1.1 Tạo file .env (local development)
```bash
# Tạo file .env trong thư mục gốc của dự án (KHÔNG commit file này)
GROQ_API_KEY=your_groq_api_key_here
```

### 1.2 Kiểm tra các file đã được tạo
Đảm bảo các file sau đã có trong dự án:
- ✅ `startup.sh` - Script khởi động cho Azure
- ✅ `requirements.txt` - Dependencies đã cập nhật
- ✅ `.env` - Biến môi trường (KHÔNG commit)
- ✅ `src/models.py` - Đã cập nhật để sử dụng biến môi trường

## 🌐 Bước 2: Tạo Azure App Service

### 2.1 Đăng nhập Azure Portal
1. Truy cập [portal.azure.com](https://portal.azure.com)
2. Đăng nhập với tài khoản Azure Students

### 2.2 Tạo App Service
1. Click **"Create a resource"**
2. Tìm và chọn **"Web App"**
3. Cấu hình như sau:

**Basic Settings:**
- **Subscription**: Azure for Students
- **Resource Group**: Tạo mới hoặc chọn có sẵn (ví dụ: `pubhealth-rg`)
- **Name**: `pubhealth-qa-app` (hoặc tên khác duy nhất)
- **Publish**: Code
- **Runtime stack**: Python 3.11
- **Operating System**: Linux
- **Region**: **Malaysia West** (hoặc Japan West, Korea Central - dành cho Azure Students)

**App Service Plan:**
- **Plan**: Basic B1 (miễn phí với Azure Students)

4. Click **"Review + Create"** → **"Create"**

## ⚙️ Bước 3: Cấu hình Environment Variables

### 3.1 Truy cập App Service Settings
1. Vào **App Service** vừa tạo
2. Ở menu bên trái, chọn **"Configuration"**
3. Tab **"Application settings"**

### 3.2 Thêm các biến môi trường sau:

| Name | Value | Note |
|------|-------|------|
| `GROQ_API_KEY` | `[your_groq_api_key]` | API key của bạn |
| `MONGODB_URL` | `[your_mongodb_url]` | Connection string |
| `DATABASE_NAME` | `pubhealthqa` | Database name |
| `SECRET_KEY` | `[tạo mới từ script]` | JWT secret key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token expire time |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | Azure build setting |
| `WEBSITE_STARTUP_FILE` | `startup.sh` | Startup script |

### 3.3 Lưu cấu hình
Click **"Save"** và đợi restart hoàn tất.

## 📁 Bước 4: Deploy Code

### 4.1 Option A: Deploy từ GitHub (Khuyến nghị)

1. **Push code lên GitHub:**
   ```bash
   git add .
   git commit -m "feat: add Azure deployment configuration"
   git push origin main
   ```

2. **Cấu hình Deployment Center:**
   - Trong Azure Portal, vào App Service
   - Chọn **"Deployment Center"**
   - Source: **GitHub**
   - Authorize và chọn repository
   - Branch: **main**
   - Build provider: **App Service build service**
   - Click **"Save"**

### 4.2 Option B: Deploy bằng Azure CLI

```bash
# Cài đặt Azure CLI nếu chưa có
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Đăng nhập
az login

# Deploy với region được phép cho Azure Students
az webapp up --resource-group pubhealth-rg --name pubhealth-qa-app --runtime "PYTHON:3.11" --sku B1 --location "malaysiawwest"
```

### 4.3 Option C: Deploy bằng ZIP

1. **Tạo ZIP file:**
   ```bash
   # Loại bỏ các thư mục không cần thiết
   zip -r deployment.zip . -x "*.git*" "*__pycache__*" "*.pyc" "*venv*" "*node_modules*" "*.env"
   ```

2. **Upload ZIP:**
   - Vào **"Development Tools"** → **"Advanced Tools"** → **"Go"**
   - Drag & drop file ZIP vào `/site/wwwroot/`

## 🔍 Bước 5: Kiểm tra Deployment

### 5.1 Kiểm tra Log
1. Vào **"Monitoring"** → **"Log stream"**
2. Xem log startup để đảm bảo không có lỗi

### 5.2 Test ứng dụng
1. Truy cập URL của App Service (ví dụ: `https://pubhealth-qa-app.azurewebsites.net`)
2. Kiểm tra endpoint health: `/health`
3. Test chức năng đăng ký/đăng nhập
4. Test chatbot functionality

## 🛠️ Bước 6: Troubleshooting

### 6.1 Các lỗi thường gặp:

**Lỗi: Module not found**
```bash
# Kiểm tra requirements.txt đã đủ chưa
# Đảm bảo SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

**Lỗi: Application failed to start**
```bash
# Kiểm tra startup.sh file
# Xem log trong Log stream
```

**Lỗi: MongoDB connection**
```bash
# Kiểm tra MONGODB_URL trong Application settings
# Đảm bảo MongoDB cho phép kết nối từ Azure IP
```

**Lỗi: Region Policy (Azure Students)**
- Đổi region sang: Malaysia West, Japan West, Korea Central, Indonesia Central

### 6.2 Debug Commands:
```bash
# SSH vào container (nếu cần)
# Vào Development Tools > SSH

# Kiểm tra file structure
ls -la /home/site/wwwroot/

# Kiểm tra Python environment
python --version
pip list

# Test MongoDB connection
python -c "import pymongo; print('MongoDB connection OK')"
```

## 🔐 Tạo SECRET_KEY

Chạy lệnh sau để tạo SECRET_KEY an toàn:

```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
```

Copy kết quả và paste vào Azure Application Settings.

## 📊 Bước 7: Monitoring & Maintenance

### 7.1 Setup Application Insights (Optional)
1. Tạo Application Insights resource
2. Copy Instrumentation Key
3. Thêm vào Application Settings: `APPINSIGHTS_INSTRUMENTATIONKEY`

### 7.2 Setup Custom Domain (Optional)
1. Vào **"Custom domains"**
2. Add domain và verify ownership
3. Configure SSL certificate

## 🎉 Hoàn thành!

Ứng dụng của bạn đã được deploy thành công lên Azure App Service!

**URL ứng dụng:** `https://[app-name].azurewebsites.net`

### Các endpoint quan trọng:
- **Trang chủ:** `/`
- **Health check:** `/health`
- **API docs:** `/docs`
- **Login:** `/login`
- **Register:** `/register`

## 📞 Hỗ trợ

Nếu gặp vấn đề gì, hãy kiểm tra:
1. Log stream trong Azure Portal
2. Application settings đã đúng chưa
3. MongoDB connection string
4. GROQ API key hợp lệ

---

**⚠️ Bảo mật quan trọng:**
- Không bao giờ commit file .env
- Không share API keys trong code
- Mỗi environment nên có SECRET_KEY riêng