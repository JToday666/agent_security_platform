<template>
  <Navbar />
  <main class="page-container contact-page">
    <div class="content">
      <div class="contact-card">
        <h1 class="page-title">联系我们</h1>
        <p class="page-subtitle">如果您有任何问题或建议，欢迎通过以下方式与我们取得联系。</p>

        <div class="contact-grid">
          <div class="contact-item">
            <span class="icon">📧</span>
            <div class="info">
              <h3>邮箱</h3>
              <a href="mailto:support@example.com">support@example.com</a>
            </div>
          </div>

          <div class="contact-item">
            <span class="icon">📞</span>
            <div class="info">
              <h3>电话</h3>
              <a href="tel:+8612345678901">+86 123-4567-8901</a>
            </div>
          </div>

          <div class="contact-item">
            <span class="icon">📍</span>
            <div class="info">
              <h3>地址</h3>
              <p>北京市朝阳区某某科技园 A 座 10 层</p>
            </div>
          </div>

          <div class="contact-item">
            <span class="icon">🌐</span>
            <div class="info">
              <h3>社交媒体</h3>
              <div class="social-links">
                <a href="#" target="_blank">Twitter</a> ·
                <a href="#" target="_blank">GitHub</a>
              </div>
            </div>
          </div>
        </div>

        <div class="note">
          <p>我们会在 24 小时内回复您的邮件，感谢您的支持！</p>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import Navbar from "@/components/NavBar.vue";
</script>

<style scoped>
.page-container {
  min-height: 100vh;
  padding-top: 70px; /* 为固定导航栏留出空间 */
  background: linear-gradient(145deg, #667eea 0%, #764ba2 100%);
  display: flex;
  justify-content: center;
  align-items: center;
}

.content {
  max-width: 800px;
  width: 100%;
  padding: 2rem;
}

.contact-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 3rem 2.5rem;
  color: white;
  box-shadow: 0 20px 35px -8px rgba(0, 0, 0, 0.2);
}

.page-title {
  font-size: 2.8rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  text-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  text-align: center;
}

.page-subtitle {
  font-size: 1.1rem;
  margin-bottom: 2.5rem;
  opacity: 0.9;
  text-align: center;
  line-height: 1.6;
}

.contact-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.8rem;
  margin: 2rem 0;
}

.contact-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  background: rgba(255, 255, 255, 0.1);
  padding: 1.5rem;
  border-radius: 1.2rem;
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition:
    transform 0.2s,
    background 0.2s;
}

.contact-item:hover {
  transform: translateY(-5px);
  background: rgba(255, 255, 255, 0.15);
}

.icon {
  font-size: 2rem;
  line-height: 1;
}

.info h3 {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 0.3rem;
  color: white;
}

.info a,
.info p {
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  font-size: 0.95rem;
  line-height: 1.5;
  word-break: break-word;
}

.info a:hover {
  text-decoration: underline;
  color: white;
}

.social-links {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.social-links a {
  color: rgba(255, 255, 255, 0.9);
}

.social-links a:hover {
  color: white;
}

.note {
  text-align: center;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  font-style: italic;
  opacity: 0.9;
}

/* 移动端适应 */
@media (max-width: 640px) {
  .content {
    padding: 1rem;
  }
  .contact-card {
    padding: 2rem 1.5rem;
  }
  .page-title {
    font-size: 2.2rem;
  }
  .contact-grid {
    grid-template-columns: 1fr;
  }
}
</style>
