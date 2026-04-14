<template>
  <div class="content submit-page layout-page-shell layout-page-shell--wide">
    <PageHeroCard
      title="提交评测"
      description="填写智能体信息、选择数据集并确认运行参数后创建评测任务。"
      tone="workspace"
      title-tone="brand"
    >
      <template #actions>
        <UiButton :to="RouteLocation.datasetList" variant="secondary">
          浏览数据集
        </UiButton>
      </template>
    </PageHeroCard>

    <PageStateCard
      v-if="pageLoading"
      title="正在初始化提交页"
      message="请稍候。"
      :loading="true"
    />

    <PageStateCard
      v-else-if="pageError"
      title="页面初始化失败"
      :message="pageError"
      action-text="重新加载"
      @action="initializePage"
    />

    <form
      v-else-if="form && submitMeta"
      class="submit-form layout-page-grid"
      @submit.prevent="handleSubmit"
    >
      <div class="submit-main layout-page-stack">
        <SubmitMethodSelector
          :model-value="form.submitMethod"
          :methods="submitMeta.supportedMethods"
          @update:model-value="setSubmitMethod"
        />
        <SubmitBasicInfoForm v-model="form" :field-errors="fieldErrors" />
        <SubmitParameterControls v-model="form" :meta="submitMeta" />
        <SubmitDatasetPanel
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
        <SectionCard
          title="排行榜公开设置"
          description="公开后，此次评测结果可参与排行榜展示；不公开时，仅本人可见。"
        >
          <UiToggleField
            v-model="form.publicToLeaderboard"
            :title="form.publicToLeaderboard ? '公开到排行榜' : '仅本人可见'"
            description="可以随提交一起保存，默认按平台设置填充。"
          />
        </SectionCard>
      </div>

      <div class="submit-side layout-sticky-actions">
        <SubmitActionBar
          :agent-name="form.agentName.trim()"
          :submit-method="form.submitMethod"
          :selected-category-count="selectedCategoryCount"
          :selected-dataset-count="form.selectedDatasetIds.length"
          :selected-dataset-names="selectedDatasetNames"
          :difficulty="form.parameters.difficulty"
          :timeout-minutes="form.parameters.timeoutMinutes"
          :retry-enabled="form.parameters.retryEnabled"
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
import SubmitActionBar from "@/modules/submission/components/SubmitActionBar.vue";
import SubmitBasicInfoForm from "@/modules/submission/components/SubmitBasicInfoForm.vue";
import SubmitDatasetPanel from "@/modules/submission/components/SubmitDatasetPanel.vue";
import SubmitMethodSelector from "@/modules/submission/components/SubmitMethodSelector.vue";
import SubmitParameterControls from "@/modules/submission/components/SubmitParameterControls.vue";
import { useSubmitAgentPage } from "@/modules/submission/composables/useSubmitAgentPage";
import ConfirmDialog from "@/shared/ui/feedback/ConfirmDialog.vue";
import PageHeroCard from "@/shared/ui/page/PageHeroCard.vue";
import PageStateCard from "@/shared/ui/feedback/PageStateCard.vue";
import SectionCard from "@/shared/ui/page/SectionCard.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import UiToggleField from "@/shared/ui/forms/UiToggleField.vue";

const {
  form,
  submitMeta,
  pageLoading,
  pageError,
  submitting,
  submitError,
  fieldErrors,
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

.submit-form {
  align-items: start;
}

.submit-main,
.submit-side {
  min-width: 0;
}

.submit-side {
  align-self: start;
  height: fit-content;
}

@media (max-width: 1180px) {
  .submit-side {
    width: 100%;
  }
}
</style>