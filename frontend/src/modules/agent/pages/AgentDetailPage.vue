<template>
  <div class="content agent-detail-page layout-page-shell layout-page-shell--wide">
    <PageHero
      :title="detail?.name || 'Agent 详情'"
      description="查看非敏感配置、验证结果与可用操作。"
    >
      <template #actions>
        <UiButton
          :to="RouteLocation.agentManagement"
          variant="secondary"
          leading-icon="lucide:list"
        >
          返回管理页
        </UiButton>
      </template>
    </PageHero>

    <PageStatePanel
      v-if="loading"
      title="正在读取 Agent"
      message="请稍候。"
      :loading="true"
    />

    <PageStatePanel
      v-else-if="error"
      title="Agent 加载失败"
      :message="error"
      action-text="重试"
      @action="loadDetail"
    />

    <div v-else-if="detail" class="detail-layout">
      <main class="detail-main">
        <SectionBlock title="状态摘要" surface="panel">
          <dl class="summary-grid">
            <div
              v-for="item in summaryItems"
              :key="item.label"
              class="summary-item"
            >
              <dt>{{ item.label }}</dt>
              <dd v-if="item.kind === 'status'">
                <AgentStatusTag :status="detail.status" />
              </dd>
              <dd v-else>{{ item.value }}</dd>
            </div>
          </dl>
          <p class="detail-description">{{ detail.description || "暂无描述" }}</p>
        </SectionBlock>

        <SectionBlock title="连接配置">
          <dl class="detail-grid">
            <div
              v-for="item in connectionItems"
              :key="item.label"
              class="detail-field"
            >
              <dt>{{ item.label }}</dt>
              <dd>{{ item.value }}</dd>
            </div>
          </dl>
        </SectionBlock>

        <SectionBlock title="鉴权摘要">
          <dl class="detail-grid">
            <div
              v-for="item in authItems"
              :key="item.label"
              class="detail-field"
            >
              <dt>{{ item.label }}</dt>
              <dd>{{ item.value }}</dd>
            </div>
          </dl>
        </SectionBlock>

        <div class="detail-section-pair">
          <SectionBlock title="输入字段逻辑映射" surface="panel">
            <div class="mapping-tree">
              <article
                v-for="item in inputMappingItems"
                :key="item.label"
                class="mapping-node ui-glow-frame"
              >
                <div class="mapping-node__source">
                  <span class="mapping-n-label">{{ item.sourceLabel }}</span>
                  <strong class="mapping-n-value">{{ item.source }}</strong>
                </div>
                <div class="mapping-node__connector">
                  <span class="mapping-line"></span>
                  <span class="mapping-arrow-ring">
                    <AppIcon icon="lucide:arrow-right" class="mapping-arrow" />
                  </span>
                  <span class="mapping-line"></span>
                </div>
                <div class="mapping-node__target">
                  <span class="mapping-n-label">{{ item.targetLabel }}</span>
                  <code class="mapping-n-code" :class="{ 'is-empty': item.empty }">{{ item.target }}</code>
                </div>
              </article>
            </div>
          </SectionBlock>

          <SectionBlock title="输出字段逻辑映射" surface="panel">
            <div class="mapping-tree mapping-tree--reverse">
              <article
                v-for="item in outputMappingItems"
                :key="item.label"
                class="mapping-node ui-glow-frame"
              >
                <div class="mapping-node__source">
                  <span class="mapping-n-label">{{ item.sourceLabel }}</span>
                  <code class="mapping-n-code" :class="{ 'is-empty': item.empty }">{{ item.source }}</code>
                </div>
                <div class="mapping-node__connector">
                  <span class="mapping-line"></span>
                  <span class="mapping-arrow-ring">
                    <AppIcon icon="lucide:arrow-right" class="mapping-arrow" />
                  </span>
                  <span class="mapping-line"></span>
                </div>
                <div class="mapping-node__target">
                  <span class="mapping-n-label">{{ item.targetLabel }}</span>
                  <strong class="mapping-n-value">{{ item.target }}</strong>
                </div>
              </article>
            </div>
          </SectionBlock>
        </div>

        <SectionBlock title="自定义固定字段">
          <AgentCodePreview
            :code="customRequestBodyJson"
            language="json"
            max-height="360px"
          />
        </SectionBlock>

        <SectionBlock title="状态集合">
          <dl class="detail-grid">
            <div
              v-for="item in statusItems"
              :key="item.label"
              class="detail-field"
            >
              <dt>{{ item.label }}</dt>
              <dd>{{ item.value }}</dd>
            </div>
          </dl>
        </SectionBlock>

        <SectionBlock title="最近一次验证结果" class="verification-block" surface="panel">
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
                  <AppIcon :icon="verificationResultIcon" />
                </span>
                <div class="verification-summary__text">
                  <span class="verification-summary__sub">验证结果</span>
                  <strong class="verification-summary__strong">{{ verificationResultLabel }}</strong>
                </div>
              </div>
              <div class="verification-summary__stats">
                <div
                  v-for="item in verificationStatItems"
                  :key="item.label"
                  class="verification-stat-item"
                >
                  <span class="verification-stat-label">{{ item.label }}</span>
                  <strong class="verification-stat-value">{{ item.value }}</strong>
                </div>
              </div>
            </div>

            <div
              v-if="verificationMessageGroups.length"
              class="verification-message-groups"
            >
              <div class="verification-detail-header">诊断明细</div>
              <section
                v-for="group in verificationMessageGroups"
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
      </main>

      <aside class="detail-actions">
        <div class="detail-actions__head">
          <span>当前状态</span>
          <AgentStatusTag :status="detail.status" size="sm" />
        </div>
        <dl class="detail-actions__meta">
          <div>
            <dt>最近验证</dt>
            <dd>{{ verificationLabel }}</dd>
          </div>
          <div>
            <dt>调用模式</dt>
            <dd>{{ getInvokeModeLabel(detail.invokeMode) }}</dd>
          </div>
        </dl>
        <UiButton
          variant="secondary"
          block
          leading-icon="lucide:rotate-cw"
          :disabled="!detail.actions.canVerify || busy"
          :loading="busyAction === 'verify'"
          @click="handleVerify"
        >
          验证
        </UiButton>
        <UiButton
          :to="RouteLocation.agentRegister({ copyFrom: detail.agentId })"
          variant="secondary"
          block
          leading-icon="lucide:copy-plus"
        >
          复制新建
        </UiButton>
        <UiButton
          :to="RouteLocation.agentSubmitWithAgent(detail.agentId)"
          variant="primary"
          block
          leading-icon="lucide:file-plus-2"
          :disabled="!detail.actions.canSubmitEvaluation"
        >
          提交评测
        </UiButton>
        <UiButton
          variant="danger"
          block
          leading-icon="lucide:archive"
          :disabled="!detail.actions.canArchive || busy"
          :loading="busyAction === 'archive'"
          @click="archiveDialogVisible = true"
        >
          归档
        </UiButton>
        <InlineNotice
          v-if="actionError"
          tone="danger"
          :message="actionError"
        />
      </aside>
    </div>

    <ConfirmDialog
      v-model="archiveDialogVisible"
      title="归档 Agent"
      message="归档后，该 Agent 不能再提交评测，但仍可复制新建。"
      confirm-text="确认归档"
      cancel-text="取消"
      :loading="busyAction === 'archive'"
      @confirm="handleArchive"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { RouteLocation } from "@/app/router/route-names";
import {
  archiveAgent,
  getAgentDetail,
  verifyAgent,
} from "@/modules/agent/api/agent-api";
import AgentCodePreview from "@/modules/agent/components/AgentCodePreview.vue";
import AgentStatusTag from "@/modules/agent/components/AgentStatusTag.vue";
import { getInvokeModeLabel } from "@/modules/agent/model/agent-display";
import type {
  AgentAuthType,
  AgentDetail,
  AgentVerificationMessage,
} from "@/shared/types/agent-registry-types";
import { formatDateTimeLabel } from "@/modules/dataset/lib/dataset-utils";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";
import UiTag from "@/shared/ui/display/UiTag.vue";
import ConfirmDialog from "@/shared/ui/feedback/ConfirmDialog.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";

interface DetailTextItem {
  label: string;
  value: string;
  kind?: "text" | "status";
}

interface MappingDisplayItem {
  label: string;
  sourceLabel: string;
  source: string;
  targetLabel: string;
  target: string;
  empty: boolean;
}

interface VerificationMessageGroup {
  label: string;
  tone: "warning" | "danger";
  messages: AgentVerificationMessage[];
}

const route = useRoute();
const router = useRouter();

const detail = ref<AgentDetail | null>(null);
const loading = ref(true);
const error = ref("");
const actionError = ref("");
const busyAction = ref<"verify" | "archive" | "">("");
const archiveDialogVisible = ref(false);

const agentId = computed(() =>
  typeof route.params.agentId === "string" ? route.params.agentId : "",
);
const busy = computed(() => Boolean(busyAction.value));
const verificationLabel = computed(() => {
  if (!detail.value?.verifiedAt) {
    return "未验证";
  }

  const result =
    detail.value.lastVerification?.passed === true
      ? "通过"
      : detail.value.lastVerification?.passed === false
        ? "失败"
        : "未知";
  return `${formatDateTimeLabel(detail.value.verifiedAt)} · ${result}`;
});
const authLabelMap: Record<AgentAuthType, string> = {
  none: "不使用鉴权",
  bearer: "Bearer Token",
  api_key_header: "API Key Header",
  custom_header: "自定义 Header",
};
const authLabel = computed(() =>
  detail.value ? authLabelMap[detail.value.auth.type] : "",
);
const authHeaderName = computed(() => {
  const publicConfig = detail.value?.auth.publicConfig;
  const headerName = publicConfig?.headerName;
  return typeof headerName === "string" ? headerName : "";
});
const verificationResultLabel = computed(() =>
  detail.value?.lastVerification?.passed ? "验证通过" : "验证失败",
);
const verificationResultIcon = computed(() =>
  detail.value?.lastVerification?.passed
    ? "lucide:circle-check-big"
    : "lucide:triangle-alert",
);

const displayValue = (value: unknown): string => {
  if (typeof value === "number") {
    return String(value);
  }

  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }

  return "-";
};

const toMappingValue = (value: unknown): { text: string; empty: boolean } => {
  if (typeof value === "string" && value.trim()) {
    return { text: value.trim(), empty: false };
  }

  if (typeof value === "number") {
    return { text: String(value), empty: false };
  }

  return { text: "未配置", empty: true };
};

const mapInputMappingItems = (
  value: Record<string, unknown>,
): MappingDisplayItem[] =>
  Object.entries(value).map(([key, item]) => {
    const target = toMappingValue(item);
    return {
      label: key,
      sourceLabel: "平台字段",
      source: key,
      targetLabel: "Agent 字段",
      target: target.text,
      empty: target.empty,
    };
  });

const mapOutputMappingItems = (
  value: Record<string, unknown>,
): MappingDisplayItem[] =>
  Object.entries(value).map(([key, item]) => {
    const source = toMappingValue(item);
    return {
      label: key,
      sourceLabel: "响应路径",
      source: source.text,
      targetLabel: "平台字段",
      target: key,
      empty: source.empty,
    };
  });

const summaryItems = computed<DetailTextItem[]>(() => {
  if (!detail.value) {
    return [];
  }

  return [
    { label: "状态", value: detail.value.status, kind: "status" },
    { label: "调用模式", value: getInvokeModeLabel(detail.value.invokeMode) },
    { label: "最近验证", value: verificationLabel.value },
    { label: "更新时间", value: formatDateTimeLabel(detail.value.updatedAt) },
  ];
});

const connectionItems = computed<DetailTextItem[]>(() => {
  if (!detail.value) {
    return [];
  }

  const { connection } = detail.value;
  return [
    { label: "服务根地址", value: displayValue(connection.baseUrl) },
    { label: "提交任务路径", value: displayValue(connection.invokePath) },
    {
      label: "结果路径模板",
      value: displayValue(connection.resultPathTemplate),
    },
    {
      label: "请求超时",
      value: `${connection.requestTimeoutSeconds} 秒`,
    },
    {
      label: "轮询间隔",
      value: `${connection.pollIntervalSeconds} 秒`,
    },
    {
      label: "轮询总超时",
      value: `${connection.pollTimeoutSeconds} 秒`,
    },
  ];
});

const authItems = computed<DetailTextItem[]>(() => {
  if (!detail.value) {
    return [];
  }

  return [
    { label: "鉴权方式", value: authLabel.value },
    ...(authHeaderName.value
      ? [{ label: "Header 名称", value: authHeaderName.value }]
      : []),
    {
      label: "凭据状态",
      value: detail.value.auth.hasCredential ? "已配置" : "未配置",
    },
  ];
});

const inputMappingItems = computed<MappingDisplayItem[]>(() =>
  detail.value ? mapInputMappingItems(detail.value.platformInputMapping) : [],
);
const outputMappingItems = computed<MappingDisplayItem[]>(() =>
  detail.value ? mapOutputMappingItems(detail.value.platformOutputMapping) : [],
);
const statusItems = computed<DetailTextItem[]>(() => {
  if (!detail.value) {
    return [];
  }

  return [
    {
      label: "终态",
      value: detail.value.terminalStatuses.join("、") || "-",
    },
    {
      label: "成功态",
      value: detail.value.successStatuses.join("、") || "-",
    },
  ];
});
const customRequestBodyJson = computed(() =>
  JSON.stringify(detail.value?.customRequestBody ?? {}, null, 2),
);
const verificationStatItems = computed<DetailTextItem[]>(() => {
  const verification = detail.value?.lastVerification;
  if (!verification) {
    return [];
  }

  return [
    {
      label: "验证时间",
      value: detail.value?.verifiedAt
        ? formatDateTimeLabel(detail.value.verifiedAt)
        : "未知",
    },
    { label: "错误", value: String(verification.errors.length) },
    { label: "警告", value: String(verification.warnings.length) },
  ];
});
const verificationMessageGroups = computed<VerificationMessageGroup[]>(() => {
  const verification = detail.value?.lastVerification;
  if (!verification) {
    return [];
  }

  return [
    {
      label: "错误",
      tone: "danger" as const,
      messages: verification.errors,
    },
    {
      label: "警告",
      tone: "warning" as const,
      messages: verification.warnings,
    },
  ].filter((group) => group.messages.length > 0);
});

const loadDetail = async () => {
  loading.value = true;
  error.value = "";
  actionError.value = "";

  try {
    detail.value = await getAgentDetail(agentId.value);
  } catch (loadError) {
    error.value =
      loadError instanceof Error ? loadError.message : "Agent 详情加载失败。";
  } finally {
    loading.value = false;
  }
};

const handleVerify = async () => {
  if (!detail.value) {
    return;
  }

  busyAction.value = "verify";
  actionError.value = "";
  try {
    await verifyAgent(detail.value.agentId);
    await loadDetail();
  } catch (verifyError) {
    actionError.value =
      verifyError instanceof Error ? verifyError.message : "Agent 验证失败。";
  } finally {
    busyAction.value = "";
  }
};

const handleArchive = async () => {
  if (!detail.value) {
    return;
  }

  busyAction.value = "archive";
  actionError.value = "";
  try {
    await archiveAgent(detail.value.agentId);
    archiveDialogVisible.value = false;
    await router.push(RouteLocation.agentManagement);
  } catch (archiveError) {
    actionError.value =
      archiveError instanceof Error ? archiveError.message : "Agent 归档失败。";
  } finally {
    busyAction.value = "";
  }
};

onMounted(async () => {
  await loadDetail();
});
</script>

<style scoped lang="scss">
.agent-detail-page {
  padding-bottom: 2.5rem;
}

.detail-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 340px);
  gap: 1.5rem;
  align-items: start;
}

.detail-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

.summary-grid,
.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.35rem 1.15rem;
}

.summary-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.summary-item,
.detail-field {
  min-width: 0;
  padding: 0.72rem 0;
  border-top: 1px solid var(--color-border-soft);
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    background var(--duration-fast) var(--ease-standard);
}

.summary-item {
  border-top: 0;
  padding-block: 0.1rem;
}

.detail-field:hover {
  border-color: var(--color-border-strong);
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.06), transparent 72%);
}

.detail-grid .detail-field:nth-child(-n + 2) {
  border-top-color: transparent;
}

.summary-item dt,
.detail-field dt,
.detail-actions__meta dt {
  color: var(--color-text-subtle);
  font-size: 0.86rem;
}

.summary-item dd,
.detail-field dd,
.detail-actions__meta dd {
  margin: 0.32rem 0 0;
  color: var(--color-text-dark);
  font-weight: 700;
  overflow-wrap: anywhere;
  line-height: 1.55;
}

.detail-description {
  margin: 0;
  padding-top: 0.9rem;
  border-top: 1px solid var(--color-border-soft);
  color: var(--color-text-muted);
  line-height: 1.65;
}

.detail-section-pair {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.15rem;
  align-items: start;
}

.detail-actions {
  position: sticky;
  top: calc(var(--nav-height, 4rem) + 1.25rem);
  align-self: start;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-card-md);
  background:
    radial-gradient(circle at 100% 0%, rgba(99, 102, 241, 0.12), transparent 34%),
    rgba(255, 255, 255, 0.8);
  box-shadow: var(--shadow-surface-mid);
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.detail-actions:hover,
.detail-actions:focus-within {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-panel-elevated);
  transform: translateY(-1px);
}

.detail-actions__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  color: var(--color-text-dark);
  font-weight: 800;
}

.detail-actions__meta {
  display: grid;
  gap: 0.7rem;
  margin: 0;
  padding: 0.8rem 0;
  border-block: 1px solid var(--color-border-soft);
}

@media (max-width: 1080px) {
  .detail-layout,
  .detail-section-pair {
    grid-template-columns: 1fr;
  }

  .detail-actions {
    position: static;
  }
}

@media (max-width: 860px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .summary-grid,
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .detail-grid .detail-field:nth-child(-n + 2) {
    border-top-color: var(--color-border-soft);
  }

  .detail-grid .detail-field:first-child {
    border-top-color: transparent;
  }

  .verification-summary {
    flex-direction: column;
    align-items: flex-start;
  }

  .verification-summary__stats {
    width: 100%;
    gap: 1rem;
  }
}
.mapping-tree {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.mapping-node {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-card-sm);
  padding: 1rem;
  box-shadow: 0 4px 12px -8px rgba(15, 23, 42, 0.08);
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.mapping-node:hover,
.mapping-node:focus-within {
  border-color: rgba(99, 102, 241, 0.24);
  box-shadow: var(--shadow-surface-soft);
  transform: translateY(-1px);
}

.mapping-tree--reverse .mapping-node {
  background:
    linear-gradient(90deg, rgba(240, 253, 250, 0.54), rgba(255, 255, 255, 0.86)),
    rgba(255, 255, 255, 0.9);
}

.mapping-node__source,
.mapping-node__target {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.mapping-node__target {
  align-items: flex-end;
  text-align: right;
}

.mapping-n-label {
  font-size: 0.78rem;
  color: var(--color-text-subtle);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.mapping-n-value {
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-text-main);
  word-break: break-all;
}

.mapping-n-code {
  font-size: 0.95rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
    "Liberation Mono", "Courier New", monospace;
  background: var(--color-surface-muted);
  color: #0369a1;
  padding: 0.25rem 0.5rem;
  border-radius: 0.4rem;
  border: 1px solid rgba(148, 163, 184, 0.16);
  word-break: break-all;

  &.is-empty {
    opacity: 0.4;
    text-decoration: line-through;
  }
}

.mapping-node__connector {
  display: flex;
  align-items: center;
  padding: 0 1rem;
  color: var(--color-primary);
  opacity: 0.8;
}

.mapping-line {
  flex: 1;
  height: 2px;
  min-width: 2rem;
  background: var(--grad-progress);
  opacity: 0.4;
}

.mapping-arrow-ring {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  border-radius: 50%;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 10px rgba(37, 99, 235, 0.2);
  z-index: 1;
}

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
  .mapping-node {
    flex-direction: column;
    align-items: stretch;
  }

  .mapping-node__target {
    align-items: flex-start;
    text-align: left;
  }

  .mapping-node__connector {
    align-self: center;
    padding: 0.65rem 0;
    transform: rotate(90deg);
  }

  .verification-table th,
  .verification-table td {
    padding-inline: 0.95rem;
  }
}
</style>

