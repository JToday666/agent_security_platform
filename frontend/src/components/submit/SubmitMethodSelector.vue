<template>
  <section class="layout-section-card ui-surface-white">
    <div class="layout-section-head">
      <h2>提交方式 <span class="required-mark">*</span></h2>
      <p>根据当前平台能力选择接入方式，提交前会按照对应字段进行本地校验和预检查。</p>
    </div>

    <div class="grid-auto-fit" style="--grid-min-size: 220px; --grid-gap: 0.9rem; margin-top: 1rem;">
      <button
        v-for="method in methods"
        :key="method"
        type="button"
        class="method-card"
        :class="{ active: model === method }"
        @click="model = method"
      >
        <strong>{{ methodLabels[method].title }}</strong>
        <span>{{ methodLabels[method].description }}</span>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { SubmitMethod } from "@/types/AgentTypes";

defineProps<{
  methods: SubmitMethod[];
}>();

const model = defineModel<SubmitMethod>({ required: true });

const methodLabels: Record<
  SubmitMethod,
  { title: string; description: string }
> = {
  api: {
    title: "API 接入",
    description: "适合已有在线服务与固定访问地址的智能体。",
  },
  docker: {
    title: "Docker 镜像",
    description: "适合通过容器封装部署、需要统一运行环境的智能体。",
  },
};
</script>

<style scoped>
.required-mark {
  color: #dc2626;
}

.method-card {
  border: 1px solid #dbeafe;
  background: #f8fafc;
  border-radius: 1.2rem;
  padding: 1rem 1.05rem;
  text-align: left;
  cursor: pointer;
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    box-shadow 0.18s ease;
}

.method-card strong {
  display: block;
  color: #0f172a;
  font-size: 1rem;
}

.method-card span {
  display: block;
  margin-top: 0.45rem;
  color: #64748b;
  line-height: 1.6;
}

.method-card.active {
  border-color: #2563eb;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.1), rgba(124, 58, 237, 0.08));
  box-shadow: 0 12px 30px -16px rgba(37, 99, 235, 0.6);
}

.method-card:hover {
  transform: translateY(-2px);
}
</style>