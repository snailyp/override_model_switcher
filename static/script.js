document.addEventListener("DOMContentLoaded", function () {
  // 注册 Service Worker
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/service-worker.js')
        .then(registration => {
          console.log('ServiceWorker registration successful with scope: ', registration.scope);
        })
        .catch(error => {
          console.log('ServiceWorker registration failed: ', error);
        });
    });
  }
  
  changeBackground();

  const currentChannel = document.getElementById("currentChannel").value;
  const currentModel = document.getElementById("currentModel").value;
  const uploadConfigButton = document.getElementById("uploadConfigButton");
  const bulkUploadButton = document.getElementById("bulkUploadButton");
  const switchChannelButton = document.getElementById("switchChannelButton");
  const deleteChannelButton = document.getElementById("deleteChannelButton");
  const switchButton = document.getElementById("switchButton");
  const modelSelect = document.getElementById("modelSelect");
  const channelSelect = document.getElementById("channelSelect");

  const clearConfigButton = document.getElementById("clearConfigButton");
  const customAlert = document.getElementById("customAlert");
  const alertMessage = document.getElementById("alertMessage");
  const closeAlert = document.getElementById("closeAlert");
  const opacityControlWrapper = document.querySelector('.opacity-control-wrapper');
  const opacityControl = document.querySelector('.opacity-control');
  const opacitySlider = document.getElementById("opacitySlider");
  const opacityValue = document.getElementById("opacityValue");
  const cards = document.querySelectorAll(".card");
  const clearBulkUploadButton = document.getElementById(
    "clearBulkUploadButton"
  );
  const exportChannelsButton = document.getElementById("exportChannelsButton");
  const exportModelsBtn = document.getElementById("exportModelsBtn");
  const testModelBtn = document.getElementById("testModelBtn");

  opacityControlWrapper.addEventListener('mouseenter', function() {
    opacityControl.style.transform = 'translateX(0)';
  });

  opacityControlWrapper.addEventListener('mouseleave', function() {
    opacityControl.style.transform = 'translateX(100%)';
  });

  function showMessage(text, type) {
    alertMessage.innerHTML = text;
    alertMessage.style.color = type === "error" ? "#ff0000" : "#006600";
    alertMessage.style.maxHeight = "300px";
    alertMessage.style.overflow = "auto";
    alertMessage.style.wordBreak = "break-word";
    alertMessage.style.textAlign = "left";
    customAlert.style.display = "block";
  }

  closeAlert.onclick = function () {
    customAlert.style.display = "none";
  };

  window.onclick = function (event) {
    if (event.target == customAlert) {
      customAlert.style.display = "none";
    }
  };

  // 初始化：获取渠道列表和模型列表
  fetchChannels().then(() => {
    if (currentChannel) {
      channelSelect.value = currentChannel;
    }
  });

  fetchModels().then(() => {
    if (currentModel) {
      modelSelect.value = currentModel;
    }
  });
  
  // 初始化当前状态显示
  updateCurrentStatus();

  uploadConfigButton.addEventListener("click", uploadConfig);
  bulkUploadButton.addEventListener("click", bulkUploadConfig);
  switchChannelButton.addEventListener("click", switchChannel);
  deleteChannelButton.addEventListener("click", deleteChannel);
  switchButton.addEventListener("click", switchModel);
  clearConfigButton.addEventListener("click", clearConfig);
  clearBulkUploadButton.addEventListener("click", clearBulkUpload);
  exportChannelsButton.addEventListener("click", exportChannels);
  document
    .getElementById("changeBackgroundBtn")
    .addEventListener("click", changeBackground);
  document
    .getElementById("scrollTopBtn")
    .addEventListener("click", scrollToTop);
  exportModelsBtn.addEventListener("click", exportModels);
  testModelBtn.addEventListener("click", testModel);

  async function testModel() {
    const selectedModel = document.getElementById("modelSelect").value;
    
    if (!selectedModel) {
      showMessage("请选择要测试的模型", "error");
      return;
    }
    
    showLoader();
    try {
      const response = await fetch("/test_model", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ model: selectedModel }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.available) {
          // 显示测试成功的消息和原始JSON
          const jsonStr = JSON.stringify(data, null, 2);
          showMessage(`<div>模型 ${selectedModel} 测试成功！✅</div><pre style="background-color:#f5f5f5;padding:10px;border-radius:5px;margin-top:10px;font-size:12px;">${jsonStr}</pre>`, "success");
        } else {
          // 显示测试失败的消息和原始JSON
          const jsonStr = JSON.stringify(data, null, 2);
          showMessage(`<div>模型 ${selectedModel} 测试失败 ❌</div><pre style="background-color:#f5f5f5;padding:10px;border-radius:5px;margin-top:10px;font-size:12px;">${jsonStr}</pre>`, "error");
        }
      } else {
        const errorData = await response.json();
        const jsonStr = JSON.stringify(errorData, null, 2);
        showMessage(`<div>测试失败 ❌</div><pre style="background-color:#f5f5f5;padding:10px;border-radius:5px;margin-top:10px;font-size:12px;">${jsonStr}</pre>`, "error");
      }
    } catch (error) {
      showMessage("测试模型时发生错误", "error");
    } finally {
      hideLoader();
    }
  }

  async function testModels() {
    const selectedChannel = document.getElementById("channelSelect").value;
    showLoader();
    try {
      const response = await fetch("/test_all_models", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ channel: selectedChannel }),
      });

      if (response.ok) {
        const data = await response.json();
        showMessage(`模型检测结果: ${JSON.stringify(data.results)}`, "success");
      } else {
        const errorData = await response.json();
        showMessage(`模型检测失败: ${errorData.message}`, "error");
      }
    } catch (error) {
      showMessage("检测模型时发生错误", "error");
    } finally {
      hideLoader();
    }
  }

  function showPrompt(message) {
    return new Promise((resolve) => {
      const customPrompt = document.getElementById("customPrompt");
      const promptMessage = document.getElementById("promptMessage");
      const promptInput = document.getElementById("promptInput");
      const promptOk = document.getElementById("promptOk");
      const promptCancel = document.getElementById("promptCancel");

      promptMessage.textContent = message;
      customPrompt.style.display = "block";

      promptOk.onclick = function () {
        customPrompt.style.display = "none";
        resolve(promptInput.value);
      };

      promptCancel.onclick = function () {
        customPrompt.style.display = "none";
        resolve(null);
      };

      window.onclick = function (event) {
        if (event.target == customPrompt) {
          customPrompt.style.display = "none";
          resolve(null);
        }
      };
    });
  }
  async function exportModels() {
    try {
      const response = await fetch("/export_models");
      if (response.ok) {
        const modelsText = await response.text();
        const blob = new Blob([modelsText], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "models_list.txt";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showMessage("模型列表已成功导出", "success");
      } else {
        showMessage("导出模型列表失败", "error");
      }
    } catch (error) {
      showMessage("导出模型列表时发生错误", "error");
    }
  }
  // 设置初始透明度为 70%
  setOpacity(0.7);
  opacitySlider.addEventListener("input", function () {
    const opacity = this.value / 100;
    setOpacity(opacity);
  });
  function setOpacity(opacity) {
    opacityValue.textContent = Math.round(opacity * 100) + "%";
    cards.forEach((card) => {
      card.style.opacity = opacity;
    });
  }
  function clearConfig() {
    document.getElementById("channelName").value = "";
    document.getElementById("baseUrl").value = "";
    document.getElementById("apiKey").value = "";
  }

  function clearBulkUpload() {
    document.getElementById("bulkChannelConfig").value = "";
  }
  async function uploadConfig() {
    const channelName = document.getElementById("channelName").value;
    const baseUrl = document.getElementById("baseUrl").value;
    const apiKey = document.getElementById("apiKey").value;

    if (!channelName || !baseUrl || !apiKey) {
      showMessage("请填写所有字段", "error");
      return;
    }

    try {
      const response = await fetch("/add_channel", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          channel_name: channelName,
          base_url: baseUrl,
          api_key: apiKey,
        }),
      });

      if (response.ok) {
        showMessage("配置上传成功", "success");
        fetchChannels(); // 刷新渠道列表
      } else {
        showMessage("配置上传失败", "error");
      }
    } catch (error) {
      showMessage("上传配置时发生错误", "error");
    }
  }

  async function bulkUploadConfig() {
    const bulkConfig = document.getElementById("bulkChannelConfig").value;
    try {
      const channels = JSON.parse(bulkConfig);
      const response = await fetch("/bulk_add_channels", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(channels),
      });
      if (response.ok) {
        showMessage("批量配置上传成功", "success");
        fetchChannels(); // 刷新渠道列表
      } else {
        showMessage("批量配置上传失败", "error");
      }
    } catch (error) {
      showMessage("批量上传配置时发生错误，请检查JSON格式是否正确", "error");
    }
  }

  async function deleteChannel() {
    const selectedChannel = channelSelect.value;

    if (!selectedChannel) {
      showMessage("请选择要删除的渠道", "error");
      return;
    }

    const confirmResult = await showConfirm(
      `确定要删除渠道 "${selectedChannel}" 吗？`
    );
    if (!confirmResult) {
      return;
    }

    try {
      const response = await fetch(`/delete_channel/${selectedChannel}`, {
        method: "DELETE",
      });

      if (response.ok) {
        showMessage(`已删除渠道: ${selectedChannel}`, "success");
        fetchChannels(); // 刷新渠道列表
        fetchModels(); //刷新模型列表
        updateCurrentStatus(); // 更新当前状态显示
      } else {
        showMessage("删除渠道失败", "error");
      }
    } catch (error) {
      showMessage("删除渠道时发生错误", "error");
    }
  }

  async function switchChannel() {
    const selectedChannel = channelSelect.value;

    try {
      const response = await fetch("/switch_channel", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ channel_name: selectedChannel }),
      });

      if (response.ok) {
        showMessage(`已切换到渠道: ${selectedChannel}`, "success");
        fetchModels(); // 刷新模型列表
        updateCurrentStatus(); // 更新当前状态显示
      } else {
        const errorData = await response.json();
        showMessage(`切换失败: ${errorData.detail}`, "error");
      }
    } catch (error) {
      showMessage("切换渠道时发生错误", "error");
    }
  }

  async function switchModel() {
    const selectedModel = modelSelect.value;

    showLoader();
    try {
      const response = await fetch("/switch/override_model", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ model: selectedModel }),
      });

      if (response.ok) {
        showMessage(`模型已切换为: ${selectedModel}`, "success");
        updateCurrentStatus(); // 更新当前状态显示
      } else {
        const errorData = await response.json();
        showMessage(`切换失败: ${errorData.detail}`, "error");
      }
    } catch (error) {
      showMessage("切换模型时发生错误", "error");
    } finally {
      hideLoader();
    }
  }
  
  async function updateCurrentStatus() {
    try {
      // 获取当前通道
      const channelResponse = await fetch("/get_current_channel");
      if (channelResponse.ok) {
        const channelData = await channelResponse.json();
        document.getElementById("currentChannelDisplay").innerHTML = 
          `当前通道: <span>${channelData.current_channel}</span>`;
      }
      
      // 获取当前模型
      const modelResponse = await fetch("/get_current_model");
      if (modelResponse.ok) {
        const modelData = await modelResponse.json();
        document.getElementById("currentModelDisplay").innerHTML = 
          `当前模型: <span>${modelData.current_model}</span>`;
      }
    } catch (error) {
      console.error("更新状态显示失败:", error);
    }
  }

  async function fetchChannels() {
    try {
      const response = await fetch("/get_channels");
      if (response.ok) {
        const channels = await response.json();
        updateChannelSelect(channels);
      } else {
        showMessage("获取渠道列表失败", "error");
      }
    } catch (error) {
      showMessage("获取渠道列表时发生错误", "error");
    }
  }

  async function exportChannels() {
    const apiKey = await showPrompt("请输入 API Key:");

    if (!apiKey) {
      showMessage("API Key 不能为空", "error");
      return;
    }
    try {
      const response = await fetch("/export_channels", {
        headers: {
          Authorization: `Bearer ${apiKey}`,
        },
      });
      if (response.ok) {
        const channels = await response.json();
        const blob = new Blob([JSON.stringify(channels, null, 2)], {
          type: "application/json",
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "channels_config.json";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showMessage("渠道配置已成功导出", "success");
      } else {
        showMessage("导出渠道配置失败", "error");
      }
    } catch (error) {
      showMessage("导出渠道配置时发生错误", "error");
    }
  }

  async function fetchModels() {
    try {
      const response = await fetch("/v1/models");
      if (response.ok) {
        const data = await response.json();
        updateModelSelect(data.data);
      } else {
        showMessage("获取模型列表失败", "error");
      }
    } catch (error) {
      showMessage("获取模型列表时发生错误", "error");
    }
  }

  function updateChannelSelect(channels) {
    channelSelect.innerHTML = "";
    channels.forEach((channel) => {
      const option = document.createElement("option");
      option.value = channel;
      option.textContent = channel;
      channelSelect.appendChild(option);
    });
  }

  function updateModelSelect(models) {
    modelSelect.innerHTML = "";
    models.forEach((model) => {
      const option = document.createElement("option");
      option.value = model.id;
      option.textContent = model.id;
      modelSelect.appendChild(option);
    });
  }

  function showLoader() {
    loader.style.display = "block";
  }

  function hideLoader() {
    loader.style.display = "none";
  }

  function showConfirm(message) {
    return new Promise((resolve) => {
      const customConfirm = document.getElementById("customConfirm");
      const confirmMessage = document.getElementById("confirmMessage");
      const confirmYes = document.getElementById("confirmYes");
      const confirmNo = document.getElementById("confirmNo");

      confirmMessage.textContent = message;
      customConfirm.style.display = "block";

      confirmYes.onclick = function () {
        customConfirm.style.display = "none";
        resolve(true);
      };

      confirmNo.onclick = function () {
        customConfirm.style.display = "none";
        resolve(false);
      };

      window.onclick = function (event) {
        if (event.target == customConfirm) {
          customConfirm.style.display = "none";
          resolve(false);
        }
      };
    });
  }

  // https://api.timelessq.com/bing/random
  // https://api.paugram.com/wallpaper/?source=gh&category=us
  // https://api.suyanw.cn/api/comic/api.php
  function changeBackground() {
    const randomParam = Date.now();
    const wallpaperUrl = `/wallpaper?v=${randomParam}`;

    const img = new Image();
    img.onload = function () {
      document.body.style.backgroundImage = `url('${wallpaperUrl}')`;
    };
    img.src = wallpaperUrl;
  }

  function scrollToTop() {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  window.addEventListener("scroll", function () {
    var scrollBtn = document.getElementById("scrollTopBtn");
    if (window.pageYOffset > 300) {
      scrollBtn.style.display = "block";
    } else {
      scrollBtn.style.display = "none";
    }
  });
});
