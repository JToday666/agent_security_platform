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
        <SectionBlock title="基础信息">
          <dl class="detail-grid">
            <div>
              <dt>状态</dt>
              <dd><AgentStatusTag :status="detail.status" /></dd>
            </div>
            <div>
              <dt>调用模式</dt>
              <dd>{{ getInvokeModeLabel(detail.invokeMode) }}</dd>
            </div>
            <div>
              <dt>最近验证</dt>
              <dd>{{ verificationLabel }}</dd>
            </div>
            <div>
              <dt>创建时间</dt>
              <dd>{{ formatDateTimeLabel(detail.createdAt) }}</dd>
            </div>
          </dl>
          <p class="detail-description">{{ detail.description || "暂无描述" }}</p>
        </SectionBlock>

        <SectionBlock title="连接配置">
          <dl class="detail-grid">
            <div>
              <dt>baseUrl</dt>
              <dd>{{ detail.connection.baseUrl }}</dd>
            </div>
            <div>
              <dt>invokePath</dt>
              <dd>{{ detail.connection.invokePath }}</dd>
            </div>
            <div>
              <dt>resultPathTemplate</dt>
              <dd>{{ detail.connection.resultPathTemplate || "-" }}</dd>
            </div>
            <div>
              <dt>请求超时</dt>
              <dd>{{ detail.connection.requestTimeoutSeconds }} 秒</dd>
            </div>
            <div>
              <dt>轮询间隔</dt>
              <dd>{{ detail.connection.pollIntervalSeconds }} 秒</dd>
            </div>
            <div>
              <dt>轮询总超时</dt>
              <dd>{{ detail.connection.pollTimeoutSeconds }} 秒</dd>
            </div>
          </dl>
        </SectionBlock>

        <SectionBlock title="鉴权摘要">
          <dl class="detail-grid">
            <div>
              <dt>鉴权方式</dt>
              <dd>{{ authLabel }}</dd>
            </div>
            <div v-if="authHeaderName">
              <dt>Header 名称</dt>
              <dd>{{ authHeaderName }}</dd>
            </div>
            <div>
              <dt>凭据状态</dt>
              <dd>{{ detail.auth.hasCredential ? "已配置" : "未配置" }}</dd>
            </div>
          </dl>
        </SectionBlock>

        <SectionBlock title="输入字段映射">
          <dl class="mapping-list">
            <div
              v-for="[key, value] in objectEntries(detail.platformInputMapping)"
              :key="key"
            >
              <dt>{{ key }}</dt>
              <dd>{{ value || "-" }}</dd>
            </div>
          </dl>
        </SectionBlock>

        <SectionBlock title="自定义固定字段">
          <pre class="json-block"><code>{{ prettyJson(detail.customRequestBody) }}</code></pre>
        </SectionBlock>

        <SectionBlock title="输出字段映射">
          <dl class="mapping-list">
            <div
              v-for="[key, value] in objectEntries(detail.platformOutputMapping)"
              :key="key"
            >
              <dt>{{ key }}</dt>
              <dd>{{ value || "-" }}</dd>
            </div>
          </dl>
        </SectionBlock>

        <SectionBlock title="状态集合">
          <dl class="detail-grid">
            <div>
              <dt>终态</dt>
              <dd>{{ detail.terminalStatuses.join("、") }}</dd>
            </div>
            <div>
              <dt>成功态</dt>
              <dd>{{ detail.successStatuses.join("、") }}</dd>
            </div>
          </dl>
        </SectionBlock>

        <SectionBlock title="最近一次验证结果">
          <InlineNotice
            v-if="!detail.lastVerification"
            tone="info"
            message="尚未验证。"
          />
          <div v-else class="verification-result">
            <InlineNotice
              :tone="detail.lastVerification.passed ? 'success' : 'danger'"
              :message="detail.lastVerification.passed ? '验证通过。' : '验证失败。'"
            />
            <ul v-if="verificationMessages.length" class="message-list">
              <li
                v-for="message in verificationMessages"
                :key="`${message.code}-${message.message}`"
              >
                {{ message.message }}
              </li>
            </ul>
          </div>
        </SectionBlock>
      </main>

      <aside class="detail-actions">
        <h2>操作</h2>
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
import AgentStatusTag from "@/modules/agent/components/AgentStatusTag.vue";
import { getInvokeModeLabel } from "@/modules/agent/model/agent-display";
import type {
  AgentAuthType,
  AgentDetail,
  AgentVerificationMessage,
} from "@/shared/types/agent-registry-types";
import { formatDateTimeLabel } from "@/modules/dataset/lib/dataset-utils";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import ConfirmDialog from "@/shared/ui/feedback/ConfirmDialog.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";

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
const verificationMessages = computed<AgentVerificationMessage[]>(() => [
  ...(detail.value?.lastVerification?.warnings ?? []),
  ...(detail.value?.lastVerification?.errors ?? []),
]);

const objectEntries = <T extends object>(value: T): Array<[string, unknown]> =>
  Object.entries(value);

const prettyJson = (value: unknown): string => JSON.stringify(value, null, 2);

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
  grid-template-columns: minmax(0, 1fr) minmax(280px, 320px);
  gap: 1.5rem;
  align-items: start;
}

.detail-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

.detail-grid,
.mapping-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.35rem 1.15rem;
}

.detail-grid div,
.mapping-list div {
  min-width: 0;
  padding: 0.72rem 0;
  border-top: 1px solid var(--color-border-soft);
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    background var(--duration-fast) var(--ease-standard);
}

.detail-grid div:hover,
.mapping-list div:hover {
  border-color: var(--color-border-strong);
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.06), transparent 72%);
}

.detail-grid div:nth-child(-n + 2),
.mapping-list div:nth-child(-n + 2) {
  border-top-color: transparent;
}

.detail-grid dt,
.mapping-list dt {
  color: var(--color-text-subtle);
  font-size: 0.86rem;
}

.detail-grid dd,
.mapping-list dd {
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

.json-block {
  margin: 0;
  padding: 0.95rem;
  border-radius: var(--radius-card-sm);
  background: #0f172a;
  color: #e2e8f0;
  overflow: auto;
  font-size: 0.84rem;
  line-height: 1.6;
  box-shadow: inset 0 0 0 1px rgba(226, 232, 240, 0.08);
}

.verification-result,
.message-list {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.message-list {
  margin: 0;
  padding-left: 1.15rem;
  color: var(--color-text-muted);
  line-height: 1.65;
}

.detail-actions {
  position: sticky;
  top: calc(var(--nav-height) + 1.25rem);
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

.detail-actions h2 {
  margin: 0 0 0.2rem;
  color: var(--color-text-dark);
  font-size: 1.05rem;
}

@media (max-width: 1080px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }

  .detail-actions {
    position: static;
  }
}

@media (max-width: 700px) {
  .detail-grid,
  .mapping-list {
    grid-template-columns: 1fr;
  }

  .detail-grid div:nth-child(-n + 2),
  .mapping-list div:nth-child(-n + 2) {
    border-top-color: var(--color-border-soft);
  }

  .detail-grid div:first-child,
  .mapping-list div:first-child {
    border-top-color: transparent;
  }
}
</style>
