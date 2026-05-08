<template>
  <div class="agent-register-form">
    <section class="agent-register-step" aria-live="polite">
      <header class="agent-register-step__head">
        <span class="agent-register-step__eyebrow">
          步骤 {{ currentStepIndex + 1 }} / {{ steps.length }}
        </span>
        <h2>{{ currentStepTitle }}</h2>
        <p>{{ currentStepDescription }}</p>
        <InlineNotice
          v-if="submitError"
          tone="danger"
          :message="submitError"
        />
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
            placeholder="例如：Skyvern Agent"
            help="用于在平台内识别该智能体，建议使用服务或能力名称。"
            @update:model-value="updateBasicField('name', $event)"
          />
          <FormField
            label="Agent 描述"
            :model-value="form.description"
            type="textarea"
            :rows="5"
            placeholder="简要说明用途。"
            help="说明该智能体适合处理的任务，便于后续提交评测时选择。"
            @update:model-value="updateBasicField('description', $event)"
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
            help="提交轮询适用于异步任务；同步响应适用于一次请求直接返回结果。"
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
            help="填写 Agent 服务的协议、域名和端口，不包含具体接口路径。"
            @update:model-value="updateConnectionTextField('baseUrl', $event)"
          />
          <FormField
            label="提交任务路径"
            :model-value="form.connection.invokePath"
            :error="fieldErrors.invokePath"
            required
            placeholder="/v1/run/tasks"
            help="平台提交任务时调用的路径，会与服务根地址拼接。"
            @update:model-value="updateConnectionTextField('invokePath', $event)"
          />
          <FormField
            v-if="form.invokeMode === 'submit_poll'"
            label="结果路径模板"
            :model-value="form.connection.resultPathTemplate || ''"
            :error="fieldErrors.resultPathTemplate"
            required
            placeholder="/v1/run/tasks/{externalRunId}"
            help="轮询模式下用于查询任务结果的路径，可使用 {externalRunId} 占位。"
            @update:model-value="updateConnectionTextField('resultPathTemplate', $event)"
          />
          <FormField
            label="请求超时（秒）"
            :model-value="String(form.connection.requestTimeoutSeconds)"
            type="number"
            help="单次提交请求等待响应的最长时间。"
            @update:model-value="updateConnectionNumberField('requestTimeoutSeconds', $event)"
          />
          <FormField
            v-if="form.invokeMode === 'submit_poll'"
            label="轮询间隔（秒）"
            :model-value="String(form.connection.pollIntervalSeconds)"
            type="number"
            help="平台两次查询结果之间的等待时间。"
            @update:model-value="updateConnectionNumberField('pollIntervalSeconds', $event)"
          />
          <FormField
            v-if="form.invokeMode === 'submit_poll'"
            label="轮询总超时（秒）"
            :model-value="String(form.connection.pollTimeoutSeconds)"
            type="number"
            help="超过该时间仍未进入终态时，平台会停止等待。"
            @update:model-value="updateConnectionNumberField('pollTimeoutSeconds', $event)"
          />
          <FormField
            label="鉴权方式"
            :model-value="form.auth.type"
            type="select"
            :options="authOptions"
            leading-icon="lucide:key-round"
            help="选择平台调用 Agent 服务时使用的鉴权方式。"
            @update:model-value="$emit('set-auth-type', String($event))"
          />
          <FormField
            v-if="form.auth.type === 'bearer'"
            label="Bearer Token"
            :model-value="form.auth.token"
            type="password"
            :error="fieldErrors.authSecret"
            placeholder="创建时写入，详情页不展示明文"
            help="平台会以 Authorization: Bearer Token 形式发送。"
            @update:model-value="updateAuthField('token', $event)"
          />
          <template
            v-if="form.auth.type === 'api_key_header' || form.auth.type === 'custom_header'"
          >
            <FormField
              label="Header 名称"
              :model-value="form.auth.headerName"
              :error="fieldErrors.authHeaderName"
              placeholder="x-api-key"
              help="填写服务要求的请求头名称。"
              @update:model-value="updateAuthField('headerName', $event)"
            />
            <FormField
              label="Header 密钥"
              :model-value="form.auth.secret"
              type="password"
              :error="fieldErrors.authHeaderSecret"
              placeholder="创建时写入，详情页不展示明文"
              help="平台会把该密钥写入上方 Header。"
              @update:model-value="updateAuthField('secret', $event)"
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
            :placeholder="getInputMappingPlaceholder(item.key)"
            :help="getInputMappingHelp(item.key)"
            @update:model-value="updateInputMapping(item.key, $event)"
          />
          <UiToggleField
            :model-value="form.requestOptions.structuredOutput.supported"
            title="支持结构化输出"
            description="平台会在请求体中附加结构化输出字段。"
            @update:model-value="updateStructuredOutputSupported"
          />
          <FormField
            v-if="form.requestOptions.structuredOutput.supported"
            label="结构化输出字段别名"
            :model-value="form.requestOptions.structuredOutput.fieldAlias"
            :error="fieldErrors.structuredOutputAlias"
            placeholder="outputSchema"
            help="填写 Agent 请求体中接收输出 schema 的顶层字段名。"
            @update:model-value="updateStructuredOutputAlias"
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
            :placeholder="getOutputMappingPlaceholder(item.key)"
            :help="getOutputMappingHelp(item.key)"
            @update:model-value="updateOutputMapping(item.key, $event)"
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
            <span>仅使用上一步配置的任务字段。</span>
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
                help="填写外部请求体中的固定字段名。"
                @update:model-value="updateCustomFieldValue(field.id, 'key', $event)"
              />
              <FormField
                label="类型"
                :model-value="field.valueType"
                type="select"
                :options="customTypeOptions"
                help="选择固定字段值的类型。"
                @update:model-value="$emit('set-custom-field-type', field.id, String($event))"
              />
              <FormField
                label="字段值"
                :model-value="field.value"
                help="每次请求都会带上的固定值。"
                @update:model-value="updateCustomFieldValue(field.id, 'value', $event)"
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
            help="填写 Agent 返回的终态状态值，多个值用逗号或换行分隔。"
            @update:model-value="updateStatusField('terminalStatusesText', $event)"
          />
          <FormField
            label="成功态"
            :model-value="form.successStatusesText"
            :error="fieldErrors.successStatuses"
            placeholder="completed"
            help="填写代表任务成功的状态值，必须包含在终态集合内。"
            @update:model-value="updateStatusField('successStatusesText', $event)"
          />
        </div>

        <AgentCreateResultPanel
          :created-agent="createdAgent"
          :verifying="verifyingCreatedAgent"
          @verify="$emit('verify-created')"
        />
      </div>
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
  AgentConnectionConfig,
  AgentInputMapping,
  AgentOutputMapping,
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

const emit = defineEmits<{
  (event: "apply-template", templateId: string): void;
  (event: "set-invoke-mode", value: string): void;
  (event: "set-auth-type", value: string): void;
  (event: "set-custom-field-type", fieldId: string, value: string): void;
  (event: "set-custom-fields-choice", value: AgentRegisterCustomFieldsChoice): void;
  (event: "add-custom-field"): void;
  (event: "remove-custom-field", fieldId: string): void;
  (event: "verify-created"): void;
  (event: "step-edited", stepId: AgentRegisterStepId): void;
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

const markStepEdited = (stepId: AgentRegisterStepId) => {
  emit("step-edited", stepId);
};

const updateBasicField = (
  key: "name" | "description",
  value: string,
) => {
  props.form[key] = value;
  markStepEdited("basic");
};

const updateConnectionTextField = (
  key: Extract<keyof AgentConnectionConfig, "baseUrl" | "invokePath" | "resultPathTemplate">,
  value: string,
) => {
  props.form.connection[key] = value;
  markStepEdited("connection");
};

const updateConnectionNumberField = (
  key: Extract<
    keyof AgentConnectionConfig,
    "requestTimeoutSeconds" | "pollIntervalSeconds" | "pollTimeoutSeconds"
  >,
  value: string,
) => {
  props.form.connection[key] = Number(value);
  markStepEdited("connection");
};

const updateAuthField = (
  key: "token" | "headerName" | "secret",
  value: string,
) => {
  props.form.auth[key] = value;
  markStepEdited("connection");
};

const updateInputMapping = (key: keyof AgentInputMapping, value: string) => {
  props.form.platformInputMapping[key] = value;
  markStepEdited("inputMapping");
};

const updateStructuredOutputSupported = (value: boolean) => {
  props.form.requestOptions.structuredOutput.supported = value;
  if (!value) {
    props.form.requestOptions.structuredOutput.fieldAlias = "";
  }
  markStepEdited("inputMapping");
};

const updateStructuredOutputAlias = (value: string) => {
  props.form.requestOptions.structuredOutput.fieldAlias = value;
  markStepEdited("inputMapping");
};

const updateOutputMapping = (key: keyof AgentOutputMapping, value: string) => {
  props.form.platformOutputMapping[key] = value;
  markStepEdited("outputMapping");
};

const updateCustomFieldValue = (
  fieldId: string,
  key: "key" | "value",
  value: string,
) => {
  const field = props.form.customRequestFields.find((item) => item.id === fieldId);
  if (!field) {
    return;
  }

  field[key] = value;
  markStepEdited("customFields");
};

const updateStatusField = (
  key: "terminalStatusesText" | "successStatusesText",
  value: string,
) => {
  props.form[key] = value;
  markStepEdited("statuses");
};

const inputMappingHelp: Record<keyof AgentInputMapping, string> = {
  task: "必填。填写 Agent 请求体中接收任务目标的顶层字段名，例如 prompt。",
  entryUrl: "可选。需要起始网址时，平台会把样本入口写入该字段。",
  timeoutSeconds: "可选。需要任务级超时时间时填写该字段名。",
  sampleId: "可选。需要样本 ID 参与追踪时填写该字段名。",
  evaluationId: "可选。需要评测任务 ID 参与追踪时填写该字段名。",
  maxSteps: "可选。需要限制 Agent 最大执行步数时填写该字段名。",
};

const inputMappingPlaceholder: Record<keyof AgentInputMapping, string> = {
  task: "prompt",
  entryUrl: "url",
  timeoutSeconds: "timeoutSeconds",
  sampleId: "sampleId",
  evaluationId: "evaluationId",
  maxSteps: "maxSteps",
};

const outputMappingHelp: Record<keyof AgentOutputMapping, string> = {
  externalRunId: "轮询模式必填。填写提交响应中运行 ID 的路径；顶层字段写 runId，嵌套字段写 data.runId。",
  status: "轮询模式必填。填写结果响应中状态字段的路径；顶层字段写 status，嵌套字段写 data.status。",
  finalAnswer: "可选。填写最终答案或文本结果所在路径，例如 answer 或 output.answer。",
  errorMessage: "可选。填写错误信息所在路径，便于失败时展示原因，例如 error.message。",
};

const outputMappingPlaceholder: Record<keyof AgentOutputMapping, string> = {
  externalRunId: "runId",
  status: "status",
  finalAnswer: "answer",
  errorMessage: "error.message",
};

const getInputMappingHelp = (key: keyof AgentInputMapping): string =>
  inputMappingHelp[key];

const getInputMappingPlaceholder = (key: keyof AgentInputMapping): string =>
  inputMappingPlaceholder[key];

const getOutputMappingHelp = (key: keyof AgentOutputMapping): string =>
  outputMappingHelp[key];

const getOutputMappingPlaceholder = (key: keyof AgentOutputMapping): string =>
  outputMappingPlaceholder[key];
</script>

<style scoped lang="scss">
.agent-register-form {
  min-height: 100%;
}

.agent-register-step {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
  min-height: 100%;
  min-width: 0;
  padding: 1rem 1.15rem 1.15rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: var(--radius-control-sm);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(248, 250, 252, 0.78)),
    rgba(255, 255, 255, 0.76);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.06);
}

.agent-register-step__head {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  width: 100%;
  flex-direction: column;
  gap: 0.45rem;
  padding-block: 0.12rem 0.85rem;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.94)),
    rgba(255, 255, 255, 0.96);
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.agent-register-step__eyebrow {
  color: var(--color-primary);
  font-size: 0.78rem;
  font-weight: 800;
}

.agent-register-step__head h2 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.28rem;
  line-height: 1.2;
}

.agent-register-step__head p {
  max-width: 780px;
  margin: 0;
  color: var(--color-text-subtle);
  line-height: 1.65;
}

.agent-register-step__body,
.custom-field-list {
  display: flex;
  flex-direction: column;
  gap: 0.95rem;
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
  display: flex;
  flex-direction: column;
  gap: 0;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: var(--radius-control-sm);
  background: rgba(255, 255, 255, 0.54);
  overflow: visible;
}

.form-grid--three {
  display: flex;
}

.form-grid > :deep(.form-field),
.mapping-grid > :deep(.form-field),
.mapping-grid > :deep(.ui-toggle-field) {
  display: grid;
  width: 100%;
  max-width: none;
  grid-template-columns: minmax(12rem, 0.72fr) minmax(16rem, 34rem);
  gap: 0.38rem 1.25rem;
  align-items: start;
  padding: 1rem 1.1rem;
  border-top: 0;
  border-bottom: 1px solid rgba(148, 163, 184, 0.14);
}

.form-grid > :deep(.form-field:last-child),
.mapping-grid > :deep(.form-field:last-child),
.mapping-grid > :deep(.ui-toggle-field:last-child) {
  border-bottom: 0;
}

.form-grid > :deep(.form-field .form-field-label),
.mapping-grid > :deep(.form-field .form-field-label) {
  grid-column: 1;
  grid-row: 1;
  align-self: start;
  padding-top: 0.82rem;
}

.form-grid > :deep(.form-field .form-field-control),
.mapping-grid > :deep(.form-field .form-field-control) {
  grid-column: 2;
  grid-row: 1;
  width: min(100%, 34rem);
}

.form-grid > :deep(.form-field .form-field-help),
.form-grid > :deep(.form-field .form-field-error),
.mapping-grid > :deep(.form-field .form-field-help),
.mapping-grid > :deep(.form-field .form-field-error) {
  grid-column: 1;
  grid-row: 1;
  align-self: start;
  max-width: 22rem;
  margin-top: 2.42rem;
  line-height: 1.6;
}

.form-grid > :deep(.form-field--select),
.mapping-grid > :deep(.form-field--select) {
  position: relative;
  z-index: 2;
}

.form-grid > :deep(.form-field--select:focus-within),
.mapping-grid > :deep(.form-field--select:focus-within) {
  z-index: 8;
}

.mapping-grid > :deep(.ui-toggle-field .ui-toggle-field__copy) {
  grid-column: 1;
}

.mapping-grid > :deep(.ui-toggle-field .ui-toggle-field__input) {
  grid-column: 2;
  justify-self: start;
  margin-top: 0.22rem;
}

.custom-field-row :deep(.form-field) {
  width: 100%;
  max-width: 34rem;
}

.custom-field-row {
  display: flex;
  width: 100%;
  max-width: 36rem;
  flex-direction: column;
  gap: 0.75rem;
  align-items: flex-start;
  padding: 0.95rem;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 0.9rem;
  background: rgba(255, 255, 255, 0.58);
}

.custom-field-row:first-child {
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

@media (max-width: 760px) {
  .agent-register-step {
    padding: 0.9rem;
  }

  .template-grid,
  .custom-choice-grid {
    grid-template-columns: 1fr;
  }

  .form-grid > :deep(.form-field),
  .mapping-grid > :deep(.form-field),
  .mapping-grid > :deep(.ui-toggle-field) {
    grid-template-columns: 1fr;
    gap: 0.5rem;
    padding: 0.95rem;
  }

  .form-grid > :deep(.form-field .form-field-label),
  .mapping-grid > :deep(.form-field .form-field-label) {
    padding-top: 0;
  }

  .form-grid > :deep(.form-field .form-field-control),
  .form-grid > :deep(.form-field .form-field-help),
  .form-grid > :deep(.form-field .form-field-error),
  .mapping-grid > :deep(.form-field .form-field-control),
  .mapping-grid > :deep(.form-field .form-field-help),
  .mapping-grid > :deep(.form-field .form-field-error),
  .mapping-grid > :deep(.ui-toggle-field .ui-toggle-field__copy),
  .mapping-grid > :deep(.ui-toggle-field .ui-toggle-field__input) {
    grid-column: 1;
    grid-row: auto;
    max-width: none;
    margin-top: 0;
  }
}
</style>
