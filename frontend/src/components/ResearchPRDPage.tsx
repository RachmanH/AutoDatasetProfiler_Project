import { useState, useEffect } from 'react';
import { getResearchSuggestions, generateResearchPRD } from '../api';
import type {
  AnalyzeResponse,
  ResearchTitleSuggestion,
  ResearchTaskSuggestion,
  ResearchPRDSuggestionsResponse,
} from '../types';

interface Props {
  analyzeData: AnalyzeResponse;
  onBack: () => void;
}

export default function ResearchPRDPage({ analyzeData, onBack }: Props) {
  const [suggestions, setSuggestions] = useState<ResearchPRDSuggestionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedTitleIdx, setSelectedTitleIdx] = useState(0);
  const [selectedTaskIdx, setSelectedTaskIdx] = useState(0);
  const [customTitle, setCustomTitle] = useState('');
  const [background, setBackground] = useState('');
  const [objectives, setObjectives] = useState('');
  const [questions, setQuestions] = useState('');
  const [targetColumn, setTargetColumn] = useState(analyzeData.primary_task_suggestion.target_column || '');
  const [notes, setNotes] = useState('');

  const [generating, setGenerating] = useState(false);
  const [prdResult, setPrdResult] = useState<string | null>(null);

  useEffect(() => {
    fetchSuggestions();
  }, []);

  async function fetchSuggestions() {
    setLoading(true);
    try {
      const res = await getResearchSuggestions(
        analyzeData.dataset_id,
        analyzeData.dataset_fingerprint,
        analyzeData.llm_understanding,
        analyzeData.primary_task_suggestion,
      );
      setSuggestions(res);
      if (res.research_questions.length > 0) {
        setQuestions(res.research_questions.join('\n'));
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to fetch suggestions');
    } finally {
      setLoading(false);
    }
  }

  const columns = analyzeData.preview.length > 0 ? Object.keys(analyzeData.preview[0]) : [];

  async function handleGenerate() {
    if (!suggestions) return;
    const title = customTitle || suggestions.title_suggestions[selectedTitleIdx]?.title || '';
    const task = suggestions.task_suggestions[selectedTaskIdx]?.task || analyzeData.primary_task_suggestion.suggested_task;

    setGenerating(true);
    setPrdResult(null);
    try {
      const res = await generateResearchPRD({
        dataset_id: analyzeData.dataset_id,
        selected_title: title,
        selected_task: task,
        research_background: background,
        research_objectives: objectives.split('\n').filter(s => s.trim()),
        research_questions: questions.split('\n').filter(s => s.trim()),
        target_column: targetColumn || null,
        additional_notes: notes || null,
        dataset_fingerprint: analyzeData.dataset_fingerprint,
        llm_understanding: analyzeData.llm_understanding,
      });
      if (res.success) {
        setPrdResult(res.prd_markdown);
      } else {
        setError('Failed to generate PRD. Please try again.');
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to generate PRD');
    } finally {
      setGenerating(false);
    }
  }

  function handleCopyPRD() {
    if (prdResult) {
      navigator.clipboard.writeText(prdResult);
    }
  }

  if (prdResult) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <button onClick={() => setPrdResult(null)} className="text-sm text-gray-500 hover:text-gray-700">
            &larr; Back to form
          </button>
          <button onClick={onBack} className="text-sm text-gray-500 hover:text-gray-700">
            Back to dashboard
          </button>
          <button onClick={handleCopyPRD} className="ml-auto text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded-lg">
            Copy Markdown
          </button>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="prose prose-sm max-w-none">
            {prdResult.split('\n').map((line, i) => {
              if (line.startsWith('# ')) return <h1 key={i} className="text-2xl font-bold text-gray-900 mt-6 mb-3">{line.slice(2)}</h1>;
              if (line.startsWith('## ')) return <h2 key={i} className="text-xl font-semibold text-gray-800 mt-5 mb-2 border-b border-gray-200 pb-1">{line.slice(3)}</h2>;
              if (line.startsWith('### ')) return <h3 key={i} className="text-lg font-medium text-gray-700 mt-4 mb-1">{line.slice(4)}</h3>;
              if (line.startsWith('- ')) return <li key={i} className="text-gray-700 ml-4">{line.slice(2)}</li>;
              if (line.startsWith('**') && line.endsWith('**')) return <p key={i} className="font-semibold text-gray-800 mt-2">{line.slice(2, -2)}</p>;
              if (line.trim() === '') return <br key={i} />;
              return <p key={i} className="text-gray-700 leading-relaxed">{line}</p>;
            })}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <button onClick={onBack} className="text-sm text-gray-500 hover:text-gray-700">
        &larr; Back to dashboard
      </button>

      <div className="text-center mb-2">
        <h2 className="text-2xl font-semibold text-gray-900">Generate PRD Riset</h2>
        <p className="text-gray-500 text-sm mt-1">
          Pilih judul, task, isi form, lalu generate PRD riset siap pakai.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
      )}

      {loading ? (
        <div className="flex flex-col items-center gap-3 py-12">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-500">AI sedang menganalisis dataset dan menyiapkan saran riset...</p>
        </div>
      ) : suggestions ? (
        <>
          {/* Title Selection */}
          <Section title="Pilih Judul Riset">
            <div className="space-y-2">
              {suggestions.title_suggestions.map((t, i) => (
                <label
                  key={i}
                  className={`block p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedTitleIdx === i && !customTitle
                      ? 'border-blue-400 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="title"
                    checked={selectedTitleIdx === i && !customTitle}
                    onChange={() => { setSelectedTitleIdx(i); setCustomTitle(''); }}
                    className="mr-2"
                  />
                  <span className="font-medium text-gray-800">{t.title}</span>
                  <p className="text-xs text-gray-500 mt-1 ml-5">{t.description}</p>
                  <div className="flex gap-2 mt-1 ml-5">
                    <span className="text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-700">{formatTask(t.task)}</span>
                    <span className="text-xs text-gray-400">{t.method_suggestion}</span>
                  </div>
                </label>
              ))}
              <div className="mt-2">
                <input
                  type="text"
                  placeholder="Atau tulis judul sendiri..."
                  value={customTitle}
                  onChange={(e) => setCustomTitle(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                />
              </div>
            </div>
          </Section>

          {/* Task Selection */}
          <Section title="Pilih Task Machine Learning">
            <div className="space-y-2">
              {suggestions.task_suggestions.map((t, i) => (
                <label
                  key={i}
                  className={`block p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedTaskIdx === i
                      ? 'border-green-400 bg-green-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="task"
                    checked={selectedTaskIdx === i}
                    onChange={() => setSelectedTaskIdx(i)}
                    className="mr-2"
                  />
                  <span className="font-medium text-gray-800">{formatTask(t.task)}</span>
                  <p className="text-xs text-gray-500 mt-1 ml-5">{t.description}</p>
                  <div className="flex flex-wrap gap-1 mt-2 ml-5">
                    {t.suitable_methods.map((m, j) => (
                      <span key={j} className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">{m}</span>
                    ))}
                  </div>
                  <div className="flex flex-wrap gap-1 mt-1 ml-5">
                    {t.evaluation_metrics.map((m, j) => (
                      <span key={j} className="text-xs px-2 py-0.5 rounded bg-purple-100 text-purple-700">{m}</span>
                    ))}
                  </div>
                </label>
              ))}
            </div>
          </Section>

          {/* Form */}
          <Section title="Detail Riset">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Latar Belakang</label>
                <textarea
                  value={background}
                  onChange={(e) => setBackground(e.target.value)}
                  placeholder="Jelaskan konteks masalah dan mengapa riset ini penting..."
                  rows={3}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tujuan Riset (satu per baris)</label>
                <textarea
                  value={objectives}
                  onChange={(e) => setObjectives(e.target.value)}
                  placeholder={"Menganalisis pola sentimen pada ulasan\nMembandingkan performa model klasifikasi\n..."}
                  rows={3}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Pertanyaan Riset (satu per baris)</label>
                <textarea
                  value={questions}
                  onChange={(e) => setQuestions(e.target.value)}
                  rows={4}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                />
                <p className="text-xs text-gray-400 mt-1">Pre-filled dari saran AI. Edit sesuai kebutuhan.</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Target Column</label>
                  <select
                    value={targetColumn}
                    onChange={(e) => setTargetColumn(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  >
                    <option value="">-- Auto --</option>
                    {columns.map(col => (
                      <option key={col} value={col}>{col}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Catatan Tambahan</label>
                  <input
                    type="text"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Misal: fokus pada metode ensemble"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  />
                </div>
              </div>
            </div>
          </Section>

          {/* Generate Button */}
          <div className="flex justify-center">
            <button
              onClick={handleGenerate}
              disabled={generating || (!customTitle && suggestions.title_suggestions.length === 0)}
              className="px-8 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {generating ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Generating PRD...
                </span>
              ) : (
                'Generate PRD Riset'
              )}
            </button>
          </div>
        </>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-500">Failed to load research suggestions.</p>
          <button onClick={fetchSuggestions} className="mt-2 text-blue-600 hover:text-blue-700 text-sm font-medium">
            Try again
          </button>
        </div>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <h3 className="px-4 py-3 text-sm font-medium text-gray-700 border-b border-gray-200 bg-gray-50">{title}</h3>
      <div className="p-4">{children}</div>
    </div>
  );
}

function formatTask(task: string): string {
  return task.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}
