document.getElementById('switchButton').onclick = async function() {
    const selectedModel = document.getElementById('modelSelect').value;
    const messageElement = document.getElementById('message');
    const button = document.getElementById('switchButton');

    // 禁用按钮并显示加载状态
    button.disabled = true;
    button.textContent = '切换中...';

    try {
        const response = await fetch('/switch/override_models', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ model: selectedModel })
        });

        const data = await response.json();
        console.log(data);

        // 显示消息
        messageElement.style.display = 'block';
        messageElement.textContent = data['message'];
        messageElement.style.backgroundColor = '#e7f3fe';
        messageElement.style.borderLeft = '6px solid #2196F3';
    } catch (error) {
        console.error('Error:', error);
        messageElement.style.display = 'block';
        messageElement.textContent = '发生错误，请稍后重试。';
        messageElement.style.backgroundColor = '#ffebee';
        messageElement.style.borderLeft = '6px solid #f44336';
    } finally {
        // 恢复按钮状态
        button.disabled = false;
        button.textContent = '切换模型';
    }
};
