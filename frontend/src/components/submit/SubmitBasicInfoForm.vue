<template>
  <section class="layout-section-card ui-surface-white">
    <div class="layout-section-head">
      <h2>智能体信息</h2>
      <p>基础信息和提交通道字段都会在正式提交前经过本地校验和 mock 预检查。</p>
    </div>

    <div class="field-grid">
      <label class="field full">
        <span>智能体名称</span>
        <input
          v-model="form.agentName"
          type="text"
          class="ui-input-pill ui-input-focus-ring"
          placeholder="例如：安全卫士 v1.0"
        />
      </label>

      <label class="field full">
        <span>智能体描述</span>
        <textarea
          v-model="form.description"
          class="textarea"
          rows="4"
          placeholder="简要说明智能体定位、核心能力和适用场景。"
        />
      </label>

      <template v-if="form.submitMethod === 'api'">
        <label class="field full">
          <span>API 地址</span>
          <input
            v-model="form.api.baseUrl"
            type="url"
            class="ui-input-pill ui-input-focus-ring"
            placeholder="https://example.com/agent/run"
          />
        </label>
        <label class="field full">
          <span>API Token</span>
          <input
            v-model="form.api.token"
            type="password"
            class="ui-input-pill ui-input-focus-ring"
            placeholder="仅保存在当前页面内存，不会持久化"
          />
        </label>
      </template>

      <template v-else>
        <label class="field full">
          <span>镜像地址</span>
          <input
            v-model="form.docker.imageUri"
            type="text"
            class="ui-input-pill ui-input-focus-ring"
            placeholder="registry.example.com/agent:latest"
          />
        </label>
        <label class="field">
          <span>镜像仓库用户名</span>
          <input
            v-model="form.docker.username"
            type="text"
            class="ui-input-pill ui-input-focus-ring"
            placeholder="可选"
          />
        </label>
        <label class="field">
          <span>镜像仓库密码</span>
          <input
            v-model="form.docker.password"
            type="password"
            class="ui-input-pill ui-input-focus-ring"
            placeholder="仅保存在当前页面内存"
          />
        </label>
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { SubmitFormState } from "@/types/AgentTypes";

const form = defineModel<SubmitFormState>({ required: true });
</script>

<style scoped>
.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.field.full {
  grid-column: 1 / -1;
}

.field span {
  color: #334155;
  font-weight: 600;
}

.field input,
.textarea {
  width: 100%;
  padding: 0.82rem 1rem;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  color: #0f172a;
}

.textarea {
  border-radius: 1.2rem;
  resize: vertical;
  min-height: 120px;
  font: inherit;
}

.textarea:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

@media (max-width: 768px) {
  .field-grid {
    grid-template-columns: 1fr;
  }
}
</style>
