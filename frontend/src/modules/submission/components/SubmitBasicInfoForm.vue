<template>
  <SectionCard
    title="智能体信息"
    description="填写智能体名称、简介和接入信息，便于平台识别能力范围并发起评测。"
  >
    <div class="grid-auto-fit">
      <FormField
        label="智能体名称"
        :model-value="form.agentName"
        type="text"
        placeholder="例如：安全卫士 v1.0"
        :error="fieldErrors.agentName"
        :required="true"
        full
        @update:model-value="form.agentName = $event"
      />

      <FormField
        label="智能体描述"
        :model-value="form.description"
        type="textarea"
        placeholder="简要说明智能体定位、核心能力和适用场景。"
        full
        :rows="6"
        @update:model-value="form.description = $event"
      />

      <template v-if="form.submitMethod === 'api'">
        <FormField
          label="API 地址"
          :model-value="form.api.baseUrl"
          type="url"
          placeholder="https://example.com/agent/run"
          :error="fieldErrors.apiBaseUrl"
          :required="true"
          leading-icon="lucide:link"
          full
          @update:model-value="form.api.baseUrl = $event"
        />
        <FormField
          label="API Token"
          :model-value="form.api.token"
          type="password"
          placeholder="仅用于本次接入校验，离开页面后需重新填写"
          leading-icon="lucide:key-round"
          full
          @update:model-value="form.api.token = $event"
        />
      </template>

      <template v-else>
        <FormField
          label="镜像地址"
          :model-value="form.docker.imageUri"
          type="text"
          placeholder="registry.example.com/agent:latest"
          :error="fieldErrors.dockerImageUri"
          :required="true"
          leading-icon="lucide:package"
          full
          @update:model-value="form.docker.imageUri = $event"
        />
        <FormField
          label="镜像仓库用户名"
          :model-value="form.docker.username"
          type="text"
          placeholder="可选"
          leading-icon="lucide:user"
          @update:model-value="form.docker.username = $event"
        />
        <FormField
          label="镜像仓库密码"
          :model-value="form.docker.password"
          type="password"
          placeholder="仅用于当前镜像认证，离开页面后需重新填写"
          leading-icon="lucide:lock"
          @update:model-value="form.docker.password = $event"
        />
      </template>
    </div>
  </SectionCard>
</template>

<script setup lang="ts">
import FormField from "@/shared/ui/forms/FormField.vue";
import SectionCard from "@/shared/ui/page/SectionCard.vue";
import type {
  SubmitFieldErrors,
  SubmitFormState,
} from "@/shared/types/agent-types";

withDefaults(
  defineProps<{
    fieldErrors?: SubmitFieldErrors;
  }>(),
  {
    fieldErrors: () => ({}),
  },
);

const form = defineModel<SubmitFormState>({ required: true });
</script>

<style scoped lang="scss">
.grid-auto-fit {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}
</style>