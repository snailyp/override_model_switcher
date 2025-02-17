import tkinter as tk
from tkinter import ttk, messagebox
import requests
from typing import Optional

BASE_URL = "http://localhost:8000"

class ModelSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("API 通道和模型切换工具")
        self.root.geometry("700x600")
        
        # 当前状态
        self.current_channel: Optional[str] = None
        self.current_model: Optional[str] = None
        
        self.create_widgets()
        self.refresh_status()

    def create_widgets(self):
        # 状态显示区域
        status_frame = ttk.LabelFrame(self.root, text="当前状态", padding=10)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.current_channel_label = ttk.Label(status_frame, text="当前通道: 加载中...")
        self.current_channel_label.pack(anchor="w")
        
        self.current_model_label = ttk.Label(status_frame, text="当前模型: 加载中...")
        self.current_model_label.pack(anchor="w")

        # 配置上传部分
        config_frame = ttk.LabelFrame(self.root, text="添加新通道", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)

        # 渠道名称
        ttk.Label(config_frame, text="通道名称:").pack(anchor="w")
        self.channel_name = ttk.Entry(config_frame, width=40)
        self.channel_name.pack(fill="x", pady=2)

        # Base URL
        ttk.Label(config_frame, text="Base URL:").pack(anchor="w")
        self.base_url = ttk.Entry(config_frame, width=40)
        self.base_url.pack(fill="x", pady=2)

        # API Key
        ttk.Label(config_frame, text="API Key:").pack(anchor="w")
        self.api_key = ttk.Entry(config_frame, width=40)
        self.api_key.pack(fill="x", pady=2)

        ttk.Button(config_frame, text="添加通道", command=self.upload_config).pack(pady=5)

        # 通道切换部分
        channel_frame = ttk.LabelFrame(self.root, text="切换通道", padding=10)
        channel_frame.pack(fill="x", padx=10, pady=5)
        
        self.channel_select = ttk.Combobox(channel_frame, width=38)
        self.channel_select.pack(side="left", padx=5)
        
        ttk.Button(channel_frame, text="切换", command=self.switch_channel).pack(side="left", padx=5)
        ttk.Button(channel_frame, text="刷新", command=self.fetch_channels).pack(side="left", padx=5)
        ttk.Button(channel_frame, text="删除", command=self.delete_channel).pack(side="left", padx=5)

        # 模型切换部分
        model_frame = ttk.LabelFrame(self.root, text="切换模型", padding=10)
        model_frame.pack(fill="x", padx=10, pady=5)
        
        self.model_select = ttk.Combobox(model_frame, width=38)
        self.model_select.pack(side="left", padx=5)
        
        ttk.Button(model_frame, text="切换", command=self.switch_model).pack(side="left", padx=5)
        ttk.Button(model_frame, text="刷新", command=self.fetch_models).pack(side="left", padx=5)

        # 操作按钮
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(button_frame, text="刷新状态", command=self.refresh_status).pack(side="left", padx=5)
        ttk.Button(button_frame, text="测试当前通道", command=self.test_current_channel).pack(side="left")

    def refresh_status(self):
        """刷新当前状态显示"""
        try:
            # 获取当前通道
            response = requests.get(f"{BASE_URL}/get_current_channel")
            if response.ok:
                self.current_channel = response.json()["current_channel"]
                self.current_channel_label.config(text=f"当前通道: {self.current_channel}")
            
            # 获取当前模型
            response = requests.get(f"{BASE_URL}/get_current_model")
            if response.ok:
                self.current_model = response.json()["current_model"]
                self.current_model_label.config(text=f"当前模型: {self.current_model}")
            
            # 刷新通道和模型列表
            self.fetch_channels()
            self.fetch_models()
            
        except requests.RequestException as e:
            self.show_error(f"刷新状态失败: {str(e)}")

    def upload_config(self):
        """上传新通道配置"""
        channel_name = self.channel_name.get().strip()
        base_url = self.base_url.get().strip()
        api_key = self.api_key.get().strip()

        if not all([channel_name, base_url, api_key]):
            self.show_error("请填写所有字段")
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
                self.show_success("通道添加成功")
                self.fetch_channels()
                # 清空输入框
                self.channel_name.delete(0, tk.END)
                self.base_url.delete(0, tk.END)
                self.api_key.delete(0, tk.END)
            else:
                self.show_error(f"添加失败: {response.json().get('detail', '')}")
        except requests.RequestException as e:
            self.show_error(f"添加失败: {str(e)}")

    def switch_channel(self):
        """切换通道"""
        selected_channel = self.channel_select.get()
        if not selected_channel:
            self.show_error("请选择要切换的通道")
            return

        try:
            response = requests.post(
                f"{BASE_URL}/switch_channel",
                json={"channel_name": selected_channel}
            )
            if response.ok:
                self.show_success(f"已切换到通道: {selected_channel}")
                self.refresh_status()
            else:
                self.show_error(f"切换失败: {response.json().get('detail', '')}")
        except requests.RequestException as e:
            self.show_error(f"切换失败: {str(e)}")

    def switch_model(self):
        """切换模型"""
        selected_model = self.model_select.get()
        if not selected_model:
            self.show_error("请选择要切换的模型")
            return

        try:
            response = requests.post(
                f"{BASE_URL}/switch/override_model",
                json={"model": selected_model}
            )
            if response.ok:
                self.show_success(f"已切换到模型: {selected_model}")
                self.refresh_status()
            else:
                self.show_error(f"切换失败: {response.json().get('detail', '')}")
        except requests.RequestException as e:
            self.show_error(f"切换失败: {str(e)}")

    def fetch_channels(self):
        """获取通道列表"""
        try:
            response = requests.get(f"{BASE_URL}/get_channels")
            if response.ok:
                channels = response.json()
                self.channel_select["values"] = channels
                if self.current_channel in channels:
                    self.channel_select.set(self.current_channel)
        except requests.RequestException as e:
            self.show_error(f"获取通道列表失败: {str(e)}")

    def fetch_models(self):
        """获取模型列表"""
        try:
            response = requests.get(f"{BASE_URL}/v1/models")
            if response.ok:
                models = [model["id"] for model in response.json()["data"]]
                self.model_select["values"] = models
                if self.current_model in models:
                    self.model_select.set(self.current_model)
        except requests.RequestException as e:
            self.show_error(f"获取模型列表失败: {str(e)}")

    def test_current_channel(self):
        """测试当前通道"""
        if not self.current_channel:
            self.show_error("没有选择通道")
            return

        try:
            response = requests.post(f"{BASE_URL}/test_all_models", params={"channel_name": self.current_channel})
            if response.ok:
                results = response.json()["results"]
                self.show_test_results(results)
            else:
                self.show_error(f"测试失败: {response.json().get('detail', '')}")
        except requests.RequestException as e:
            self.show_error(f"测试失败: {str(e)}")

    def show_test_results(self, results):
        """显示测试结果"""
        result_window = tk.Toplevel(self.root)
        result_window.title("测试结果")
        result_window.geometry("400x300")

        text = tk.Text(result_window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for model, status in results.items():
            text.insert(tk.END, f"{model}: {status}\n")
        
        text.config(state=tk.DISABLED)

    def show_error(self, message):
        messagebox.showerror("错误", message)

    def delete_channel(self):
        """删除选中的通道"""
        selected_channel = self.channel_select.get()
        if not selected_channel:
            self.show_error("请选择要删除的通道")
            return

        if messagebox.askyesno("确认", f"确定要删除通道 {selected_channel} 吗？"):
            try:
                response = requests.delete(
                    f"{BASE_URL}/delete_channel",
                    json={"channel_name": selected_channel}
                )
                if response.ok:
                    self.show_success(f"已删除通道: {selected_channel}")
                    self.refresh_status()
                else:
                    self.show_error(f"删除失败: {response.json().get('detail', '')}")
            except requests.RequestException as e:
                self.show_error(f"删除失败: {str(e)}")

    def show_success(self, message):
        messagebox.showinfo("成功", message)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModelSwitcher(root)
    root.mainloop()
