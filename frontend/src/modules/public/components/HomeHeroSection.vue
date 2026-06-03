<template>
  <section class="hero-stage" aria-labelledby="home-hero-title">
    <div class="hero-shell">
      <BrandLogo
        class="hero-logo"
        :alt="t('common.brand.logoAlt')"
        :priority="true"
      />

      <h1 id="home-hero-title" class="hero-title ui-title-gradient">
        {{ displayedTitle }}
      </h1>

      <p class="hero-description">
        <span>{{ displayedDescriptionPrimary }}</span>
        <span>{{ displayedDescriptionSecondary }}</span>
      </p>

      <div class="hero-actions">
        <UiButton
          :to="RouteLocation.attackScenarioLibrary"
          variant="primary"
          size="lg"
          leading-icon="app:action.browseAttackScenarioLibrary"
        >
          {{ t("common.actions.browseAttackScenarioLibrary") }}
        </UiButton>
        <UiButton
          v-if="isLogin"
          :to="RouteLocation.agentSubmit"
          variant="primary"
          size="lg"
          leading-icon="app:action.submitEvaluation"
        >
          {{ t("common.actions.submitEvaluation") }}
        </UiButton>
        <UiButton
          v-else
          variant="primary"
          size="lg"
          leading-icon="app:action.login"
          @click="$emit('login')"
        >
          {{ t("common.actions.loginRegister") }}
        </UiButton>
        <UiButton
          :to="isLogin ? RouteLocation.userCenter : RouteLocation.contact"
          variant="primary"
          size="lg"
          :leading-icon="
            isLogin ? 'app:action.viewRecords' : 'app:action.contactUs'
          "
        >
          {{
            isLogin
              ? t("common.actions.viewRecords")
              : t("common.actions.contactUs")
          }}
        </UiButton>
      </div>
    </div>

    <HomeSectionJump
      :id="quickstartJumpId"
      variant="hero"
      :title="quickstartJump.title"
      :description="quickstartJump.description"
      :controls="quickstartContentId"
      :jump-aria-label="quickstartJumpAriaLabel"
      @activate="$emit('jump')"
    />
  </section>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { RouteLocation } from "@/app/router/route-names";
import type { HomeSectionJumpConfig } from "@/modules/public/model/home-page-types";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import BrandLogo from "@/shared/ui/branding/BrandLogo.vue";
import HomeSectionJump from "./HomeSectionJump.vue";

defineEmits<{
  login: [];
  jump: [];
}>();

defineProps<{
  displayedTitle: string;
  displayedDescriptionPrimary: string;
  displayedDescriptionSecondary: string;
  isLogin: boolean;
  quickstartJump: HomeSectionJumpConfig;
  quickstartContentId: string;
  quickstartJumpId: string;
  quickstartJumpAriaLabel: string;
}>();

const { t } = useI18n();
</script>

<style scoped lang="scss">
.hero-stage {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-width: 0;
  min-height: calc(100dvh - var(--nav-height) - 1rem);
  padding: 3.6rem 0 1.5rem;
  isolation: isolate;
}

.hero-shell {
  position: relative;
  z-index: 1;
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.15rem;
  min-width: 0;
  text-align: center;
}

.hero-logo {
  width: 5rem;
  flex-shrink: 0;
  filter: drop-shadow(0 12px 28px rgba(79, 70, 229, 0.14));
}

.hero-title {
  margin: 0;
  min-height: 1.22em;
  padding-block: 0.08em 0.12em;
  font-size: 5.25rem;
  line-height: 1.02;
  letter-spacing: 0;
  text-wrap: balance;
  overflow-wrap: anywhere;
}

.hero-title.ui-title-gradient {
  text-shadow: 0 10px 24px rgba(99, 102, 241, 0.12);
}

.hero-description {
  display: flex;
  flex-direction: column;
  gap: 0.18rem;
  min-height: 3.74em;
  max-width: min(72ch, 760px);
  margin: 0 auto;
  color: rgba(71, 85, 105, 0.96);
  font-size: 1.08rem;
  font-weight: 500;
  line-height: 1.68;
  text-align: center;
  overflow-wrap: anywhere;
}

.hero-description span {
  display: block;
  min-height: 1.68em;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.95rem;
  min-width: 0;
  margin-top: 0.35rem;
}

.hero-actions :deep(.ui-button) {
  min-width: 166px;
  min-height: 3.5rem;
}

.hero-actions :deep(.ui-button--primary) {
  padding-inline: 1.5rem;
  border-color: rgba(255, 255, 255, 0.2);
  background: linear-gradient(135deg, #2e6fff 0%, #3d6af3 54%, #5a4cf4 100%);
  box-shadow: 0 22px 40px -24px rgba(59, 103, 245, 0.52);
}

.hero-actions :deep(.ui-button--primary:hover:not(.ui-button--disabled)) {
  box-shadow:
    0 26px 46px -24px rgba(59, 103, 245, 0.56),
    0 0 0 1px rgba(255, 255, 255, 0.2) inset;
}

.hero-actions :deep(.ui-button__content) {
  white-space: normal;
}

@media (max-width: 1080px) {
  .hero-description {
    max-width: min(64ch, 100%);
  }
}

@media (max-width: 768px) {
  .hero-stage {
    min-height: auto;
    padding-top: 2.25rem;
  }

  .hero-title {
    min-height: 1.18em;
    font-size: 3rem;
  }

  .hero-description {
    max-width: 34ch;
    min-height: 4.8em;
    line-height: 1.58;
  }

  .hero-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .hero-actions :deep(.ui-button) {
    width: 100%;
  }
}

@media (max-width: 420px) {
  .hero-title {
    font-size: 2.55rem;
  }

  .hero-description {
    max-width: 100%;
  }
}
</style>
