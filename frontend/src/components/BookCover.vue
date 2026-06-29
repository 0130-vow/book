<script setup lang="ts">
import { computed } from "vue";
import { BookOpen } from "lucide-vue-next";

const props = defineProps<{ src?: string; title: string; size?: "sm" | "md" | "lg" }>();
const initials = computed(() => props.title.slice(0, 2));
</script>

<template>
  <div :class="['book-cover', `book-cover-${size || 'md'}`]">
    <img v-if="src" :src="src" :alt="`${title}封面`" />
    <div v-else class="cover-fallback">
      <BookOpen :size="22" />
      <strong>{{ initials }}</strong>
    </div>
  </div>
</template>
