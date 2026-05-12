<template>
  <div class="content submit-page layout-page-shell layout-page-shell--wide">
    <PageHero
      :title="t('submission.page.title')"
      :description="t('submission.page.description')"
      description-wrap="single-line"
    >
      <template #actions>
        <UiButton
          :to="RouteLocation.datasetList"
          variant="secondary"
          leading-icon="app:action.browseDataset"
        >
          {{ t("common.actions.browseDataset") }}
        </UiButton>
      </template>
    </PageHero>

    <PageStatePanel
      v-if="pageLoading"
      :title="t('submission.page.loadingTitle')"
      :message="t('common.feedback.pleaseWait')"
      :loading="true"
    />

    <PageStatePanel
      v-else-if="pageError"
      :title="t('submission.page.errorTitle')"
      :message="pageError"
      :action-text="t('submission.actions.reload')"
      @action="initializePage"
    />

    <form
      v-else-if="form && submitMeta"
      class="submit-interface submit-interface--stacked"
      @submit.prevent="handleSubmit"
    >
      <div class="submit-interface__canvas">
        <SubmitMethodSelector
          :model-value="form.submitMethod"
          :methods="submitMeta.supportedMethods"
          @update:model-value="setSubmitMethod"
        />

        <SubmitBasicInfoForm
          v-model="form"
          :agents="availableAgents"
          :agent-error-message="agentErrorMessage"
          @select-agent="setAgentId"
        />

        <SubmitParameterControls
          v-model="form"
          :meta="submitMeta"
        />

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

        <section
          class="leaderboard-display-row"
          :aria-label="t('submission.leaderboardDisplay.aria')"
        >
          <div class="section-head">
            <h2>{{ t("submission.leaderboardDisplay.title") }}</h2>
            <p>{{ t("submission.leaderboardDisplay.description") }}</p>
          </div>
          <UiChoiceCardGroup
            v-model="form.leaderboardDisplayMode"
            :options="leaderboardDisplayOptions"
          />
        </section>
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
          :leaderboard-display-mode="form.leaderboardDisplayMode"
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
      :confirm-text="t('submission.confirm.submitTitle')"
      :cancel-text="t('submission.confirm.back')"
      :loading="submitting"
      @confirm="confirmSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { RouteLocation } from "@/app/router/route-names";
import { useSubmitAgentPage } from "@/modules/submission/composables/useSubmitAgentPage";
import SubmitActionBar from "@/modules/submission/components/SubmitActionBar.vue";
import SubmitBasicInfoForm from "@/modules/submission/components/SubmitBasicInfoForm.vue";
import SubmitDatasetPanel from "@/modules/submission/components/SubmitDatasetPanel.vue";
import SubmitMethodSelector from "@/modules/submission/components/SubmitMethodSelector.vue";
import SubmitParameterControls from "@/modules/submission/components/SubmitParameterControls.vue";
import type { LeaderboardDisplayMode } from "@/shared/types/agent-types";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import ConfirmDialog from "@/shared/ui/feedback/ConfirmDialog.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import UiChoiceCardGroup from "@/shared/ui/forms/UiChoiceCardGroup.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";

const { t } = useI18n();

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

const leaderboardDisplayOptions = computed<
  Array<{
    value: LeaderboardDisplayMode;
    title: string;
    description: string;
  }>
>(() => [
  {
    value: "public",
    title: t("submission.leaderboardDisplay.public.title"),
    description: t("submission.leaderboardDisplay.public.description"),
  },
  {
    value: "anonymous",
    title: t("submission.leaderboardDisplay.anonymous.title"),
    description: t("submission.leaderboardDisplay.anonymous.description"),
  },
]);
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
  min-width: 0;
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

.leaderboard-display-row {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  padding-top: 0.25rem;
}

.section-head h2 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.08rem;
  overflow-wrap: anywhere;
}

.section-head p {
  margin: 0.35rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.65;
  overflow-wrap: anywhere;
}

@media (max-width: 1180px), (max-height: 760px) {
  .submit-interface--stacked {
    grid-template-columns: 1fr;
  }

  .submit-interface__inspector {
    position: static;
  }
}

@media (max-width: 640px) {
  .submit-page {
    padding-bottom: 1.75rem;
  }

  .submit-interface {
    gap: 1rem;
  }
}
</style>
