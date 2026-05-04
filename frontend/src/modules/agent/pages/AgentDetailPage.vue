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
        <AgentDetailSummary :detail="detail" :items="summaryItems" />
        <AgentConnectionPanel
          :connection-items="connectionItems"
          :auth-items="authItems"
          :status-items="statusItems"
          :custom-request-body-json="customRequestBodyJson"
        />
        <AgentMappingPanel
          :input-items="inputMappingItems"
          :output-items="outputMappingItems"
        />
        <AgentVerificationPanel
          :detail="detail"
          :result-icon="verificationResultIcon"
          :result-label="verificationResultLabel"
          :stat-items="verificationStatItems"
          :message-groups="verificationMessageGroups"
        />
      </main>

      <AgentDetailActionsPanel
        :detail="detail"
        :verification-label="verificationLabel"
        :busy="busy"
        :busy-action="busyAction"
        :action-error="actionError"
        @verify="handleVerify"
        @archive="archiveDialogVisible = true"
      />
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
import { RouteLocation } from "@/app/router/route-names";
import AgentConnectionPanel from "@/modules/agent/components/AgentConnectionPanel.vue";
import AgentDetailActionsPanel from "@/modules/agent/components/AgentDetailActionsPanel.vue";
import AgentDetailSummary from "@/modules/agent/components/AgentDetailSummary.vue";
import AgentMappingPanel from "@/modules/agent/components/AgentMappingPanel.vue";
import AgentVerificationPanel from "@/modules/agent/components/AgentVerificationPanel.vue";
import { useAgentDetailPage } from "@/modules/agent/composables/useAgentDetailPage";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import ConfirmDialog from "@/shared/ui/feedback/ConfirmDialog.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";

const {
  detail,
  loading,
  error,
  actionError,
  busyAction,
  archiveDialogVisible,
  busy,
  verificationLabel,
  verificationResultLabel,
  verificationResultIcon,
  summaryItems,
  connectionItems,
  authItems,
  inputMappingItems,
  outputMappingItems,
  statusItems,
  customRequestBodyJson,
  verificationStatItems,
  verificationMessageGroups,
  loadDetail,
  handleVerify,
  handleArchive,
} = useAgentDetailPage();
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

@media (max-width: 1080px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }
}
</style>
