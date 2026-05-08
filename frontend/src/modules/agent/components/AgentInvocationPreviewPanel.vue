<template>
  <aside class="preview-pane">
    <div class="preview-pane__tabs">
      <button
        v-for="tab in previewTabs"
        :key="tab.value"
        type="button"
        :class="{ active: modelValue === tab.value }"
        @click="$emit('update:modelValue', tab.value)"
      >
        {{ tab.label }}
      </button>
    </div>

    <InlineNotice
      v-if="missingMessage"
      tone="info"
      :message="missingMessage"
    />

    <AgentCodePreview
      v-if="hasCode"
      :code="code"
      :language="language"
      fill-height
    />

    <UiButton
      v-if="hasCode"
      variant="secondary"
      size="sm"
      leading-icon="lucide:copy"
      @click="$emit('copy')"
    >
      复制代码
    </UiButton>
  </aside>
</template>

<script setup lang="ts">
import { computed } from "vue";
import AgentCodePreview from "@/modules/agent/components/AgentCodePreview.vue";
import {
  previewTabs,
  type AgentPreviewTab,
} from "@/modules/agent/composables/useAgentRegisterPage";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";

const props = defineProps<{
  modelValue: AgentPreviewTab;
  missingMessage: string;
  code: string;
  language: "curl" | "python" | "json";
}>();

defineEmits<{
  (event: "update:modelValue", value: AgentPreviewTab): void;
  (event: "copy"): void;
}>();

const hasCode = computed(() => props.code.trim().length > 0);
</script>

<style scoped lang="scss">
.preview-pane {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  max-height: 100%;
  overflow: hidden;
  padding: 0.9rem;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-control-sm);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 250, 252, 0.9)),
    #fff;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.08);
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.preview-pane:focus-within,
.preview-pane:hover {
  border-color: var(--color-border-strong);
  box-shadow: 0 22px 52px rgba(15, 23, 42, 0.1);
}

.preview-pane__tabs {
  display: flex;
  gap: 0.35rem;
  flex: 0 0 auto;
  min-width: 0;
  padding: 0.22rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: var(--radius-control-sm);
  background: rgba(241, 245, 249, 0.72);
}

.preview-pane__tabs button {
  flex: 1 1 0;
  min-width: 0;
  min-height: 2.05rem;
  border: 1px solid transparent;
  border-radius: var(--radius-control-sm);
  background: transparent;
  color: var(--color-text-muted);
  font-size: 0.82rem;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
  transition:
    background var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    color var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard);
}

.preview-pane__tabs button:hover,
.preview-pane__tabs button:focus-visible {
  outline: none;
  color: var(--color-primary);
  background: rgba(255, 255, 255, 0.72);
}

.preview-pane__tabs button.active {
  color: #1d4ed8;
  border-color: rgba(37, 99, 235, 0.18);
  background: #fff;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
}

.preview-pane > :deep(.agent-code-preview) {
  flex: 1 1 auto;
  min-height: 0;
}

.preview-pane > :deep(.ui-button) {
  flex: 0 0 auto;
  align-self: flex-start;
}

@media (max-width: 420px) {
  .preview-pane__tabs button {
    font-size: 0.76rem;
  }
}

</style>
