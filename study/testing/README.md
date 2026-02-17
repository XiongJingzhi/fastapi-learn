# Testing Toolkit

## 1) 命令行 Smoke Test

先启动目标示例（示例）：

```bash
uvicorn study.level1.examples.01_request_validation:app --reload --port 8000
```

再执行：

```bash
BASE_URL=http://localhost:8000 ./study/testing/smoke_level1.sh
```

## 2) Postman 一键导入

导入以下两个文件即可开始测试：

- `study/testing/postman/fastapi-learning.postman_collection.json`
- `study/testing/postman/fastapi-learning.local.postman_environment.json`

导入步骤：

1. 打开 Postman -> `Import`
2. 选择以上两个 JSON 文件
3. 选择环境 `FastAPI Learning Local`
4. 根据你当前启动的示例，修改环境变量 `base_url`
5. 在对应 Folder 点击 `Run`

## 3) 推荐启动命令

每次只启动一个示例 app，避免路由冲突：

```bash
uvicorn study.level1.examples.01_request_validation:app --reload --port 8000
uvicorn study.level1.examples.05_restful_api:app --reload --port 8000
uvicorn study.level2.examples.01_di_basics:app --reload --port 8000
uvicorn study.level3.examples.01_database_basics:app --reload --port 8000
uvicorn study.level4.examples.02_message_queue:app --reload --port 8000
uvicorn study.level5.examples.main:app --reload --port 8000
```

## 4) Newman（Postman CLI）运行

先启动对应 app（例如 level1）：

```bash
uvicorn study.level1.examples.01_request_validation:app --reload --port 8000
```

执行 collection 中某个 folder：

```bash
BASE_URL=http://127.0.0.1:8000 \
FOLDER="Level1 - 01 Request Validation" \
./study/testing/newman/run_newman.sh
```

生成报告：

- `study/testing/newman/newman-report.xml`

## 5) CI 工作流

已提供 GitHub Actions 工作流：

- `.github/workflows/newman-level1.yml`

流程：

1. 安装 Python 依赖（`uv sync`）
2. 安装 `newman`
3. 启动 `study.level1.examples.01_request_validation:app`
4. 运行 `Level1 - 01 Request Validation` folder
5. 上传 junit 报告与 uvicorn 日志
