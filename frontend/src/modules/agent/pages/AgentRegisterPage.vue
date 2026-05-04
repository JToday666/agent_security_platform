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
      <AgentRegisterForm
        :templates="templates"
        :form="form"
        :field-errors="fieldErrors"
        :submit-error="submitError"
        :submitting="submitting"
        :created-agent="createdAgent"
        :verifying-created-agent="verifyingCreatedAgent"
        @apply-template="applyTemplate"
        @set-invoke-mode="setInvokeMode"
        @set-auth-type="setAuthType"
        @set-custom-field-type="setCustomFieldType"
        @add-custom-field="addCustomField"
        @remove-custom-field="removeCustomField"
        @create="handleCreate"
        @verify-created="verifyCreatedAgent"
      />

      <AgentInvocationPreviewPanel
        v-model="previewTab"
        :missing-message="preview.missingMessage"
        :code="previewCode"
        :language="previewLanguage"
        @copy="copyPreview"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouteLocation } from "@/app/router/route-names";
import AgentInvocationPreviewPanel from "@/modules/agent/components/AgentInvocationPreviewPanel.vue";
import AgentRegisterForm from "@/modules/agent/components/AgentRegisterForm.vue";
import { useAgentRegisterPage } from "@/modules/agent/composables/useAgentRegisterPage";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";

const {
  templates,
  form,
  loading,
  pageError,
  submitError,
  submitting,
  fieldErrors,
  createdAgent,
  verifyingCreatedAgent,
  previewTab,
  preview,
  previewCode,
  previewLanguage,
  initializePage,
  applyTemplate,
  setInvokeMode,
  setAuthType,
  setCustomFieldType,
  addCustomField,
  removeCustomField,
  handleCreate,
  verifyCreatedAgent,
  copyPreview,
} = useAgentRegisterPage();
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

@media (max-width: 1180px) {
  .agent-register-layout {
    grid-template-columns: 1fr;
  }
}
</style>
