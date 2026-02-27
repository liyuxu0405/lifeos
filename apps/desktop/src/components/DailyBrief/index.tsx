import { useEffect } from "react";
import { RefreshCw, Star, TrendingUp, CheckCircle, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { useStore } from "../../stores/useStore";

export default function DailyBrief() {
  const { todayBrief, briefLoading, loadTodayBrief } = useStore();

  useEffect(() => {
    if (!todayBrief) loadTodayBrief();
  }, []);

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="mx-auto max-w-2xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-white">今日简报</h1>
            <p className="text-sm text-gray-500">
              {new Date().toLocaleDateString("zh-CN", {
                year: "numeric",
                month: "long",
                day: "numeric",
                weekday: "long",
              })}
            </p>
          </div>
          <button
            onClick={() => loadTodayBrief(true)}
            disabled={briefLoading}
            className="flex items-center gap-2 rounded-lg border border-gray-700 px-3 py-1.5 text-sm text-gray-400 transition hover:border-purple-500 hover:text-purple-400 disabled:opacity-50"
          >
            <RefreshCw size={14} className={briefLoading ? "animate-spin" : ""} />
            重新生成
          </button>
        </div>

        {briefLoading && !todayBrief ? (
          <LoadingSkeleton />
        ) : todayBrief ? (
          <div className="space-y-5">
            {/* Greeting */}
            <Card gradient="from-purple-900/30 to-blue-900/20">
              <div className="flex gap-3">
                <span className="text-2xl">☀️</span>
                <p className="text-gray-200 leading-relaxed">{todayBrief.greeting}</p>
              </div>
            </Card>

            {/* Highlights */}
            {todayBrief.highlights.length > 0 && (
              <Card>
                <SectionTitle icon={<Star size={16} className="text-amber-400" />} title="近期亮点" />
                <ul className="mt-3 space-y-2">
                  {todayBrief.highlights.map((h, i) => (
                    <li key={i} className="flex gap-2 text-gray-300 text-sm leading-relaxed">
                      <span className="mt-0.5 text-amber-400/60">▸</span>
                      {h}
                    </li>
                  ))}
                </ul>
              </Card>
            )}

            {/* Patterns - THE WOW MOMENT */}
            {todayBrief.patterns.length > 0 && (
              <Card gradient="from-emerald-900/20 to-teal-900/10" border="border-emerald-800/40">
                <SectionTitle
                  icon={<TrendingUp size={16} className="text-emerald-400" />}
                  title="发现的规律"
                  badge="✨ AI 发现"
                />
                <ul className="mt-3 space-y-2">
                  {todayBrief.patterns.map((p, i) => (
                    <li key={i} className="flex gap-2 text-gray-300 text-sm leading-relaxed">
                      <span className="mt-0.5 text-emerald-400">◆</span>
                      {p}
                    </li>
                  ))}
                </ul>
              </Card>
            )}

            {/* Priorities */}
            {todayBrief.priorities.length > 0 && (
              <Card>
                <SectionTitle icon={<CheckCircle size={16} className="text-blue-400" />} title="今日建议" />
                <ol className="mt-3 space-y-2">
                  {todayBrief.priorities.map((p, i) => (
                    <li key={i} className="flex gap-3 text-gray-300 text-sm leading-relaxed">
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-900/60 text-xs text-blue-400 font-medium">
                        {i + 1}
                      </span>
                      {p}
                    </li>
                  ))}
                </ol>
              </Card>
            )}

            {/* Reflection */}
            {todayBrief.reflection && (
              <Card gradient="from-purple-900/20 to-pink-900/10" border="border-purple-800/30">
                <div className="flex gap-3 items-start">
                  <Sparkles size={16} className="mt-0.5 shrink-0 text-purple-400" />
                  <p className="text-gray-400 text-sm italic">{todayBrief.reflection}</p>
                </div>
              </Card>
            )}

            <p className="text-center text-xs text-gray-700 pb-4">
              生成于 {new Date(todayBrief.generated_at).toLocaleTimeString("zh-CN")}
            </p>
          </div>
        ) : (
          <EmptyState onGenerate={() => loadTodayBrief(true)} />
        )}
      </div>
    </div>
  );
}

function Card({
  children,
  gradient = "",
  border = "border-gray-800",
}: {
  children: React.ReactNode;
  gradient?: string;
  border?: string;
}) {
  return (
    <div className={`rounded-xl border ${border} bg-gradient-to-br ${gradient || "from-gray-900 to-gray-900"} p-4`}>
      {children}
    </div>
  );
}

function SectionTitle({
  icon,
  title,
  badge,
}: {
  icon: React.ReactNode;
  title: string;
  badge?: string;
}) {
  return (
    <div className="flex items-center gap-2">
      {icon}
      <span className="text-sm font-medium text-gray-300">{title}</span>
      {badge && (
        <span className="rounded-full bg-emerald-900/50 px-2 py-0.5 text-xs text-emerald-400">
          {badge}
        </span>
      )}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {[80, 120, 100, 90].map((h, i) => (
        <div key={i} className={`h-${h === 80 ? '20' : h === 120 ? '28' : h === 100 ? '24' : '20'} rounded-xl bg-gray-900`} />
      ))}
    </div>
  );
}

function EmptyState({ onGenerate }: { onGenerate: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="mb-4 text-5xl">🌅</div>
      <h3 className="mb-2 text-lg font-medium text-gray-300">今日简报尚未生成</h3>
      <p className="mb-6 text-sm text-gray-600">
        添加数据源后，LifeOS 每天早上 8 点自动生成简报
      </p>
      <button
        onClick={onGenerate}
        className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-500 transition"
      >
        立即生成
      </button>
    </div>
  );
}
