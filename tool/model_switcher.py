import tkinter as tk
from tkinter import messagebox
import requests

# 设置API的URL
API_URL = "http://localhost:8000/switch/override_models"
base_url = ""
api_key = ""
def fetch_models():
    # 发送 GET 请求到 OpenAI API 以获取模型列表
    try:
        response = requests.get(
            f"{base_url}/v1/models", headers={"Authorization": f"Bearer {api_key}"}
        )
        response.raise_for_status()  # 检查请求是否成功
        return response.json()
    except requests.exceptions.RequestException as e:
        return None

def get_allowed_models():
    models_data = fetch_models()
    # 检查获取的数据是否有效
    if models_data and 'data' in models_data:
        return [model['id'] for model in models_data['data']]
    return []

def switch_model(model):
    try:
        response = requests.post(API_URL, json={"model": model})
        if response.status_code == 200:
            messagebox.showinfo("成功", f"模型已切换为 {model}")
            current_model.set(f"当前模型：{model}")  # 更新当前模型标签
        else:
            messagebox.showerror("错误", f"切换失败: {response.text}")
    except requests.RequestException as e:
        messagebox.showerror("错误", f"请求失败: {str(e)}")

# 创建主窗口
root = tk.Tk()

# 初始化当前模型变量
current_model = tk.StringVar(value="当前模型：无")
root.title("模型切换工具")

# 设置窗口大小和位置
root.geometry("300x300+50+50")

# 创建标签
label = tk.Label(root, text="选择要切换的模型:")
label.pack(pady=10)

# 显示当前生效的模型信息
current_model_label = tk.Label(root, textvariable=current_model)
current_model_label.pack(pady=10)

# 获取可用模型并创建下拉选择菜单
MODELS = get_allowed_models()
model_menu = tk.OptionMenu(root, current_model, *MODELS, command=switch_model)
model_menu.pack(pady=10)

# 运行主循环
root.mainloop()