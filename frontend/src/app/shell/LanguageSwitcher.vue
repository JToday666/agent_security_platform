<template>
  <div
    ref="switcherRoot"
    class="language-switcher"
    :class="`language-switcher--${variant}`"
  >
    <button
      class="language-switcher__trigger"
      type="button"
      aria-haspopup="menu"
      :aria-expanded="open ? 'true' : 'false'"
      :aria-label="buttonLabel"
      :title="buttonLabel"
      :disabled="Boolean(switchingLocale)"
      @click="toggleMenu"
    >
      <AppIcon icon="app:control.language" class="language-switcher__icon" />
      <span class="language-switcher__text">
        <span class="language-switcher__trigger-label">
          {{ t("layout.language.trigger") }}
        </span>
      </span>
      <AppIcon
        icon="app:control.expand"
        class="language-switcher__chevron"
        :class="{ 'is-open': open }"
      />
    </button>

    <Transition name="fade-slide-y">
      <div
        v-if="open"
        class="language-switcher__menu"
        role="menu"
        :aria-label="t('layout.language.trigger')"
      >
        <button
          v-for="option in LANGUAGE_OPTIONS"
          :key="option.locale"
          class="language-switcher__option"
          :class="{ 'is-current': option.locale === currentLocale }"
          type="button"
          role="menuitem"
          :aria-current="option.locale === currentLocale ? 'true' : undefined"
          :disabled="switchingLocale === option.locale"
          @click="selectLocale(option.locale)"
        >
          <span class="language-switcher__option-label">
            {{ option.nativeLabel }}
          </span>
          <AppIcon
            v-if="option.locale === currentLocale"
            icon="app:action.select"
            class="language-switcher__check"
          />
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter } from "vue-router";
import {
  normalizeLocale,
  switchLocale,
  type SupportedLocale,
} from "@/app/i18n";
import { LANGUAGE_OPTIONS } from "@/app/shell/language-switcher";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";

withDefaults(
  defineProps<{
    variant?: "desktop" | "mobile";
  }>(),
  {
    variant: "desktop",
  },
);

const emit = defineEmits<{
  (event: "selected"): void;
}>();

const route = useRoute();
const router = useRouter();
const { locale, t } = useI18n();

const open = ref(false);
const switchingLocale = ref<SupportedLocale | null>(null);
const switcherRoot = ref<HTMLElement | null>(null);

const currentLocale = computed(() => normalizeLocale(locale.value));
const buttonLabel = computed(() => t("layout.language.trigger"));

const closeMenu = () => {
  open.value = false;
};

const toggleMenu = () => {
  if (switchingLocale.value) {
    return;
  }

  open.value = !open.value;
};

const selectLocale = async (targetLocale: SupportedLocale) => {
  if (switchingLocale.value) {
    return;
  }

  if (targetLocale === currentLocale.value) {
    closeMenu();
    emit("selected");
    return;
  }

  switchingLocale.value = targetLocale;

  try {
    await switchLocale(router, route, targetLocale);
    closeMenu();
    emit("selected");
  } finally {
    switchingLocale.value = null;
  }
};

const handleDocumentClick = (event: MouseEvent) => {
  if (!switcherRoot.value?.contains(event.target as Node)) {
    closeMenu();
  }
};

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === "Escape") {
    closeMenu();
  }
};

watch(
  () => route.fullPath,
  () => closeMenu(),
);

onMounted(() => {
  document.addEventListener("click", handleDocumentClick);
  document.addEventListener("keydown", handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener("click", handleDocumentClick);
  document.removeEventListener("keydown", handleKeydown);
});
</script>

<style scoped lang="scss">
.language-switcher {
  position: relative;
  min-width: 0;
}

.language-switcher__trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.42rem;
  width: fit-content;
  max-width: 8.4rem;
  min-width: 0;
  min-height: 2.6rem;
  padding: 0.46rem 0.68rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: var(--radius-pill);
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.9),
    rgba(255, 255, 255, 0.76)
  );
  box-shadow: 0 16px 30px -28px rgba(15, 23, 42, 0.16);
  color: #334155;
  cursor: pointer;
  font-size: 0.86rem;
  font-weight: 700;
  line-height: 1.2;
  transition:
    transform var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    background var(--duration-fast) var(--ease-standard),
    color var(--duration-fast) var(--ease-standard);
}

.language-switcher__trigger:hover:not(:disabled),
.language-switcher__trigger:focus-visible {
  border-color: rgba(99, 102, 241, 0.22);
  background: rgba(255, 255, 255, 0.94);
  color: var(--color-primary);
  transform: translateY(-1px);
}

.language-switcher__trigger:disabled {
  cursor: wait;
  opacity: 0.72;
}

.language-switcher__icon,
.language-switcher__chevron,
.language-switcher__check {
  flex: 0 0 auto;
  width: 0.98rem;
  height: 0.98rem;
}

.language-switcher__chevron {
  transition: transform var(--duration-base) var(--ease-standard);
}

.language-switcher__chevron.is-open {
  transform: rotate(180deg);
}

.language-switcher__text {
  display: inline-flex;
  min-width: 0;
  align-items: center;
  gap: 0.26rem;
}

.language-switcher__trigger-label,
.language-switcher__option-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.language-switcher__menu {
  position: absolute;
  top: calc(100% + 0.55rem);
  right: 0;
  z-index: calc(var(--z-nav) + 1);
  display: flex;
  width: max-content;
  min-width: 10.8rem;
  max-width: min(18rem, calc(100vw - 2rem));
  flex-direction: column;
  gap: 0.18rem;
  padding: 0.46rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: var(--radius-card-sm);
  background: rgba(255, 255, 255, 0.97);
  box-shadow: 0 24px 44px -28px rgba(15, 23, 42, 0.28);
  backdrop-filter: blur(var(--blur-10));
}

.language-switcher__option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  min-width: 0;
  padding: 0.68rem 0.72rem;
  border: 0;
  border-radius: 0.85rem;
  background: transparent;
  color: #334155;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 650;
  text-align: left;
}

.language-switcher__option:hover,
.language-switcher__option:focus-visible,
.language-switcher__option.is-current {
  background: rgba(219, 234, 254, 0.66);
  color: var(--color-primary);
}

.language-switcher__option:disabled {
  cursor: wait;
  opacity: 0.72;
}

.language-switcher__check {
  color: var(--color-primary);
}

.language-switcher--mobile {
  width: 100%;
}

.language-switcher--mobile .language-switcher__trigger {
  justify-content: space-between;
  width: 100%;
  max-width: none;
  min-height: 3.2rem;
  padding: 0.82rem 1rem;
  border-radius: 1.1rem;
  background: rgba(255, 255, 255, 0.92);
  text-align: left;
}

.language-switcher--mobile .language-switcher__text {
  flex: 1;
  justify-content: flex-start;
}

.language-switcher--mobile .language-switcher__menu {
  position: static;
  width: 100%;
  min-width: 0;
  max-width: 100%;
  margin-top: 0.52rem;
}

@media (max-width: 1180px) {
  .language-switcher--desktop .language-switcher__trigger {
    max-width: 7.6rem;
    padding-inline: 0.58rem;
  }
}
</style>
