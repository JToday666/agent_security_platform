<template>
  <section class="detail-section">
    <div class="section-head">
      <div>
        <h2>基础信息</h2>
        <p>提交、数据集和运行参数。</p>
      </div>
    </div>

    <div class="detail-groups">
      <section v-for="group in groups" :key="group.title" class="detail-group">
        <div class="detail-group__title">
          <AppIcon :icon="group.icon" />
          <h3>{{ group.title }}</h3>
        </div>
        <dl>
          <div v-for="item in group.items" :key="item.label">
            <dt>{{ item.label }}</dt>
            <dd :title="item.value">{{ item.value }}</dd>
          </div>
        </dl>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { EvaluationDetailGroup } from "@/modules/evaluation/lib/evaluation-detail-view";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";

defineProps<{
  groups: EvaluationDetailGroup[];
}>();
</script>

<style scoped lang="scss">
.detail-section {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding-top: 1.65rem;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
}

.detail-section::before {
  position: absolute;
  top: -1px;
  left: 0;
  width: 8rem;
  height: 1px;
  background: linear-gradient(90deg, #2563eb, rgba(37, 99, 235, 0));
  content: "";
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.section-head h2 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.18rem;
}

.section-head p {
  margin: 0.35rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.68;
}

.detail-groups {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1.2rem;
}

.detail-group {
  min-width: 0;
  padding-top: 0.95rem;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.detail-group__title {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  color: var(--color-primary);
}

.detail-group__title h3 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1rem;
}

.detail-group dl {
  margin: 0.55rem 0 0;
}

.detail-group dl div {
  min-width: 0;
  padding: 0.75rem 0.85rem 0.75rem 0;
  border-top: 1px solid rgba(148, 163, 184, 0.13);
}

.detail-group dt {
  color: var(--color-text-subtle);
  font-size: 0.8rem;
  font-weight: 800;
}

.detail-group dd {
  margin: 0.34rem 0 0;
  overflow-wrap: anywhere;
  color: var(--color-text-dark);
  font-weight: 800;
  line-height: 1.42;
}

@media (max-width: 1180px) {
  .detail-groups {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 860px) {
  .detail-groups {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .section-head {
    flex-direction: column;
  }
}
</style>
