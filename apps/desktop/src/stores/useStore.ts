/**
 * LifeOS 全局状态管理
 */
import { create } from "zustand";
import { api, DailyBrief, ContextEvent, Insight, Plugin, SystemStatus } from "../hooks/useLifeOSAPI";

interface LifeOSState {
  // Status
  status: SystemStatus | null;
  isBackendReady: boolean;

  // Navigation
  activeTab: "brief" | "chat" | "timeline" | "insights" | "plugins" | "settings";
  setActiveTab: (tab: LifeOSState["activeTab"]) => void;

  // Daily Brief
  todayBrief: DailyBrief | null;
  briefLoading: boolean;
  loadTodayBrief: (force?: boolean) => Promise<void>;

  // Timeline
  events: ContextEvent[];
  eventsLoading: boolean;
  loadTimeline: (days?: number) => Promise<void>;

  // Insights
  insights: Insight[];
  insightsLoading: boolean;
  loadInsights: () => Promise<void>;
  dismissInsight: (id: string) => Promise<void>;

  // Plugins
  plugins: Plugin[];
  pluginsLoading: boolean;
  loadPlugins: () => Promise<void>;
  enablePlugin: (name: string, config: Record<string, unknown>) => Promise<{ success: boolean; error?: string }>;
  disablePlugin: (name: string) => Promise<void>;
  syncPlugin: (name: string) => Promise<{ new_events: number }>;

  // Init
  initialize: () => Promise<void>;
}

export const useStore = create<LifeOSState>((set, get) => ({
  status: null,
  isBackendReady: false,
  activeTab: "brief",

  setActiveTab: (tab) => set({ activeTab: tab }),

  // ── Daily Brief ──
  todayBrief: null,
  briefLoading: false,
  loadTodayBrief: async (force = false) => {
    set({ briefLoading: true });
    try {
      const brief = await api.getTodayBrief(force);
      set({ todayBrief: brief });
    } catch (e) {
      console.error("Failed to load brief:", e);
    } finally {
      set({ briefLoading: false });
    }
  },

  // ── Timeline ──
  events: [],
  eventsLoading: false,
  loadTimeline: async (days = 7) => {
    set({ eventsLoading: true });
    try {
      const { events } = await api.getTimeline(days);
      set({ events });
    } catch (e) {
      console.error("Failed to load timeline:", e);
    } finally {
      set({ eventsLoading: false });
    }
  },

  // ── Insights ──
  insights: [],
  insightsLoading: false,
  loadInsights: async () => {
    set({ insightsLoading: true });
    try {
      const { insights } = await api.getInsights();
      set({ insights });
    } catch (e) {
      console.error("Failed to load insights:", e);
    } finally {
      set({ insightsLoading: false });
    }
  },
  dismissInsight: async (id: string) => {
    await api.dismissInsight(id);
    set((state) => ({ insights: state.insights.filter((i) => i.id !== id) }));
  },

  // ── Plugins ──
  plugins: [],
  pluginsLoading: false,
  loadPlugins: async () => {
    set({ pluginsLoading: true });
    try {
      const { plugins } = await api.listPlugins();
      set({ plugins });
    } catch (e) {
      console.error("Failed to load plugins:", e);
    } finally {
      set({ pluginsLoading: false });
    }
  },
  enablePlugin: async (name, config) => {
    const result = await api.enablePlugin(name, config);
    if (result.success) await get().loadPlugins();
    return result;
  },
  disablePlugin: async (name) => {
    await api.disablePlugin(name);
    await get().loadPlugins();
  },
  syncPlugin: async (name) => {
    return api.syncPlugin(name);
  },

  // ── Init ──
  initialize: async () => {
    // 等待后端就绪（最多 15 秒）
    let attempts = 0;
    while (attempts < 30) {
      try {
        const status = await api.status();
        set({ status, isBackendReady: true });
        break;
      } catch {
        await new Promise((r) => setTimeout(r, 500));
        attempts++;
      }
    }
    if (!get().isBackendReady) {
      console.error("Backend failed to start");
      return;
    }
    // 并行加载初始数据
    await Promise.all([
      get().loadTodayBrief(),
      get().loadInsights(),
      get().loadPlugins(),
    ]);
  },
}));
