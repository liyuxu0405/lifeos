/**
 * LifeOS API Hook
 * 统一的后端 API 调用层
 */

// 1. 确保端口与后端 main.py 启动的一致
const API_BASE_URL = "http://127.0.0.1:52700";
const API_BASE = `${API_BASE_URL}/api`;

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// --- Types ---

export interface DailyBrief {
  date: string;
  greeting: string;
  highlights: string[];
  patterns: string[];
  priorities: string[];
  reflection: string;
  raw_markdown: string;
  generated_at: string;
}

export interface ContextEvent {
  id: string;
  source: string;
  event_type: string;
  title: string;
  content: string;
  timestamp: string;
  entities: string[];
  tags: string[];
  metadata: Record<string, unknown>;
  _score?: number;
}

export interface Insight {
  id: string;
  insight_type: string;
  title: string;
  description: string;
  evidence: string[];
  suggested_action: string;
  confidence: number;
  created_at: string;
  dismissed: boolean;
}

// 定义配置字段的接口类型
export interface ConfigField {
  type: string;
  label: string;
  description?: string;
  required?: boolean;
  secret?: boolean;
  placeholder?: string;
  default?: unknown;
}

export interface Plugin {
  name: string;
  display_name: string;
  description: string;
  icon: string;
  category: string;
  config_schema: Record<string, ConfigField>;
  enabled: boolean;
  last_sync: string | null;
}

export interface SystemStatus {
  llm_provider: string;
  events_indexed: number;
  data_dir: string;
}

export interface Settings {
  ollama_url: string;
  chat_model: string;
  embedding_model: string;
  has_openai_key: boolean;
  has_anthropic_key: boolean;
}

// --- API Methods ---

export const api = {
  // --- System ---
  status: () => request<SystemStatus>("/status"),
  health: () => fetch("http://127.0.0.1:52700/health").then((r) => r.json()),

  // --- Daily Brief ---
  getTodayBrief: (force = false) =>
    request<DailyBrief>(`/brief/today${force ? "?force=true" : ""}`),
  getBriefByDate: (date: string) => request<DailyBrief>(`/brief/${date}`),

  // --- Context Search ---
  search: (query: string, options?: { limit?: number; days_filter?: number; source_filter?: string }) =>
    request<{ results: ContextEvent[]; total: number }>("/search", {
      method: "POST",
      body: JSON.stringify({ query, ...options }),
    }),

  // --- Timeline ---
  getTimeline: (days = 7, limit = 100) =>
    request<{ events: ContextEvent[]; total: number }>(
      `/timeline?days=${days}&limit=${limit}`
    ),

  // --- Chat (核心对话) ---
  chat: (message: string, useContext = true) =>
    request<{ response: string; context_used: boolean }>("/chat", {
      method: "POST",
      body: JSON.stringify({ message, use_context: useContext }),
    }),

  // --- Insights (修复报错的关键点) ---
  getInsights: () => request<{ insights: Insight[] }>("/insights"),
  runAnalysis: () => request<{ new_insights: number; insights: Insight[] }>("/insights/analyze", { method: "POST" }),
  dismissInsight: (id: string) =>
    request<{ success: boolean }>(`/insights/${id}/dismiss`, { method: "POST" }),

  // --- Plugins ---
  listPlugins: () => request<{ plugins: Plugin[] }>("/plugins"),
  enablePlugin: (name: string, config: Record<string, unknown>) =>
    request<{ success: boolean; error?: string }>(`/plugins/${name}/enable`, {
      method: "POST",
      body: JSON.stringify({ config }),
    }),
  disablePlugin: (name: string) =>
    request<{ success: boolean }>(`/plugins/${name}/disable`, { method: "POST" }),
  syncPlugin: (name: string) =>
    request<{ success: boolean; new_events: number }>(`/plugins/${name}/sync`, { method: "POST" }),

  // --- Settings ---
  getSettings: () => request<Settings>("/settings"),
  updateSettings: (settings: Partial<Settings & { openai_api_key?: string; anthropic_api_key?: string }>) =>
    request<{ success: boolean; active_provider: string }>("/settings", {
      method: "POST",
      body: JSON.stringify(settings),
    }),
};