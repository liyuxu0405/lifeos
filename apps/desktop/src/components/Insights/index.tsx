import { useEffect } from "react";
import { Lightbulb, X, Zap, TrendingDown, HelpCircle, RefreshCw } from "lucide-react";
import { useStore } from "../../stores/useStore";
import { Insight } from "../../hooks/useLifeOSAPI";
import { api } from "../../hooks/useLifeOSAPI";

const INSIGHT_ICONS: Record<string, React.ReactNode> = {
  repeated_thought: <Zap size={16} className="text-amber-400" />,
  goal_drift: <TrendingDown size={16} className="text-red-400" />,
  knowledge_gap: <HelpCircle size={16} className="text-blue-400" />,
  overdue_task: <Zap size={16} className="text-orange-400" />,
  relationship_signal: <Lightbulb size={16} className="text-purple-400" />,
};

const INSIGHT_COLORS: Record<string, string> = {
  repeated_thought: "border-amber-800/40 bg-amber-900/10",
  goal_drift: "border-red-800/40 bg-red-900/10",
  knowledge_gap: "border-blue-800/40 bg-blue-900/10",
  overdue_task: "border-orange-800/40 bg-orange-900/10",
  relationship_signal: "border-purple-800/40 bg-purple-900/10",
};

export default function InsightsPanel() {
  const { insights, insightsLoading, loadInsights, dismissInsight } = useStore();

  useEffect(() => {
    loadInsights();
  }, []);

  const runAnalysis = async () => {
    await api.runAnalysis();
    await loadInsights();
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-gray-800 px-6 py-4">
        <div>
          <h2 className="text-lg font-semibold text-white">洞察</h2>
          <p className="text-xs text-gray-500">AI 主动发现的行为规律</p>
        </div>
        <button
          onClick={runAnalysis}
          disabled={insightsLoading}
          className="flex items-center gap-2 rounded-lg border border-gray-700 px-3 py-1.5 text-sm text-gray-400 transition hover:border-purple-500 hover:text-purple-400 disabled:opacity-50"
        >
          <RefreshCw size={14} className={insightsLoading ? "animate-spin" : ""} />
          立即分析
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {insightsLoading && insights.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-purple-500 border-t-transparent" />
          </div>
        ) : insights.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="mb-3 text-4xl">🔍</div>
            <p className="text-gray-500 text-sm">暂无洞察</p>
            <p className="mt-1 text-xs text-gray-700">
              积累更多数据后，AI 会发现你的行为规律
            </p>
            <button
              onClick={runAnalysis}
              className="mt-4 rounded-lg bg-purple-600 px-4 py-2 text-sm text-white hover:bg-purple-500 transition"
            >
              立即分析
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {insights.map((insight) => (
              <InsightCard
                key={insight.id}
                insight={insight}
                onDismiss={() => dismissInsight(insight.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function InsightCard({
  insight,
  onDismiss,
}: {
  insight: Insight;
  onDismiss: () => void;
}) {
  const colorClass = INSIGHT_COLORS[insight.insight_type] || "border-gray-800 bg-gray-900";
  const icon = INSIGHT_ICONS[insight.insight_type] || <Lightbulb size={16} />;
  const confidence = Math.round(insight.confidence * 100);

  return (
    <div className={`relative rounded-xl border ${colorClass} p-4`}>
      <button
        onClick={onDismiss}
        className="absolute right-3 top-3 text-gray-700 hover:text-gray-400 transition"
      >
        <X size={14} />
      </button>

      <div className="flex items-start gap-3 pr-6">
        <div className="mt-0.5 shrink-0">{icon}</div>
        <div className="flex-1">
          <p className="font-medium text-gray-200 text-sm">{insight.title}</p>
          <p className="mt-1 text-sm text-gray-400 leading-relaxed">{insight.description}</p>

          {insight.evidence.length > 0 && (
            <div className="mt-3 space-y-1">
              {insight.evidence.slice(0, 3).map((e, i) => (
                <p key={i} className="text-xs text-gray-600 flex gap-2">
                  <span>»</span>
                  <span>{e}</span>
                </p>
              ))}
            </div>
          )}

          <div className="mt-3 flex items-center justify-between">
            <p className="text-xs text-gray-500 italic">{insight.suggested_action}</p>
            <span className="shrink-0 ml-3 text-xs text-gray-700">{confidence}% 置信度</span>
          </div>
        </div>
      </div>
    </div>
  );
}
