<template>
  <div class="content contact-page layout-page-shell layout-page-shell--compact">
    <div class="contact-card layout-page-panel ui-surface-glass">
      <div class="contact-header">
        <div class="contact-brand ui-surface-white">
          <BrandLogo class="contact-logo" alt="智能体安全评测平台标志" />
        </div>
        <h1 class="page-title layout-page-title">联系我们</h1>
        <p class="page-subtitle layout-page-subtitle">
          如果您有任何问题或建议，欢迎通过以下方式与我们取得联系。
        </p>
      </div>

      <div class="contact-grid">
        <div
          v-for="item in contactItems"
          :key="item.title"
          class="contact-item ui-surface-white ui-hover-card"
        >
          <AppIcon :icon="item.icon" class="icon" />
          <div class="info" :class="`info--${item.type}`">
            <h3>{{ item.title }}</h3>

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
                <template v-for="(social, index) in item.links" :key="social.name">
                  <a
                    :href="social.url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="info-value info-value--single-line social-link"
                  >
                    <AppIcon :icon="social.icon" class="social-brand-icon" />
                    <span>{{ social.name }}</span>
                  </a>
                  <span
                    v-if="index < item.links.length - 1"
                    class="separator"
                    aria-hidden="true"
                  >
                    ·
                  </span>
                </template>
              </div>
            </template>
          </div>
        </div>
      </div>

      <div class="note">
        <p>我们会在 24 小时内回复您的来信，感谢您的关注与支持。</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import AppIcon from "@/shared/ui/AppIcon.vue";
import BrandLogo from "@/shared/ui/BrandLogo.vue";

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

<style scoped>
.contact-page {
  min-height: calc(100vh - var(--nav-height));
  display: flex;
  align-items: center;
  padding-bottom: 2.5rem;
}

.contact-card {
  border-radius: 2.4rem;
}

.contact-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.8rem;
}

.contact-brand {
  width: fit-content;
  padding: 0.9rem 1.1rem;
  border-radius: 1.5rem;
}

.contact-logo {
  width: clamp(5.75rem, 12vw, 7.5rem);
}

.page-title {
  text-align: center;
}

.page-subtitle {
  margin-bottom: 1.5rem;
  text-align: center;
}

.contact-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.25rem;
  margin: 2rem 0;
}

.contact-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.85rem;
  padding: 1.5rem 1.35rem;
  min-height: 220px;
  text-align: center;
}

.icon {
  width: 2.25rem;
  height: 2.25rem;
  color: #2563eb;
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.05));
}

.info {
  flex: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
}

.info h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
  color: #0f172a;
}

.info-value {
  margin: 0;
  color: #64748b;
  text-decoration: none;
  font-size: 1rem;
  line-height: 1.55;
  text-align: center;
  word-break: break-word;
  transition: color 0.2s ease;
}

.info-value--single-line {
  white-space: nowrap;
}

.info-value--address {
  max-width: 16ch;
  text-wrap: balance;
}

.info a:hover,
.social-link:hover {
  color: #2563eb;
  text-decoration: underline;
}

.social-links {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.35rem;
  width: 100%;
}

.social-links a {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  color: #64748b;
}

.social-links a:hover {
  color: #2563eb;
}

.social-brand-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.separator {
  color: #cbd5e1;
  margin: 0 0.1rem;
}

.note {
  text-align: center;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e2e8f0;
  color: #64748b;
  font-style: italic;
}

@media (max-width: 768px) {
  .contact-page {
    align-items: flex-start;
  }

  .contact-card {
    border-radius: 2rem;
  }

  .contact-grid {
    grid-template-columns: 1fr;
  }

  .contact-item {
    min-height: auto;
    padding: 1.25rem 1.15rem;
  }
}

@media (max-width: 480px) {
  .contact-brand {
    padding: 0.75rem 0.95rem;
  }

  .info-value,
  .info-value--single-line {
    font-size: 0.95rem;
    white-space: normal;
  }
}
</style>