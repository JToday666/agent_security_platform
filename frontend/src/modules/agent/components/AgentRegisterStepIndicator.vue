<template>
  <nav class="agent-register-steps" aria-label="注册步骤">
    <button
      v-for="(step, index) in steps"
      :key="step.id"
      type="button"
      class="agent-register-steps__segment"
      :class="{
        'agent-register-steps__segment--active': currentStepId === step.id,
        'agent-register-steps__segment--completed': completedStepIds.includes(step.id),
        'agent-register-steps__segment--locked': !canEnterStep(step.id),
      }"
      :aria-current="currentStepId === step.id ? 'step' : undefined"
      :aria-disabled="!canEnterStep(step.id)"
      :aria-label="`${index + 1}. ${step.title}`"
      :title="step.title"
      @click="handleSelect(step.id)"
    >
      <span class="agent-register-steps__bar" aria-hidden="true" />
      <span class="agent-register-steps__tooltip" role="tooltip">
        {{ step.title }}
      </span>
    </button>
  </nav>
</template>

<script setup lang="ts">
import type {
  AgentRegisterStep,
  AgentRegisterStepId,
} from "@/modules/agent/model/agent-registration";

const props = defineProps<{
  steps: AgentRegisterStep[];
  currentStepId: AgentRegisterStepId;
  completedStepIds: AgentRegisterStepId[];
  enterableStepIds: AgentRegisterStepId[];
}>();

const emit = defineEmits<{
  (event: "select-step", stepId: AgentRegisterStepId): void;
}>();

const canEnterStep = (stepId: AgentRegisterStepId) =>
  props.enterableStepIds.includes(stepId);

const handleSelect = (stepId: AgentRegisterStepId) => {
  if (canEnterStep(stepId)) {
    emit("select-step", stepId);
  }
};
</script>

<style scoped lang="scss">
.agent-register-steps {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(2rem, 1fr));
  gap: 0.45rem;
  width: 100%;
  padding-block: 0.3rem 0.2rem;
}

.agent-register-steps__segment {
  position: relative;
  display: flex;
  align-items: center;
  min-width: 0;
  height: 1.75rem;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
  appearance: none;
}

.agent-register-steps__segment:focus-visible {
  outline: none;
}

.agent-register-steps__bar {
  display: block;
  width: 100%;
  height: 0.42rem;
  border-radius: var(--radius-pill);
  background: rgba(148, 163, 184, 0.32);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.62);
  transition:
    height var(--duration-fast) var(--ease-standard),
    background var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.agent-register-steps__segment:hover .agent-register-steps__bar,
.agent-register-steps__segment:focus-visible .agent-register-steps__bar {
  transform: translateY(-1px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.76),
    0 6px 14px rgba(15, 23, 42, 0.08);
}

.agent-register-steps__segment--completed .agent-register-steps__bar,
.agent-register-steps__segment--active .agent-register-steps__bar {
  background: linear-gradient(90deg, #2563eb, #0ea5e9);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.42),
    0 6px 16px rgba(37, 99, 235, 0.18);
}

.agent-register-steps__segment--active .agent-register-steps__bar {
  height: 0.68rem;
  background: linear-gradient(90deg, #1d4ed8, #0284c7);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.5),
    0 8px 20px rgba(37, 99, 235, 0.26);
}

.agent-register-steps__segment--locked {
  cursor: not-allowed;
}

.agent-register-steps__tooltip {
  position: absolute;
  bottom: calc(100% + 0.45rem);
  left: 50%;
  z-index: 3;
  max-width: 12rem;
  padding: 0.35rem 0.55rem;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: var(--radius-control-sm);
  background: rgba(15, 23, 42, 0.92);
  color: #fff;
  font-size: 0.76rem;
  font-weight: 700;
  line-height: 1.3;
  opacity: 0;
  pointer-events: none;
  text-align: center;
  transform: translate(-50%, 0.25rem);
  white-space: nowrap;
  transition:
    opacity var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.agent-register-steps__segment:hover .agent-register-steps__tooltip,
.agent-register-steps__segment:focus-visible .agent-register-steps__tooltip {
  opacity: 1;
  transform: translate(-50%, 0);
}

.agent-register-steps__tooltip::after {
  position: absolute;
  top: 100%;
  left: 50%;
  width: 0.45rem;
  height: 0.45rem;
  background: rgba(15, 23, 42, 0.92);
  content: "";
  transform: translate(-50%, -50%) rotate(45deg);
}

@media (prefers-reduced-motion: reduce) {
  .agent-register-steps__bar,
  .agent-register-steps__tooltip {
    transition: none;
  }
}

@media (max-width: 760px) {
  .agent-register-steps {
    gap: 0.28rem;
  }
}
</style>
