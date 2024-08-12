# override_model_switcher

## 项目简介

override_model_switcher是一个用于管理和切换 OpenAI API 配置的工具。它允许用户上传、管理多个 API 渠道的配置，并在不同的渠道和模型之间进行切换。该工具提供了一个 Web 界面和 API 接口，方便用户进行操作。

## 主要功能

1. 上传和管理 API 配置
2. 批量上传渠道配置
3. 切换当前使用的 API 渠道
4. 选择和切换 AI 模型
5. 提供 API 代理，支持流式和非流式响应

## 技术栈

- 后端：FastAPI
- 前端：HTML, JavaScript, CSS
- 数据存储：JSON 文件
- 容器化：Docker

## 安装和运行

### 使用 Docker

1. 构建 Docker 镜像：

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

访问 `http://localhost:8000` 即可使用 Web 界面。

## 配置

- 在 `.env` 文件中设置默认的 API 配置。

   ```plaintext
   DEFAULT_BASE_URL=xxx #默认BASE_URL
   DEFAULT_API_KEY=xxx #默认API_KEY,同时也用作调用override api接口的apikey，注意保存
   DEFAULT_MODEL=gpt-4o #默认模型
   CURRENT_CHANNEL=default #当前使用的渠道
   ```

- 使用 `config.json` 文件存储和管理多个渠道的配置,格式如下,无需配置,项目自动生成。

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

## API 接口

- `/v1/chat/completions`：代理 OpenAI 的聊天完成接口
- `/switch/override_model`：切换当前使用的模型
- `/add_channel`：添加新的 API 渠道配置
- `/bulk_add_channels`：批量添加 API 渠道配置
- `/switch_channel`：切换当前使用的 API 渠道
- 更多接口请参考 `app/routes.py` 文件

## 许可证

本项目采用 MIT 许可证。详情请见 [LICENSE](LICENSE) 文件。

## 作者

snailyp
