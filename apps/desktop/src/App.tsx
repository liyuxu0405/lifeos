import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BookOpen, MessageSquare, Clock, Lightbulb, Puzzle, Settings
} from "lucide-react";
import { useStore } from "./stores/useStore";
import DailyBrief from "./components/DailyBrief";
import ChatInterface from "./components/ChatInterface";
import Timeline from "./components/Timeline";
import InsightsPanel from "./components/Insights";
import PluginManager from "./components/PluginManager";
import SettingsPanel from "./components/Settings";

const NAV_ITEMS = [
  { id: "brief", icon: BookOpen, label: "简报" },
  { id: "chat", icon: MessageSquare, label: "对话" },
  { id: "timeline", icon: Clock, label: "时间轴" },
  { id: "insights", icon: Lightbulb, label: "洞察" },
  { id: "plugins", icon: Puzzle, label: "插件" },
  { id: "settings", icon: Settings, label: "设置" },
] as const;

export default function App() {
  const { activeTab, setActiveTab, isBackendReady, initialize, insights } = useStore();

  useEffect(() => {
    initialize();
  }, []);

  if (!isBackendReady) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-950">
        <div className="text-center">
          <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-purple-500 border-t-transparent" />
          <p className="text-gray-400">正在启动 LifeOS...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 overflow-hidden">
      {/* 侧边导航 */}
      <nav className="flex w-16 flex-col items-center gap-1 border-r border-gray-800 bg-gray-900 py-4">
        {/* Logo */}
        <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-purple-600">
          <span className="text-lg font-bold">L</span>
        </div>

        {NAV_ITEMS.map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            title={label}
            className={`relative flex h-10 w-10 items-center justify-center rounded-xl transition-all ${
              activeTab === id
                ? "bg-purple-600 text-white"
                : "text-gray-500 hover:bg-gray-800 hover:text-gray-300"
            }`}
          >
            <Icon size={18} />
            {/* 洞察红点 */}
            {id === "insights" && insights.length > 0 && (
              <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-amber-400" />
            )}
          </button>
        ))}
      </nav>

      {/* 主内容区 */}
      <main className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
            className="h-full"
          >
            {activeTab === "brief" && <DailyBrief />}
            {activeTab === "chat" && <ChatInterface />}
            {activeTab === "timeline" && <Timeline />}
            {activeTab === "insights" && <InsightsPanel />}
            {activeTab === "plugins" && <PluginManager />}
            {activeTab === "settings" && <SettingsPanel />}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
