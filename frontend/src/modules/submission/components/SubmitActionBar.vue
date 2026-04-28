<template>
  <section class="action-card ui-surface-glass">
    <div class="section-head">
      <h2>任务摘要</h2>
      <p>确认当前配置后即可创建评测任务。</p>
    </div>

    <dl class="summary-grid">
      <div class="summary-item">
        <dt>智能体名称</dt>
        <dd>{{ agentName || "未选择" }}</dd>
      </div>
      <div class="summary-item">
        <dt>提交方式</dt>
        <dd>{{ submitMethod === "docker" ? "Docker" : "API" }}</dd>
      </div>
      <div class="summary-item">
        <dt>已选风险域</dt>
        <dd>{{ selectedCategoryCount }}</dd>
      </div>
      <div class="summary-item">
        <dt>已选数据集</dt>
        <dd>{{ selectedDatasetCount }}</dd>
      </div>
    </dl>

    <div class="section-head section-head--compact">
      <h3>运行参数</h3>
    </div>

    <dl class="summary-grid summary-grid--compact">
      <div class="summary-item">
        <dt>难度</dt>
        <dd>{{ difficulty }}</dd>
      </div>
      <div class="summary-item">
        <dt>超时</dt>
        <dd>{{ timeoutMinutes }} 分钟</dd>
      </div>
      <div class="summary-item">
        <dt>最大步数</dt>
        <dd>{{ maxSteps }} 步</dd>
      </div>
      <div class="summary-item">
        <dt>公开结果</dt>
        <dd>{{ publicToLeaderboard ? "公开" : "私有" }}</dd>
      </div>
    </dl>

    <div class="section-head section-head--compact">
      <h3>已选数据集</h3>
    </div>

    <div v-if="selectedDatasetNames.length" class="dataset-tags">
      <UiTag
        v-for="name in previewNames"
        :key="name"
        tone="info"
        size="sm"
      >
        {{ name }}
      </UiTag>
      <UiTag v-if="remainingCount > 0" tone="neutral" size="sm">
        +{{ remainingCount }}
      </UiTag>
    </div>
    <p v-else class="empty-text">尚未选择数据集。</p>

    <div v-if="errorMessage" class="notice-list">
      <InlineNotice tone="danger" :message="errorMessage" />
    </div>

    <div class="action-row">
      <UiButton variant="secondary" type="button" block @click="$emit('reset')">
        重置
      </UiButton>
      <UiButton
        variant="primary"
        type="submit"
        block
        :disabled="submitting || !canSubmit"
      >
        {{ submitting ? "提交中..." : "提交任务" }}
      </UiButton>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import UiTag from "@/shared/ui/display/UiTag.vue";

defineEmits<{
  (event: "reset"): void;
}>();

const props = withDefaults(
  defineProps<{
    agentName: string;
    submitMethod: "api" | "docker";
    selectedCategoryCount: number;
    selectedDatasetCount: number;
    selectedDatasetNames: string[];
    difficulty: number;
    timeoutMinutes: number;
    maxSteps: number;
    publicToLeaderboard: boolean;
    submitting: boolean;
    canSubmit: boolean;
    errorMessage?: string;
  }>(),
  {
    errorMessage: "",
  },
);

const compactPreviewLimit = 3;
const previewNames = computed(() =>
  props.selectedDatasetNames.slice(0, compactPreviewLimit),
);
const remainingCount = computed(
  () => props.selectedDatasetNames.length - previewNames.value.length,
);
</script>

<style scoped lang="scss">
.action-card {
  max-height: calc(100vh - var(--nav-height) - 2.8rem);
  border-radius: 1.2rem;
  padding: 1rem 0.95rem;
  display: flex;
  flex-direction: column;
  gap: 0.82rem;
}

.section-head h2,
.section-head h3 {
  margin: 0;
  color: var(--color-text-dark);
}

.section-head p {
  margin: 0.32rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.58;
}

.section-head--compact {
  margin-top: 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.62rem;
}

.summary-item {
  padding: 0.72rem 0.8rem;
  border-radius: 0.95rem;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.summary-item dt {
  color: var(--color-text-subtle);
  font-size: 0.82rem;
}

.summary-item dd {
  margin: 0.32rem 0 0;
  color: var(--color-text-dark);
  font-size: 0.92rem;
  font-weight: 700;
}

.dataset-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.empty-text {
  margin: 0;
  color: var(--color-text-subtle);
  line-height: 1.6;
}

.notice-list {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.action-row {
  display: flex;
  gap: 0.65rem;
}

@media (max-width: 768px) {
  .action-card {
    max-height: none;
  }

  .summary-grid,
  .action-row {
    grid-template-columns: 1fr;
    flex-direction: column;
  }
}
</style>
