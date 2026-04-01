<template>
  <section class="gallery">
    <div v-if="!media.length" class="empty-card ui-surface-white">
      <p>当前数据集暂未提供媒体资源。</p>
    </div>

    <div v-else class="media-grid">
      <article
        v-for="item in media"
        :key="item.mediaId"
        class="media-card ui-surface-white"
      >
        <div class="media-preview">
          <img
            v-if="item.type === 'image' && !failedMediaIds.includes(item.mediaId)"
            :src="item.url"
            :alt="item.title"
            @error="markFailed(item.mediaId)"
          />
          <video
            v-else-if="item.type === 'video' && !failedMediaIds.includes(item.mediaId)"
            :src="item.url"
            :poster="item.coverUrl || undefined"
            controls
            preload="metadata"
            @error="markFailed(item.mediaId)"
          />
          <div v-else class="fallback">
            <span>资源暂不可用</span>
          </div>
        </div>

        <div class="media-body">
          <h3>{{ item.title }}</h3>
          <p>{{ item.description || "该媒体用于辅助理解数据集结构与运行效果。" }}</p>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { DatasetMediaItem } from "@/types/DatasetTypes";

defineProps<{
  media: DatasetMediaItem[];
}>();

const failedMediaIds = ref<string[]>([]);

const markFailed = (mediaId: string) => {
  if (failedMediaIds.value.includes(mediaId)) return;
  failedMediaIds.value = [...failedMediaIds.value, mediaId];
};
</script>

<style scoped>
.empty-card {
  padding: 1.4rem;
  border-radius: 1.2rem;
  color: #64748b;
}

.media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.media-card {
  overflow: hidden;
  border-radius: 1.4rem;
}

.media-preview {
  aspect-ratio: 16 / 10;
  background: #e2e8f0;
}

.media-preview img,
.media-preview video,
.fallback {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e2e8f0, #f8fafc);
  color: #64748b;
  font-weight: 600;
}

.media-body {
  padding: 1rem 1.1rem 1.2rem;
}

.media-body h3 {
  margin: 0;
  color: #0f172a;
  font-size: 1.1rem;
}

.media-body p {
  margin: 0.7rem 0 0;
  color: #475569;
  line-height: 1.7;
}
</style>
