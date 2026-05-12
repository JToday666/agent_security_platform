<template>
  <SectionBlock
    :title="t('submission.method.title')"
    :description="t('submission.method.description')"
  >
    <UiChoiceCardGroup v-model="model" :options="methodOptions" />
  </SectionBlock>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { SubmitMethod } from "@/shared/types/agent-types";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";
import UiChoiceCardGroup from "@/shared/ui/forms/UiChoiceCardGroup.vue";

const props = defineProps<{
  methods: SubmitMethod[];
}>();

const model = defineModel<SubmitMethod>({ required: true });
const { t } = useI18n();

const methodValues: SubmitMethod[] = ["api", "docker"];

const methodOptions = computed(() =>
  methodValues.map((method) => {
    const isDocker = method === "docker";
    const supported = props.methods.includes(method);

    return {
      value: method,
      title: t(`submission.method.options.${method}.title`),
      description: t(`submission.method.options.${method}.description`),
      meta: isDocker
        ? t("submission.method.meta.developing")
        : supported
          ? ""
          : t("submission.method.meta.unavailable"),
      disabled: isDocker || !supported,
    };
  })
);
</script>
