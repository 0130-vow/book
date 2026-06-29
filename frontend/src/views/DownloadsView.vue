<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { CheckCircle2, Download, LoaderCircle, RotateCcw } from "lucide-vue-next";
import { api } from "../api";
import PageHeader from "../components/PageHeader.vue";
import type { DownloadJob, ShelfBook } from "../types";

const jobs = ref<DownloadJob[]>([]);
const shelf = ref<ShelfBook[]>([]);
let timer: number | undefined;

async function load() {
  [jobs.value, shelf.value] = await Promise.all([api.downloads(), api.shelf()]);
}

function name(job: DownloadJob) {
  return shelf.value.find((book) => book.id === job.book_id)?.title || `书籍 #${job.book_id}`;
}

function percent(job: DownloadJob) {
  return job.total ? Math.round((job.completed / job.total) * 100) : 0;
}

async function retry(job: DownloadJob) {
  await api.startDownload(job.book_id);
  load();
}

onMounted(() => {
  load();
  timer = window.setInterval(load, 3000);
});
onBeforeUnmount(() => timer && window.clearInterval(timer));
</script>

<template>
  <div class="page downloads-page">
    <PageHeader title="下载中心" subtitle="OFFLINE LIBRARY" />
    <div v-if="jobs.length" class="download-list">
      <article v-for="job in jobs" :key="job.id" class="download-row">
        <div :class="['download-icon', job.status]">
          <CheckCircle2 v-if="job.status === 'completed'" :size="21" />
          <LoaderCircle v-else-if="job.status === 'downloading' || job.status === 'queued'" :size="21" class="spin" />
          <RotateCcw v-else :size="21" />
        </div>
        <div class="download-copy">
          <div><h3>{{ name(job) }}</h3><span>{{ job.status === "completed" ? "已离线" : job.status === "failed" ? "下载失败" : `${percent(job)}%` }}</span></div>
          <p>{{ job.completed }} / {{ job.total || "…" }} 章</p>
          <div class="progress-track"><span :style="{ width: `${percent(job)}%` }" /></div>
          <small v-if="job.error">{{ job.error }}</small>
        </div>
        <button v-if="job.status === 'failed'" class="icon-button" type="button" title="重试" @click="retry(job)"><RotateCcw :size="18" /></button>
      </article>
    </div>
    <div v-else class="empty-state"><Download :size="30" /><h3>还没有离线书籍</h3><p>在书籍详情页点击下载，即可缓存全书。</p></div>
  </div>
</template>
