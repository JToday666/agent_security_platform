<template>
  <div class="agent-register-form">
    <section class="agent-register-step" aria-live="polite">
      <header class="agent-register-step__head">
        <span class="agent-register-step__eyebrow">
          {{
            t("agent.registerForm.stepCounter", {
              current: currentStepIndex + 1,
              total: steps.length,
            })
          }}
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
              <strong>{{ t("agent.register.template.title") }}</strong>
              <span>{{ t("agent.register.template.description") }}</span>
            </span>
            <span class="template-tile__tags">
              <UiTag tone="neutral" size="sm">
                {{ t("agent.common.templateTagCustom") }}
              </UiTag>
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
                {{ t("agent.common.recommended") }}
              </UiTag>
              <UiTag tone="neutral" size="sm">{{ template.level }}</UiTag>
              <UiTag
                v-for="tag in template.tags.filter((item) => item !== t('agent.common.recommended'))"
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
            :label="t('agent.fields.name')"
            :model-value="form.name"
            :error="fieldErrors.name"
            required
            :placeholder="t('agent.placeholders.nameExample')"
            :help="t('agent.registerForm.helps.name')"
            @update:model-value="updateBasicField('name', $event)"
          />
          <FormField
            :label="t('agent.fields.description')"
            :model-value="form.description"
            type="textarea"
            :rows="5"
            :placeholder="t('agent.placeholders.descriptionBrief')"
            :help="t('agent.registerForm.helps.description')"
            @update:model-value="updateBasicField('description', $event)"
          />
        </div>
      </div>

      <div
        v-else-if="currentStepId === 'connection'"
        class="agent-register-step__body"
      >
        <div class="form-grid">
          <FormField
            :label="t('agent.fields.invokeMode')"
            :model-value="form.invokeMode"
            type="select"
            :options="invokeModeOptions"
            leading-icon="app:field.invokeMode"
            :help="t('agent.registerForm.helps.invokeMode')"
            @update:model-value="$emit('set-invoke-mode', String($event))"
          />
          <FormField
            :label="t('agent.fields.connectionBaseUrl')"
            :model-value="form.connection.baseUrl"
            type="url"
            :error="fieldErrors.baseUrl"
            required
            leading-icon="app:field.connection"
            placeholder="https://api.agent.example.com"
            :help="t('agent.registerForm.helps.baseUrl')"
            @update:model-value="updateConnectionTextField('baseUrl', $event)"
          />
          <FormField
            :label="t('agent.fields.taskPath')"
            :model-value="form.connection.invokePath"
            :error="fieldErrors.invokePath"
            required
            placeholder="/v1/run/tasks"
            :help="t('agent.registerForm.helps.taskPath')"
            @update:model-value="updateConnectionTextField('invokePath', $event)"
          />
          <FormField
            v-if="form.invokeMode === 'submit_poll'"
            :label="t('agent.fields.resultPathTemplate')"
            :model-value="form.connection.resultPathTemplate || ''"
            :error="fieldErrors.resultPathTemplate"
            required
            placeholder="/v1/run/tasks/{externalRunId}"
            :help="t('agent.registerForm.helps.resultPathTemplate')"
            @update:model-value="updateConnectionTextField('resultPathTemplate', $event)"
          />
          <FormField
            :label="t('agent.fields.requestTimeout')"
            :model-value="String(form.connection.requestTimeoutSeconds)"
            type="number"
            :help="t('agent.registerForm.helps.requestTimeout')"
            @update:model-value="updateConnectionNumberField('requestTimeoutSeconds', $event)"
          />
          <FormField
            v-if="form.invokeMode === 'submit_poll'"
            :label="t('agent.fields.pollInterval')"
            :model-value="String(form.connection.pollIntervalSeconds)"
            type="number"
            :help="t('agent.registerForm.helps.pollInterval')"
            @update:model-value="updateConnectionNumberField('pollIntervalSeconds', $event)"
          />
          <FormField
            v-if="form.invokeMode === 'submit_poll'"
            :label="t('agent.fields.pollTimeout')"
            :model-value="String(form.connection.pollTimeoutSeconds)"
            type="number"
            :help="t('agent.registerForm.helps.pollTimeout')"
            @update:model-value="updateConnectionNumberField('pollTimeoutSeconds', $event)"
          />
          <FormField
            :label="t('agent.fields.authMethod')"
            :model-value="form.auth.type"
            type="select"
            :options="authOptions"
            leading-icon="app:field.apiKey"
            :help="t('agent.registerForm.helps.authMethod')"
            @update:model-value="$emit('set-auth-type', String($event))"
          />
          <FormField
            v-if="form.auth.type === 'bearer'"
            label="Bearer Token"
            :model-value="form.auth.token"
            type="password"
            :error="fieldErrors.authSecret"
            :placeholder="t('agent.registerForm.notVisibleSecretPlaceholder')"
            :help="t('agent.registerForm.helps.authSecret')"
            @update:model-value="updateAuthField('token', $event)"
          />
          <template
            v-if="form.auth.type === 'api_key_header' || form.auth.type === 'custom_header'"
          >
            <FormField
              :label="t('agent.fields.authHeaderName')"
              :model-value="form.auth.headerName"
              :error="fieldErrors.authHeaderName"
              placeholder="x-api-key"
              :help="t('agent.registerForm.helps.authHeaderName')"
              @update:model-value="updateAuthField('headerName', $event)"
            />
            <FormField
              :label="t('agent.fields.authHeaderSecret')"
              :model-value="form.auth.secret"
              type="password"
              :error="fieldErrors.authHeaderSecret"
              :placeholder="t('agent.registerForm.notVisibleSecretPlaceholder')"
              :help="t('agent.registerForm.helps.authHeaderSecret')"
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
            :title="t('agent.registerForm.structuredOutputTitle')"
            :description="t('agent.registerForm.helps.structuredOutput')"
            @update:model-value="updateStructuredOutputSupported"
          />
          <FormField
            v-if="form.requestOptions.structuredOutput.supported"
            :label="t('agent.fields.structuredOutputAlias')"
            :model-value="form.requestOptions.structuredOutput.fieldAlias"
            :error="fieldErrors.structuredOutputAlias"
            placeholder="outputSchema"
            :help="t('agent.registerForm.helps.structuredOutputAlias')"
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
            <strong>{{ t("agent.registerForm.customFields.addFixed") }}</strong>
            <span>{{ t("agent.registerForm.customFields.addFixedDescription") }}</span>
          </button>
          <button
            type="button"
            class="custom-choice"
            :class="{ 'custom-choice--active': customFieldsChoice === 'skip' }"
            @click="$emit('set-custom-fields-choice', 'skip')"
          >
            <strong>{{ t("agent.registerForm.customFields.skipFixed") }}</strong>
            <span>{{ t("agent.registerForm.customFields.skipFixedDescription") }}</span>
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
                :label="t('agent.fields.customFieldKey')"
                :model-value="field.key"
                :help="t('agent.registerForm.customFields.fieldKeyHelp')"
                @update:model-value="updateCustomFieldValue(field.id, 'key', $event)"
              />
              <FormField
                :label="t('agent.fields.customFieldType')"
                :model-value="field.valueType"
                type="select"
                :options="customTypeOptions"
                :help="t('agent.registerForm.customFields.fieldTypeHelp')"
                @update:model-value="$emit('set-custom-field-type', field.id, String($event))"
              />
              <FormField
                :label="t('agent.fields.customFieldValue')"
                :model-value="field.value"
                :help="t('agent.registerForm.customFields.fieldValueHelp')"
                @update:model-value="updateCustomFieldValue(field.id, 'value', $event)"
              />
              <UiButton
                variant="ghost"
                size="sm"
                leading-icon="app:action.delete"
                @click="$emit('remove-custom-field', field.id)"
              >
                {{ t("common.actions.delete") }}
              </UiButton>
            </div>
          </div>
          <UiButton
            variant="secondary"
            size="sm"
            leading-icon="app:action.add"
            @click="$emit('add-custom-field')"
          >
            {{ t("agent.registerForm.customFields.addField") }}
          </UiButton>
        </template>

        <InlineNotice
          v-if="usesNoTemplate && customFieldsChoice === 'skip'"
          tone="info"
          :message="t('agent.registerForm.customFields.skipNotice')"
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
            :label="t('agent.fields.terminalStatuses')"
            :model-value="form.terminalStatusesText"
            :error="fieldErrors.terminalStatuses"
            placeholder="completed, failed, timed_out"
            :help="t('agent.registerForm.helps.statusTerminal')"
            @update:model-value="updateStatusField('terminalStatusesText', $event)"
          />
          <FormField
            :label="t('agent.fields.successStatuses')"
            :model-value="form.successStatusesText"
            :error="fieldErrors.successStatuses"
            placeholder="completed"
            :help="t('agent.registerForm.helps.statusSuccess')"
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
import { useI18n } from "vue-i18n";
import AgentCreateResultPanel from "@/modules/agent/components/AgentCreateResultPanel.vue";
import {
  buildAuthOptions,
  buildCustomTypeOptions,
  buildInputMappingItems,
  buildInvokeModeOptions,
  buildOutputMappingItems,
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

const { t } = useI18n();
const invokeModeOptions = computed(() => buildInvokeModeOptions(t));
const authOptions = computed(() => buildAuthOptions(t));
const customTypeOptions = computed(() => buildCustomTypeOptions(t));
const inputMappingItems = computed(() => buildInputMappingItems(t));
const outputMappingItems = computed(() => buildOutputMappingItems(t));

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
    return outputMappingItems.value;
  }

  return outputMappingItems.value.filter(
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

const inputMappingPlaceholder: Record<keyof AgentInputMapping, string> = {
  task: "prompt",
  entryUrl: "url",
  timeoutSeconds: "timeoutSeconds",
  sampleId: "sampleId",
  evaluationId: "evaluationId",
  maxSteps: "maxSteps",
};

const outputMappingPlaceholder: Record<keyof AgentOutputMapping, string> = {
  externalRunId: "runId",
  status: "status",
  success: "isTaskSuccessful",
  finalAnswer: "answer",
  errorMessage: "error.message",
};

const getInputMappingHelp = (key: keyof AgentInputMapping): string =>
  t(`agent.registerForm.inputMappingHelp.${key}`);

const getInputMappingPlaceholder = (key: keyof AgentInputMapping): string =>
  inputMappingPlaceholder[key];

const getOutputMappingHelp = (key: keyof AgentOutputMapping): string =>
  t(`agent.registerForm.outputMappingHelp.${key}`);

const getOutputMappingPlaceholder = (key: keyof AgentOutputMapping): string =>
  outputMappingPlaceholder[key];
</script>

<style scoped lang="scss">
.agent-register-form {
  container-type: inline-size;
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

.form-grid > :deep(.form-field),
.mapping-grid > :deep(.form-field),
.mapping-grid > :deep(.ui-toggle-field) {
  display: grid;
  width: 100%;
  max-width: none;
  min-width: 0;
  grid-template-columns: minmax(11rem, 0.62fr) minmax(0, 1fr);
  grid-template-rows: auto auto;
  gap: 0.35rem 1rem;
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
  min-width: 0;
}

.form-grid > :deep(.form-field .form-field-control),
.mapping-grid > :deep(.form-field .form-field-control) {
  grid-column: 2;
  grid-row: 1;
  width: 100%;
  min-width: 0;
}

.form-grid > :deep(.form-field .form-field-help),
.mapping-grid > :deep(.form-field .form-field-help) {
  grid-column: 1;
  grid-row: 2;
  align-self: start;
  max-width: 20rem;
  line-height: 1.6;
}

.form-grid > :deep(.form-field .form-field-error),
.mapping-grid > :deep(.form-field .form-field-error) {
  grid-column: 2;
  grid-row: 2;
  align-self: start;
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
  grid-row: 1 / span 2;
  min-width: 0;
}

.mapping-grid > :deep(.ui-toggle-field .ui-toggle-field__input) {
  grid-column: 2;
  grid-row: 1 / span 2;
  justify-self: start;
  margin-top: 0.22rem;
  min-width: 0;
}

.custom-field-row {
  display: flex;
  width: 100%;
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

@container (max-width: 560px) {
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
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 0.5rem;
    padding: 0.95rem;
  }

  .form-grid > :deep(.form-field .form-field-help),
  .mapping-grid > :deep(.form-field .form-field-help),
  .form-grid > :deep(.form-field .form-field-error),
  .mapping-grid > :deep(.form-field .form-field-error),
  .mapping-grid > :deep(.ui-toggle-field .ui-toggle-field__copy) {
    max-width: none;
  }

  .mapping-grid > :deep(.ui-toggle-field .ui-toggle-field__input) {
    align-self: flex-start;
    margin-top: 0;
  }
}

@media (max-width: 760px) {
  .agent-register-step {
    padding: 0.9rem;
  }

  .template-grid,
  .custom-choice-grid {
    grid-template-columns: 1fr;
  }
}
</style>
