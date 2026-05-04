<template>
  <SectionBlock
    title="提交方式"
    description="选择本次提交使用的接入方式。"
  >
    <UiChoiceCardGroup v-model="model" :options="methodOptions" />
  </SectionBlock>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { SubmitMethod } from "@/shared/types/agent-types";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";
import UiChoiceCardGroup from "@/shared/ui/forms/UiChoiceCardGroup.vue";

const props = defineProps<{
  methods: SubmitMethod[];
}>();

const model = defineModel<SubmitMethod>({ required: true });

const methodLabels: Record<SubmitMethod, { title: string; description: string }> = {
  api: {
    title: "API 接入",
    description: "适用于已经有在线服务的 Agent。",
  },
  docker: {
    title: "Docker 镜像",
    description: "该功能正在开发，当前暂不能创建 Docker 评测。",
  },
};

const methodOptions = computed(() =>
  Object.entries(methodLabels).map(([value, meta]) => {
    const method = value as SubmitMethod;
    const isDocker = method === "docker";
    const supported = props.methods.includes(method);

    return {
      value: method,
      title: meta.title,
      description: meta.description,
      meta: isDocker ? "开发中" : supported ? "" : "暂不可用",
      disabled: isDocker || !supported,
    };
  })
);
</script>
