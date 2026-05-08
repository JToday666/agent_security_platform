<template>
  <SectionBlock title="最近一次验证结果" class="verification-block">
    <InlineNotice
      v-if="!detail.lastVerification"
      tone="info"
      message="尚未验证。"
    />
    <div v-else class="verification-result">
      <div
        class="verification-summary"
        :class="{
          'verification-summary--passed': detail.lastVerification.passed,
          'verification-summary--failed': !detail.lastVerification.passed,
        }"
      >
        <div class="verification-summary__indicator">
          <span class="verification-summary__icon-ring" aria-hidden="true">
            <AppIcon :icon="resultIcon" />
          </span>
          <div class="verification-summary__text">
            <span class="verification-summary__sub">验证结果</span>
            <strong class="verification-summary__strong">{{ resultLabel }}</strong>
          </div>
        </div>
        <div class="verification-summary__stats">
          <div
            v-for="item in statItems"
            :key="item.label"
            class="verification-stat-item"
          >
            <span class="verification-stat-label">{{ item.label }}</span>
            <strong class="verification-stat-value">{{ item.value }}</strong>
          </div>
        </div>
      </div>

      <div v-if="messageGroups.length" class="verification-message-groups">
        <div class="verification-detail-header">诊断明细</div>
        <section
          v-for="group in messageGroups"
          :key="group.label"
          class="verification-message-group"
          :class="`verification-message-group--${group.tone}`"
        >
          <div class="verification-message-group__head">
            <UiTag :tone="group.tone" class="verification-tag" size="sm">
              {{ group.label }}
            </UiTag>
            <span class="verification-count">{{ group.messages.length }} 项</span>
          </div>
          <div class="verification-table-wrapper">
            <table class="verification-table">
              <thead>
                <tr>
                  <th>类型标识</th>
                  <th>详情描述</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="message in group.messages"
                  :key="`${group.label}-${message.code}-${message.message}`"
                >
                  <td class="verification-code-cell">
                    <code>{{ message.code }}</code>
                  </td>
                  <td class="verification-message-cell">{{ message.message }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  </SectionBlock>
</template>

<script setup lang="ts">
import AppIcon from "@/shared/ui/branding/AppIcon.vue";
import UiTag from "@/shared/ui/display/UiTag.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";
import type {
  AgentDetailTextItem,
  AgentVerificationMessageGroup,
} from "@/modules/agent/lib/agent-detail-view";
import type { AgentDetail } from "@/shared/types/agent-registry-types";

defineProps<{
  detail: AgentDetail;
  resultIcon: string;
  resultLabel: string;
  statItems: AgentDetailTextItem[];
  messageGroups: AgentVerificationMessageGroup[];
}>();
</script>

<style scoped lang="scss">
.verification-result {
  display: flex;
  flex-direction: column;
  gap: 1.8rem;
  padding-top: 0.5rem;
}

.verification-summary {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 1.5rem;
  border-radius: var(--radius-card-sm);
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.4) 0%, rgba(255, 255, 255, 0.8) 100%);
  border: 1px solid rgba(37, 99, 235, 0.2);
  box-shadow: var(--shadow-surface-soft);
}

.verification-summary--passed {
  background: linear-gradient(135deg, rgba(240, 253, 244, 0.5) 0%, rgba(255, 255, 255, 0.9) 100%);
  border-color: rgba(34, 197, 94, 0.35);
}

.verification-summary--failed {
  background: linear-gradient(135deg, rgba(254, 242, 242, 0.4) 0%, rgba(255, 255, 255, 0.9) 100%);
  border-color: rgba(239, 68, 68, 0.35);
  box-shadow: 0 8px 16px -8px rgba(239, 68, 68, 0.15);
}

.verification-summary__indicator {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  min-width: 14rem;
}

.verification-summary__icon-ring {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 50%;
  font-size: 1.6rem;
}

.verification-summary--passed .verification-summary__icon-ring {
  background: rgba(34, 197, 94, 0.15);
  color: #16a34a;
}

.verification-summary--failed .verification-summary__icon-ring {
  background: rgba(239, 68, 68, 0.15);
  color: #dc2626;
}

.verification-summary__text {
  display: flex;
  flex-direction: column;
}

.verification-summary__sub {
  font-size: 0.85rem;
  color: var(--color-text-subtle);
}

.verification-summary__strong {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text-dark);
}

.verification-summary__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 2.5rem;
  flex: 1;
}

.verification-stat-item {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.verification-stat-label {
  font-size: 0.85rem;
  color: var(--color-text-subtle);
}

.verification-stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-dark);
}

.verification-message-groups {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.verification-detail-header {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--color-text-main);
  margin-bottom: -0.5rem;
}

.verification-message-group {
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-card-sm);
  background: rgba(255, 255, 255, 0.9);
  overflow: hidden;
  box-shadow: var(--shadow-surface-soft);
}

.verification-message-group__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.8rem 1.2rem;
  background: linear-gradient(90deg, rgba(248, 250, 252, 0.6) 0%, rgba(255, 255, 255, 0.6) 100%);
  border-bottom: 1px solid var(--color-border-soft);
}

.verification-count {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-subtle);
}

.verification-table-wrapper {
  overflow-x: auto;
}

.verification-table {
  width: 100%;
  min-width: 560px;
  border-collapse: collapse;
  text-align: left;
}

.verification-table th,
.verification-table td {
  padding: 0.85rem 1.2rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
}

.verification-table th {
  font-size: 0.82rem;
  color: var(--color-text-muted);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.verification-table tbody tr:last-child td {
  border-bottom: none;
}

.verification-code-cell code {
  background: rgba(241, 245, 249, 0.8);
  color: #475569;
  padding: 0.2rem 0.5rem;
  border-radius: 0.3rem;
  font-size: 0.85rem;
  font-family: ui-monospace, SFMono-Regular, monospace;
}

.verification-message-cell {
  font-size: 0.95rem;
  color: var(--color-text-main);
  line-height: 1.5;
}

.verification-message-group--danger {
  border-color: rgba(239, 68, 68, 0.3);
}

.verification-message-group--danger .verification-message-group__head {
  background: linear-gradient(90deg, rgba(254, 242, 242, 0.6) 0%, rgba(255, 255, 255, 0.6) 100%);
  border-bottom-color: rgba(239, 68, 68, 0.15);
}

.verification-message-group--warning {
  border-color: rgba(245, 158, 11, 0.3);
}

.verification-message-group--warning .verification-message-group__head {
  background: linear-gradient(90deg, rgba(255, 251, 235, 0.6) 0%, rgba(255, 255, 255, 0.6) 100%);
  border-bottom-color: rgba(245, 158, 11, 0.15);
}

@media (max-width: 700px) {
  .verification-summary {
    flex-direction: column;
    align-items: flex-start;
  }

  .verification-summary__stats {
    width: 100%;
    gap: 1rem;
  }

  .verification-table th,
  .verification-table td {
    padding-inline: 0.95rem;
  }
}
</style>
