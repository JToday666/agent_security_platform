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
    description: "适用于已经有在线服务的智能体。",
  },
  docker: {
    title: "Docker 镜像",
    description: "适用于通过镜像部署的智能体。",
  },
};

const methodOptions = computed(() =>
  Object.entries(methodLabels)
    .filter(([value]) => props.methods.includes(value as SubmitMethod))
    .map(([value, meta]) => ({
      value: value as SubmitMethod,
      title: meta.title,
      description: meta.description,
    }))
);
</script>
