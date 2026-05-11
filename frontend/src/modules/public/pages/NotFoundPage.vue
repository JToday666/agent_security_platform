<template>
  <div class="content not-found-page layout-page-shell">
    <PageHero
      :eyebrow="t('public.notFound.eyebrow')"
      :title="t('public.notFound.title')"
      :description="t('public.notFound.description')"
      align="center"
    />

    <SectionBlock
      class="not-found-section"
      :title="t('public.notFound.sectionTitle')"
      :description="t('public.notFound.sectionDescription')"
    >
      <template #actions>
        <UiButton :to="RouteLocation.home" variant="secondary">
          {{ t("common.actions.returnHome") }}
        </UiButton>
        <UiButton :to="RouteLocation.datasetList" variant="primary">
          {{ t("public.notFound.datasetAction") }}
        </UiButton>
      </template>
    </SectionBlock>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { RouteLocation } from "@/app/router/route-names";
import PageHero from "@/shared/ui/page/PageHero.vue";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";

const { t } = useI18n();
</script>

<style scoped lang="scss">
.not-found-section {
  gap: 0.9rem;
}

.not-found-section :deep(.section-block__head),
.not-found-section :deep(.section-block__copy) {
  align-items: center;
  text-align: center;
}

.not-found-section :deep(.section-block__actions) {
  justify-content: center;
}
</style>
