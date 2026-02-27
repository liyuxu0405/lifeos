import { useEffect, useState } from "react";
import { useStore } from "../../stores/useStore";
import { Plugin, ConfigField } from "../../hooks/useLifeOSAPI";
import { RefreshCw, Check, X, ChevronRight, Loader2 } from "lucide-react";

const CATEGORY_LABELS: Record<string, string> = {
  notes: "📝 笔记",
  code: "💻 代码",
  calendar: "📅 日历",
  communication: "💬 沟通",
  browser: "🌐 浏览器",
  other: "📦 其他",
};

export default function PluginManager() {
  const { plugins, pluginsLoading, loadPlugins, enablePlugin, disablePlugin, syncPlugin } = useStore();
  const [configuring, setConfiguring] = useState<Plugin | null>(null);

  useEffect(() => {
    loadPlugins();
  }, []);

  const byCategory = plugins.reduce((acc, p) => {
    const cat = p.category || "other";
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(p);
    return acc;
  }, {} as Record<string, Plugin[]>);

  return (
    <div className="flex h-full">
      {/* Plugin List */}
      <div className="flex-1 overflow-y-auto">
        <div className="border-b border-gray-800 px-6 py-4">
          <h2 className="text-lg font-semibold text-white">数据源插件</h2>
          <p className="text-xs text-gray-500">连接你的工具，让 AI 真正了解你</p>
        </div>

        <div className="p-6 space-y-6">
          {Object.entries(byCategory).map(([cat, catPlugins]) => (
            <div key={cat}>
              <p className="mb-3 text-xs font-medium text-gray-600 uppercase tracking-wider">
                {CATEGORY_LABELS[cat] || cat}
              </p>
              <div className="space-y-2">
                {catPlugins.map((plugin) => (
                  <PluginRow
                    key={plugin.name}
                    plugin={plugin}
                    onConfigure={() => setConfiguring(plugin)}
                    onDisable={() => disablePlugin(plugin.name)}
                    onSync={() => syncPlugin(plugin.name)}
                  />
                ))}
              </div>
            </div>
          ))}

          {/* Community plugins hint */}
          <div className="rounded-xl border border-dashed border-gray-800 p-4 text-center">
            <p className="text-sm text-gray-600">想要更多插件？</p>
            <a
              href="https://github.com/lifeos-app/lifeos/blob/main/docs/PLUGIN_GUIDE.md"
              target="_blank"
              className="mt-1 text-xs text-purple-600 hover:text-purple-400 transition"
            >
              查看插件开发指南 →
            </a>
          </div>
        </div>
      </div>

      {/* Config Panel */}
      {configuring && (
        <ConfigPanel
          plugin={configuring}
          onClose={() => setConfiguring(null)}
          onSave={async (config) => {
            const result = await enablePlugin(configuring.name, config);
            if (result.success) setConfiguring(null);
            return result;
          }}
        />
      )}
    </div>
  );
}

function PluginRow({
  plugin,
  onConfigure,
  onDisable,
  onSync,
}: {
  plugin: Plugin;
  onConfigure: () => void;
  onDisable: () => void;
  onSync: () => void;
}) {
  const [syncing, setSyncing] = useState(false);

  const handleSync = async () => {
    setSyncing(true);
    await onSync();
    setSyncing(false);
  };

  return (
    <div className="flex items-center gap-3 rounded-xl border border-gray-800 bg-gray-900/50 p-4 transition hover:border-gray-700">
      <span className="text-2xl shrink-0">{plugin.icon}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-200">{plugin.display_name}</p>
        <p className="text-xs text-gray-600 truncate">{plugin.description}</p>
        {plugin.last_sync && (
          <p className="text-xs text-gray-700 mt-0.5">
            上次同步: {new Date(plugin.last_sync).toLocaleString("zh-CN")}
          </p>
        )}
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {plugin.enabled ? (
          <>
            <span className="flex items-center gap-1 rounded-full bg-green-900/40 px-2 py-0.5 text-xs text-green-400">
              <Check size={10} />
              已连接
            </span>
            <button
              onClick={handleSync}
              disabled={syncing}
              className="rounded-lg border border-gray-700 p-1.5 text-gray-500 hover:text-gray-300 transition disabled:opacity-50"
              title="立即同步"
            >
              <RefreshCw size={13} className={syncing ? "animate-spin" : ""} />
            </button>
            <button
              onClick={onDisable}
              className="rounded-lg border border-gray-700 p-1.5 text-gray-500 hover:text-red-400 transition"
              title="禁用"
            >
              <X size={13} />
            </button>
          </>
        ) : (
          <button
            onClick={onConfigure}
            className="flex items-center gap-1.5 rounded-lg bg-purple-600 px-3 py-1.5 text-xs text-white hover:bg-purple-500 transition"
          >
            连接
            <ChevronRight size={13} />
          </button>
        )}
      </div>
    </div>
  );
}

function ConfigPanel({
  plugin,
  onClose,
  onSave,
}: {
  plugin: Plugin;
  onClose: () => void;
  onSave: (config: Record<string, unknown>) => Promise<{ success: boolean; error?: string }>;
}) {
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleSave = async () => {
    setSaving(true);
    setError("");
    const result = await onSave(formData);
    if (!result.success) {
      setError(result.error || "配置失败，请检查输入");
    }
    setSaving(false);
  };

  return (
    <div className="w-96 border-l border-gray-800 bg-gray-950 flex flex-col">
      <div className="flex items-center justify-between border-b border-gray-800 px-5 py-4">
        <div className="flex items-center gap-2">
          <span className="text-xl">{plugin.icon}</span>
          <span className="font-medium text-white">{plugin.display_name}</span>
        </div>
        <button onClick={onClose} className="text-gray-600 hover:text-gray-400 transition">
          <X size={18} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {Object.entries(plugin.config_schema).map(([key, field]) => (
          <ConfigField
            key={key}
            fieldKey={key}
            field={field}
            value={formData[key] || ""}
            onChange={(v) => setFormData((prev) => ({ ...prev, [key]: v }))}
          />
        ))}

        {error && (
          <div className="rounded-lg border border-red-800 bg-red-900/20 p-3 text-sm text-red-400">
            {error}
          </div>
        )}
      </div>

      <div className="border-t border-gray-800 p-5">
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-purple-600 py-2.5 text-sm font-medium text-white hover:bg-purple-500 transition disabled:opacity-50"
        >
          {saving ? (
            <>
              <Loader2 size={15} className="animate-spin" />
              正在连接...
            </>
          ) : (
            "保存并连接"
          )}
        </button>
      </div>
    </div>
  );
}

function ConfigFieldComponent({
  fieldKey,
  field,
  value,
  onChange,
}: {
  fieldKey: string;
  field: ConfigField;
  value: string;
  onChange: (v: string) => void;
}) {
  const isTextarea = field.type === "textarea";

  return (
    <div className="space-y-1.5">
      <label className="block text-sm text-gray-300">
        {field.label}
        {field.required && <span className="ml-1 text-red-500">*</span>}
      </label>
      {field.description && (
        <p className="text-xs text-gray-600 whitespace-pre-line">{field.description}</p>
      )}
      {isTextarea ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          rows={6}
          className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-200 placeholder-gray-700 outline-none focus:border-purple-600 transition font-mono"
        />
      ) : (
        <input
          type={field.secret ? "password" : "text"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-200 placeholder-gray-700 outline-none focus:border-purple-600 transition"
        />
      )}
    </div>
  );
}

const ConfigField = ConfigFieldComponent;
