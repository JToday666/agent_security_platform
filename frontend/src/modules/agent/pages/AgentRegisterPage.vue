<template>
  <div class="content agent-register-page layout-page-shell layout-page-shell--wide">
    <PageHero
      title="注册智能体"
      description="填写接入配置并创建 Agent。验证通过后可用于提交评测。"
    >
      <template #actions>
        <UiButton
          :to="RouteLocation.agentManagement"
          variant="secondary"
          leading-icon="lucide:list"
        >
          返回管理页
        </UiButton>
      </template>
    </PageHero>

    <PageStatePanel
      v-if="loading"
      title="正在初始化注册页"
      message="请稍候。"
      :loading="true"
    />

    <PageStatePanel
      v-else-if="pageError"
      title="注册页初始化失败"
      :message="pageError"
      action-text="重新加载"
      @action="initializePage"
    />

    <div v-else class="agent-register-layout">
      <form class="agent-register-form" @submit.prevent="handleCreate">
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
              @click="applyTemplate(template.templateId)"
            >
              <span class="template-row__copy">
                <strong>{{ template.name }}</strong>
                <span>{{ template.description }}</span>
              </span>
              <span class="template-row__tags">
                <UiTag
                  v-if="template.recommended"
                  tone="success"
                  size="sm"
                >
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
              @update:model-value="setInvokeMode"
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
              @update:model-value="setAuthType"
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
                @update:model-value="setCustomFieldType(field.id, $event)"
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
                @click="removeCustomField(field.id)"
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
              @click="addCustomField"
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

        <InlineNotice
          v-if="createdAgent"
          tone="success"
          title="Agent 已创建"
          message="验证通过后可用于提交评测。"
        >
          <template #actions>
            <UiButton
              variant="secondary"
              size="sm"
              :loading="verifyingCreatedAgent"
              leading-icon="lucide:rotate-cw"
              @click="verifyCreatedAgent"
            >
              立即验证
            </UiButton>
            <UiButton
              :to="RouteLocation.agentDetail(createdAgent.agentId)"
              variant="primary"
              size="sm"
              leading-icon="lucide:eye"
            >
              查看详情
            </UiButton>
          </template>
        </InlineNotice>

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

      <aside class="preview-pane">
        <div class="preview-pane__tabs">
          <button
            v-for="tab in previewTabs"
            :key="tab.value"
            type="button"
            :class="{ active: previewTab === tab.value }"
            @click="previewTab = tab.value"
          >
            {{ tab.label }}
          </button>
        </div>

        <InlineNotice
          v-if="preview.missingMessage"
          tone="info"
          :message="preview.missingMessage"
        />

        <pre v-else class="code-preview"><code>{{ previewCode }}</code></pre>

        <UiButton
          v-if="!preview.missingMessage"
          variant="secondary"
          size="sm"
          leading-icon="lucide:copy"
          @click="copyPreview"
        >
          复制代码
        </UiButton>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { RouteLocation } from "@/app/router/route-names";
import {
  createAgent,
  getAgentDetail,
  getAgentTemplates,
  verifyAgent,
} from "@/modules/agent/api/agent-api";
import {
  buildAgentCreatePayload,
  buildAgentInvocationPreview,
  createAgentRegisterFormFromDetail,
  createAgentRegisterFormFromTemplate,
  createCustomRequestField,
  createEmptyAgentRegisterForm,
  selectDefaultTemplate,
  type AgentCustomFieldType,
  type AgentRegisterFieldErrors,
  type AgentRegisterForm,
} from "@/modules/agent/model/agent-registration";
import type {
  AgentAuthType,
  AgentCreateResponse,
  AgentInputMapping,
  AgentOutputMapping,
  AgentTemplate,
} from "@/shared/types/agent-registry-types";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import UiTag from "@/shared/ui/display/UiTag.vue";
import FormField from "@/shared/ui/forms/FormField.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";

const route = useRoute();
const router = useRouter();

const templates = ref<AgentTemplate[]>([]);
const form = ref<AgentRegisterForm>(createEmptyAgentRegisterForm());
const loading = ref(true);
const pageError = ref("");
const submitError = ref("");
const submitting = ref(false);
const fieldErrors = ref<AgentRegisterFieldErrors>({});
const createdAgent = ref<AgentCreateResponse | null>(null);
const verifyingCreatedAgent = ref(false);
const previewTab = ref<"curl" | "python" | "body">("curl");

const invokeModeOptions = [
  { label: "提交轮询", value: "submit_poll" },
  { label: "同步响应", value: "sync_response" },
];
const authOptions = [
  { label: "不使用鉴权", value: "none" },
  { label: "Bearer Token", value: "bearer" },
  { label: "API Key Header", value: "api_key_header" },
  { label: "自定义 Header", value: "custom_header" },
];
const customTypeOptions = [
  { label: "字符串", value: "string" },
  { label: "数字", value: "number" },
  { label: "布尔值", value: "boolean" },
  { label: "JSON", value: "json" },
];
const previewTabs = [
  { label: "curl", value: "curl" as const },
  { label: "Python", value: "python" as const },
  { label: "请求体", value: "body" as const },
];
const inputMappingItems: Array<{
  key: keyof AgentInputMapping;
  label: string;
}> = [
  { key: "task", label: "task → Agent 字段" },
  { key: "entryUrl", label: "entryUrl → Agent 字段" },
  { key: "timeoutSeconds", label: "timeoutSeconds → Agent 字段" },
  { key: "sampleId", label: "sampleId → Agent 字段" },
  { key: "evaluationId", label: "evaluationId → Agent 字段" },
  { key: "maxSteps", label: "maxSteps → Agent 字段" },
];
const outputMappingItems: Array<{
  key: keyof AgentOutputMapping;
  label: string;
}> = [
  { key: "externalRunId", label: "externalRunId ← 响应路径" },
  { key: "status", label: "status ← 响应路径" },
  { key: "finalAnswer", label: "finalAnswer ← 响应路径" },
  { key: "errorMessage", label: "errorMessage ← 响应路径" },
  { key: "stepCount", label: "stepCount ← 响应路径" },
  { key: "artifacts", label: "artifacts ← 响应路径" },
];

const preview = computed(() => buildAgentInvocationPreview(form.value));
const previewCode = computed(() => {
  if (previewTab.value === "python") {
    return preview.value.python;
  }

  if (previewTab.value === "body") {
    return JSON.stringify(preview.value.requestBody, null, 2);
  }

  return preview.value.curl;
});

const initializePage = async () => {
  loading.value = true;
  pageError.value = "";
  submitError.value = "";
  createdAgent.value = null;
  fieldErrors.value = {};

  try {
    const loadedTemplates = await getAgentTemplates();
    templates.value = loadedTemplates;

    const copyFrom =
      typeof route.query.copyFrom === "string" ? route.query.copyFrom : "";
    if (copyFrom) {
      const detail = await getAgentDetail(copyFrom);
      form.value = createAgentRegisterFormFromDetail(detail);
      return;
    }

    const template = selectDefaultTemplate(loadedTemplates);
    form.value = template
      ? createAgentRegisterFormFromTemplate(template)
      : createEmptyAgentRegisterForm();
  } catch (error) {
    pageError.value =
      error instanceof Error ? error.message : "注册页初始化失败。";
  } finally {
    loading.value = false;
  }
};

const applyTemplate = (templateId: string) => {
  const template = templates.value.find((item) => item.templateId === templateId);
  if (!template || createdAgent.value) {
    return;
  }

  const currentName = form.value.name;
  const currentDescription = form.value.description;
  form.value = createAgentRegisterFormFromTemplate(template);
  form.value.name = currentName;
  form.value.description = currentDescription;
  fieldErrors.value = {};
};

const setInvokeMode = (value: string) => {
  form.value.invokeMode =
    value === "sync_response" ? "sync_response" : "submit_poll";
};

const setAuthType = (value: string) => {
  const nextType = authOptions.some((option) => option.value === value)
    ? (value as AgentAuthType)
    : "none";
  form.value.auth.type = nextType;
};

const setCustomFieldType = (fieldId: string, value: string) => {
  const nextType = customTypeOptions.some((option) => option.value === value)
    ? (value as AgentCustomFieldType)
    : "string";
  const field = form.value.customRequestFields.find(
    (item) => item.id === fieldId,
  );
  if (field) {
    field.valueType = nextType;
  }
};

const addCustomField = () => {
  form.value.customRequestFields.push(createCustomRequestField());
};

const removeCustomField = (fieldId: string) => {
  form.value.customRequestFields = form.value.customRequestFields.filter(
    (field) => field.id !== fieldId,
  );
};

const handleCreate = async () => {
  submitError.value = "";
  fieldErrors.value = {};
  const result = buildAgentCreatePayload(form.value);
  if (!result.valid || !result.payload) {
    fieldErrors.value = result.fieldErrors;
    submitError.value = result.errors[0] || "Agent 创建参数校验失败。";
    return;
  }

  submitting.value = true;
  try {
    createdAgent.value = await createAgent(result.payload);
  } catch (error) {
    submitError.value =
      error instanceof Error ? error.message : "Agent 创建失败。";
  } finally {
    submitting.value = false;
  }
};

const verifyCreatedAgent = async () => {
  if (!createdAgent.value) {
    return;
  }

  verifyingCreatedAgent.value = true;
  submitError.value = "";

  try {
    await verifyAgent(createdAgent.value.agentId);
    await router.push(RouteLocation.agentDetail(createdAgent.value.agentId));
  } catch (error) {
    submitError.value =
      error instanceof Error ? error.message : "Agent 验证失败。";
  } finally {
    verifyingCreatedAgent.value = false;
  }
};

const copyPreview = async () => {
  if (!previewCode.value) {
    return;
  }

  await navigator.clipboard?.writeText(previewCode.value);
};

onMounted(async () => {
  await initializePage();
});
</script>

<style scoped lang="scss">
.agent-register-page {
  padding-bottom: 2.5rem;
}

.agent-register-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 380px);
  gap: 1.5rem;
  align-items: start;
}

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

.preview-pane {
  position: sticky;
  top: calc(var(--nav-height) + 1.25rem);
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 0;
  padding: 1rem;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-card-md);
  background:
    radial-gradient(circle at 100% 0%, rgba(99, 102, 241, 0.12), transparent 34%),
    rgba(255, 255, 255, 0.78);
  box-shadow: var(--shadow-surface-mid);
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard);
}

.preview-pane:focus-within,
.preview-pane:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-panel-elevated);
}

.preview-pane__tabs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.45rem;
}

.preview-pane__tabs button {
  min-height: 2.45rem;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.76);
  color: var(--color-text-muted);
  font-weight: 700;
  cursor: pointer;
  transition:
    background var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    color var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard);
}

.preview-pane__tabs button:hover,
.preview-pane__tabs button:focus-visible {
  outline: none;
  color: var(--color-primary);
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-surface-soft);
  transform: translateY(-1px);
}

.preview-pane__tabs button.active {
  color: var(--color-primary);
  border-color: rgba(99, 102, 241, 0.22);
  background: var(--grad-primary-soft);
}

.code-preview {
  max-height: 620px;
  overflow: auto;
  margin: 0;
  padding: 1rem;
  border-radius: var(--radius-card-sm);
  background: #0f172a;
  color: #e2e8f0;
  font-size: 0.82rem;
  line-height: 1.6;
  box-shadow: inset 0 0 0 1px rgba(226, 232, 240, 0.08);
}

@media (max-width: 1180px) {
  .agent-register-layout,
  .form-grid--three {
    grid-template-columns: 1fr;
  }

  .preview-pane {
    position: static;
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
