<template>
  <div class="content contact-page layout-page-shell layout-page-shell--compact">
    <section class="contact-hero" aria-labelledby="contact-hero-title">
      <BrandLogo class="contact-logo contact-hero__logo" alt="智能体安全评测平台标识" />
      <h1 id="contact-hero-title" class="contact-hero__title ui-title-gradient">联系我们</h1>
      <p class="contact-hero__description">
        如果您有任何问题、建议或合作想法，欢迎通过以下方式与我们取得联系。
      </p>
    </section>

    <section class="contact-grid contact-grid--quad">
      <article
        v-for="item in contactItems"
        :key="item.title"
        class="contact-item ui-surface-white ui-hover-card"
      >
        <div class="contact-item-head">
          <AppIcon :icon="item.icon" class="icon" />
          <h2>{{ item.title }}</h2>
        </div>

        <div class="info">
          <template v-if="item.type === 'link'">
            <a :href="item.link" class="info-value info-value--single-line">
              {{ item.text }}
            </a>
          </template>

          <template v-else-if="item.type === 'text'">
            <p class="info-value info-value--address">{{ item.text }}</p>
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
                <AppIcon :icon="social.icon" class="social-brand-icon" />
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
import AppIcon from "@/shared/ui/branding/AppIcon.vue";
import BrandLogo from "@/shared/ui/branding/BrandLogo.vue";

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

const contactItems: ContactItem[] = [
  {
    icon: "lucide:mail",
    title: "邮箱",
    type: "link",
    text: "u202312421@hust.edu.com",
    link: "mailto:u202312421@hust.edu.com",
  },
  {
    icon: "lucide:phone",
    title: "电话",
    type: "link",
    text: "+86 13886038599",
    link: "tel:+8613886038599",
  },
  {
    icon: "lucide:map-pin",
    title: "地址",
    type: "text",
    text: "武汉市东西湖区国家网络安全基地",
  },
  {
    icon: "lucide:globe",
    title: "社交媒体",
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
];
</script>

<style scoped lang="scss">
.contact-page {
  padding-bottom: 2.3rem;
}

.contact-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.85rem;
  padding: 0.8rem 0 0.35rem;
  text-align: center;
}

.contact-logo {
  width: clamp(3.8rem, 8vw, 4.4rem);
}

.contact-hero__title {
  margin: 0;
  color: var(--color-text-dark);
  font-size: clamp(1.72rem, 3.45vw, 2.56rem);
  font-weight: 800;
  line-height: 1.06;
  letter-spacing: -0.04em;
  text-wrap: balance;
}

.contact-hero__description {
  width: 100%;
  max-width: none;
  margin: 0;
  color: var(--color-text-muted);
  font-size: 0.98rem;
  line-height: 1.66;
  white-space: nowrap;
}

.contact-grid {
  display: grid;
  gap: 0.85rem;
  margin-top: 1rem;
}

.contact-grid--quad {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.contact-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.72rem;
  min-height: 176px;
  padding: 1.08rem 1rem;
  border-radius: 1.2rem;
  text-align: center;
}

.contact-item-head {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.52rem;
  width: 100%;
}

.contact-item-head h2 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.02rem;
}

.info {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.38rem;
  width: 100%;
}

.icon {
  width: 1.8rem;
  height: 1.8rem;
  color: #4f46e5;
}

.info-value {
  margin: 0;
  color: var(--color-text-subtle);
  text-decoration: none;
  font-size: 0.94rem;
  line-height: 1.62;
  word-break: break-word;
  transition: color var(--duration-fast) var(--ease-standard);
}

.info-value--single-line {
  white-space: nowrap;
}

.info-value--address {
  max-width: 18ch;
  text-wrap: balance;
}

.info a:hover,
.social-link:hover {
  color: var(--color-primary);
}

.social-links {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  flex-wrap: wrap;
  gap: 0.5rem 0.72rem;
}

.social-links a {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.social-brand-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .contact-grid--quad {
    grid-template-columns: 1fr;
  }

  .contact-hero__description,
  .info-value--single-line {
    white-space: normal;
  }
}
</style>
