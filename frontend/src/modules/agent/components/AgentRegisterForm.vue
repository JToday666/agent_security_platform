<template>
  <form class="agent-register-form" @submit.prevent="$emit('create')">
    <SectionBlock
      title="选择模板"
      description="模板会预填连接、映射和状态字段，可按实际接口调整。"
    >
      <div class="template-list">
        <button
          v-for="template in templates"
          :key="template.templateId"
          type="button"
          class="template-row"
          :class="{ 'template-row--active': form.templateId === template.templateId }"
          @click="$emit('apply-template', template.templateId)"
        >
          <span class="template-row__copy">
            <strong>{{ template.name }}</strong>
            <span>{{ template.description }}</span>
          </span>
          <span class="template-row__tags">
            <UiTag v-if="template.recommended" tone="success" size="sm">
              推荐
            </UiTag>
            <UiTag tone="neutral" size="sm">
              {{ template.level }}
            </UiTag>
          </span>
        </button>
      </div>
      <InlineNotice
        v-if="fieldErrors.templateId"
        tone="warning"
        :message="fieldErrors.templateId"
      />
    </SectionBlock>

    <SectionBlock
      title="基本信息"
      description="Agent 创建后核心运行配置不支持原地修改，需要调整时可复制新建。"
    >
      <div class="form-grid">
        <FormField
          label="Agent 名称"
          :model-value="form.name"
          :error="fieldErrors.name"
          required
          full
          placeholder="例如：Skyvern Agent"
          @update:model-value="form.name = $event"
        />
        <FormField
          label="Agent 描述"
          :model-value="form.description"
          type="textarea"
          :rows="4"
          full
          placeholder="简要说明用途。"
          @update:model-value="form.description = $event"
        />
        <FormField
          label="调用模式"
          :model-value="form.invokeMode"
          type="select"
          :options="invokeModeOptions"
          leading-icon="lucide:workflow"
          @update:model-value="$emit('set-invoke-mode', String($event))"
        />
      </div>
    </SectionBlock>

    <SectionBlock title="连接与鉴权">
      <div class="form-grid form-grid--three">
        <FormField
          label="服务根地址"
          :model-value="form.connection.baseUrl"
          type="url"
          :error="fieldErrors.baseUrl"
          required
          leading-icon="lucide:link"
          placeholder="https://api.agent.example.com"
          @update:model-value="form.connection.baseUrl = $event"
        />
        <FormField
          label="提交任务路径"
          :model-value="form.connection.invokePath"
          :error="fieldErrors.invokePath"
          required
          placeholder="/v1/run/tasks"
          @update:model-value="form.connection.invokePath = $event"
        />
        <FormField
          label="结果路径模板"
          :model-value="form.connection.resultPathTemplate || ''"
          :error="fieldErrors.resultPathTemplate"
          placeholder="/v1/run/tasks/{externalRunId}"
          @update:model-value="form.connection.resultPathTemplate = $event"
        />
        <FormField
          label="请求超时（秒）"
          :model-value="String(form.connection.requestTimeoutSeconds)"
          type="number"
          @update:model-value="form.connection.requestTimeoutSeconds = Number($event)"
        />
        <FormField
          label="轮询间隔（秒）"
          :model-value="String(form.connection.pollIntervalSeconds)"
          type="number"
          @update:model-value="form.connection.pollIntervalSeconds = Number($event)"
        />
        <FormField
          label="轮询总超时（秒）"
          :model-value="String(form.connection.pollTimeoutSeconds)"
          type="number"
          @update:model-value="form.connection.pollTimeoutSeconds = Number($event)"
        />
        <FormField
          label="鉴权方式"
          :model-value="form.auth.type"
          type="select"
          :options="authOptions"
          leading-icon="lucide:key-round"
          @update:model-value="$emit('set-auth-type', String($event))"
        />
        <FormField
          v-if="form.auth.type === 'bearer'"
          label="Bearer Token"
          :model-value="form.auth.token"
          type="password"
          :error="fieldErrors.authSecret"
          placeholder="创建时写入，详情页不展示明文"
          @update:model-value="form.auth.token = $event"
        />
        <template
          v-if="form.auth.type === 'api_key_header' || form.auth.type === 'custom_header'"
        >
          <FormField
            label="Header 名称"
            :model-value="form.auth.headerName"
            :error="fieldErrors.authSecret"
            placeholder="x-api-key"
            @update:model-value="form.auth.headerName = $event"
          />
          <FormField
            label="Header 密钥"
            :model-value="form.auth.secret"
            type="password"
            :error="fieldErrors.authSecret"
            placeholder="创建时写入，详情页不展示明文"
            @update:model-value="form.auth.secret = $event"
          />
        </template>
      </div>
    </SectionBlock>

    <SectionBlock
      title="输入字段映射"
      description="这里填写你的 Agent 请求体字段名，字段值由平台在评测时写入。"
    >
      <div class="mapping-grid">
        <FormField
          v-for="item in inputMappingItems"
          :key="item.key"
          :label="item.label"
          :model-value="form.platformInputMapping[item.key] || ''"
          :error="item.key === 'task' ? fieldErrors.taskMapping : ''"
          :required="item.key === 'task'"
          @update:model-value="form.platformInputMapping[item.key] = $event"
        />
      </div>
    </SectionBlock>

    <SectionBlock
      title="自定义固定字段"
      description="这些字段会原样合并到每次请求体中。"
    >
      <div class="custom-field-list">
        <div
          v-for="field in form.customRequestFields"
          :key="field.id"
          class="custom-field-row"
        >
          <FormField
            label="字段名"
            :model-value="field.key"
            @update:model-value="field.key = $event"
          />
          <FormField
            label="类型"
            :model-value="field.valueType"
            type="select"
            :options="customTypeOptions"
            @update:model-value="$emit('set-custom-field-type', field.id, String($event))"
          />
          <FormField
            label="字段值"
            :model-value="field.value"
            @update:model-value="field.value = $event"
          />
          <UiButton
            variant="ghost"
            size="sm"
            leading-icon="lucide:trash-2"
            @click="$emit('remove-custom-field', field.id)"
          >
            删除
          </UiButton>
        </div>
      </div>
      <InlineNotice
        v-if="fieldErrors.customRequestBody"
        tone="warning"
        :message="fieldErrors.customRequestBody"
      />
      <template #actions>
        <UiButton
          variant="secondary"
          size="sm"
          leading-icon="lucide:plus"
          @click="$emit('add-custom-field')"
        >
          添加字段
        </UiButton>
      </template>
    </SectionBlock>

    <SectionBlock
      title="输出字段映射"
      description="这里填写 Agent 响应 JSON 路径，平台会从对应路径读取结果。"
    >
      <div class="mapping-grid">
        <FormField
          v-for="item in outputMappingItems"
          :key="item.key"
          :label="item.label"
          :model-value="form.platformOutputMapping[item.key] || ''"
          :error="fieldErrors.outputMapping"
          @update:model-value="form.platformOutputMapping[item.key] = $event"
        />
      </div>
    </SectionBlock>

    <SectionBlock title="状态集合">
      <div class="form-grid">
        <FormField
          label="终态"
          :model-value="form.terminalStatusesText"
          :error="fieldErrors.terminalStatuses"
          placeholder="completed, failed, timed_out"
          @update:model-value="form.terminalStatusesText = $event"
        />
        <FormField
          label="成功态"
          :model-value="form.successStatusesText"
          :error="fieldErrors.successStatuses"
          placeholder="completed"
          @update:model-value="form.successStatusesText = $event"
        />
        <label class="structured-output">
          <input
            v-model="form.requestOptions.structuredOutput.supported"
            type="checkbox"
          />
          <span>支持结构化输出</span>
        </label>
        <FormField
          label="结构化输出字段别名"
          :model-value="form.requestOptions.structuredOutput.fieldAlias"
          placeholder="outputSchema"
          @update:model-value="form.requestOptions.structuredOutput.fieldAlias = $event"
        />
      </div>
    </SectionBlock>

    <InlineNotice
      v-if="submitError"
      tone="danger"
      :message="submitError"
    />

    <AgentCreateResultPanel
      :created-agent="createdAgent"
      :verifying="verifyingCreatedAgent"
      @verify="$emit('verify-created')"
    />

    <div class="submit-row">
      <UiButton
        variant="primary"
        type="submit"
        leading-icon="lucide:save"
        :loading="submitting"
        :disabled="Boolean(createdAgent)"
      >
        创建 Agent
      </UiButton>
    </div>
  </form>
</template>

<script setup lang="ts">
import AgentCreateResultPanel from "@/modules/agent/components/AgentCreateResultPanel.vue";
import {
  authOptions,
  customTypeOptions,
  inputMappingItems,
  invokeModeOptions,
  outputMappingItems,
} from "@/modules/agent/composables/useAgentRegisterPage";
import type {
  AgentRegisterFieldErrors,
  AgentRegisterForm,
} from "@/modules/agent/model/agent-registration";
import type {
  AgentCreateResponse,
  AgentTemplate,
} from "@/shared/types/agent-registry-types";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import UiTag from "@/shared/ui/display/UiTag.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import FormField from "@/shared/ui/forms/FormField.vue";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";

defineProps<{
  templates: AgentTemplate[];
  form: AgentRegisterForm;
  fieldErrors: AgentRegisterFieldErrors;
  submitError: string;
  submitting: boolean;
  createdAgent: AgentCreateResponse | null;
  verifyingCreatedAgent: boolean;
}>();

defineEmits<{
  (event: "apply-template", templateId: string): void;
  (event: "set-invoke-mode", value: string): void;
  (event: "set-auth-type", value: string): void;
  (event: "set-custom-field-type", fieldId: string, value: string): void;
  (event: "add-custom-field"): void;
  (event: "remove-custom-field", fieldId: string): void;
  (event: "create"): void;
  (event: "verify-created"): void;
}>();
</script>

<style scoped lang="scss">
.agent-register-form {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

.template-list,
.custom-field-list {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.template-row {
  position: relative;
  width: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.92rem 0.85rem;
  border: 0;
  border-top: 1px solid var(--color-border-soft);
  border-radius: var(--radius-card-sm);
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition:
    background var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.template-row:first-child {
  border-top: 0;
}

.template-row:hover,
.template-row:focus-visible {
  outline: none;
  background:
    radial-gradient(circle at 10% 0%, rgba(59, 130, 246, 0.1), transparent 34%),
    rgba(255, 255, 255, 0.54);
  box-shadow: var(--shadow-surface-soft);
  transform: translateY(-1px);
}

.template-row:focus-visible {
  box-shadow: var(--shadow-focus-primary);
}

.template-row--active {
  background: var(--grad-primary-soft);
  box-shadow: var(--shadow-surface-soft);
}

.template-row--active .template-row__copy strong {
  color: var(--color-primary);
}

.template-row__copy,
.template-row__tags {
  display: flex;
  min-width: 0;
}

.template-row__copy {
  flex: 1;
  flex-direction: column;
  gap: 0.36rem;
}

.template-row__copy strong {
  color: var(--color-text-dark);
}

.template-row__copy span {
  color: var(--color-text-muted);
  line-height: 1.58;
}

.template-row__tags {
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.45rem;
}

.form-grid,
.mapping-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem 1.1rem;
}

.form-grid--three {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.custom-field-row {
  display: grid;
  grid-template-columns: minmax(140px, 1fr) minmax(120px, 0.6fr) minmax(160px, 1fr) auto;
  gap: 0.75rem;
  align-items: end;
  padding: 0.85rem 0.75rem 0;
  border-top: 1px solid var(--color-border-soft);
  border-radius: var(--radius-card-sm);
  transition:
    background var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard);
}

.custom-field-row:first-child {
  border-top: 0;
  padding-top: 0;
}

.custom-field-row:hover,
.custom-field-row:focus-within {
  background: rgba(255, 255, 255, 0.5);
  box-shadow: var(--shadow-surface-soft);
}

.structured-output {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  min-height: 3rem;
  color: var(--color-text-main);
  font-weight: 600;
  cursor: pointer;
}

.structured-output input {
  width: 1rem;
  height: 1rem;
  accent-color: var(--color-primary);
}

.submit-row {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 1180px) {
  .form-grid--three {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .form-grid,
  .mapping-grid,
  .custom-field-row {
    grid-template-columns: 1fr;
  }

  .template-row,
  .template-row__tags {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
