# Override Model Switcher

这是一个基于 FastAPI 的 Web 应用程序，允许用户在不同的 OpenAI 模型之间进行切换。它包括后端 API 和前端界面。

## 项目结构

- `app/`: 包含主要的应用程序逻辑
  - `openai.py`: 处理与 OpenAI API 的通信
  - `routes.py`: 定义 API 路由
  - `log_config.py`: 设置日志配置
- `static/`: 包含前端的静态文件
  - `script.js`: 前端功能的 JavaScript 文件
- `templates/`: 可能包含 HTML 模板
- `tool/`: 包含额外的实用工具
  - `model_switcher.py`: 实现模型切换功能
- `main.py`: 应用程序的入口点
- `requirements.txt`: 列出项目依赖
- `.env`: 包含环境变量（API 密钥、URL 等）
- `Dockerfile`: 用于构建 Docker 镜像

## 设置

### 本地设置

1. 克隆仓库
2. 安装依赖：

   ```bash

   pip install -r requirements.txt

   ```

3. 设置 `.env` 文件，包含以下变量：
   - `BASE_URL`: OpenAI API 的基础 URL
   - `API_KEY`: 您的 OpenAI API 密钥
   - `OVERRIDE_MODEL`: 要使用的默认模型

### Docker 设置

1. 构建 Docker 镜像：

   ```bash

   docker build -t override-model-switcher .

   ```

2. 运行 Docker 容器：

   ```bash

   docker run -p 8000:8000 -e BASE_URL=<your_base_url> -e API_KEY=<your_api_key> -e OVERRIDE_MODEL=<your_default_model> override-model-switcher

   ```

## 运行应用程序

### 本地运行

使用以下命令运行应用程序：

```bash

python main.py

```

服务器将在 `http://0.0.0.0:8000` 上启动。

### 使用 Docker 运行

如果使用 Docker，在运行 Docker 容器后，应用程序将自动启动并在 `http://localhost:8000` 上可用。

## 功能

- 从 OpenAI API 获取可用模型
- 允许在不同模型之间切换
- 提供用于轻松切换模型的 Web 界面
- 实现 CORS 以处理跨源请求
- 提供静态文件服务

## API 端点

- GET `/`: 提供 Web 模型切换界面
- GET `/v1/models`: 获取可用模型列表
- POST `/switch/override_models`: 切换到指定的模型
- POST `/v1/chat/completions`: 处理聊天补全

## 前端

前端提供了用户友好的界面，用于模型切换，并相应地显示成功或错误消息。

## 注意

确保保密您的 API 密钥，不要在公共仓库中暴露它。在使用 Docker 时，请通过环境变量传递敏感信息，而不是将其包含在镜像中。
