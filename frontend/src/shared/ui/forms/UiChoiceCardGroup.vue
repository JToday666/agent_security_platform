<template>
  <div class="ui-choice-card-group">
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      class="ui-choice-card-group__item"
      :class="{ 'ui-choice-card-group__item--active': modelValue === option.value }"
      @click="$emit('update:modelValue', option.value)"
    >
      <strong class="ui-choice-card-group__title">{{ option.title }}</strong>
      <span class="ui-choice-card-group__description">{{ option.description }}</span>
    </button>
  </div>
</template>

<script setup lang="ts" generic="T extends string">
defineProps<{
  modelValue: T;
  options: Array<{
    value: T;
    title: string;
    description: string;
  }>;
}>();

defineEmits<{
  (event: "update:modelValue", value: T): void;
}>();
</script>

<style scoped lang="scss">
.ui-choice-card-group {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.9rem;
}

.ui-choice-card-group__item {
  padding: 1rem 1.05rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 1.25rem;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.92));
  text-align: left;
  cursor: pointer;
  transition:
    transform var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard);
}

.ui-choice-card-group__item:hover {
  transform: translateY(-2px);
}

.ui-choice-card-group__item--active {
  border-color: rgba(99, 102, 241, 0.24);
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.1), rgba(124, 58, 237, 0.08));
  box-shadow: 0 18px 30px -20px rgba(79, 70, 229, 0.42);
}

.ui-choice-card-group__title {
  display: block;
  color: var(--color-text-dark);
  font-size: 1rem;
}

.ui-choice-card-group__description {
  display: block;
  margin-top: 0.45rem;
  color: var(--color-text-subtle);
  line-height: 1.65;
}
</style>
