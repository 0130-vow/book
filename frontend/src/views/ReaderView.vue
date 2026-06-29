<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  List,
  Moon,
  SlidersHorizontal,
  Sun
} from "lucide-vue-next";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";
import type { BookDetail, Progress } from "../types";

interface ReaderSettings {
  fontSize: number;
  lineHeight: number;
  margin: number;
  theme: "auto" | "white" | "warm" | "gray" | "dark";
  mode: "scroll" | "page";
}

const route = useRoute();
const router = useRouter();
const source = computed(() => String(route.params.source));
const bookId = computed(() => String(route.params.id));
const shelfId = computed(() => Number(route.query.shelf || 0));
const detail = ref<BookDetail>();
const chapter = ref<{ id: string; index: number; title: string; content: string }>();
const chapterIndex = ref(0);
const directoryOpen = ref(false);
const settingsOpen = ref(false);
const loading = ref(true);
const readerBody = ref<HTMLElement>();
const touchStart = ref(0);
let timer: number | undefined;

const stored = localStorage.getItem("bookhub-reader-settings");
const settings = ref<ReaderSettings>(
  stored
    ? JSON.parse(stored)
    : { fontSize: 19, lineHeight: 1.9, margin: 24, theme: "warm", mode: "scroll" }
);

const themeClass = computed(() => `reader-theme-${settings.value.theme}`);
const readingStyle = computed(() => ({
  "--reader-font-size": `${settings.value.fontSize}px`,
  "--reader-line-height": String(settings.value.lineHeight),
  "--reader-margin": `${settings.value.margin}px`
}));

function persistSettings() {
  localStorage.setItem("bookhub-reader-settings", JSON.stringify(settings.value));
}

function position() {
  const el = readerBody.value;
  if (!el) return 0;
  const horizontal = settings.value.mode === "page";
  const extent = horizontal
    ? el.scrollWidth - el.clientWidth
    : el.scrollHeight - el.clientHeight;
  if (extent <= 0) return 0;
  return Math.min(1, (horizontal ? el.scrollLeft : el.scrollTop) / extent);
}

async function save() {
  if (!shelfId.value || !chapter.value) return;
  await api.saveProgress({
    book_id: shelfId.value,
    source: source.value,
    chapter_id: chapter.value.id,
    chapter_index: chapterIndex.value,
    total_chapters: detail.value?.chapters.length || 1,
    position: position(),
    mode: settings.value.mode
  });
}

async function openChapter(index: number, restorePosition = 0) {
  if (!detail.value || index < 0 || index >= detail.value.chapters.length) return;
  await save();
  loading.value = true;
  chapterIndex.value = index;
  const target = detail.value.chapters[index];
  chapter.value = await api.chapter(source.value, bookId.value, target.id, shelfId.value || undefined);
  directoryOpen.value = false;
  await nextTick();
  if (readerBody.value) {
    const horizontal = settings.value.mode === "page";
    const max = horizontal
      ? readerBody.value.scrollWidth - readerBody.value.clientWidth
      : readerBody.value.scrollHeight - readerBody.value.clientHeight;
    if (horizontal) readerBody.value.scrollLeft = max * restorePosition;
    else readerBody.value.scrollTop = max * restorePosition;
  }
  loading.value = false;
}

function onTouchStart(event: TouchEvent) {
  touchStart.value = event.changedTouches[0].clientX;
}

function onTouchEnd(event: TouchEvent) {
  if (settings.value.mode !== "page") return;
  const delta = event.changedTouches[0].clientX - touchStart.value;
  if (Math.abs(delta) < 70) return;
  turnPage(delta < 0 ? 1 : -1);
}

function toggleNight() {
  settings.value.theme = settings.value.theme === "dark" ? "warm" : "dark";
  persistSettings();
}

function turnPage(direction: -1 | 1) {
  const el = readerBody.value;
  if (!el || settings.value.mode !== "page") {
    openChapter(chapterIndex.value + direction);
    return;
  }
  const max = el.scrollWidth - el.clientWidth;
  const next = Math.max(0, Math.min(max, el.scrollLeft + direction * el.clientWidth));
  if (
    (direction < 0 && el.scrollLeft <= 1) ||
    (direction > 0 && el.scrollLeft >= max - 1)
  ) {
    openChapter(chapterIndex.value + direction);
    return;
  }
  el.scrollTo({ left: next, behavior: "smooth" });
}

onMounted(async () => {
  detail.value = await api.detail(source.value, bookId.value);
  let progress: Progress = {};
  if (shelfId.value) progress = await api.progress(shelfId.value, source.value);
  const index = Math.min(progress.chapter_index || 0, detail.value.chapters.length - 1);
  await openChapter(index, progress.position || 0);
  timer = window.setInterval(save, 5000);
  window.addEventListener("beforeunload", save);
});

onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer);
  window.removeEventListener("beforeunload", save);
  save();
});
</script>

<template>
  <div :class="['reader', themeClass]" :style="readingStyle">
    <header class="reader-topbar">
      <button type="button" title="返回" @click="router.back()"><ArrowLeft :size="21" /></button>
      <div>
        <strong>{{ detail?.title || "BookHub" }}</strong>
        <span>{{ chapter?.title || "载入中" }}</span>
      </div>
      <button type="button" title="切换夜间模式" @click="toggleNight">
        <Sun v-if="settings.theme === 'dark'" :size="20" />
        <Moon v-else :size="20" />
      </button>
    </header>

    <main
      ref="readerBody"
      :class="['reader-body', { 'page-reading': settings.mode === 'page' }]"
      @touchstart="onTouchStart"
      @touchend="onTouchEnd"
    >
      <van-loading v-if="loading" vertical>载入章节</van-loading>
      <article v-else-if="chapter" class="chapter-content">
        <p class="chapter-number">第 {{ chapter.index + 1 }} 章</p>
        <h1>{{ chapter.title }}</h1>
        <p v-for="(paragraph, index) in chapter.content.split(/\n+/).filter(Boolean)" :key="index">
          {{ paragraph }}
        </p>
      </article>
    </main>

    <footer class="reader-toolbar">
      <button type="button" title="向前" :disabled="chapterIndex === 0 && position() === 0" @click="turnPage(-1)">
        <ChevronLeft :size="22" />
      </button>
      <button type="button" title="目录" @click="directoryOpen = true"><List :size="21" /></button>
      <span>{{ chapterIndex + 1 }} / {{ detail?.chapters.length || 0 }}</span>
      <button type="button" title="阅读设置" @click="settingsOpen = true"><SlidersHorizontal :size="20" /></button>
      <button
        type="button"
        title="向后"
        @click="turnPage(1)"
      >
        <ChevronRight :size="22" />
      </button>
    </footer>

    <van-popup v-model:show="directoryOpen" position="left" class="directory-panel">
      <header><p class="eyebrow">CONTENTS</p><h2>{{ detail?.title }}</h2></header>
      <button
        v-for="item in detail?.chapters"
        :key="item.id"
        type="button"
        :class="{ active: item.index === chapterIndex }"
        @click="openChapter(item.index)"
      >
        <span>{{ String(item.index + 1).padStart(2, "0") }}</span>{{ item.title }}
      </button>
    </van-popup>

    <van-popup v-model:show="settingsOpen" position="bottom" round class="reader-settings">
      <div class="settings-title"><h2>阅读设置</h2><span>{{ settings.mode === "scroll" ? "滚动模式" : "翻页模式" }}</span></div>
      <label>字号 <strong>{{ settings.fontSize }}</strong></label>
      <van-slider v-model="settings.fontSize" :min="15" :max="28" @change="persistSettings" />
      <label>行距 <strong>{{ settings.lineHeight.toFixed(1) }}</strong></label>
      <van-slider v-model="settings.lineHeight" :min="1.4" :max="2.4" :step="0.1" @change="persistSettings" />
      <label>页边距 <strong>{{ settings.margin }}</strong></label>
      <van-slider v-model="settings.margin" :min="12" :max="48" @change="persistSettings" />
      <div class="theme-swatches" aria-label="阅读背景">
        <button
          v-for="item in ['auto', 'white', 'warm', 'gray', 'dark'] as const"
          :key="item"
          :class="[item, { active: settings.theme === item }]"
          type="button"
          :title="item"
          @click="settings.theme = item; persistSettings()"
        />
      </div>
      <div class="mode-switch">
        <button :class="{ active: settings.mode === 'scroll' }" type="button" @click="settings.mode = 'scroll'; persistSettings()">滚动</button>
        <button :class="{ active: settings.mode === 'page' }" type="button" @click="settings.mode = 'page'; persistSettings()">翻页</button>
      </div>
    </van-popup>
  </div>
</template>
