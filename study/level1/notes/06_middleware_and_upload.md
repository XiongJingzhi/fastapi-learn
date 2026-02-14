# 中间件与文件上传 - FastAPI 高级特性

## 🎯 什么是中间件？

### 类比理解

```
中间件就像"安检员"

客户端请求 → 安检员1（CORS检查）
            → 安检员2（日志记录）
            → 安检员3（认证）
            → 安检员4（限流）
            → 你的端点处理
            → 安检员4（添加响应头）
            → 安检员3（格式化响应）
            → 安检员2（记录响应）
            → 客户端收到响应
```

**中间件的特点**：

1. ✅ **全局性**：影响所有请求
2. ✅ **可组合**：可以叠加多个中间件
3. ✅ **灵活性**：在请求前后做处理
4. ✅ **透明性**：端点不知道中间件的存在

---

## 🔧 FastAPI 中间件

### 中间件执行顺序

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

app = FastAPI()

# 添加中间件（顺序很重要！）
@app.middleware("http")
async def add_process_time(request: Request, call_next):
    """添加处理时间到响应头"""
    start_time = time.time()

    # 调用下一个中间件或端点
    response = await call_next(request)

    # 处理响应
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求和响应"""
    print(f"📥 {request.method} {request.url}")

    response = await call_next(request)

    print(f"📤 {response.status_code}")
    return response

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 执行顺序：
# 1. log_requests 开始
# 2. add_process_time 开始
# 3. CORS 检查
# 4. 端点处理
# 5. add_process_time 结束
# 6. log_requests 结束
```

### 自定义中间件

```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class CustomMiddleware(BaseHTTPMiddleware):
    """自定义中间件基类"""

    async def dispatch(self, request: Request, call_next):
        """处理请求和响应"""

        # 请求前处理
        print(f"Before: {request.url}")

        # 调用下一个
        response = await call_next(request)

        # 响应后处理
        print(f"After: {response.status_code}")

        # 可以修改响应
        response.headers["X-Custom-Header"] = "Custom Value"

        return response

# 使用
app.add_middleware(CustomMiddleware)
```

---

## 🛡️ 常用内置中间件

### 1. CORS（跨域资源共享）

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    # 允许的源
    allow_origins=[
        "http://localhost:3000",
        "https://myapp.com",
    ],
    # 允许的凭证（cookies）
    allow_credentials=True,
    # 允许的方法
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    # 允许的头
    allow_headers=["*"],
    # 预检请求缓存时间（秒）
    max_age=600,
)
```

### 2. HTTPS 重定向

```python
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

# 自动重定向 HTTP 到 HTTPS
app.add_middleware(HTTPSRedirectMiddleware)
```

### 3. 可信主机

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    # 允许的主机
    allowed_hosts=[
        "example.com",
        "*.example.com",
        "localhost",
    ]
)
```

### 4. GZip 压缩

```python
from starlette.middleware.gzip import GZipMiddleware

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # 大于 1KB 才压缩
)
```

### 5. Session 中间件

```python
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key",
    session_cookie="session_id",
    max_age=3600,  # 1小时
)

@app.get("/set")
async def set_session(request: Request):
    request.session["user"] = "alice"
    return {"message": "Session set"}

@app.get("/get")
async def get_session(request: Request):
    user = request.session.get("user")
    return {"user": user}
```

---

## 📤 文件上传

### 基础文件上传

```python
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from typing import List
import os

app = FastAPI()

# 配置上传目录
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/uploadfile/")
async def create_upload_file(file: bytes = File(...)):
    """
    上传小文件（作为字节）

    适合：
    - 小文件（几 KB）
    - 需要立即处理的文件
    """
    # file 是 bytes
    file_size = len(file)

    return {
        "file_size": file_size,
        "message": "File uploaded successfully"
    }

@app.post("/uploadfile/upload")
async def create_upload_file_upload(file: UploadFile = File(...)):
    """
    上传文件（使用 UploadFile）

    适合：
    - 大文件
    - 需要流式处理
    - 需要文件元数据
    """
    # 保存文件
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "file_location": file_location
    }
```

### HTML 上传表单

```python
@app.get("/upload")
async def upload_form():
    """显示上传表单"""
    content = """
    <html>
        <head>
            <title>上传文件</title>
        </head>
        <body>
            <form action="/uploadfile/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="file">
                <input type="submit" value="上传">
            </form>
        </body>
    </html>
    """
    return HTMLResponse(content=content)
```

### 多文件上传

```python
@app.post("/uploadfiles/")
async def create_upload_files(files: List[UploadFile] = File(...)):
    """
    上传多个文件

    使用：
    curl -X POST "http://localhost:8000/uploadfiles/" \\
      -F "files=@file1.txt" \\
      -F "files=@file2.txt"
    """
    uploaded_files = []

    for file in files:
        file_location = f"{UPLOAD_DIR}/{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())

        uploaded_files.append({
            "filename": file.filename,
            "content_type": file.content_type,
            "file_location": file_location
        })

    return {
        "uploaded_files": uploaded_files,
        "count": len(uploaded_files)
    }
```

### 文件 + 表单数据

```python
from pydantic import BaseModel

class FileMetadata(BaseModel):
    """文件元数据"""
    description: str
    category: str

@app.post("/upload-with-metadata/")
async def upload_with_metadata(
    file: UploadFile = File(...),
    description: str = Form(...),
    category: str = Form(...)
):
    """
    同时上传文件和表单数据

    使用：
    curl -X POST "http://localhost:8000/upload-with-metadata/" \\
      -F "file=@test.txt" \\
      -F "description=Test file" \\
      -F "category=documents"
    """
    file_location = f"{UPLOAD_DIR}/{file.filename}"

    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())

    return {
        "filename": file.filename,
        "description": description,
        "category": category,
        "file_location": file_location
    }
```

---

## 🎨 高级文件处理

### 1. 文件类型验证

```python
from pathlib import Path

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file(file: UploadFile) -> bool:
    """验证文件"""
    # 检查文件扩展名
    file_ext = Path(file.filename).suffix
    if file_ext.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError(f"不支持的文件类型: {file_ext}")

    # 检查文件大小
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"文件太大: {file_size} bytes")

    return True

@app.post("/upload-validated/")
async def upload_validated_file(file: UploadFile = File(...)):
    """上传验证过的文件"""
    try:
        validate_file(file)

        # 保存文件
        file_location = f"{UPLOAD_DIR}/{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())

        return {"message": "File uploaded successfully", "file": file.filename}

    except ValueError as e:
        return {"error": str(e)}, 400
```

### 2. 异步大文件处理

```python
import shutil
import aiofiles

@app.post("/upload-large/")
async def upload_large_file(file: UploadFile = File(...)):
    """
    异步处理大文件

    优点：
    - 不阻塞事件循环
    - 可以处理大文件
    - 内存友好
    """
    file_location = f"{UPLOAD_DIR}/{file.filename}"

    # 异步写入文件
    async with aiofiles.open(file_location, 'wb') as f:
        # 分块读取和写入
        while content := await file.read(1024 * 1024):  # 1MB chunks
            await f.write(content)

    return {"message": "Large file uploaded successfully"}
```

### 3. 生成唯一文件名

```python
import uuid
from datetime import datetime

def generate_unique_filename(original_filename: str) -> str:
    """生成唯一文件名"""
    # 获取文件扩展名
    file_ext = Path(original_filename).suffix

    # 生成唯一标识
    unique_id = uuid.uuid4().hex[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 组合新文件名
    new_filename = f"{timestamp}_{unique_id}{file_ext}"

    return new_filename

@app.post("/upload-unique/")
async def upload_with_unique_name(file: UploadFile = File(...)):
    """上传文件并生成唯一文件名"""
    unique_filename = generate_unique_filename(file.filename)
    file_location = f"{UPLOAD_DIR}/{unique_filename}"

    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())

    return {
        "original_filename": file.filename,
        "unique_filename": unique_filename,
        "file_location": file_location
    }
```

### 4. 文件分片上传

```python
from fastapi import UploadFile, File, Form
from typing import Optional

@app.post("/upload-chunk/")
async def upload_chunk(
    file: UploadFile = File(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    file_id: str = Form(...)
):
    """
    分片上传

    流程：
    1. 客户端将大文件分成多个小块
    2. 逐个上传每个块
    3. 服务器保存临时文件
    4. 所有块上传完成后合并
    """
    chunk_dir = f"{UPLOAD_DIR}/chunks/{file_id}"
    os.makedirs(chunk_dir, exist_ok=True)

    chunk_path = f"{chunk_dir}/chunk_{chunk_index}"

    with open(chunk_path, "wb") as f:
        f.write(await file.read())

    # 如果是最后一个块，合并所有块
    if chunk_index == total_chunks - 1:
        import glob

        chunks = sorted(glob.glob(f"{chunk_dir}/chunk_*"))
        output_path = f"{UPLOAD_DIR}/{file_id}"

        with open(output_path, "wb") as outfile:
            for chunk in chunks:
                with open(chunk, "rb") as infile:
                    outfile.write(infile.read())

        # 删除临时文件
        shutil.rmtree(chunk_dir)

        return {"message": "File merged successfully", "file": file_id}

    return {"message": f"Chunk {chunk_index} uploaded"}
```

---

## 📥 文件下载

### 基础文件下载

```python
from fastapi.responses import FileResponse

@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    下载文件

    返回：
    - 文件内容
    - 正确的 Content-Type
    - Content-Disposition 头（浏览器会弹出下载对话框）
    """
    file_path = f"{UPLOAD_DIR}/{filename}"

    if not os.path.exists(file_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )
```

### 流式大文件下载

```python
from fastapi.responses import StreamingResponse
import io

@app.get("/download-large/{filename}")
async def download_large_file(filename: str):
    """
    流式下载大文件

    优点：
    - 内存友好
    - 边读边发送
    - 适合大文件
    """
    file_path = f"{UPLOAD_DIR}/{filename}"

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    def iterfile():
        """生成器：分块读取文件"""
        with open(file_path, mode="rb") as file_like:
            yield from file_like

    return StreamingResponse(
        iterfile(),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
```

---

## 🛡️ 安全考虑

### 1. 文件扩展名验证

```python
import os

def is_safe_filename(filename: str) -> bool:
    """检查文件名是否安全"""
    # 检查路径遍历
    if ".." in filename or filename.startswith("/"):
        return False

    # 检查文件扩展名
    allowed_extensions = {".txt", ".pdf", ".png", ".jpg"}
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_extensions

@app.post("/upload-safe/")
async def upload_safe_file(file: UploadFile = File(...)):
    """安全上传文件"""
    if not is_safe_filename(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename"
        )

    # 继续处理...
    return {"message": "File is safe"}
```

### 2. 病毒扫描

```python
# 注意：需要安装 clamd 或使用云服务

def scan_for_virus(file_path: str) -> bool:
    """扫描病毒（示例）"""
    # 实际实现需要集成杀毒软件
    # 例如：pyclamd, subprocess 调用 clamscan
    # 或使用云服务 API
    return True

@app.post("/upload-scanned/")
async def upload_scanned_file(file: UploadFile = File(...)):
    """上传文件并扫描病毒"""
    # 保存到临时位置
    temp_path = f"{UPLOAD_DIR}/temp_{file.filename}"
    with open(temp_path, "wb+") as f:
        f.write(await file.read())

    # 扫描病毒
    if not scan_for_virus(temp_path):
        os.remove(temp_path)
        raise HTTPException(
            status_code=400,
            detail="Virus detected in file"
        )

    # 移动到最终位置
    final_path = f"{UPLOAD_DIR}/{file.filename}"
    os.rename(temp_path, final_path)

    return {"message": "File is clean and uploaded"}
```

---

## 🎯 总结

**中间件核心要点**：

1. ✅ **全局处理**：影响所有请求/响应
2. ✅ **可组合**：可以叠加多个中间件
3. ✅ **顺序重要**：按声明顺序执行
4. ✅ **灵活性**：请求前后都可以处理

**文件上传核心要点**：

1. ✅ **小文件**：使用 `bytes`
2. ✅ **大文件**：使用 `UploadFile`
3. ✅ **安全验证**：检查类型、大小、扩展名
4. ✅ **唯一文件名**：避免冲突
5. ✅ **病毒扫描**：生产环境必需

**最佳实践**：
- 总是验证上传的文件
- 限制文件大小
- 使用唯一文件名
- 异步处理大文件
- 定期清理临时文件

**下一步**：学习 WebSocket 和部署

---

**中间件和文件上传让应用更强大！** 🚀
