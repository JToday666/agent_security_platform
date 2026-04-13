<template>
  <section class="action-card ui-surface-panel">
    <div class="section-head">
      <h2>任务摘要</h2>
      <p>确认当前配置后即可创建评测任务。</p>
    </div>

    <dl class="summary-grid">
      <div class="summary-item">
        <dt>智能体名称</dt>
        <dd>{{ agentName || "未填写" }}</dd>
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
        <dt>自动重试</dt>
        <dd>{{ retryEnabled ? "开启" : "关闭" }}</dd>
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
    retryEnabled: boolean;
    publicToLeaderboard: boolean;
    submitting: boolean;
    canSubmit: boolean;
    errorMessage?: string;
  }>(),
  {
    errorMessage: "",
  },
);

const previewNames = computed(() => props.selectedDatasetNames.slice(0, 4));
const remainingCount = computed(
  () => props.selectedDatasetNames.length - previewNames.value.length,
);
</script>

<style scoped>
.action-card {
  border-radius: 1.35rem;
  padding: 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.95rem;
}

.section-head h2,
.section-head h3 {
  margin: 0;
  color: var(--color-text-dark);
}

.section-head p {
  margin: 0.38rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.6;
}

.section-head--compact {
  margin-top: 0.1rem;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.summary-item {
  padding: 0.82rem 0.9rem;
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.summary-item dt {
  color: var(--color-text-subtle);
  font-size: 0.82rem;
}

.summary-item dd {
  margin: 0.4rem 0 0;
  color: var(--color-text-dark);
  font-size: 0.96rem;
  font-weight: 700;
}

.dataset-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
}

.empty-text {
  margin: 0;
  color: var(--color-text-subtle);
  line-height: 1.6;
}

.notice-list {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.action-row {
  display: flex;
  gap: 0.75rem;
}

@media (max-width: 768px) {
  .summary-grid,
  .action-row {
    grid-template-columns: 1fr;
    flex-direction: column;
  }
}
</style>
