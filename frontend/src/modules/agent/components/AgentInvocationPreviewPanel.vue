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
      v-else
      :code="code"
      :language="language"
    />

    <UiButton
      v-if="!missingMessage"
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
import AgentCodePreview from "@/modules/agent/components/AgentCodePreview.vue";
import { previewTabs, type AgentPreviewTab } from "@/modules/agent/composables/useAgentRegisterPage";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";

defineProps<{
  modelValue: AgentPreviewTab;
  missingMessage: string;
  code: string;
  language: "curl" | "python" | "json";
}>();

defineEmits<{
  (event: "update:modelValue", value: AgentPreviewTab): void;
  (event: "copy"): void;
}>();
</script>

<style scoped lang="scss">
.preview-pane {
  position: sticky;
  top: calc(var(--nav-height) + 1.25rem);
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 0;
  padding: 1rem;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-card-md);
  background:
    radial-gradient(circle at 100% 0%, rgba(99, 102, 241, 0.12), transparent 34%),
    rgba(255, 255, 255, 0.78);
  box-shadow: var(--shadow-surface-mid);
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard);
}

.preview-pane:focus-within,
.preview-pane:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-panel-elevated);
}

.preview-pane__tabs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.45rem;
}

.preview-pane__tabs button {
  min-height: 2.45rem;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-card-sm);
  background: rgba(255, 255, 255, 0.76);
  color: var(--color-text-muted);
  font-weight: 700;
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
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-surface-soft);
  transform: translateY(-1px);
}

.preview-pane__tabs button.active {
  color: #312e81;
  border-color: rgba(99, 102, 241, 0.36);
  background:
    linear-gradient(180deg, rgba(238, 242, 255, 0.92), rgba(255, 255, 255, 0.88)),
    var(--grad-primary-soft);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.78),
    0 12px 24px rgba(79, 70, 229, 0.12);
}

@media (max-width: 1180px) {
  .preview-pane {
    position: static;
  }
}
</style>
