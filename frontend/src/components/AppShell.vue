<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { BookMarked, Download, Home, Search, Settings } from "lucide-vue-next";

const route = useRoute();
const router = useRouter();
const reader = computed(() => route.path.startsWith("/read/"));
const items = [
  { path: "/", label: "首页", icon: Home },
  { path: "/search", label: "搜索", icon: Search },
  { path: "/shelf", label: "书架", icon: BookMarked },
  { path: "/downloads", label: "下载", icon: Download },
  { path: "/settings", label: "设置", icon: Settings }
];
</script>

<template>
  <div :class="['app-layout', { 'reader-layout': reader }]">
    <aside v-if="!reader" class="side-nav">
      <button class="side-brand" type="button" @click="router.push('/')">
        <span>BH</span><strong>BookHub</strong>
      </button>
      <nav aria-label="主导航">
        <button
          v-for="item in items"
          :key="item.path"
          type="button"
          :class="{ active: route.path === item.path }"
          :title="item.label"
          @click="router.push(item.path)"
        >
          <component :is="item.icon" :size="20" />
          <span>{{ item.label }}</span>
        </button>
      </nav>
    </aside>
    <div class="app-content"><router-view /></div>
    <nav v-if="!reader" class="bottom-nav" aria-label="主导航">
      <button
        v-for="item in items"
        :key="item.path"
        type="button"
        :class="{ active: route.path === item.path }"
        @click="router.push(item.path)"
      >
        <component :is="item.icon" :size="20" />
        <span>{{ item.label }}</span>
      </button>
    </nav>
  </div>
</template>
