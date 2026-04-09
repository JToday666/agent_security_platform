<template>
  <section class="visibility-card layout-section-card ui-surface-white">
    <div class="copy">
      <h2>排行榜公开设置</h2>
      <p>公开后，该次评测结果可参与排行榜展示；不公开时，仅本人可见。</p>
    </div>
    <label class="toggle-wrap">
      <span>{{ form.publicToLeaderboard ? "公开到排行榜" : "仅本人可见" }}</span>
      <input v-model="form.publicToLeaderboard" type="checkbox" class="toggle-input" />
    </label>
  </section>
</template>

<script setup lang="ts">
import type { SubmitFormState } from "@/shared/types/AgentTypes";

const form = defineModel<SubmitFormState>({ required: true });
</script>

<style scoped>
.visibility-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.copy h2 {
  margin: 0;
  color: #0f172a;
  font-size: 1.22rem;
}

.copy p {
  margin: 0.45rem 0 0;
  color: #64748b;
  line-height: 1.7;
}

.toggle-wrap {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.9rem 1rem;
  border-radius: 999px;
  background: #f8fafc;
  font-weight: 700;
  color: #0f172a;
}

.toggle-input {
  width: 20px;
  height: 20px;
  accent-color: #2563eb;
}

@media (max-width: 768px) {
  .section-card {
    flex-direction: column;
    align-items: stretch;
  }

  .toggle-wrap {
    justify-content: space-between;
  }
}
</style>
