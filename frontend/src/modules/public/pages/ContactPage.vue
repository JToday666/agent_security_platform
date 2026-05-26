<template>
  <div class="content contact-page layout-page-shell layout-page-shell--wide">
    <PageHero
      :title="t('public.contact.title')"
      :description="t('public.contact.description')"
      align="center"
      description-wrap="single-line"
    >
      <template #prefix>
        <BrandLogo class="contact-logo" :alt="t('public.contact.logoAlt')" />
      </template>
    </PageHero>

    <section class="contact-overview" :aria-labelledby="primaryTitleId">
      <article class="contact-panel">
        <div class="contact-panel__copy">
          <p class="contact-panel__kicker">
            {{ t("public.contact.primary.kicker") }}
          </p>
          <h2 :id="primaryTitleId">{{ t("public.contact.primary.title") }}</h2>
          <p>{{ t("public.contact.primary.description") }}</p>
          <div class="contact-panel__actions">
            <UiButton
              class="contact-action-button"
              :href="emailHref"
              variant="secondary"
              size="md"
              leading-icon="app:contact.email"
            >
              {{ t("public.contact.primary.emailAction") }}
            </UiButton>
            <UiButton
              class="contact-action-button"
              :href="phoneHref"
              variant="secondary"
              size="md"
              leading-icon="app:contact.phone"
            >
              {{ t("public.contact.primary.phoneAction") }}
            </UiButton>
          </div>
        </div>

        <dl class="contact-channel-list">
          <div
            v-for="channel in contactChannels"
            :key="channel.key"
            class="contact-channel"
            :class="`contact-channel--${channel.tone}`"
          >
            <dt>
              <span class="contact-icon-shell">
                <AppIcon :icon="channel.icon" />
              </span>
              <span>{{ channel.label }}</span>
            </dt>
            <dd>
              <template v-if="channel.type === 'link'">
                <a :href="channel.href" class="contact-value">
                  {{ channel.value }}
                </a>
              </template>
              <template v-else-if="channel.type === 'text'">
                <span class="contact-value">{{ channel.value }}</span>
              </template>
              <template v-else>
                <span class="contact-social-links">
                  <a
                    v-for="social in channel.links"
                    :key="social.name"
                    :href="social.url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="contact-social-link"
                  >
                    <AppIcon :icon="social.icon" />
                    <span>{{ social.name }}</span>
                  </a>
                </span>
              </template>
            </dd>
          </div>
        </dl>
      </article>
    </section>

    <section class="contact-paths">
      <div class="contact-path-list">
        <article
          v-for="path in contactPaths"
          :key="path.key"
          class="contact-path-item"
          :class="`contact-path-item--${path.tone}`"
        >
          <span class="contact-path-item__icon">
            <AppIcon :icon="path.icon" />
          </span>
          <h3>{{ path.title }}</h3>
          <p>{{ path.description }}</p>
          <UiButton
            v-if="path.kind === 'route'"
            :to="path.to"
            variant="text"
            size="sm"
          >
            {{ path.actionLabel }}
          </UiButton>
          <UiButton
            v-else
            :href="path.href"
            :target="path.target"
            :rel="path.rel"
            variant="text"
            size="sm"
          >
            {{ path.actionLabel }}
          </UiButton>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { RouteLocationRaw } from "vue-router";
import { useI18n } from "vue-i18n";
import { RouteLocation } from "@/app/router/route-names";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";
import BrandLogo from "@/shared/ui/branding/BrandLogo.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";
import type { AppIconName } from "@/shared/ui/branding/app-icon-registry";

const CONTACT_EMAIL = "u202312421@hust.edu.com";
const CONTACT_PHONE_TEXT = "+86 13886038599";
const CONTACT_PHONE_NUMBER = "+8613886038599";
const GITHUB_URL = "https://github.com/JToday666/agent_security_platform";
const X_URL = "https://x.com/agent_security_demo";

type ContactTone = "email" | "phone" | "address" | "social";
type ContactPathTone = "integration" | "datasets" | "collaboration" | "social";

interface ContactSocialLink {
  name: string;
  icon: AppIconName;
  url: string;
}

type ContactChannel =
  | {
      key: string;
      icon: AppIconName;
      tone: ContactTone;
      label: string;
      type: "link";
      value: string;
      href: string;
    }
  | {
      key: string;
      icon: AppIconName;
      tone: ContactTone;
      label: string;
      type: "text";
      value: string;
    }
  | {
      key: string;
      icon: AppIconName;
      tone: ContactTone;
      label: string;
      type: "social";
      links: ContactSocialLink[];
    };

interface ContactPathBase {
  key: string;
  icon: AppIconName;
  tone: ContactPathTone;
  title: string;
  description: string;
  actionLabel: string;
}

type ContactPath =
  | (ContactPathBase & {
      kind: "link";
      href: string;
      target?: string;
      rel?: string;
    })
  | (ContactPathBase & {
      kind: "route";
      to: RouteLocationRaw;
    });

const { t } = useI18n();

const primaryTitleId = "contact-primary-title";
const emailHref = `mailto:${CONTACT_EMAIL}`;
const phoneHref = `tel:${CONTACT_PHONE_NUMBER}`;

const contactChannels = computed<ContactChannel[]>(() => [
  {
    key: "email",
    icon: "app:contact.email",
    tone: "email",
    label: t("public.contact.email"),
    type: "link",
    value: CONTACT_EMAIL,
    href: emailHref,
  },
  {
    key: "phone",
    icon: "app:contact.phone",
    tone: "phone",
    label: t("public.contact.phone"),
    type: "link",
    value: CONTACT_PHONE_TEXT,
    href: phoneHref,
  },
  {
    key: "address",
    icon: "app:contact.address",
    tone: "address",
    label: t("public.contact.address"),
    type: "text",
    value: t("public.contact.addressValue"),
  },
  {
    key: "social",
    icon: "app:contact.social",
    tone: "social",
    label: t("public.contact.social"),
    type: "social",
    links: [
      {
        name: "GitHub",
        icon: "brand:github",
        url: GITHUB_URL,
      },
      {
        name: "X",
        icon: "brand:x",
        url: X_URL,
      },
    ],
  },
]);

const contactPaths = computed<ContactPath[]>(() => [
  {
    key: "integration",
    kind: "link",
    icon: "app:home.section.evaluation",
    tone: "integration",
    title: t("public.contact.paths.items.integration.title"),
    description: t("public.contact.paths.items.integration.description"),
    actionLabel: t("public.contact.paths.items.integration.action"),
    href: emailHref,
  },
  {
    key: "datasets",
    kind: "route",
    icon: "app:home.section.dataset",
    tone: "datasets",
    title: t("public.contact.paths.items.datasets.title"),
    description: t("public.contact.paths.items.datasets.description"),
    actionLabel: t("public.contact.paths.items.datasets.action"),
    to: RouteLocation.datasetList,
  },
  {
    key: "collaboration",
    kind: "link",
    icon: "app:action.contactUs",
    tone: "collaboration",
    title: t("public.contact.paths.items.collaboration.title"),
    description: t("public.contact.paths.items.collaboration.description"),
    actionLabel: t("public.contact.paths.items.collaboration.action"),
    href: emailHref,
  },
  {
    key: "social",
    kind: "link",
    icon: "brand:github",
    tone: "social",
    title: t("public.contact.paths.items.social.title"),
    description: t("public.contact.paths.items.social.description"),
    actionLabel: t("public.contact.paths.items.social.action"),
    href: GITHUB_URL,
    target: "_blank",
    rel: "noopener noreferrer",
  },
]);
</script>

<style scoped lang="scss">
.contact-page {
  padding-bottom: 2.6rem;
}

.contact-logo {
  width: 4.2rem;
}

.contact-overview,
.contact-paths {
  min-width: 0;
}

.contact-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
  gap: clamp(1.4rem, 4vw, 3rem);
  min-width: 0;
  padding-block: clamp(0.4rem, 2vw, 1rem) clamp(1.2rem, 3vw, 2rem);
}

.contact-panel__copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  justify-content: center;
  gap: 0.85rem;
}

.contact-panel__kicker {
  margin: 0;
  color: var(--color-primary);
  font-size: 0.78rem;
  font-weight: 850;
  letter-spacing: 0;
}

.contact-panel__copy h2 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 2.45rem;
  line-height: 1.15;
  letter-spacing: 0;
  overflow-wrap: anywhere;
}

.contact-panel__copy p:last-of-type {
  margin: 0;
  max-width: 58ch;
  color: var(--color-text-muted);
  font-size: 1rem;
  line-height: 1.72;
  overflow-wrap: anywhere;
}

.contact-panel__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  min-width: 0;
  margin-top: 0.35rem;
}

.contact-action-button {
  border-color: rgba(148, 163, 184, 0.22);
  background: rgba(255, 255, 255, 0.92);
  color: var(--color-text-dark);
  box-shadow: 0 12px 26px -24px rgba(15, 23, 42, 0.32);
}

.contact-action-button:hover:not(.ui-button--disabled) {
  border-color: rgba(37, 99, 235, 0.26);
  background: var(--color-white);
  color: var(--color-primary);
  box-shadow: var(--shadow-surface-soft);
}

.contact-action-button:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus-primary);
}

.contact-channel-list {
  display: grid;
  min-width: 0;
  margin: 0;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
}

.contact-channel {
  display: grid;
  grid-template-columns: minmax(8rem, 0.42fr) minmax(0, 0.58fr);
  gap: 1rem;
  min-width: 0;
  padding: 1rem;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
}

.contact-channel:first-child {
  border-top-color: transparent;
}

.contact-channel dt,
.contact-channel dd {
  min-width: 0;
}

.contact-channel dt {
  display: flex;
  align-items: center;
  gap: 0.62rem;
  color: var(--color-text-dark);
  font-weight: 800;
}

.contact-channel dd {
  display: flex;
  align-items: center;
  margin: 0;
  color: var(--color-text-muted);
  line-height: 1.6;
}

.contact-icon-shell,
.contact-path-item__icon {
  display: inline-flex;
  width: 2.4rem;
  height: 2.4rem;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--contact-tone-border, rgba(37, 99, 235, 0.16));
  border-radius: var(--radius-control-sm);
  background: var(--contact-tone-bg, rgba(219, 234, 254, 0.58));
  color: var(--contact-tone-color, var(--color-primary));
}

.contact-channel--phone,
.contact-path-item--datasets {
  --contact-tone-bg: rgba(204, 251, 241, 0.58);
  --contact-tone-border: rgba(13, 148, 136, 0.18);
  --contact-tone-color: #0f766e;
}

.contact-channel--address,
.contact-path-item--collaboration {
  --contact-tone-bg: rgba(254, 243, 199, 0.62);
  --contact-tone-border: rgba(217, 119, 6, 0.2);
  --contact-tone-color: #b45309;
}

.contact-channel--social,
.contact-path-item--social {
  --contact-tone-bg: rgba(237, 233, 254, 0.66);
  --contact-tone-border: rgba(99, 102, 241, 0.2);
  --contact-tone-color: #4f46e5;
}

.contact-value,
.contact-social-link {
  min-width: 0;
  color: inherit;
  text-decoration: none;
  overflow-wrap: anywhere;
  transition: color var(--duration-fast) var(--ease-standard);
}

.contact-value:hover,
.contact-social-link:hover {
  color: var(--color-primary);
}

.contact-social-links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  min-width: 0;
}

.contact-social-link {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 800;
}

.contact-social-link :deep(svg) {
  width: 1rem;
  height: 1rem;
}

.contact-paths {
  margin-top: clamp(1.8rem, 5vw, 3.6rem);
}

.contact-path-list {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  min-width: 0;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
}

.contact-path-item {
  display: flex;
  min-width: 0;
  min-height: 13.5rem;
  flex-direction: column;
  gap: 0.72rem;
  padding: 1.15rem 1.1rem 1.15rem 0;
  border-left: 1px solid rgba(148, 163, 184, 0.18);
}

.contact-path-item:first-child {
  border-left: 0;
}

.contact-path-item h3 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.04rem;
  line-height: 1.42;
  overflow-wrap: anywhere;
}

.contact-path-item p {
  margin: 0;
  flex: 1;
  color: var(--color-text-muted);
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.contact-path-item :deep(.ui-button) {
  align-self: flex-start;
}

@media (min-width: 1181px) and (min-height: 760px) {
  .contact-page {
    padding-top: 0.95rem;
    padding-bottom: 1.35rem;
  }

  .contact-page :deep(.page-hero) {
    gap: 0.4rem;
    margin-bottom: clamp(1rem, 2.4vh, 1.45rem);
  }

  .contact-page :deep(.page-hero__title) {
    font-size: 2.7rem;
  }

  .contact-page :deep(.page-hero__description) {
    margin-top: 0.42rem;
    line-height: 1.55;
  }

  .contact-logo {
    width: 3.7rem;
  }

  .contact-panel {
    gap: clamp(1.2rem, 3vw, 2.4rem);
    padding-block: 0.15rem 0.8rem;
  }

  .contact-panel__copy {
    gap: 0.68rem;
  }

  .contact-panel__copy h2 {
    font-size: 2.18rem;
  }

  .contact-panel__copy p:last-of-type {
    line-height: 1.6;
  }

  .contact-channel {
    padding: 0.78rem 1rem;
  }

  .contact-paths {
    margin-top: clamp(1rem, 3vh, 2rem);
  }

  .contact-path-item {
    min-height: 10.9rem;
    gap: 0.55rem;
    padding: 0.95rem 1rem 0.95rem 0;
  }

  .contact-path-item p {
    line-height: 1.58;
  }
}

@media (max-width: 1080px) {
  .contact-panel {
    grid-template-columns: 1fr;
  }

  .contact-path-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .contact-path-item:nth-child(2n + 1) {
    border-left: 0;
  }
}

@media (max-width: 768px) {
  .contact-panel__copy h2 {
    font-size: 1.85rem;
  }

  .contact-panel__actions,
  .contact-panel__actions :deep(.ui-button) {
    width: 100%;
  }

  .contact-channel {
    grid-template-columns: 1fr;
    gap: 0.45rem;
  }

  .contact-path-list {
    grid-template-columns: 1fr;
  }

  .contact-path-item {
    min-height: auto;
    padding-right: 0;
    border-left: 0;
    border-top: 1px solid rgba(148, 163, 184, 0.18);
  }

  .contact-path-item:first-child {
    border-top: 0;
  }
}
</style>
