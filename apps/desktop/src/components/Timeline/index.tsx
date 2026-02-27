import { useEffect, useState } from "react";
import { useStore } from "../../stores/useStore";
import { ContextEvent } from "../../hooks/useLifeOSAPI";
import { formatDistanceToNow } from "date-fns";
import { zhCN } from "date-fns/locale";

const SOURCE_ICONS: Record<string, string> = {
  markdown_files: "📝",
  github: "🐙",
  google_calendar: "📅",
  notion: "🗒️",
  linear: "📋",
  slack: "💬",
};

const EVENT_COLORS: Record<string, string> = {
  "note.created": "bg-blue-500",
  "note.updated": "bg-blue-400",
  "code.committed": "bg-green-500",
  "code.pr.opened": "bg-emerald-500",
  "code.pr.merged": "bg-purple-500",
  "code.issue.opened": "bg-orange-500",
  "code.issue.closed": "bg-gray-500",
  "calendar.meeting": "bg-amber-500",
  "task.completed": "bg-teal-500",
};

const DAYS_OPTIONS = [3, 7, 14, 30];

export default function Timeline() {
  const { events, eventsLoading, loadTimeline } = useStore();
  const [days, setDays] = useState(7);
  const [selectedSource, setSelectedSource] = useState<string>("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    loadTimeline(days);
  }, [days]);

  const sources = ["all", ...new Set(events.map((e) => e.source))];

  const filtered = selectedSource === "all"
    ? events
    : events.filter((e) => e.source === selectedSource);

  // Group by date
  const byDate: Record<string, ContextEvent[]> = {};
  filtered.forEach((e) => {
    const d = e.timestamp.slice(0, 10);
    if (!byDate[d]) byDate[d] = [];
    byDate[d].push(e);
  });

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-800 px-6 py-4">
        <div>
          <h2 className="text-lg font-semibold text-white">时间轴</h2>
          <p className="text-xs text-gray-500">{filtered.length} 条记录</p>
        </div>
        <div className="flex gap-2">
          {/* Source filter */}
          <select
            value={selectedSource}
            onChange={(e) => setSelectedSource(e.target.value)}
            className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-1.5 text-xs text-gray-300 outline-none"
          >
            {sources.map((s) => (
              <option key={s} value={s}>
                {s === "all" ? "全部来源" : `${SOURCE_ICONS[s] || "📦"} ${s}`}
              </option>
            ))}
          </select>
          {/* Days filter */}
          <div className="flex rounded-lg border border-gray-700 overflow-hidden">
            {DAYS_OPTIONS.map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1.5 text-xs transition ${
                  days === d
                    ? "bg-purple-600 text-white"
                    : "bg-gray-900 text-gray-500 hover:text-gray-300"
                }`}
              >
                {d}天
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {eventsLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-purple-500 border-t-transparent" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="mb-3 text-4xl">📭</div>
            <p className="text-gray-500 text-sm">暂无记录</p>
            <p className="mt-1 text-xs text-gray-700">请先在插件设置中添加数据源</p>
          </div>
        ) : (
          Object.entries(byDate)
            .sort(([a], [b]) => b.localeCompare(a))
            .map(([date, dateEvents]) => (
              <div key={date} className="mb-6">
                <div className="mb-3 flex items-center gap-3">
                  <span className="text-xs font-medium text-gray-500">{formatDate(date)}</span>
                  <div className="flex-1 border-t border-gray-800" />
                  <span className="text-xs text-gray-700">{dateEvents.length} 条</span>
                </div>
                <div className="space-y-2 pl-3 border-l border-gray-800">
                  {dateEvents.map((event) => (
                    <EventCard
                      key={event.id}
                      event={event}
                      expanded={expandedId === event.id}
                      onToggle={() =>
                        setExpandedId(expandedId === event.id ? null : event.id)
                      }
                    />
                  ))}
                </div>
              </div>
            ))
        )}
      </div>
    </div>
  );
}

function EventCard({
  event,
  expanded,
  onToggle,
}: {
  event: ContextEvent;
  expanded: boolean;
  onToggle: () => void;
}) {
  const dotColor = EVENT_COLORS[event.event_type] || "bg-gray-500";
  const icon = SOURCE_ICONS[event.source] || "📦";
  const time = new Date(event.timestamp).toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div
      className="-ml-px cursor-pointer rounded-r-lg border border-transparent p-3 transition hover:border-gray-800 hover:bg-gray-900"
      onClick={onToggle}
    >
      <div className="flex items-start gap-3">
        <div className="flex items-center gap-2 shrink-0 mt-0.5">
          <div className={`h-2 w-2 rounded-full ${dotColor} -ml-[17px] ring-2 ring-gray-950`} />
          <span className="text-base">{icon}</span>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-300 truncate">
            {event.title || event.content.slice(0, 60)}
          </p>
          <div className="mt-0.5 flex items-center gap-2">
            <span className="text-xs text-gray-700">{time}</span>
            <span className="text-xs text-gray-700">{event.source}</span>
            {event.tags.slice(0, 2).map((tag) => (
              <span key={tag} className="text-xs text-purple-600">#{tag}</span>
            ))}
          </div>
        </div>
      </div>
      {expanded && event.content && (
        <div className="mt-2 ml-7 rounded-lg bg-gray-800/50 p-3">
          <p className="text-xs text-gray-400 leading-relaxed whitespace-pre-wrap">
            {event.content.slice(0, 400)}
            {event.content.length > 400 && "..."}
          </p>
        </div>
      )}
    </div>
  );
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);

  if (d.toDateString() === today.toDateString()) return "今天";
  if (d.toDateString() === yesterday.toDateString()) return "昨天";
  return d.toLocaleDateString("zh-CN", { month: "long", day: "numeric" });
}
