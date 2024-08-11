document.addEventListener("DOMContentLoaded", function () {
  const currentChannel = document.getElementById("currentChannel").value;
  const currentModel = document.getElementById("currentModel").value;
  const uploadConfigButton = document.getElementById("uploadConfigButton");
  const bulkUploadButton = document.getElementById("bulkUploadButton");
  const switchChannelButton = document.getElementById("switchChannelButton");
  const deleteChannelButton = document.getElementById("deleteChannelButton");
  const switchButton = document.getElementById("switchButton");
  const messageElement = document.getElementById("message");
  const loader = document.getElementById("loader");
  const modelSelect = document.getElementById("modelSelect");
  const channelSelect = document.getElementById("channelSelect");
  const toggleBtns = document.querySelectorAll(".toggle-btn");

  const clearConfigButton = document.getElementById("clearConfigButton");
  const clearBulkUploadButton = document.getElementById(
    "clearBulkUploadButton"
  );

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

  uploadConfigButton.addEventListener("click", uploadConfig);
  bulkUploadButton.addEventListener("click", bulkUploadConfig);
  switchChannelButton.addEventListener("click", switchChannel);
  deleteChannelButton.addEventListener("click", deleteChannel);
  switchButton.addEventListener("click", switchModel);
  clearConfigButton.addEventListener("click", clearConfig);
  clearBulkUploadButton.addEventListener("click", clearBulkUpload);

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

    if (!confirm(`确定要删除渠道 "${selectedChannel}" 吗？`)) {
      return;
    }

    try {
      const response = await fetch(`/delete_channel/${selectedChannel}`, {
        method: "DELETE",
      });

      if (response.ok) {
        showMessage(`已删除渠道: ${selectedChannel}`, "success");
        fetchChannels(); // 刷新渠道列表
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
        body: JSON.stringify({ channel: selectedChannel }),
      });

      if (response.ok) {
        showMessage(`已切换到渠道: ${selectedChannel}`, "success");
        fetchModels(); // 刷新模型列表
      } else {
        showMessage("切换渠道失败", "error");
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

  function showMessage(text, type) {
    messageElement.textContent = text;
    messageElement.style.display = "block";
    messageElement.style.backgroundColor =
      type === "error" ? "#ffcccc" : "#ccffcc";
    messageElement.style.color = type === "error" ? "#ff0000" : "#006600";
  }

  function showLoader() {
    loader.style.display = "block";
  }

  function hideLoader() {
    loader.style.display = "none";
  }

  toggleBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      const configForm = this.closest('.config-form');
      configForm.classList.toggle('expanded');
    });
  });
});
