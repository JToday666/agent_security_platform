<template>
  <div class="content agent-register-page layout-page-shell layout-page-shell--wide">
    <PageHero
      title="注册 Agent"
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

    <div
      v-else
      class="agent-register-workspace"
    >
      <AgentRegisterStepIndicator
        :steps="registerSteps"
        :current-step-id="currentStepId"
        :completed-step-ids="completedStepIds"
        :enterable-step-ids="enterableStepIds"
        @select-step="goToStep"
      />

      <div
        class="agent-register-main"
        :class="{ 'agent-register-main--preview': showPreviewPanel }"
      >
        <section class="agent-register-main__form" aria-label="注册 Agent 表单">
          <AgentRegisterForm
            :templates="templates"
            :form="form"
            :field-errors="fieldErrors"
            :submit-error="submitError"
            :created-agent="createdAgent"
            :verifying-created-agent="verifyingCreatedAgent"
            :current-step-id="currentStepId"
            :steps="registerSteps"
            :custom-fields-choice="customFieldsChoice"
            :uses-no-template="usesNoTemplate"
            @apply-template="applyTemplate"
            @set-invoke-mode="setInvokeMode"
            @set-auth-type="setAuthType"
            @set-custom-field-type="setCustomFieldType"
            @set-custom-fields-choice="setCustomFieldsChoice"
            @add-custom-field="addCustomField"
            @remove-custom-field="removeCustomField"
            @verify-created="verifyCreatedAgent"
          />
        </section>

        <Transition name="agent-register-preview">
          <section
            v-if="showPreviewPanel"
            class="agent-register-main__preview"
            aria-label="调用代码预览"
          >
            <AgentInvocationPreviewPanel
              v-model="previewTab"
              :missing-message="preview.missingMessage"
              :code="previewCode"
              :language="previewLanguage"
              @copy="copyPreview"
            />
          </section>
        </Transition>
      </div>

      <footer class="agent-register-footer" aria-label="注册 Agent 操作">
        <UiButton
          v-if="!isFirstStep"
          variant="secondary"
          leading-icon="lucide:arrow-left"
          @click="goToPreviousStep"
        >
          上一步
        </UiButton>
        <span
          v-else
          class="agent-register-footer__spacer"
          aria-hidden="true"
        ></span>

        <UiButton
          v-if="isLastStep"
          variant="primary"
          leading-icon="lucide:check"
          :loading="submitting"
          :disabled="Boolean(createdAgent)"
          @click="handleCreate"
        >
          确认注册
        </UiButton>
        <UiButton
          v-else
          variant="primary"
          leading-icon="lucide:arrow-right"
          @click="goToNextStep"
        >
          下一步
        </UiButton>
      </footer>
    </div>

    <ConfirmDialog
      v-model="templateChangeDialogVisible"
      title="切换注册模板"
      message="切换模板会替换连接、映射、状态和自定义固定字段配置，已填写的 Agent 名称和描述会保留。"
      confirm-text="切换模板"
      cancel-text="继续编辑"
      @confirm="confirmTemplateChange"
      @cancel="cancelTemplateChange"
    />
  </div>
</template>

<script setup lang="ts">
import { RouteLocation } from "@/app/router/route-names";
import AgentInvocationPreviewPanel from "@/modules/agent/components/AgentInvocationPreviewPanel.vue";
import AgentRegisterForm from "@/modules/agent/components/AgentRegisterForm.vue";
import AgentRegisterStepIndicator from "@/modules/agent/components/AgentRegisterStepIndicator.vue";
import { useAgentRegisterPage } from "@/modules/agent/composables/useAgentRegisterPage";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import ConfirmDialog from "@/shared/ui/feedback/ConfirmDialog.vue";
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
  currentStepId,
  registerSteps,
  completedStepIds,
  enterableStepIds,
  isFirstStep,
  isLastStep,
  showPreviewPanel,
  customFieldsChoice,
  usesNoTemplate,
  templateChangeDialogVisible,
  initializePage,
  applyTemplate,
  confirmTemplateChange,
  cancelTemplateChange,
  goToStep,
  goToNextStep,
  goToPreviousStep,
  setInvokeMode,
  setAuthType,
  setCustomFieldType,
  setCustomFieldsChoice,
  addCustomField,
  removeCustomField,
  handleCreate,
  verifyCreatedAgent,
  copyPreview,
} = useAgentRegisterPage();
</script>

<style scoped lang="scss">
.agent-register-page {
  display: flex;
  height: calc(100dvh - var(--nav-height));
  min-height: 0;
  flex-direction: column;
  overflow: hidden;
  padding-bottom: 1rem;
}

.agent-register-page :deep(.page-hero) {
  flex: 0 0 auto;
  margin-bottom: 1rem;
}

.agent-register-workspace {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  flex: 1 1 auto;
  gap: 0.9rem;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
}

.agent-register-main {
  display: grid;
  grid-template-columns: minmax(0, min(920px, 100%)) minmax(0, 0);
  gap: 0;
  align-items: stretch;
  justify-content: center;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
  transition:
    grid-template-columns 220ms var(--ease-standard),
    gap 220ms var(--ease-standard);
}

.agent-register-main--preview {
  grid-template-columns: minmax(0, 1fr) clamp(360px, 28vw, 400px);
  gap: 1.4rem;
  justify-content: stretch;
}

.agent-register-main__form,
.agent-register-main__preview {
  min-height: 0;
  min-width: 0;
}

.agent-register-main__form {
  width: 100%;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 0.1rem 0.25rem 0.5rem 0;
  scrollbar-gutter: stable;
  justify-self: center;
}

.agent-register-main--preview .agent-register-main__form {
  justify-self: stretch;
}

.agent-register-main__preview {
  display: flex;
  overflow: hidden;
}

.agent-register-footer {
  z-index: 4;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  min-width: 0;
  padding-block: 0.85rem 0;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(247, 249, 252, 0.98);
}

.agent-register-footer :deep(.ui-button) {
  min-width: 6.8rem;
}

.agent-register-footer__spacer {
  width: 1px;
  height: 1px;
}

.agent-register-preview-enter-active,
.agent-register-preview-leave-active {
  transition:
    opacity 220ms var(--ease-standard),
    transform 220ms var(--ease-standard);
}

.agent-register-preview-enter-from,
.agent-register-preview-leave-to {
  opacity: 0;
  pointer-events: none;
  transform: translateX(0.8rem);
}

@media (max-width: 1180px) {
  .agent-register-main,
  .agent-register-main--preview {
    grid-template-columns: 1fr;
    gap: 1rem;
    align-content: start;
    align-items: start;
    overflow-x: hidden;
    overflow-y: auto;
  }

  .agent-register-main__form {
    overflow: visible;
    padding: 0;
    justify-self: stretch;
  }

  .agent-register-main__preview {
    min-height: clamp(22rem, 48dvh, 34rem);
  }
}

@media (max-width: 760px) {
  .agent-register-page {
    padding-bottom: 0.75rem;
  }

  .agent-register-workspace {
    gap: 0.75rem;
  }

  .agent-register-footer {
    gap: 0.75rem;
    padding-top: 0.75rem;
  }

  .agent-register-footer :deep(.ui-button) {
    min-width: 6.4rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .agent-register-main,
  .agent-register-preview-enter-active,
  .agent-register-preview-leave-active {
    transition: none;
  }
}
</style>
