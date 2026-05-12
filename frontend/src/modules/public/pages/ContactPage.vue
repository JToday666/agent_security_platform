<template>
  <div class="content contact-page layout-page-shell layout-page-shell--compact">
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

    <section class="contact-grid contact-grid--quad">
      <article
        v-for="item in contactItems"
        :key="item.title"
        class="contact-item"
      >
        <div class="contact-item__head">
          <span
            class="contact-icon-shell"
            :class="`contact-icon-shell--${item.tone}`"
          >
            <AppIcon :icon="item.icon" class="icon" />
          </span>
          <h2>{{ item.title }}</h2>
        </div>

        <div class="info">
          <template v-if="item.type === 'link'">
            <a :href="item.link" class="info-value info-value--single-line">
              {{ item.text }}
            </a>
          </template>

          <template v-else-if="item.type === 'text'">
            <p class="info-value info-value--address">
              {{ item.text }}
            </p>
          </template>

          <template v-else-if="item.type === 'social'">
            <div class="social-links">
              <a
                v-for="social in item.links"
                :key="social.name"
                :href="social.url"
                target="_blank"
                rel="noopener noreferrer"
                class="info-value info-value--single-line social-link"
                :class="`social-link--${social.tone}`"
              >
                <AppIcon :icon="social.icon" class="social-icon" />
                <span>{{ social.name }}</span>
              </a>
            </div>
          </template>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";
import BrandLogo from "@/shared/ui/branding/BrandLogo.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";
import type { AppIconName } from "@/shared/ui/branding/app-icon-registry";

type ContactItem =
  | {
      icon: AppIconName;
      tone: "email" | "phone" | "address" | "social";
      title: string;
      type: "link";
      text: string;
      link: string;
    }
  | {
      icon: AppIconName;
      tone: "email" | "phone" | "address" | "social";
      title: string;
      type: "text";
      text: string;
    }
  | {
      icon: AppIconName;
      tone: "email" | "phone" | "address" | "social";
      title: string;
      type: "social";
      links: {
        name: string;
        icon: AppIconName;
        tone: "x" | "github";
        url: string;
      }[];
    };

const { t } = useI18n();

const contactItems = computed<ContactItem[]>(() => [
  {
    icon: "app:contact.email",
    tone: "email",
    title: t("public.contact.email"),
    type: "link",
    text: "u202312421@hust.edu.com",
    link: "mailto:u202312421@hust.edu.com",
  },
  {
    icon: "app:contact.phone",
    tone: "phone",
    title: t("public.contact.phone"),
    type: "link",
    text: "+86 13886038599",
    link: "tel:+8613886038599",
  },
  {
    icon: "app:contact.address",
    tone: "address",
    title: t("public.contact.address"),
    type: "text",
    text: t("public.contact.addressValue"),
  },
  {
    icon: "app:contact.social",
    tone: "social",
    title: t("public.contact.social"),
    type: "social",
    links: [
      {
        name: "X",
        icon: "brand:x",
        tone: "x",
        url: "https://x.com/agent_security_demo",
      },
      {
        name: "GitHub",
        icon: "brand:github",
        tone: "github",
        url: "https://github.com/JToday666/agent_security_platform",
      },
    ],
  },
]);
</script>

<style scoped lang="scss">
.contact-page {
  padding-bottom: 2.3rem;
}

.contact-logo {
  width: 4.2rem;
}

.contact-grid {
  display: grid;
  gap: 1rem;
  margin-top: 1rem;
}

.contact-grid--quad {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.contact-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.9rem;
  min-height: 196px;
  padding: 1.35rem 1.1rem;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
  text-align: center;
}

.contact-item__head {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  width: 100%;
}

.contact-item__head h2 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.02rem;
}

.contact-icon-shell {
  width: 3rem;
  height: 3rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 1rem;
  background: var(
    --contact-icon-bg,
    linear-gradient(135deg, rgba(219, 234, 254, 0.88), rgba(237, 233, 254, 0.82))
  );
  border: 1px solid var(--contact-icon-border, rgba(99, 102, 241, 0.12));
  box-shadow: 0 16px 28px -24px var(--contact-icon-shadow, rgba(79, 70, 229, 0.28));
}

.contact-icon-shell--email {
  --contact-icon-bg: linear-gradient(135deg, rgba(219, 234, 254, 0.92), rgba(224, 242, 254, 0.86));
  --contact-icon-border: rgba(37, 99, 235, 0.16);
  --contact-icon-color: #2563eb;
  --contact-icon-shadow: rgba(37, 99, 235, 0.3);
}

.contact-icon-shell--phone {
  --contact-icon-bg: linear-gradient(135deg, rgba(220, 252, 231, 0.9), rgba(204, 251, 241, 0.84));
  --contact-icon-border: rgba(13, 148, 136, 0.16);
  --contact-icon-color: #0f766e;
  --contact-icon-shadow: rgba(13, 148, 136, 0.28);
}

.contact-icon-shell--address {
  --contact-icon-bg: linear-gradient(135deg, rgba(254, 243, 199, 0.9), rgba(255, 237, 213, 0.84));
  --contact-icon-border: rgba(217, 119, 6, 0.16);
  --contact-icon-color: #b45309;
  --contact-icon-shadow: rgba(217, 119, 6, 0.26);
}

.contact-icon-shell--social {
  --contact-icon-bg: linear-gradient(135deg, rgba(237, 233, 254, 0.9), rgba(219, 234, 254, 0.84));
  --contact-icon-border: rgba(99, 102, 241, 0.16);
  --contact-icon-color: #4f46e5;
  --contact-icon-shadow: rgba(79, 70, 229, 0.28);
}

.icon {
  width: 1.35rem;
  height: 1.35rem;
  color: var(--contact-icon-color, #4f46e5);
}

.info {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.42rem;
  width: 100%;
}

.info-value {
  margin: 0;
  color: var(--color-text-subtle);
  text-decoration: none;
  font-size: 0.94rem;
  line-height: 1.62;
  word-break: break-word;
  text-align: center;
  transition: color var(--duration-fast) var(--ease-standard);
}

.info-value--single-line {
  white-space: nowrap;
}

.info-value--address {
  max-width: 18ch;
  text-wrap: balance;
}

.social-links {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 0.5rem 0.72rem;
  width: 100%;
}

.social-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.42rem;
  min-height: 2rem;
  padding: 0.36rem 0.68rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.72);
  color: var(--social-link-color, var(--color-text-muted));
  font-weight: 700;
  box-shadow: 0 10px 22px -22px rgba(15, 23, 42, 0.32);
  transition:
    transform var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    background var(--duration-fast) var(--ease-standard),
    color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard);
}

.social-link--x {
  --social-link-color: #0f172a;
  --social-link-hover-border: rgba(15, 23, 42, 0.18);
}

.social-link--github {
  --social-link-color: #24292f;
  --social-link-hover-border: rgba(36, 41, 47, 0.18);
}

.social-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.info a:hover,
.social-link:hover {
  color: var(--social-link-color, var(--color-primary));
}

.social-link:hover {
  transform: translateY(-1px);
  border-color: var(--social-link-hover-border, rgba(99, 102, 241, 0.2));
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 14px 26px -24px rgba(15, 23, 42, 0.36);
}

@media (max-width: 768px) {
  .contact-grid--quad {
    grid-template-columns: 1fr;
  }

  .info-value--single-line {
    white-space: normal;
  }
}
</style>
