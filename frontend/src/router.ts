import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: () => import("./views/HomeView.vue") },
    { path: "/search", component: () => import("./views/SearchView.vue") },
    { path: "/book/:source/:id", component: () => import("./views/BookView.vue") },
    { path: "/read/:source/:id", component: () => import("./views/ReaderView.vue") },
    { path: "/shelf", component: () => import("./views/ShelfView.vue") },
    { path: "/downloads", component: () => import("./views/DownloadsView.vue") },
    { path: "/settings", component: () => import("./views/SettingsView.vue") }
  ],
  scrollBehavior: () => ({ top: 0 })
});

export default router;
