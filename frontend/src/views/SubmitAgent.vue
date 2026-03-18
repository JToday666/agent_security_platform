<template>
  <div class="form-card ui-surface-glass">
    <h1 class="page-title">提交智能体</h1>
    <p class="page-subtitle">请填写以下信息以提交您的智能体参加评估。</p>

    <form @submit.prevent="handleSubmit" class="submit-form">
      <!-- 智能体名称 -->
      <div class="form-group">
        <label for="agentName">智能体名称<span class="required">*</span></label>
        <input
          type="text"
          id="agentName"
          class="ui-input-pill ui-input-focus-ring"
          v-model="form.agentName"
          placeholder="例如：安全卫士 v1.0"
          required
        />
      </div>

      <!-- API 地址 -->
      <div class="form-group">
        <label for="apiUrl">API 地址 <span class="required">*</span></label>
        <input
          type="url"
          id="apiUrl"
          class="ui-input-pill ui-input-focus-ring"
          v-model="form.apiUrl"
          placeholder="https://your-agent.com/api"
          required
        />
        <p class="hint">智能体对外提供的 HTTP 端点，用于评估测试。</p>
      </div>

      <!-- 描述（文本区域） -->
      <div class="form-group">
        <label for="description">描述（可选）</label>
        <textarea
          id="description"
          class="ui-input-focus-ring"
          v-model="form.description"
          rows="4"
          placeholder="简要描述您的智能体特点、技术栈等"
        ></textarea>
      </div>

      <!-- 数据集选择 -->
      <div class="form-group">
        <label>选择评估数据集<span class="required">*</span></label>
        <div class="dataset-selector ui-surface-white">
          <div class="selector-header">
            <span class="selected-count">已选 {{ selectedCount }} 个</span>
            <div class="selector-actions">
              <button type="button" class="action-link" @click="selectAll">
                全选
              </button>
              <button type="button" class="action-link" @click="clearAll">
                清空
              </button>
            </div>
          </div>
          <div class="dataset-list">
            <label
              v-for="ds in datasetOptions"
              :key="ds.id"
              class="dataset-item"
            >
              <input
                type="checkbox"
                :value="ds.id"
                v-model="form.selectedDatasets"
              />
              <span class="dataset-name">{{ ds.name }}</span>
              <span class="dataset-desc">{{ ds.description }}</span>
            </label>
          </div>
        </div>
      </div>

      <!-- Docker 镜像上传 -->
      <div class="form-group">
        <label for="dockerImage"
          >Docker 镜像 <span class="required">*</span></label
        >
        <div class="upload-area">
          <input
            type="file"
            id="dockerImage"
            ref="fileInput"
            accept=".tar,.tar.gz,.tgz"
            @change="handleFileChange"
            class="file-input"
          />
          <div class="upload-placeholder" v-if="!form.dockerFile">
            <span class="upload-icon">📦</span>
            <p>点击或拖拽上传 Docker 镜像文件（支持 .tar, .tar.gz）</p>
            <button
              type="button"
              class="browse-btn ui-btn ui-btn-pill ui-btn-hover-lift"
              @click="triggerFileInput"
            >
              选择文件
            </button>
          </div>
          <div class="file-info ui-surface-white" v-else>
            <span class="file-name">{{ form.dockerFile.name }}</span>
            <span class="file-size">{{
              formatFileSize(form.dockerFile.size)
            }}</span>
            <button type="button" class="remove-file" @click="removeFile">
              ×
            </button>
          </div>
        </div>
      </div>

      <!-- 提交按钮和提示 -->
      <div class="form-actions">
        <button
          type="submit"
          class="submit-btn ui-btn ui-btn-pill ui-btn-gradient ui-btn-hover-lift"
          :disabled="submitting || !isFormValid"
        >
          {{ submitting ? "提交中.." : "提交智能体" }}
        </button>
        <p v-if="submitError" class="error-message">{{ submitError }}</p>
        <p v-if="submitSuccess" class="success-message">
          提交成功，即将跳转至评估记录。
        </p>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from "vue";
import { useRouter } from "vue-router";

// 模拟数据集选项（与数据集页面一致）
const datasetOptions = [
  {
    id: 1,
    name: "Prompt Injection Dataset",
    description: "提示注入攻击测试集",
  },
  { id: 2, name: "Jailbreak Dataset", description: "越狱攻击测试集" },
  { id: 3, name: "Data Poisoning Dataset", description: "数据投毒测试集" },
  { id: 4, name: "Privacy Leakage Dataset", description: "隐私泄露测试集" },
];

// 表单数据
const form = reactive({
  agentName: "",
  apiUrl: "",
  description: "",
  selectedDatasets: [] as number[],
  dockerFile: null as File | null,
});

const fileInput = ref<HTMLInputElement | null>(null);
const submitting = ref(false);
const submitError = ref("");
const submitSuccess = ref(false);
const router = useRouter();

// 已选数据集数量
const selectedCount = computed(() => form.selectedDatasets.length);

// 表单数据有效性验证
const isFormValid = computed(() => {
  return (
    form.agentName.trim() !== "" &&
    form.apiUrl.trim() !== "" &&
    isValidUrl(form.apiUrl) &&
    form.selectedDatasets.length > 0 &&
    form.dockerFile !== null
  );
});

// 简单的 URL 验证
function isValidUrl(url: string) {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

// 全选
const selectAll = () => {
  form.selectedDatasets = datasetOptions.map((ds) => ds.id);
};

// 清空
const clearAll = () => {
  form.selectedDatasets = [];
};

// 触发文件选择
const triggerFileInput = () => {
  fileInput.value?.click();
};

// 处理文件选择
const handleFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (file) {
    // 可添加文件类型大小验证
    form.dockerFile = file;
  }
};

// 移除已选文件
const removeFile = () => {
  form.dockerFile = null;
  if (fileInput.value) {
    fileInput.value.value = ""; // 娓呯┖ input
  }
};

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
};

// 提交表单
const handleSubmit = async () => {
  if (!isFormValid.value) return;

  submitting.value = true;
  submitError.value = "";
  submitSuccess.value = false;

  // 模拟 API 提交
  try {
    await new Promise((resolve) => setTimeout(resolve, 2000));
    // 假设提交成功
    submitSuccess.value = true;
    // 2 秒后跳转至评估记录页面
    setTimeout(() => {
      router.push("/user");
    }, 2000);
  } catch (err) {
    submitError.value = "提交失败，请稍后重试。";
    console.log(err);
  } finally {
    submitting.value = false;
  }
};
</script>

<style scoped>
/* 全局重置动画 */
.form-card {
  border-radius: 2rem;
  padding: 2.5rem;
  max-width: 800px;
  margin: 0 auto;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.page-subtitle {
  font-size: 1.1rem;
  margin-bottom: 2rem;
}

.submit-form {
  display: flex;
  flex-direction: column;
  gap: 1.8rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #334155;
}

.required {
  color: #ef4444;
  margin-left: 2px;
}

.hint {
  font-size: 0.85rem;
  color: #64748b;
  margin-top: 0.3rem;
}

/* 输入框样式 */
.form-group input[type="text"],
.form-group input[type="url"],
.form-group textarea {
  width: 100%;
  padding: 0.8rem 1.2rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 30px;
  color: #1e293b;
  font-size: 1rem;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
  font-family: inherit;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}

.form-group textarea {
  border-radius: 20px;
  resize: vertical;
}

.form-group input::placeholder,
.form-group textarea::placeholder {
  color: #94a3b8;
}

/* 数据集选择器 */
.dataset-selector {
  background: white;
  border-radius: 1.2rem;
  padding: 1.2rem;
  border: 1px solid #e2e8f0;
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.selected-count {
  font-size: 0.95rem;
  color: #64748b;
}

.selector-actions {
  display: flex;
  gap: 1rem;
}

.action-link {
  background: none;
  border: none;
  color: #2563eb;
  cursor: pointer;
  font-size: 0.9rem;
  transition: color 0.2s;
}

.action-link:hover {
  color: #1d4ed8;
  text-decoration: underline;
}

.dataset-list {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  max-height: 250px;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.dataset-item {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 0.5rem 0.8rem;
  background: #f8fafc;
  border-radius: 30px;
  transition: background 0.2s;
  cursor: pointer;
  border: 1px solid transparent;
}

.dataset-item:hover {
  background: #eef2f6;
  border-color: #cbd5e1;
}

.dataset-item input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: #2563eb;
  margin-left: 0.3rem;
}

.dataset-name {
  font-weight: 500;
  color: #0f172a;
  min-width: 180px;
}

.dataset-desc {
  font-size: 0.9rem;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 文件上传区域 */
.upload-area {
  margin-top: 0.3rem;
}

.file-input {
  display: none;
}

.upload-placeholder {
  background: #f8fafc;
  border: 2px dashed #cbd5e1;
  border-radius: 30px;
  padding: 2rem;
  text-align: center;
  transition:
    border-color 0.2s,
    background 0.2s;
  cursor: pointer;
}

.upload-placeholder:hover {
  border-color: #2563eb;
  background: #eef2f6;
}

.upload-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 0.5rem;
  color: #64748b;
}

.upload-placeholder p {
  margin-bottom: 1rem;
  color: #475569;
}

.browse-btn {
  background: white;
  color: #2563eb;
  border: 1px solid #2563eb30;
  padding: 0.5rem 1.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.02);
}

.browse-btn:hover {
  background: #2563eb0c;
  border-color: #2563eb;
  transform: translateY(-2px);
  box-shadow: 0 10px 20px -8px #2563eb;
}

.file-info {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 30px;
  padding: 0.8rem 1.2rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.file-name {
  font-weight: 500;
  color: #0f172a;
  word-break: break-word;
  flex: 1;
}

.file-size {
  font-size: 0.9rem;
  color: #64748b;
}

.remove-file {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 1.2rem;
  cursor: pointer;
  transition: color 0.2s;
}

.remove-file:hover {
  color: #ef4444;
}

/* 表单操作区 */
.form-actions {
  margin-top: 1rem;
  text-align: center;
}

.submit-btn {
  padding: 0.9rem 2.5rem;
  border: none;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  width: 100%;
  max-width: 300px;
  margin: 0 auto;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 15px 25px -8px #2563eb;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.error-message {
  color: #ef4444;
  margin-top: 1rem;
  font-size: 0.95rem;
}

.success-message {
  color: #10b981;
  margin-top: 1rem;
  font-size: 0.95rem;
}

/* 响应式 */
@media (max-width: 768px) {
  .form-card {
    padding: 1.5rem;
  }

  .dataset-item {
    flex-wrap: wrap;
  }

  .dataset-name {
    min-width: auto;
  }

  .dataset-desc {
    width: 100%;
    margin-left: 2.5rem;
    white-space: normal;
  }
}
</style>
