<script setup lang="ts">
import { onMounted, ref } from "vue";
import { CheckCircle2, KeyRound, LogOut, Server } from "lucide-vue-next";
import { useRouter } from "vue-router";
import { showSuccessToast } from "vant";
import { api, TOKEN_KEY } from "../api";
import PageHeader from "../components/PageHeader.vue";
import type { Source } from "../types";

const router = useRouter();
const sources = ref<Source[]>([]);
const token = ref(localStorage.getItem(TOKEN_KEY) || "");

function saveToken() {
  localStorage.setItem(TOKEN_KEY, token.value.trim());
  showSuccessToast("Token 已更新");
}

function logout() {
  localStorage.removeItem(TOKEN_KEY);
  location.href = "/";
}

onMounted(async () => {
  sources.value = await api.sources();
});
</script>

<template>
  <div class="page settings-page">
    <PageHeader title="系统设置" subtitle="BOOKHUB V1.1" />
    <section class="settings-section">
      <div class="settings-heading"><KeyRound :size="20" /><div><h2>访问 Token</h2><p>用于所有设备的私有访问认证</p></div></div>
      <div class="token-row">
        <van-field v-model="token" type="password" autocomplete="off" />
        <van-button type="primary" @click="saveToken">保存</van-button>
      </div>
    </section>
    <section class="settings-section">
      <div class="settings-heading"><Server :size="20" /><div><h2>书源状态</h2><p>聚合搜索与章节服务</p></div></div>
      <div class="source-list">
        <div v-for="source in sources" :key="source.identifier">
          <span><CheckCircle2 :size="17" />{{ source.name }}</span><strong>{{ source.healthy ? "正常" : "异常" }}</strong>
        </div>
      </div>
    </section>
    <button class="logout-button" type="button" @click="logout"><LogOut :size="18" />退出当前设备</button>
  </div>
</template>
