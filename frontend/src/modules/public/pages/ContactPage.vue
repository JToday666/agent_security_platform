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
          <span class="contact-icon-shell">
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

type ContactItem =
  | {
      icon: string;
      title: string;
      type: "link";
      text: string;
      link: string;
    }
  | {
      icon: string;
      title: string;
      type: "text";
      text: string;
    }
  | {
      icon: string;
      title: string;
      type: "social";
      links: { name: string; icon: string; url: string }[];
    };

const { t } = useI18n();

const contactItems = computed<ContactItem[]>(() => [
  {
    icon: "lucide:mail",
    title: t("public.contact.email"),
    type: "link",
    text: "u202312421@hust.edu.com",
    link: "mailto:u202312421@hust.edu.com",
  },
  {
    icon: "lucide:phone",
    title: t("public.contact.phone"),
    type: "link",
    text: "+86 13886038599",
    link: "tel:+8613886038599",
  },
  {
    icon: "lucide:map-pin",
    title: t("public.contact.address"),
    type: "text",
    text: t("public.contact.addressValue"),
  },
  {
    icon: "lucide:globe",
    title: t("public.contact.social"),
    type: "social",
    links: [
      {
        name: "X",
        icon: "ri:twitter-x-line",
        url: "https://x.com/agent_security_demo",
      },
      {
        name: "GitHub",
        icon: "ri:github-line",
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
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.88), rgba(237, 233, 254, 0.82));
  border: 1px solid rgba(99, 102, 241, 0.12);
  box-shadow: 0 16px 28px -24px rgba(79, 70, 229, 0.28);
}

.icon {
  width: 1.35rem;
  height: 1.35rem;
  color: #4f46e5;
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
  gap: 0.35rem;
}

.social-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.info a:hover,
.social-link:hover {
  color: var(--color-primary);
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
