document.addEventListener('DOMContentLoaded', function() {
    const switchButton = document.getElementById('switchButton');
    const modelSelect = document.getElementById('modelSelect');
    const messageElement = document.getElementById('message');
    const loader = document.getElementById('loader');

    switchButton.onclick = async function() {
        const selectedModel = modelSelect.value;

        // 禁用按钮并显示加载状态
        switchButton.disabled = true;
        switchButton.textContent = '切换中...';
        loader.style.display = 'block';
        messageElement.style.display = 'none';

        try {
            const response = await fetch('/switch/override_models', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ model: selectedModel })
            });

            if (!response.ok) {
                throw new Error('网络响应不正常');
            }

            const data = await response.json();
            console.log(data);

            // 显示成功消息
            showMessage(data['message'], 'success');
            // 保存选择的模型到 localStorage
            localStorage.setItem('selectedModel', selectedModel);
        } catch (error) {
            console.error('Error:', error);
            showMessage('发生错误，请稍后重试。', 'error');
        } finally {
            // 恢复按钮状态
            switchButton.disabled = false;
            switchButton.textContent = '切换模型';
            loader.style.display = 'none';
        }
    };

    // 从 localStorage 加载上次选择的模型
    const savedModel = localStorage.getItem('selectedModel');
    if (savedModel) {
        modelSelect.value = savedModel;
    }

    function showMessage(text, type) {
        messageElement.textContent = text;
        messageElement.style.display = 'block';
        
        if (type === 'success') {
            messageElement.style.backgroundColor = '#e8f5e9';
            messageElement.style.borderLeft = '6px solid #4caf50';
        } else if (type === 'error') {
            messageElement.style.backgroundColor = '#ffebee';
            messageElement.style.borderLeft = '6px solid #f44336';
        }
    }
});
