<template>
  <div class="content submit-page layout-page-shell layout-page-shell--wide">
    <PageHero
      title="提交评测"
      description="配置智能体标识、关联测试集与执行参数，初始化应用安全评测任务。"
      description-wrap="single-line"
    >
      <template #actions>
        <UiButton
          :to="RouteLocation.datasetList"
          variant="secondary"
          leading-icon="lucide:database"
        >
          浏览数据集
        </UiButton>
      </template>
    </PageHero>

    <PageStatePanel
      v-if="pageLoading"
      title="正在初始化提交页"
      message="请稍候。"
      :loading="true"
    />

    <PageStatePanel
      v-else-if="pageError"
      title="页面初始化失败"
      :message="pageError"
      action-text="重新加载"
      @action="initializePage"
    />

    <form
      v-else-if="form && submitMeta"
      class="submit-interface"
      @submit.prevent="handleSubmit"
    >
      <div class="submit-interface__canvas">
        <SubmitMethodSelector
          :model-value="form.submitMethod"
          :methods="submitMeta.supportedMethods"
          @update:model-value="setSubmitMethod"
        />

        <SubmitBasicInfoForm
          class="submit-step-card"
          v-model="form"
          :agents="availableAgents"
          :agent-error-message="agentErrorMessage"
          @select-agent="setAgentId"
        />

        <SubmitParameterControls
          class="submit-step-card"
          v-model="form"
          :meta="submitMeta"
        />

        <SubmitDatasetPanel
          class="submit-step-card"
          :categories="enabledCategories"
          :selected-dataset-ids="form.selectedDatasetIds"
          :expanded-category-ids="expandedCategoryIds"
          :status="datasetCatalogStatus"
          :error-message="datasetCatalogErrorMessage"
          :selection-error-message="selectionErrorMessage"
          @select-all="selectAllDatasets"
          @clear-all="clearAllDatasets"
          @toggle-category="toggleCategoryDatasets"
          @toggle-dataset="toggleDataset"
          @toggle-expanded="toggleExpandedCategory"
          @retry="retryDatasetCatalog"
        />

        <SectionBlock
          class="submit-step-card submit-step-card__wrapper"
          :title="form.publicToLeaderboard ? '公开到排行榜' : '仅本人可见'"
          description="公开后，此次评测结果可参与排行榜展示；不公开时，仅本人可见。"
          surface="panel"
        >
          <template #actions>
            <UiToggleField
              v-model="form.publicToLeaderboard"
              title=""
              class="leaderboard-toggle"
            />
          </template>
        </SectionBlock>
      </div>

      <div class="submit-interface__inspector">
        <SubmitActionBar
          :agent-name="selectedAgent?.name || ''"
          :submit-method="form.submitMethod"
          :selected-category-count="selectedCategoryCount"
          :selected-dataset-count="form.selectedDatasetIds.length"
          :selected-dataset-names="selectedDatasetNames"
          :difficulty="form.parameters.difficulty"
          :timeout-minutes="form.parameters.timeoutMinutes"
          :max-steps="form.parameters.maxSteps"
          :public-to-leaderboard="form.publicToLeaderboard"
          :submitting="submitting"
          :can-submit="canSubmit"
          :error-message="submitError"
          @reset="resetDraft"
        />
      </div>
    </form>

    <ConfirmDialog
      v-model="confirmDialogVisible"
      :title="confirmDialogTitle"
      :message="confirmDialogMessage"
      confirm-text="确认提交"
      cancel-text="返回修改"
      :loading="submitting"
      @confirm="confirmSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { RouteLocation } from "@/app/router/route-names";
import { useSubmitAgentPage } from "@/modules/submission/composables/useSubmitAgentPage";
import SubmitActionBar from "@/modules/submission/components/SubmitActionBar.vue";
import SubmitBasicInfoForm from "@/modules/submission/components/SubmitBasicInfoForm.vue";
import SubmitDatasetPanel from "@/modules/submission/components/SubmitDatasetPanel.vue";
import SubmitMethodSelector from "@/modules/submission/components/SubmitMethodSelector.vue";
import SubmitParameterControls from "@/modules/submission/components/SubmitParameterControls.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import ConfirmDialog from "@/shared/ui/feedback/ConfirmDialog.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import UiToggleField from "@/shared/ui/forms/UiToggleField.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";

const {
  form,
  submitMeta,
  pageLoading,
  pageError,
  submitting,
  submitError,
  availableAgents,
  selectedAgent,
  agentErrorMessage,
  expandedCategoryIds,
  datasetCatalogStatus,
  datasetCatalogErrorMessage,
  enabledCategories,
  selectedCategoryCount,
  selectedDatasetNames,
  selectionErrorMessage,
  confirmDialogVisible,
  confirmDialogTitle,
  confirmDialogMessage,
  canSubmit,
  setSubmitMethod,
  setAgentId,
  initializePage,
  handleSubmit,
  confirmSubmit,
  selectAllDatasets,
  clearAllDatasets,
  toggleCategoryDatasets,
  toggleDataset,
  toggleExpandedCategory,
  retryDatasetCatalog,
  resetDraft,
} = useSubmitAgentPage();
</script>

<style scoped lang="scss">
.submit-page {
  padding-bottom: 2.5rem;
}

.submit-interface {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 320px);
  gap: 1.4rem;
  align-items: start;
}

.submit-interface__canvas,
.submit-interface__inspector {
  min-width: 0;
}

.submit-interface__canvas {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.submit-interface__inspector {
  position: sticky;
  top: calc(var(--nav-height) + 1.25rem);
  align-self: start;
}

.submit-step-card__wrapper :deep(.section-block__body) {
  gap: 0;
}

:deep(.ui-toggle-field.leaderboard-toggle) {
  padding: 0;
  border-top: 0;
  flex-shrink: 0;
}

:deep(.leaderboard-toggle .ui-toggle-field__copy) {
  display: none;
}

@media (max-width: 1180px) {
  .submit-interface {
    grid-template-columns: 1fr;
  }

  .submit-interface__inspector {
    position: static;
  }
}
</style>
