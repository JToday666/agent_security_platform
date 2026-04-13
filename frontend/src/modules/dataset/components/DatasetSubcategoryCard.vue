<template>
  <article
    class="dataset-card ui-surface-white ui-hover-card"
    :style="cardStyle"
  >
    <div class="card-top">
      <span class="category-badge" :style="badgeStyle">{{ category.name }}</span>
    </div>

    <h3 class="dataset-name">{{ dataset.name }}</h3>
    <p class="dataset-description">{{ dataset.shortDescription || "暂无说明" }}</p>

    <div class="grid-cols-2 meta-grid">
      <div class="meta-item">
        <span class="meta-label">样本数</span>
        <strong>{{ formatSampleCount(dataset.sampleCount ?? undefined) }}</strong>
      </div>
      <div class="meta-item">
        <span class="meta-label">更新时间</span>
        <strong>{{ formatDateLabel(dataset.updatedAt ?? undefined) }}</strong>
      </div>
    </div>

    <div class="card-actions">
      <Button
        :to="RouteLocation.datasetDetail(dataset.datasetId)"
        variant="text"
        size="sm"
      >
        查看详情
      </Button>
      <Button
        variant="secondary"
        size="sm"
        @click="handleSubmitClick"
      >
        {{ isLogin ? "使用此数据集" : "登录后评测" }}
      </Button>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { storeToRefs } from "pinia";
import { useRouter } from "vue-router";
import { RouteLocation } from "@/app/router/RouteNames";
import type {
  DatasetCategoryViewModel,
  DatasetSubcategory,
} from "@/shared/types/DatasetTypes";
import { useUserStore } from "@/modules/account/stores/UserStore";
import Button from "@/shared/ui/actions/UiButton.vue";
import {
  formatDateLabel,
  formatSampleCount,
  getCategoryTheme,
} from "@/modules/dataset/lib";

const props = defineProps<{
  dataset: DatasetSubcategory;
  category: DatasetCategoryViewModel;
}>();

const router = useRouter();
const userStore = useUserStore();
const { isLogin } = storeToRefs(userStore);

const theme = computed(() => getCategoryTheme(props.category.categoryId));

const cardStyle = computed(() => ({
  "--dataset-soft": theme.value.soft,
  "--dataset-border": theme.value.border,
  "--dataset-text": theme.value.text,
  "--dataset-solid": theme.value.solid,
  "--dataset-shadow": theme.value.shadow,
}));

const badgeStyle = computed(() => {
  return {
    background: theme.value.soft,
    color: theme.value.text,
    border: `1px solid ${theme.value.border}`,
  };
});

const handleSubmitClick = () => {
  if (!isLogin.value) {
    userStore.openLoginDialog();
    return;
  }

  void router.push({
    ...RouteLocation.agentSubmit,
    query: {
      datasetIds: props.dataset.datasetId,
    },
  });
};
</script>

<style scoped>
.dataset-card {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 260px;
  padding: 1.3rem;
  border-radius: 1.35rem;
  color: inherit;
  border: 1px solid var(--dataset-border, rgba(226, 232, 240, 0.88));
  box-shadow: 0 14px 24px -26px var(--dataset-shadow, rgba(15, 23, 42, 0.16));
}

.dataset-card::before {
  content: "";
  position: absolute;
  inset: 0 0 auto;
  height: 3px;
  background: linear-gradient(
    90deg,
    var(--dataset-solid, #2563eb),
    rgba(255, 255, 255, 0.96)
  );
}

.dataset-card::after {
  content: "";
  position: absolute;
  top: -3rem;
  right: -3rem;
  width: 8rem;
  height: 8rem;
  border-radius: 50%;
  background: radial-gradient(circle, var(--dataset-soft, rgba(219, 234, 254, 0.6)), transparent 70%);
  opacity: 0.7;
  pointer-events: none;
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.category-badge {
  border-radius: 999px;
  padding: 0.34rem 0.7rem;
  font-size: 0.8rem;
  font-weight: 600;
}

.dataset-name {
  margin: 0.95rem 0 0.65rem;
  color: var(--color-text-dark);
  font-size: 1.22rem;
}

.dataset-description {
  margin: 0;
  color: var(--color-text-muted);
  line-height: 1.76;
  flex: 1;
}

.meta-grid {
  gap: 0.8rem;
  margin-top: 1.05rem;
}

.meta-item {
  padding: 0.85rem;
  background: linear-gradient(180deg, var(--dataset-soft, #f8fafc), #ffffff 84%);
  border: 1px solid var(--dataset-border, #e2e8f0);
  border-radius: 0.95rem;
}

.meta-label {
  display: block;
  color: var(--color-text-subtle);
  font-size: 0.8rem;
  margin-bottom: 0.35rem;
}

.meta-item strong {
  color: var(--color-text-dark);
  font-size: 0.96rem;
}

.card-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-top: 1rem;
}

@media (max-width: 640px) {
  .card-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
