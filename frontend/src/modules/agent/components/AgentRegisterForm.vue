<template>
  <div class="agent-register-form">
    <section class="agent-register-step" aria-live="polite">
      <header class="agent-register-step__head">
        <span class="agent-register-step__eyebrow">
          步骤 {{ currentStepIndex + 1 }} / {{ steps.length }}
        </span>
        <h2>{{ currentStepTitle }}</h2>
        <p>{{ currentStepDescription }}</p>
      </header>

      <div v-if="currentStepId === 'template'" class="agent-register-step__body">
        <div class="template-grid">
          <button
            type="button"
            class="template-tile"
            :class="{ 'template-tile--active': form.templateId === AGENT_NO_TEMPLATE_ID }"
            @click="$emit('apply-template', AGENT_NO_TEMPLATE_ID)"
          >
            <span class="template-tile__copy">
              <strong>不使用模板</strong>
              <span>从空配置开始，手动填写连接、映射和状态字段。</span>
            </span>
            <span class="template-tile__tags">
              <UiTag tone="neutral" size="sm">custom</UiTag>
            </span>
          </button>

          <button
            v-for="template in sortedTemplates"
            :key="template.templateId"
            type="button"
            class="template-tile"
            :class="{ 'template-tile--active': form.templateId === template.templateId }"
            @click="$emit('apply-template', template.templateId)"
          >
            <span class="template-tile__copy">
              <strong>{{ template.name }}</strong>
              <span>{{ template.description }}</span>
            </span>
            <span class="template-tile__tags">
              <UiTag v-if="template.recommended" tone="success" size="sm">
                推荐
              </UiTag>
              <UiTag tone="neutral" size="sm">{{ template.level }}</UiTag>
              <UiTag
                v-for="tag in template.tags.filter((item) => item !== '推荐')"
                :key="tag"
                tone="neutral"
                size="sm"
              >
                {{ tag }}
              </UiTag>
            </span>
          </button>
        </div>
        <InlineNotice
          v-if="fieldErrors.templateId"
          tone="warning"
          :message="fieldErrors.templateId"
        />
      </div>

      <div v-else-if="currentStepId === 'basic'" class="agent-register-step__body">
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
            :rows="5"
            full
            placeholder="简要说明用途。"
            @update:model-value="form.description = $event"
          />
        </div>
      </div>

      <div
        v-else-if="currentStepId === 'connection'"
        class="agent-register-step__body"
      >
        <div class="form-grid form-grid--three">
          <FormField
            label="调用模式"
            :model-value="form.invokeMode"
            type="select"
            :options="invokeModeOptions"
            leading-icon="lucide:workflow"
            @update:model-value="$emit('set-invoke-mode', String($event))"
          />
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
            v-if="form.invokeMode === 'submit_poll'"
            label="结果路径模板"
            :model-value="form.connection.resultPathTemplate || ''"
            :error="fieldErrors.resultPathTemplate"
            required
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
            v-if="form.invokeMode === 'submit_poll'"
            label="轮询间隔（秒）"
            :model-value="String(form.connection.pollIntervalSeconds)"
            type="number"
            @update:model-value="form.connection.pollIntervalSeconds = Number($event)"
          />
          <FormField
            v-if="form.invokeMode === 'submit_poll'"
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
      </div>

      <div
        v-else-if="currentStepId === 'inputMapping'"
        class="agent-register-step__body"
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
      </div>

      <div
        v-else-if="currentStepId === 'outputMapping'"
        class="agent-register-step__body"
      >
        <div class="mapping-grid">
          <FormField
            v-for="item in visibleOutputMappingItems"
            :key="item.key"
            :label="item.label"
            :model-value="form.platformOutputMapping[item.key] || ''"
            :error="fieldErrors.outputMapping"
            :required="
              form.invokeMode === 'submit_poll' &&
              (item.key === 'externalRunId' || item.key === 'status')
            "
            @update:model-value="form.platformOutputMapping[item.key] = $event"
          />
        </div>
      </div>

      <div
        v-else-if="currentStepId === 'customFields'"
        class="agent-register-step__body"
      >
        <div v-if="usesNoTemplate" class="custom-choice-grid">
          <button
            type="button"
            class="custom-choice"
            :class="{ 'custom-choice--active': customFieldsChoice === 'use' }"
            @click="$emit('set-custom-fields-choice', 'use')"
          >
            <strong>添加固定字段</strong>
            <span>为每次请求附加固定参数。</span>
          </button>
          <button
            type="button"
            class="custom-choice"
            :class="{ 'custom-choice--active': customFieldsChoice === 'skip' }"
            @click="$emit('set-custom-fields-choice', 'skip')"
          >
            <strong>不添加固定字段</strong>
            <span>请求体仅包含平台字段映射。</span>
          </button>
        </div>

        <template v-if="!usesNoTemplate || customFieldsChoice === 'use'">
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
          <UiButton
            variant="secondary"
            size="sm"
            leading-icon="lucide:plus"
            @click="$emit('add-custom-field')"
          >
            添加字段
          </UiButton>
        </template>

        <InlineNotice
          v-if="usesNoTemplate && customFieldsChoice === 'skip'"
          tone="info"
          message="本次注册不会添加自定义固定字段。"
        />
        <InlineNotice
          v-if="fieldErrors.customRequestBody"
          tone="warning"
          :message="fieldErrors.customRequestBody"
        />
      </div>

      <div v-else class="agent-register-step__body">
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
          <UiToggleField
            v-model="form.requestOptions.structuredOutput.supported"
            title="支持结构化输出"
            description="注册后平台会在请求中传入结构化输出字段别名。"
          />
          <FormField
            v-if="form.requestOptions.structuredOutput.supported"
            label="结构化输出字段别名"
            :model-value="form.requestOptions.structuredOutput.fieldAlias"
            placeholder="outputSchema"
            @update:model-value="form.requestOptions.structuredOutput.fieldAlias = $event"
          />
        </div>

        <AgentCreateResultPanel
          :created-agent="createdAgent"
          :verifying="verifyingCreatedAgent"
          @verify="$emit('verify-created')"
        />
      </div>

      <InlineNotice
        v-if="submitError"
        tone="danger"
        :message="submitError"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import AgentCreateResultPanel from "@/modules/agent/components/AgentCreateResultPanel.vue";
import {
  authOptions,
  customTypeOptions,
  inputMappingItems,
  invokeModeOptions,
  outputMappingItems,
  type AgentRegisterCustomFieldsChoice,
} from "@/modules/agent/composables/useAgentRegisterPage";
import type {
  AgentRegisterFieldErrors,
  AgentRegisterForm,
  AgentRegisterStep,
  AgentRegisterStepId,
} from "@/modules/agent/model/agent-registration";
import { AGENT_NO_TEMPLATE_ID } from "@/modules/agent/model/agent-registration";
import type {
  AgentCreateResponse,
  AgentTemplate,
} from "@/shared/types/agent-registry-types";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import UiTag from "@/shared/ui/display/UiTag.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import FormField from "@/shared/ui/forms/FormField.vue";
import UiToggleField from "@/shared/ui/forms/UiToggleField.vue";

const props = defineProps<{
  templates: AgentTemplate[];
  form: AgentRegisterForm;
  fieldErrors: AgentRegisterFieldErrors;
  submitError: string;
  createdAgent: AgentCreateResponse | null;
  verifyingCreatedAgent: boolean;
  currentStepId: AgentRegisterStepId;
  steps: AgentRegisterStep[];
  customFieldsChoice: AgentRegisterCustomFieldsChoice;
  usesNoTemplate: boolean;
}>();

defineEmits<{
  (event: "apply-template", templateId: string): void;
  (event: "set-invoke-mode", value: string): void;
  (event: "set-auth-type", value: string): void;
  (event: "set-custom-field-type", fieldId: string, value: string): void;
  (event: "set-custom-fields-choice", value: AgentRegisterCustomFieldsChoice): void;
  (event: "add-custom-field"): void;
  (event: "remove-custom-field", fieldId: string): void;
  (event: "verify-created"): void;
}>();

const sortedTemplates = computed(() =>
  [...props.templates].sort(
    (left, right) =>
      Number(right.recommended) - Number(left.recommended) ||
      left.sortOrder - right.sortOrder,
  ),
);

const currentStepIndex = computed(() =>
  Math.max(
    props.steps.findIndex((step) => step.id === props.currentStepId),
    0,
  ),
);
const currentStepTitle = computed(
  () => props.steps[currentStepIndex.value]?.title ?? "",
);
const currentStepDescription = computed(
  () => props.steps[currentStepIndex.value]?.description ?? "",
);
const visibleOutputMappingItems = computed(() => {
  if (props.form.invokeMode === "submit_poll") {
    return outputMappingItems;
  }

  return outputMappingItems.filter(
    (item) => item.key !== "externalRunId" && item.key !== "status",
  );
});

</script>

<style scoped lang="scss">
.agent-register-step {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  min-width: 0;
  padding-top: 0.25rem;
}

.agent-register-step__head {
  display: flex;
  max-width: 780px;
  flex-direction: column;
  gap: 0.45rem;
}

.agent-register-step__eyebrow {
  color: var(--color-primary);
  font-size: 0.78rem;
  font-weight: 800;
}

.agent-register-step__head h2 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: clamp(1.35rem, 2vw, 1.85rem);
  line-height: 1.2;
}

.agent-register-step__head p {
  margin: 0;
  color: var(--color-text-subtle);
  line-height: 1.65;
}

.agent-register-step__body,
.custom-field-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 0;
}

.template-grid,
.custom-choice-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 0.9rem;
}

.template-tile,
.custom-choice {
  display: flex;
  min-height: 9.5rem;
  flex-direction: column;
  justify-content: space-between;
  gap: 1.1rem;
  padding: 1rem;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-control-sm);
  background: rgba(255, 255, 255, 0.58);
  color: var(--color-text-main);
  text-align: left;
  cursor: pointer;
  transition:
    background var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.template-tile:hover,
.template-tile:focus-visible,
.custom-choice:hover,
.custom-choice:focus-visible {
  outline: none;
  transform: translateY(-1px);
  border-color: var(--color-border-strong);
  background: rgba(255, 255, 255, 0.78);
  box-shadow: var(--shadow-surface-soft);
}

.template-tile:focus-visible,
.custom-choice:focus-visible {
  box-shadow: var(--shadow-focus-primary);
}

.template-tile--active,
.custom-choice--active {
  border-color: rgba(37, 99, 235, 0.32);
  background: rgba(219, 234, 254, 0.52);
  box-shadow: var(--shadow-surface-soft);
}

.template-tile__copy,
.template-tile__tags {
  display: flex;
  min-width: 0;
}

.template-tile__copy {
  flex-direction: column;
  gap: 0.45rem;
}

.template-tile__copy strong,
.custom-choice strong {
  color: var(--color-text-dark);
  font-size: 1rem;
}

.template-tile__copy span,
.custom-choice span {
  color: var(--color-text-subtle);
  line-height: 1.62;
  overflow-wrap: anywhere;
}

.template-tile__tags {
  flex-wrap: wrap;
  gap: 0.42rem;
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
  padding-block: 0.85rem;
  border-top: 1px solid var(--color-border-soft);
}

.custom-field-row:first-child {
  border-top: 0;
  padding-top: 0;
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

  .template-grid,
  .custom-choice-grid {
    grid-template-columns: 1fr;
  }

}
</style>
