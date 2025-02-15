# override_model_switcher

## 项目简介

override_model_switcher最初是为override工具开发的一个模型切换管理器，目的是实现在运行时灵活切换模型而无需停止项目、修改配置并重启。随着开发的深入，我们发现这个工具不仅适用于override，还能很好地支持各种AI工具的模型管理需求。它完全兼容OpenAI的API请求格式，这意味着任何使用OpenAI API的应用都可以无缝接入使用。它提供了一个直观的Web界面和完整的API接口，让用户能够轻松管理多个API渠道配置，并在不同渠道和模型之间灵活切换。特别适合需要管理多个API密钥或在多个AI模型间切换的场景。

## 主要功能

1. **多渠道管理**
   - 支持添加、删除和管理多个API渠道
   - 提供批量导入渠道配置功能
   - 实时切换不同渠道

2. **模型管理**
   - 自动获取可用模型列表
   - 支持模型实时切换
   - 支持模型可用性测试

3. **API代理功能**
   - 完整支持OpenAI聊天接口
   - 支持流式响应和普通响应
   - 自动消息合并优化（针对Claude等模型）

4. **安全特性**
   - API密钥认证
   - CORS支持
   - 错误处理和日志记录

## 技术栈

- **后端框架**：
  - FastAPI：高性能异步Web框架
  - Uvicorn：ASGI服务器
  - Pydantic：数据验证

- **前端技术**：
  - HTML + JavaScript + CSS
  - Jinja2模板引擎

- **网络处理**：
  - HTTPX：异步HTTP客户端
  - Starlette：CORS中间件

- **其他组件**：
  - python-dotenv：环境变量管理
  - colorlog：日志美化
  - SQLAlchemy：数据库支持（可选）

## 使用说明

### 配合override工具使用

1. 在override工具中配置API代理：

   ```plaintext
   # 配置其他ai工具使用本工具作为API代理
   ai工具的模型base_url配置 = 指向model_switcher的地址
   ai工具的模型model配置 = override (固定这个名称，可以用来切换模型)
   ```

2. 在Web界面或通过API进行模型切换：
   - 添加新的API渠道（包含不同的API密钥或基础URL）
   - 选择想要使用的渠道
   - 选择该渠道下可用的模型
   - 切换完成后，override工具会自动使用新选择的模型，无需重启项目

### 独立使用

本工具完全实现了OpenAI的API接口规范，可以作为独立的API代理使用。这意味着：

- 支持所有标准的OpenAI API端点
- 请求格式与OpenAI API完全一致
- 响应格式保持与OpenAI一致
- 支持流式输出等高级特性
- 可以无缝替代OpenAI的API端点

因此，任何使用OpenAI API的应用都可以通过简单修改API基础URL来使用本工具，无需其他改动。

## 安装和运行

### 使用Docker

1. 构建镜像：

   ```bash
   docker build -t openai-api-manager .
   ```

2. 运行容器：

   ```bash
   docker run -p 8000:8000 openai-api-manager
   ```

### 本地运行

1. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

2. 运行应用：

   ```bash
   python main.py
   ```

访问 `http://localhost:8000` 使用Web界面。

## 配置说明

### 环境变量配置

在 `.env` 文件中设置：

```plaintext
DEFAULT_BASE_URL=xxx    # 默认API基础URL
DEFAULT_API_KEY=xxx     # 默认API密钥（同时用作管理接口的认证密钥）
DEFAULT_MODEL=gpt-4o    # 默认使用的模型
CURRENT_CHANNEL=default # 默认渠道名称
DATABASE_URL=mysql+pymysql://root:123456@host:port/model_switcher # 数据库连接信息
```

### 渠道配置文件

系统使用 `config.json` 存储渠道配置：

```json
{
  "channels": {
    "default": {
      "base_url": "https://xxx",
      "api_key": "sk-xxx",
      "model": "gpt-4o"
    }
  },
  "current_channel": "",
  "current_model": "",
  "api_key": ""
}
```

## API接口说明

### 基础接口

- `GET /health_check`：服务健康检查
- `GET /`：Web界面

### 模型管理

- `GET /v1/models`：获取可用模型列表
- `POST /switch/override_model`：切换当前模型
- `GET /export_models`：导出模型列表
- `POST /test_all_models`：测试指定渠道的所有模型

### 渠道管理

- `GET /get_channels`：获取所有渠道列表
- `POST /add_channel`：添加单个渠道
- `POST /bulk_add_channels`：批量添加渠道
- `DELETE /delete_channel/{channel_name}`：删除指定渠道
- `POST /switch_channel`：切换当前渠道
- `GET /export_channels`：导出所有渠道配置

### OpenAI代理

- `POST /v1/chat/completions`：代理OpenAI聊天接口
  - 支持流式响应
  - 自动消息合并
  - 模型自动替换

## 许可证

本项目采用MIT许可证。详情请见[LICENSE](LICENSE)文件。

## 作者

snailyp
