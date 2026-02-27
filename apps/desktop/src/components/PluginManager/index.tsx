import React, { useState, useEffect } from "react";
// 使用 import type 导入接口，彻底解决与本地组件名的命名冲突
import type { Plugin, ConfigField } from "../../hooks/useLifeOSAPI";
import { api } from "../../hooks/useLifeOSAPI";

// 子组件：渲染单个配置项
const ConfigFieldItem = ({
  label,
  field,
  value,
  onChange
}: {
  label: string;
  field: ConfigField;
  value: any;
  onChange: (val: any) => void
}) => {
  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-300 mb-1">
        {field.label || label} {field.required && <span className="text-red-500">*</span>}
      </label>

      {field.type === "string" && (
        <input
          type={field.secret ? "password" : "text"}
          className="w-full p-2 bg-gray-800 border border-gray-700 rounded text-white focus:border-purple-500 outline-none transition-colors"
          value={value || ""}
          placeholder={field.placeholder || `请输入 ${field.label}...`}
          onChange={(e) => onChange(e.target.value)}
        />
      )}

      {field.description && (
        <p className="text-xs text-gray-500 mt-1">{field.description}</p>
      )}
    </div>
  );
};

export const PluginManager: React.FC = () => {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingPlugin, setEditingPlugin] = useState<string | null>(null);
  const [configValues, setConfigValues] = useState<Record<string, any>>({});

  useEffect(() => {
    fetchPlugins();
  }, []);

  const fetchPlugins = async () => {
    try {
      const data = await api.listPlugins();
      setPlugins(data.plugins);
    } catch (err) {
      console.error("加载插件失败:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (plugin: Plugin) => {
    if (plugin.enabled) {
      if (confirm(`确定要禁用 ${plugin.display_name} 吗？`)) {
        await api.disablePlugin(plugin.name);
        fetchPlugins();
      }
    } else {
      setEditingPlugin(plugin.name);
      setConfigValues({});
    }
  };

  const handleEnable = async (name: string) => {
    try {
      const res = await api.enablePlugin(name, configValues);
      if (res.success) {
        setEditingPlugin(null);
        fetchPlugins();
      } else {
        alert(`开启失败: ${res.error}`);
      }
    } catch (err) {
      alert("提交配置时发生错误");
    }
  };

  if (loading) return <div className="p-8 text-gray-400">正在同步插件状态...</div>;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-white">插件管理</h1>
        <button
          onClick={fetchPlugins}
          className="text-sm text-purple-400 hover:text-purple-300 transition-colors"
        >
          刷新列表
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {plugins.map((plugin) => (
          <div key={plugin.name} className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-all">
            <div className="flex items-start justify-between">
              <div className="flex gap-4">
                <div className="text-3xl">{plugin.icon || "🧩"}</div>
                <div>
                  <h3 className="text-lg font-semibold text-white">{plugin.display_name}</h3>
                  <p className="text-sm text-gray-400 mt-1">{plugin.description}</p>
                  <div className="flex gap-3 mt-3">
                    <span className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded">
                      {plugin.category}
                    </span>
                    {plugin.last_sync && (
                      <span className="text-xs text-gray-500 py-1">
                        上次同步: {new Date(plugin.last_sync).toLocaleString()}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex flex-col items-end gap-2">
                <button
                  onClick={() => handleToggle(plugin)}
                  className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
                    plugin.enabled 
                      ? "bg-red-900/20 text-red-400 hover:bg-red-900/30" 
                      : "bg-purple-600 text-white hover:bg-purple-500"
                  }`}
                >
                  {plugin.enabled ? "禁用" : "去开启"}
                </button>
                {plugin.enabled && (
                   <button
                    onClick={() => api.syncPlugin(plugin.name).then(() => fetchPlugins())}
                    className="text-xs text-gray-500 hover:text-purple-400"
                   >
                     立即同步
                   </button>
                )}
              </div>
            </div>

            {/* 配置面板 */}
            {editingPlugin === plugin.name && (
              <div className="mt-6 pt-6 border-t border-gray-800 animate-in fade-in slide-in-from-top-2">
                <h4 className="text-sm font-bold text-purple-400 mb-4">配置选项</h4>
                {Object.entries(plugin.config_schema).map(([key, field]) => (
                  <ConfigFieldItem
                    key={key}
                    label={key}
                    field={field}
                    value={configValues[key]}
                    onChange={(val) => setConfigValues({ ...configValues, [key]: val })}
                  />
                ))}
                <div className="flex gap-3 mt-6">
                  <button
                    onClick={() => handleEnable(plugin.name)}
                    className="flex-1 bg-purple-600 hover:bg-purple-500 text-white py-2 rounded-lg font-medium transition-colors"
                  >
                    保存并开启
                  </button>
                  <button
                    onClick={() => setEditingPlugin(null)}
                    className="px-6 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
                  >
                    取消
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};