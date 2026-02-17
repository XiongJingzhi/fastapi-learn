# Apifox OpenAPI Export

Apifox 支持导入 OpenAPI 3.0/3.1 或 Swagger 2.0 的 JSON/YAML。  
本目录提供 FastAPI 示例的 OpenAPI JSON 导出工具。

## 1) 导出 OpenAPI 文件

在项目根目录执行：

```bash
.venv/bin/python study/testing/apifox/export_openapi.py
```

导出结果在：

- `study/testing/apifox/openapi/*.openapi.json`

## 2) 导入到 Apifox

1. 打开 Apifox
2. 选择 `导入` -> `OpenAPI/Swagger`
3. 选择某个 `*.openapi.json` 文件
4. 完成导入后即可生成接口目录与调试用例

## 3) 推荐导入文件

- Level 1: `level1_01_request_validation.openapi.json`
- Level 2: `level2_01_di_basics.openapi.json`
- Level 3: `level3_01_database_basics.openapi.json`
- Level 4: `level4_02_message_queue.openapi.json`
- Level 5: `level5_main.openapi.json`
