<template>
  <section class="submit-summary">
    <div class="section-head">
      <h2>任务摘要</h2>
      <p>确认当前配置后即可创建评测任务。</p>
    </div>

    <dl class="summary-list">
      <div>
        <dt>智能体名称</dt>
        <dd>{{ agentName || "未选择" }}</dd>
      </div>
      <div>
        <dt>提交方式</dt>
        <dd>{{ submitMethod === "docker" ? "Docker" : "API" }}</dd>
      </div>
      <div>
        <dt>已选风险域</dt>
        <dd>{{ selectedCategoryCount }}</dd>
      </div>
      <div>
        <dt>已选数据集</dt>
        <dd>{{ selectedDatasetCount }}</dd>
      </div>
    </dl>

    <div class="section-head section-head--compact">
      <h3>运行参数</h3>
    </div>

    <dl class="summary-list summary-list--compact">
      <div>
        <dt>难度</dt>
        <dd>{{ difficulty }}</dd>
      </div>
      <div>
        <dt>超时</dt>
        <dd>{{ timeoutMinutes }} 分钟</dd>
      </div>
      <div>
        <dt>最大步数</dt>
        <dd>{{ maxSteps }} 步</dd>
      </div>
      <div>
        <dt>榜单展示</dt>
        <dd>{{ leaderboardDisplayMode === "anonymous" ? "匿名" : "公开" }}</dd>
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

    <div class="submit-actions">
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
import type { LeaderboardDisplayMode } from "@/shared/types/agent-types";

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
    leaderboardDisplayMode: LeaderboardDisplayMode;
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
.submit-summary {
  display: flex;
  flex-direction: column;
  gap: 0.95rem;
  min-width: 0;
  padding: 1rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: var(--radius-control-sm);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 250, 252, 0.86)),
    rgba(255, 255, 255, 0.78);
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.06);
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
  overflow-wrap: anywhere;
}

.section-head--compact {
  margin-top: 0;
}

.summary-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0;
  margin: 0;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 0.75rem;
  background: rgba(255, 255, 255, 0.58);
}

.summary-list div {
  min-width: 0;
  padding: 0.76rem 0.85rem;
  border-right: 1px solid rgba(148, 163, 184, 0.12);
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.summary-list div:nth-child(2n) {
  border-right: 0;
}

.summary-list div:nth-last-child(-n + 2) {
  border-bottom: 0;
}

.summary-list dt {
  color: var(--color-text-subtle);
  font-size: 0.82rem;
}

.summary-list dd {
  margin: 0.32rem 0 0;
  overflow-wrap: anywhere;
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

.submit-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  min-width: 0;
  padding-top: 0.2rem;
}

@media (max-width: 768px) {
  .summary-list {
    grid-template-columns: 1fr;
  }

  .submit-actions {
    flex-direction: column;
  }

  .summary-list div,
  .summary-list div:nth-child(2n),
  .summary-list div:nth-last-child(-n + 2) {
    border-right: 0;
    border-bottom: 1px solid rgba(148, 163, 184, 0.12);
  }

  .summary-list div:last-child {
    border-bottom: 0;
  }
}
</style>
