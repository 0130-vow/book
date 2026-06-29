<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ArrowLeft, BookOpen, Check, Download, Library } from "lucide-vue-next";
import { useRoute, useRouter } from "vue-router";
import { showFailToast, showSuccessToast } from "vant";
import { api } from "../api";
import BookCover from "../components/BookCover.vue";
import type { BookDetail, ShelfBook } from "../types";

const route = useRoute();
const router = useRouter();
const source = computed(() => String(route.params.source));
const id = computed(() => String(route.params.id));
const book = ref<BookDetail>();
const shelfBook = ref<ShelfBook>();
const loading = ref(true);

async function refreshShelf() {
  const shelf = await api.shelf();
  shelfBook.value = shelf.find(
    (item) => item.external_id === id.value && item.current_source === source.value
  );
}

async function add() {
  if (!book.value) return;
  shelfBook.value = await api.addToShelf(book.value);
  showSuccessToast("已加入书架");
}

async function read() {
  if (!book.value) return;
  if (!shelfBook.value) await add();
  router.push({ path: `/read/${source.value}/${id.value}`, query: { shelf: shelfBook.value?.id } });
}

async function download() {
  try {
    if (!shelfBook.value) await add();
    await api.startDownload(shelfBook.value!.id);
    showSuccessToast("已加入下载");
    router.push("/downloads");
  } catch {
    showFailToast("下载任务创建失败");
  }
}

onMounted(async () => {
  try {
    [book.value] = await Promise.all([api.detail(source.value, id.value), refreshShelf()]);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="page book-page">
    <button class="icon-button back-button" type="button" title="返回" @click="router.back()">
      <ArrowLeft :size="21" />
    </button>
    <van-skeleton v-if="loading" title avatar :row="8" />
    <template v-else-if="book">
      <section class="book-hero">
        <BookCover :src="book.cover" :title="book.title" size="lg" />
        <div class="book-meta">
          <p class="eyebrow">{{ book.category || "BOOK DETAIL" }}</p>
          <h1>{{ book.title }}</h1>
          <p class="book-author">{{ book.author || "佚名" }}</p>
          <div class="meta-tags">
            <span>{{ book.status }}</span>
            <span>{{ book.source_name }}</span>
            <span>{{ book.chapters.length }} 章</span>
          </div>
          <div class="book-actions">
            <van-button type="primary" @click="read"><BookOpen :size="17" />开始阅读</van-button>
            <van-button plain :disabled="Boolean(shelfBook)" @click="add">
              <component :is="shelfBook ? Check : Library" :size="17" />
              {{ shelfBook ? "已在书架" : "加入书架" }}
            </van-button>
            <button class="icon-button" type="button" title="下载全书" @click="download">
              <Download :size="20" />
            </button>
          </div>
        </div>
      </section>

      <section class="book-description">
        <p class="eyebrow">ABOUT THE BOOK</p>
        <h2>内容简介</h2>
        <p>{{ book.intro || "暂无简介" }}</p>
      </section>

      <section class="chapter-preview">
        <div class="section-heading compact">
          <h2>目录</h2>
          <span>{{ book.chapters.length }} 章</span>
        </div>
        <button
          v-for="chapter in book.chapters.slice(0, 8)"
          :key="chapter.id"
          type="button"
          @click="read"
        >
          <span>{{ String(chapter.index + 1).padStart(2, "0") }}</span>
          {{ chapter.title }}
        </button>
      </section>
    </template>
  </div>
</template>
