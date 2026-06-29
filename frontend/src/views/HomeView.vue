<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ArrowRight, BookMarked, Search } from "lucide-vue-next";
import { useRouter } from "vue-router";
import { api } from "../api";
import BookCover from "../components/BookCover.vue";
import type { Progress, ShelfBook } from "../types";

const router = useRouter();
const keyword = ref("");
const recent = ref<(ShelfBook & { progress: Progress })[]>([]);

function submit() {
  const value = keyword.value.trim();
  if (value) router.push({ path: "/search", query: { q: value } });
}

onMounted(async () => {
  const books = (await api.shelf(undefined, "recent")).slice(0, 4);
  recent.value = books.map((book) => {
    const all = JSON.parse(book.source_data || "{}");
    return { ...book, progress: all[book.current_source] || {} };
  });
});
</script>

<template>
  <div class="page home-page">
    <header class="home-header">
      <div>
        <p class="eyebrow">YOUR PRIVATE LIBRARY</p>
        <h1>今晚，读点什么？</h1>
      </div>
      <button class="icon-button desktop-only" type="button" title="打开书架" @click="router.push('/shelf')">
        <BookMarked :size="21" />
      </button>
    </header>

    <form class="hero-search" @submit.prevent="submit">
      <Search :size="21" />
      <input v-model="keyword" aria-label="搜索书名或作者" placeholder="搜索书名、作者或关键字" />
      <button type="submit" title="搜索"><ArrowRight :size="21" /></button>
    </form>

    <section class="section-block">
      <div class="section-heading">
        <div>
          <p class="eyebrow">CONTINUE READING</p>
          <h2>继续阅读</h2>
        </div>
        <button class="text-button" type="button" @click="router.push('/shelf')">全部书架</button>
      </div>

      <div v-if="recent.length" class="continue-grid">
        <article
          v-for="book in recent"
          :key="book.id"
          class="continue-item"
          @click="router.push({ path: `/read/${book.current_source}/${book.external_id}`, query: { shelf: book.id } })"
        >
          <BookCover :src="book.cover" :title="book.title" size="md" />
          <div class="continue-copy">
            <span class="status-dot">在读</span>
            <h3>{{ book.title }}</h3>
            <p>{{ book.author || "佚名" }}</p>
            <div class="progress-track">
              <span :style="{ width: `${Math.round((book.progress.progress || 0) * 100)}%` }" />
            </div>
            <small>第 {{ (book.progress.chapter_index || 0) + 1 }} 章</small>
          </div>
        </article>
      </div>
      <div v-else class="empty-state">
        <BookMarked :size="30" />
        <h3>书架还是空的</h3>
        <p>搜一本想读的书，开始你的第一段阅读。</p>
        <van-button type="primary" size="small" @click="router.push('/search')">去搜索</van-button>
      </div>
    </section>
  </div>
</template>
