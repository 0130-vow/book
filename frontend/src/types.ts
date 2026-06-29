export interface BookBrief {
  external_id: string;
  title: string;
  author: string;
  cover: string;
  status: string;
  words: number | null;
  updated_at: string;
  source: string;
  source_name: string;
  category?: string;
}

export interface ChapterBrief {
  id: string;
  index: number;
  title: string;
}

export interface BookDetail extends BookBrief {
  intro: string;
  category: string;
  chapters: ChapterBrief[];
}

export interface ShelfBook {
  id: number;
  external_id: string;
  title: string;
  author: string;
  cover: string;
  intro: string;
  category: string;
  status: string;
  current_source: string;
  source_data: string;
  display_status: "reading" | "finished" | "archived";
  last_read_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Progress {
  chapter_id?: string;
  chapter_index?: number;
  position?: number;
  mode?: "scroll" | "page";
  updated_at?: string;
}

export interface DownloadJob {
  id: number;
  book_id: number;
  status: "queued" | "downloading" | "completed" | "failed";
  completed: number;
  total: number;
  error: string;
  created_at: string;
  updated_at: string;
}

export interface Source {
  identifier: string;
  name: string;
  enabled: boolean;
  healthy: boolean;
}
