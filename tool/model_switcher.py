import tkinter as tk
from tkinter import ttk
import requests

BASE_URL = "http://localhost:8000"


class ModelSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("API 配置和模型切换工具")
        self.root.geometry("400x500")

        self.create_widgets()
        self.fetch_channels()
        self.fetch_models()

    def create_widgets(self):
        # 配置上传部分
        ttk.Label(self.root, text="上传 API 配置").pack(pady=10)

        # 渠道名称
        channel_frame = ttk.Frame(self.root)
        channel_frame.pack(fill="x", padx=10)
        ttk.Label(channel_frame, text="渠道名称:").pack(side="left")
        self.channel_name = ttk.Entry(channel_frame, width=30)
        self.channel_name.pack(side="right", expand=True)

        # Base URL
        base_url_frame = ttk.Frame(self.root)
        base_url_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(base_url_frame, text="Base URL:").pack(side="left")
        self.base_url = ttk.Entry(base_url_frame, width=30)
        self.base_url.pack(side="right", expand=True)

        # API Key
        api_key_frame = ttk.Frame(self.root)
        api_key_frame.pack(fill="x", padx=10)
        ttk.Label(api_key_frame, text="API Key:").pack(side="left")
        self.api_key = ttk.Entry(api_key_frame, width=30)
        self.api_key.pack(side="right", expand=True)

        ttk.Button(self.root, text="上传配置", command=self.upload_config).pack(pady=10)

        # 渠道选择部分
        ttk.Label(self.root, text="选择渠道").pack(pady=10)
        self.channel_select = ttk.Combobox(self.root, width=30)
        self.channel_select.pack()

        ttk.Button(self.root, text="切换渠道", command=self.switch_channel).pack(
            pady=10
        )

        # 模型选择部分
        ttk.Label(self.root, text="选择要切换的模型").pack(pady=10)
        self.model_select = ttk.Combobox(self.root, width=30)
        self.model_select.pack()

        ttk.Button(self.root, text="切换模型", command=self.switch_model).pack(pady=10)

        # 消息显示
        self.message = tk.StringVar()
        ttk.Label(self.root, textvariable=self.message).pack(pady=10)

    def upload_config(self):
        channel_name = self.channel_name.get()
        base_url = self.base_url.get()
        api_key = self.api_key.get()

        if not channel_name or not base_url or not api_key:
            self.show_message("请填写所有字段", "error")
            return

        try:
            response = requests.post(
                f"{BASE_URL}/add_channel",
                json={
                    "channel_name": channel_name,
                    "base_url": base_url,
                    "api_key": api_key,
                },
            )
            if response.ok:
                self.show_message("配置上传成功", "success")
                self.fetch_channels()
            else:
                self.show_message("配置上传失败", "error")
        except requests.RequestException:
            self.show_message("上传配置时发生错误", "error")

    def switch_channel(self):
        selected_channel = self.channel_select.get()
        try:
            response = requests.post(
                f"{BASE_URL}/switch_channel", json={"channel": selected_channel}
            )
            if response.ok:
                self.show_message(f"已切换到渠道: {selected_channel}", "success")
                self.fetch_models()
            else:
                self.show_message("切换渠道失败", "error")
        except requests.RequestException:
            self.show_message("切换渠道时发生错误", "error")

    def switch_model(self):
        selected_model = self.model_select.get()
        try:
            response = requests.post(
                f"{BASE_URL}/switch/override_models", json={"model": selected_model}
            )
            if response.ok:
                self.show_message(f"模型已切换为: {selected_model}", "success")
            else:
                error_data = response.json()
                self.show_message(f"切换失败: {error_data.get('detail', '')}", "error")
        except requests.RequestException:
            self.show_message("切换模型时发生错误", "error")

    def fetch_channels(self):
        try:
            response = requests.get(f"{BASE_URL}/get_channels")
            if response.ok:
                channels = response.json()
                self.channel_select["values"] = channels
            else:
                self.show_message("获取渠道列表失败", "error")
        except requests.RequestException:
            self.show_message("获取渠道列表时发生错误", "error")

    def fetch_models(self):
        try:
            response = requests.get(f"{BASE_URL}/v1/models")
            if response.ok:
                data = response.json()
                models = [model["id"] for model in data["data"]]
                self.model_select["values"] = models
            else:
                self.show_message("获取模型列表失败", "error")
        except requests.RequestException:
            self.show_message("获取模型列表时发生错误", "error")

    def show_message(self, text, type):
        self.message.set(text)
        color = "red" if type == "error" else "green"
        self.root.update()


if __name__ == "__main__":
    root = tk.Tk()
    app = ModelSwitcher(root)
    root.mainloop()
