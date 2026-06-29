<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { Clock3, Search, X } from "lucide-vue-next";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";
import BookCover from "../components/BookCover.vue";
import type { BookBrief, Source } from "../types";

const route = useRoute();
const router = useRouter();
const keyword = ref(String(route.query.q || ""));
const source = ref("");
const sources = ref<Source[]>([]);
const results = ref<BookBrief[]>([]);
const loading = ref(false);
const searched = ref(false);
const history = ref<string[]>(JSON.parse(localStorage.getItem("bookhub-search-history") || "[]"));

async function search(value = keyword.value) {
  const query = value.trim();
  if (!query) return;
  keyword.value = query;
  loading.value = true;
  searched.value = true;
  try {
    results.value = await api.search(query, source.value);
    history.value = [query, ...history.value.filter((item) => item !== query)].slice(0, 8);
    localStorage.setItem("bookhub-search-history", JSON.stringify(history.value));
    router.replace({ query: { q: query } });
  } finally {
    loading.value = false;
  }
}

function clearHistory() {
  history.value = [];
  localStorage.removeItem("bookhub-search-history");
}

onMounted(async () => {
  sources.value = await api.sources();
  if (keyword.value) search();
});

watch(source, () => {
  if (keyword.value) search();
});
</script>

<template>
  <div class="page search-page">
    <header class="search-header">
      <p class="eyebrow">DISCOVER</p>
      <h1>找到下一本书</h1>
      <form class="wide-search" @submit.prevent="search()">
        <Search :size="20" />
        <input v-model="keyword" autofocus aria-label="搜索" placeholder="书名、作者或关键字" />
        <button v-if="keyword" type="button" title="清空" @click="keyword = ''"><X :size="18" /></button>
        <button class="search-submit" type="submit">搜索</button>
      </form>
      <div class="source-filter">
        <button :class="{ active: !source }" type="button" @click="source = ''">全部来源</button>
        <button
          v-for="item in sources"
          :key="item.identifier"
          :class="{ active: source === item.identifier }"
          type="button"
          @click="source = item.identifier"
        >
          {{ item.name }}
        </button>
      </div>
    </header>

    <section v-if="!searched && history.length" class="history-block">
      <div class="section-heading compact">
        <h2>最近搜索</h2>
        <button class="text-button" type="button" @click="clearHistory">清除</button>
      </div>
      <div class="history-list">
        <button v-for="item in history" :key="item" type="button" @click="search(item)">
          <Clock3 :size="15" />{{ item }}
        </button>
      </div>
    </section>

    <section v-if="searched" class="results-block">
      <p class="result-count">{{ loading ? "正在聚合书源…" : `找到 ${results.length} 个结果` }}</p>
      <div v-if="loading" class="book-list">
        <van-skeleton v-for="item in 4" :key="item" title avatar :row="3" />
      </div>
      <div v-else-if="results.length" class="book-list">
        <article
          v-for="book in results"
          :key="`${book.source}-${book.external_id}`"
          class="book-row"
          @click="router.push(`/book/${book.source}/${book.external_id}`)"
        >
          <BookCover :src="book.cover" :title="book.title" size="sm" />
          <div class="book-row-copy">
            <div class="book-title-line">
              <h3>{{ book.title }}</h3>
              <span>{{ book.source_name }}</span>
            </div>
            <p>{{ book.author || "佚名" }} · {{ book.status }}</p>
            <small>{{ book.category || book.updated_at }}<template v-if="book.words"> · {{ Math.round(book.words / 10000) }} 万字</template></small>
          </div>
        </article>
      </div>
      <div v-else class="empty-state">
        <Search :size="30" />
        <h3>没有找到匹配的书</h3>
        <p>换个书名、作者或来源再试试。</p>
      </div>
    </section>
  </div>
</template>
