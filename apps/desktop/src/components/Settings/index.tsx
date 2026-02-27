import { useEffect, useState } from "react";
import { api, Settings } from "../../hooks/useLifeOSAPI";
import { Save, Check, ExternalLink } from "lucide-react";

export default function SettingsPanel() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [form, setForm] = useState({
    ollama_url: "",
    chat_model: "",
    embedding_model: "",
    openai_api_key: "",
    anthropic_api_key: "",
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [activeProvider, setActiveProvider] = useState("");

  useEffect(() => {
    api.getSettings().then((s) => {
      setSettings(s);
      setForm((prev) => ({
        ...prev,
        ollama_url: s.ollama_url,
        chat_model: s.chat_model,
        embedding_model: s.embedding_model,
      }));
    });
    api.status().then((s) => setActiveProvider(s.llm_provider));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    const result = await api.updateSettings(form);
    setActiveProvider(result.active_provider);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const update = (key: string, value: string) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  return (
    <div className="h-full overflow-y-auto">
      <div className="border-b border-gray-800 px-6 py-4">
        <h2 className="text-lg font-semibold text-white">设置</h2>
        {activeProvider && (
          <p className="text-xs text-gray-500">
            当前 LLM：<span className="text-purple-400">{activeProvider}</span>
          </p>
        )}
      </div>

      <div className="mx-auto max-w-xl p-6 space-y-8">
        {/* Ollama Section */}
        <Section title="🦙 本地 Ollama（隐私优先，推荐）">
          <Field label="Ollama 地址">
            <input
              value={form.ollama_url}
              onChange={(e) => update("ollama_url", e.target.value)}
              placeholder="http://localhost:11434"
              className={inputClass}
            />
          </Field>
          <Field
            label="对话模型"
            hint="推荐 llama3.1:8b (8GB 显存) 或 qwen2.5:7b"
          >
            <input
              value={form.chat_model}
              onChange={(e) => update("chat_model", e.target.value)}
              placeholder="llama3.1:8b"
              className={inputClass}
            />
          </Field>
          <Field
            label="Embedding 模型"
            hint="强烈推荐 nomic-embed-text，本地最佳"
          >
            <input
              value={form.embedding_model}
              onChange={(e) => update("embedding_model", e.target.value)}
              placeholder="nomic-embed-text"
              className={inputClass}
            />
          </Field>
          <div className="flex gap-2">
            <a
              href="https://ollama.com/download"
              target="_blank"
              className="text-xs text-purple-500 hover:text-purple-400 flex items-center gap-1"
            >
              下载 Ollama <ExternalLink size={11} />
            </a>
            <span className="text-xs text-gray-700">·</span>
            <code className="text-xs text-gray-600">ollama pull llama3.1:8b</code>
          </div>
        </Section>

        {/* OpenAI Section */}
        <Section title="🤖 OpenAI（备选云端 LLM）">
          <Field label="API Key">
            <input
              type="password"
              value={form.openai_api_key}
              onChange={(e) => update("openai_api_key", e.target.value)}
              placeholder={settings?.has_openai_key ? "已配置（输入新值覆盖）" : "sk-..."}
              className={inputClass}
            />
          </Field>
        </Section>

        {/* Anthropic Section */}
        <Section title="🌊 Anthropic Claude（备选云端 LLM）">
          <Field label="API Key">
            <input
              type="password"
              value={form.anthropic_api_key}
              onChange={(e) => update("anthropic_api_key", e.target.value)}
              placeholder={settings?.has_anthropic_key ? "已配置（输入新值覆盖）" : "sk-ant-..."}
              className={inputClass}
            />
          </Field>
        </Section>

        {/* Data Section */}
        <Section title="💾 数据存储">
          <p className="text-sm text-gray-500">
            所有数据存储在本地：<code className="text-xs text-gray-400">~/.lifeos/data/</code>
          </p>
          <p className="text-xs text-gray-700 mt-1">
            数据完全归你所有，不会上传到任何服务器（使用本地 Ollama 时）
          </p>
        </Section>

        {/* Save Button */}
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-purple-600 py-3 text-sm font-medium text-white hover:bg-purple-500 transition disabled:opacity-50"
        >
          {saved ? (
            <>
              <Check size={15} />
              已保存
            </>
          ) : (
            <>
              <Save size={15} />
              {saving ? "保存中..." : "保存设置"}
            </>
          )}
        </button>
      </div>
    </div>
  );
}

const inputClass =
  "w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-200 placeholder-gray-700 outline-none focus:border-purple-600 transition";

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <h3 className="mb-4 text-sm font-medium text-gray-400">{title}</h3>
      <div className="space-y-4 rounded-xl border border-gray-800 bg-gray-900/30 p-4">
        {children}
      </div>
    </div>
  );
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label className="block text-sm text-gray-300">{label}</label>
      {children}
      {hint && <p className="text-xs text-gray-600">{hint}</p>}
    </div>
  );
}
