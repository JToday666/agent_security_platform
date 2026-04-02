<template>
  <SubmitSection
    title="智能体信息"
    description="基础信息和提交通道字段都会在正式提交前经过本地校验和 mock 预检查。"
  >
    <div class="grid-auto-fit">
      <FormField
        label="智能体名称"
        :model-value="form.agentName"
        type="text"
        placeholder="例如：安全卫士 v1.0"
        full-width
        @update:model-value="form.agentName = $event"
      />

      <FormField
        label="智能体描述"
        :model-value="form.description"
        type="textarea"
        placeholder="简要说明智能体定位、核心能力和适用场景。"
        full-width
        :rows="6"
        @update:model-value="form.description = $event"
      />

      <template v-if="form.submitMethod === 'api'">
        <FormField
          label="API 地址"
          :model-value="form.api.baseUrl"
          type="url"
          placeholder="https://example.com/agent/run"
          full-width
          @update:model-value="form.api.baseUrl = $event"
        />
        <FormField
          label="API Token"
          :model-value="form.api.token"
          type="password"
          placeholder="仅保存在当前页面内存，不会持久化"
          full-width
          @update:model-value="form.api.token = $event"
        />
      </template>

      <template v-else>
        <FormField
          label="镜像地址"
          :model-value="form.docker.imageUri"
          type="text"
          placeholder="registry.example.com/agent:latest"
          full-width
          @update:model-value="form.docker.imageUri = $event"
        />
        <FormField
          label="镜像仓库用户名"
          :model-value="form.docker.username"
          type="text"
          placeholder="可选"
          @update:model-value="form.docker.username = $event"
        />
        <FormField
          label="镜像仓库密码"
          :model-value="form.docker.password"
          type="password"
          placeholder="仅保存在当前页面内存"
          @update:model-value="form.docker.password = $event"
        />
      </template>
    </div>
  </SubmitSection>
</template>

<script setup lang="ts">
import SubmitSection from "./SubmitSection.vue";
import FormField from "@/components/common/FormField.vue";
import type { SubmitFormState } from "@/types/AgentTypes";

const form = defineModel<SubmitFormState>({ required: true });
</script>

<style scoped>
.grid-auto-fit {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  margin-top: 1rem;
}

:deep(.form-field-full-width) {
  grid-column: 1 / -1;
}
</style>
