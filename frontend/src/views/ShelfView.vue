<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { Archive, BookCheck, BookMarked, MoreHorizontal, Trash2 } from "lucide-vue-next";
import { useRouter } from "vue-router";
import { showConfirmDialog, showSuccessToast } from "vant";
import { api } from "../api";
import BookCover from "../components/BookCover.vue";
import PageHeader from "../components/PageHeader.vue";
import type { Progress, ShelfBook } from "../types";

const router = useRouter();
const active = ref<"reading" | "finished" | "archived">("reading");
const sort = ref("recent");
const books = ref<(ShelfBook & { progress: Progress })[]>([]);
const loading = ref(false);
const tabs = [
  { value: "reading", label: "在读" },
  { value: "finished", label: "已完成" },
  { value: "archived", label: "归档" }
] as const;
const sortLabel = computed(() => ({ recent: "最近阅读", title: "书名", created: "加入时间" })[sort.value]);

async function load() {
  loading.value = true;
  const rows = await api.shelf(active.value, sort.value);
  books.value = rows.map((book) => ({
    ...book,
    progress: JSON.parse(book.source_data || "{}")[book.current_source] || {}
  }));
  loading.value = false;
}

async function setStatus(book: ShelfBook, status: ShelfBook["display_status"]) {
  await api.patchShelf(book.id, { display_status: status });
  await load();
  showSuccessToast("书架已更新");
}

async function remove(book: ShelfBook) {
  await showConfirmDialog({ title: "移出书架", message: `确定移除《${book.title}》及本地缓存吗？` });
  await api.removeShelf(book.id);
  await load();
}

function read(book: ShelfBook & { progress: Progress }) {
  router.push({ path: `/read/${book.current_source}/${book.external_id}`, query: { shelf: book.id } });
}

onMounted(load);
</script>

<template>
  <div class="page shelf-page">
    <PageHeader title="我的书架" subtitle="PERSONAL COLLECTION">
      <van-popover :actions="[{ text: '最近阅读', value: 'recent' }, { text: '书名', value: 'title' }, { text: '加入时间', value: 'created' }]" @select="({ value }) => { sort = value; load(); }">
        <template #reference><button class="sort-button" type="button">{{ sortLabel }} <MoreHorizontal :size="18" /></button></template>
      </van-popover>
    </PageHeader>
    <div class="shelf-tabs">
      <button v-for="tab in tabs" :key="tab.value" :class="{ active: active === tab.value }" type="button" @click="active = tab.value; load()">
        {{ tab.label }}
      </button>
    </div>
    <div v-if="loading" class="shelf-list"><van-skeleton v-for="i in 3" :key="i" title avatar :row="2" /></div>
    <div v-else-if="books.length" class="shelf-list">
      <van-swipe-cell v-for="book in books" :key="book.id">
        <article class="shelf-row" @click="read(book)">
          <BookCover :src="book.cover" :title="book.title" size="sm" />
          <div class="shelf-copy">
            <h3>{{ book.title }}</h3>
            <p>{{ book.author || "佚名" }} · 第 {{ (book.progress.chapter_index || 0) + 1 }} 章</p>
            <div class="progress-track"><span :style="{ width: `${Math.round((book.progress.position || 0) * 100)}%` }" /></div>
            <small>{{ book.last_read_at ? new Date(book.last_read_at).toLocaleDateString() : "尚未开始" }}</small>
          </div>
        </article>
        <template #right>
          <button v-if="active === 'reading'" class="swipe-action archive" type="button" title="归档" @click="setStatus(book, 'archived')"><Archive :size="20" /></button>
          <button v-if="active === 'reading'" class="swipe-action finish" type="button" title="标记完成" @click="setStatus(book, 'finished')"><BookCheck :size="20" /></button>
          <button class="swipe-action delete" type="button" title="删除" @click="remove(book)"><Trash2 :size="20" /></button>
        </template>
      </van-swipe-cell>
    </div>
    <div v-else class="empty-state"><BookMarked :size="30" /><h3>这里还没有书</h3><p>不同状态的书会分别收纳在这里。</p></div>
  </div>
</template>
