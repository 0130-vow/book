<script setup lang="ts">
import { ref } from "vue";
import { BookOpen, KeyRound } from "lucide-vue-next";
import { showFailToast } from "vant";
import AppShell from "./components/AppShell.vue";
import { api, TOKEN_KEY } from "./api";

const authenticated = ref(Boolean(localStorage.getItem(TOKEN_KEY)));
const token = ref("");
const checking = ref(false);

async function signIn() {
  if (!token.value.trim()) return;
  checking.value = true;
  try {
    await api.verifyToken(token.value.trim());
    localStorage.setItem(TOKEN_KEY, token.value.trim());
    authenticated.value = true;
  } catch {
    showFailToast("Token 无效");
  } finally {
    checking.value = false;
  }
}
</script>

<template>
  <main v-if="!authenticated" class="auth-screen">
    <section class="auth-panel">
      <div class="brand-mark"><BookOpen :size="28" /></div>
      <p class="eyebrow">PRIVATE READING SPACE</p>
      <h1>BookHub</h1>
      <p class="auth-subtitle">回到你的私人书房</p>
      <van-field
        v-model="token"
        type="password"
        autocomplete="current-password"
        placeholder="访问 Token"
        :left-icon="undefined"
        @keyup.enter="signIn"
      >
        <template #left-icon><KeyRound :size="18" /></template>
      </van-field>
      <van-button type="primary" block :loading="checking" @click="signIn">进入书房</van-button>
    </section>
  </main>
  <AppShell v-else />
</template>
