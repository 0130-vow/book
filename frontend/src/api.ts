import axios from "axios";
import type {
  BookBrief,
  BookDetail,
  DownloadJob,
  Progress,
  ShelfBook,
  Source
} from "./types";

export const TOKEN_KEY = "bookhub-token";

const http = axios.create({ baseURL: "/api", timeout: 10000 });
http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) config.headers["X-BookHub-Token"] = token;
  return config;
});
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && localStorage.getItem(TOKEN_KEY)) {
      localStorage.removeItem(TOKEN_KEY);
      window.location.replace("/");
    }
    return Promise.reject(error);
  }
);

export const api = {
  async verifyToken(token: string) {
    const response = await fetch("/api/sources", {
      headers: { "X-BookHub-Token": token },
      cache: "no-store"
    });
    if (!response.ok) throw new Error("Token invalid");
    return (await response.json()) as Source[];
  },
  async sources() {
    return (await http.get<Source[]>("/sources")).data;
  },
  async patchSource(identifier: string, enabled: boolean) {
    return (await http.patch<Source>(`/sources/${identifier}`, { enabled })).data;
  },
  async search(keyword: string, source?: string) {
    return (
      await http.get<BookBrief[]>("/search", {
        params: { keyword, source: source || undefined }
      })
    ).data;
  },
  async detail(source: string, id: string) {
    return (await http.get<BookDetail>(`/catalog/${source}/${id}`)).data;
  },
  async chapter(source: string, bookId: string, chapterId: string, shelfId?: number) {
    return (
      await http.get(`/catalog/${source}/${bookId}/chapters/${chapterId}`, {
        params: { bookshelf_id: shelfId }
      })
    ).data as { id: string; index: number; title: string; content: string };
  },
  async shelf(status?: string, sort = "recent") {
    return (await http.get<ShelfBook[]>("/bookshelf", { params: { status, sort } })).data;
  },
  async addToShelf(book: BookDetail) {
    return (
      await http.post<ShelfBook>("/bookshelf", {
        external_id: book.external_id,
        title: book.title,
        author: book.author,
        cover: book.cover,
        intro: book.intro,
        category: book.category,
        status: book.status,
        source: book.source
      })
    ).data;
  },
  async patchShelf(id: number, data: Partial<Pick<ShelfBook, "display_status" | "current_source">>) {
    return (await http.patch<ShelfBook>(`/bookshelf/${id}`, data)).data;
  },
  async removeShelf(id: number) {
    await http.delete(`/bookshelf/${id}`);
  },
  async progress(bookId: number, source: string) {
    return (await http.get<Progress>(`/progress/${bookId}`, { params: { source } })).data;
  },
  async saveProgress(data: {
    book_id: number;
    source: string;
    chapter_id: string;
    chapter_index: number;
    total_chapters: number;
    position: number;
    mode: "scroll" | "page";
  }) {
    return (await http.post<Progress>("/progress", data)).data;
  },
  async downloads() {
    return (await http.get<DownloadJob[]>("/download")).data;
  },
  async startDownload(bookId: number) {
    return (await http.post<DownloadJob>(`/download/${bookId}`)).data;
  }
};
