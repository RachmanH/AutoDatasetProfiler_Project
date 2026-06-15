import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, ScatterChart, Scatter,
} from 'recharts';
import type { AnalyzeResponse, ChartData as ChartDataType } from '../types';

interface Props {
  analyzeData: AnalyzeResponse;
  onReset: () => void;
  onResearch: () => void;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#6b7280'];

export default function ResultDashboard({ analyzeData, onReset, onResearch }: Props) {
  const { overview, column_profiles, data_quality, eda_charts, rule_based_task_suggestion, llm_understanding, primary_task_suggestion, preprocessing_previews } = analyzeData;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <button onClick={onReset} className="text-sm text-gray-500 hover:text-gray-700">
          &larr; Upload new dataset
        </button>
        <button
          onClick={onResearch}
          className="ml-auto px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700"
        >
          Generate PRD Riset
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        <SummaryCard label="Rows" value={overview.rows.toLocaleString()} />
        <SummaryCard label="Columns" value={overview.columns.toString()} />
        <SummaryCard label="Numeric" value={overview.numeric_columns.toString()} color="blue" />
        <SummaryCard label="Categorical" value={overview.categorical_columns.toString()} color="green" />
        <SummaryCard label="Boolean" value={overview.boolean_columns.toString()} color="purple" />
        <SummaryCard label="Missing Values" value={overview.total_missing_values.toLocaleString()} color={overview.total_missing_values > 0 ? 'red' : undefined} />
        <SummaryCard label="Duplicate Rows" value={overview.duplicate_rows.toLocaleString()} />
        <SummaryCard label="Suggested Task" value={formatTask(primary_task_suggestion.suggested_task)} color="blue" />
      </div>

      {/* Primary Task Suggestion (LLM or Rule-Based) */}
      <Section title="ML Task Suggestion">
        <div className={`border rounded-lg p-4 ${
          primary_task_suggestion.source === 'llm'
            ? 'bg-emerald-50 border-emerald-200'
            : 'bg-blue-50 border-blue-200'
        }`}>
          <div className="flex items-center gap-2 mb-2">
            <span className={`text-xs px-2 py-0.5 rounded font-medium ${
              primary_task_suggestion.source === 'llm'
                ? 'bg-emerald-200 text-emerald-800'
                : 'bg-blue-200 text-blue-800'
            }`}>
              {primary_task_suggestion.source === 'llm' ? 'AI Analysis' : 'Rule-Based'}
            </span>
            {primary_task_suggestion.confidence && (
              <span className={`text-xs px-2 py-0.5 rounded ${
                primary_task_suggestion.confidence === 'high' ? 'bg-green-100 text-green-700' :
                primary_task_suggestion.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                'bg-gray-100 text-gray-600'
              }`}>
                {primary_task_suggestion.confidence} confidence
              </span>
            )}
            {primary_task_suggestion.domain_guess && (
              <span className="text-xs text-gray-500">
                Domain: {primary_task_suggestion.domain_guess}
              </span>
            )}
          </div>
          <p className="font-semibold text-gray-900 text-lg">{formatTask(primary_task_suggestion.suggested_task)}</p>
          <p className="text-sm text-gray-700 mt-1">{primary_task_suggestion.reason}</p>
          {primary_task_suggestion.target_column && (
            <p className="text-xs text-gray-500 mt-1">
              Target: <span className="font-medium">{primary_task_suggestion.target_column}</span>
            </p>
          )}
        </div>

        {/* Target Candidates from LLM */}
        {primary_task_suggestion.target_candidates && primary_task_suggestion.target_candidates.length > 0 && (
          <div className="mt-3">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Target Candidates</h4>
            <div className="space-y-2">
              {primary_task_suggestion.target_candidates.map((tc, i) => (
                <div key={i} className="bg-gray-50 rounded-lg p-3">
                  <p className="font-medium text-gray-800 text-sm">
                    {tc.column}{' '}
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      tc.confidence === 'high' ? 'bg-green-100 text-green-700' :
                      tc.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {tc.confidence}
                    </span>
                  </p>
                  <p className="text-xs text-gray-600 mt-1">{tc.reason}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Rule-Based comparison */}
        {primary_task_suggestion.source === 'llm' && rule_based_task_suggestion.suggested_task !== primary_task_suggestion.suggested_task && (
          <div className="mt-3 bg-gray-50 border border-gray-200 rounded-lg p-3">
            <p className="text-xs font-medium text-gray-500 mb-1">Rule-Based Suggestion (for comparison)</p>
            <p className="text-sm text-gray-700 font-medium">{formatTask(rule_based_task_suggestion.suggested_task)}</p>
            <p className="text-xs text-gray-500 mt-0.5">{rule_based_task_suggestion.reason}</p>
          </div>
        )}
      </Section>

      {/* Data Quality */}
      <Section title="Data Quality Check">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data_quality.id_like_columns.length > 0 && (
            <QualityItem type="warning" text={`ID-like columns: ${data_quality.id_like_columns.join(', ')}. Do not use as model features.`} />
          )}
          {data_quality.constant_columns.length > 0 && (
            <QualityItem type="warning" text={`Constant columns: ${data_quality.constant_columns.join(', ')}. Only 1 unique value.`} />
          )}
          {data_quality.high_cardinality_columns.length > 0 && (
            <QualityItem type="info" text={`High-cardinality columns: ${data_quality.high_cardinality_columns.join(', ')}. Avoid direct one-hot encoding.`} />
          )}
          {data_quality.duplicate_rows > 0 && (
            <QualityItem type="warning" text={`${data_quality.duplicate_rows} duplicate rows (${data_quality.duplicate_percentage}%).`} />
          )}
          {data_quality.total_missing_values > 0 && (
            <QualityItem type="info" text={`${data_quality.total_missing_values} total missing values across all columns.`} />
          )}
          {data_quality.id_like_columns.length === 0 && data_quality.constant_columns.length === 0 && data_quality.duplicate_rows === 0 && data_quality.total_missing_values === 0 && (
            <QualityItem type="success" text="No major data quality issues detected." />
          )}
        </div>
      </Section>

      {/* Missing Value Details */}
      {column_profiles.some(p => p.missing_count > 0) && (
        <Section title="Missing Values by Column">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Column</th>
                  <th className="px-3 py-2 text-right font-medium text-gray-600">Missing</th>
                  <th className="px-3 py-2 text-right font-medium text-gray-600">%</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Recommendation</th>
                </tr>
              </thead>
              <tbody>
                {column_profiles.filter(p => p.missing_count > 0).sort((a, b) => b.missing_count - a.missing_count).map(p => (
                  <tr key={p.column} className="border-b border-gray-100">
                    <td className="px-3 py-2 font-medium text-gray-800">{p.column}</td>
                    <td className="px-3 py-2 text-right text-gray-600">{p.missing_count}</td>
                    <td className="px-3 py-2 text-right text-gray-600">{p.missing_percentage}%</td>
                    <td className="px-3 py-2 text-gray-500 text-xs">{missingRecommendation(p.missing_percentage)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}

      {/* Column Profile Table */}
      <Section title="Column Profiles">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="px-3 py-2 text-left font-medium text-gray-600">Column</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">Type</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">Detected</th>
                <th className="px-3 py-2 text-right font-medium text-gray-600">Unique</th>
                <th className="px-3 py-2 text-right font-medium text-gray-600">Missing</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">Sample</th>
              </tr>
            </thead>
            <tbody>
              {column_profiles.map(p => (
                <tr key={p.column} className="border-b border-gray-100">
                  <td className="px-3 py-2 font-medium text-gray-800">{p.column}</td>
                  <td className="px-3 py-2 text-gray-600 font-mono text-xs">{p.dtype}</td>
                  <td className="px-3 py-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${typeColor(p.detected_type)}`}>{p.detected_type}</span>
                  </td>
                  <td className="px-3 py-2 text-right text-gray-600">{p.unique_count}</td>
                  <td className="px-3 py-2 text-right text-gray-600">{p.missing_percentage}%</td>
                  <td className="px-3 py-2 text-gray-500 text-xs max-w-[200px] truncate">
                    {p.sample_values.slice(0, 3).map(v => String(v)).join(', ')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      {/* EDA Charts */}
      <Section title="EDA Visualizations">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {eda_charts.map((chart, i) => (
            <ChartCard key={i} chart={chart} />
          ))}
        </div>
      </Section>

      {/* LLM Full Insight */}
      {llm_understanding && (
        <Section title="LLM Dataset Insight">
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-1">Understanding</h4>
              <p className="text-gray-800">{llm_understanding.dataset_understanding}</p>
            </div>

            {llm_understanding.preprocessing_recommendations.length > 0 && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Preprocessing Recommendations</h4>
                <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                  {llm_understanding.preprocessing_recommendations.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            )}

            {llm_understanding.methodological_warnings.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <h4 className="text-sm font-medium text-amber-800 mb-2">Methodological Warnings</h4>
                <ul className="list-disc list-inside text-sm text-amber-700 space-y-1">
                  {llm_understanding.methodological_warnings.map((w, i) => <li key={i}>{w}</li>)}
                </ul>
              </div>
            )}

            {llm_understanding.user_confirmation_needed.length > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="text-sm font-medium text-blue-800 mb-2">Confirmation Needed</h4>
                <ul className="list-disc list-inside text-sm text-blue-700 space-y-1">
                  {llm_understanding.user_confirmation_needed.map((c, i) => <li key={i}>{c}</li>)}
                </ul>
              </div>
            )}
          </div>
        </Section>
      )}

      {/* Preprocessing Previews */}
      {preprocessing_previews && preprocessing_previews.length > 0 && (
        <Section title="Preprocessing Preview">
          <p className="text-xs text-gray-500 mb-4">
            Preview hasil setiap langkah preprocessing yang direkomendasikan AI berdasarkan analisis pola data.
          </p>
          <div className="space-y-4">
            {preprocessing_previews.map((pp, i) => (
              <PreprocessingCard key={i} preview={pp} />
            ))}
          </div>
        </Section>
      )}

      {!llm_understanding && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-800">
          LLM insight unavailable. Showing rule-based analysis only.
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

function SummaryCard({ label, value, color }: { label: string; value: string; color?: string }) {
  const colorMap: Record<string, string> = {
    blue: 'border-blue-200 bg-blue-50',
    green: 'border-green-200 bg-green-50',
    red: 'border-red-200 bg-red-50',
    purple: 'border-purple-200 bg-purple-50',
  };
  const cls = color ? colorMap[color] || '' : 'border-gray-200';
  return (
    <div className={`rounded-lg border px-4 py-3 ${cls}`}>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-lg font-semibold text-gray-900 truncate">{value}</p>
    </div>
  );
}

function QualityItem({ type, text }: { type: 'warning' | 'info' | 'success'; text: string }) {
  const styles = {
    warning: 'bg-amber-50 border-amber-200 text-amber-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    success: 'bg-green-50 border-green-200 text-green-800',
  };
  return <div className={`rounded-lg border p-3 text-sm ${styles[type]}`}>{text}</div>;
}

function ChartCard({ chart }: { chart: ChartDataType }) {
  if (chart.chart_type === 'bar' || chart.chart_type === 'histogram') {
    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">{chart.title}</h4>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chart.data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-30} textAnchor="end" height={60} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey={chart.data[0] && 'count' in chart.data[0] ? 'count' : 'value'} fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (chart.chart_type === 'horizontal_bar') {
    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">{chart.title}</h4>
        <ResponsiveContainer width="100%" height={Math.max(200, chart.data.length * 35)}>
          <BarChart data={chart.data} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" tick={{ fontSize: 11 }} />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={120} />
            <Tooltip />
            <Bar dataKey="missing" fill="#ef4444" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (chart.chart_type === 'pie' || chart.title.includes('Type Distribution')) {
    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">{chart.title}</h4>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie data={chart.data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
              {chart.data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (chart.chart_type === 'scatter') {
    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">{chart.title}</h4>
        <ResponsiveContainer width="100%" height={250}>
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="x" name="X" tick={{ fontSize: 11 }} />
            <YAxis dataKey="y" name="Y" tick={{ fontSize: 11 }} />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
            <Scatter data={chart.data} fill="#3b82f6" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (chart.chart_type === 'boxplot') {
    const d = chart.data[0] as Record<string, unknown>;
    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">{chart.title}</h4>
        <div className="space-y-2 text-sm">
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-white rounded p-2 border border-gray-200">
              <span className="text-xs text-gray-500">Min</span>
              <p className="font-mono font-medium">{String(d.min)}</p>
            </div>
            <div className="bg-white rounded p-2 border border-gray-200">
              <span className="text-xs text-gray-500">Max</span>
              <p className="font-mono font-medium">{String(d.max)}</p>
            </div>
            <div className="bg-blue-50 rounded p-2 border border-blue-200">
              <span className="text-xs text-blue-500">Q1</span>
              <p className="font-mono font-medium text-blue-800">{String(d.q1)}</p>
            </div>
            <div className="bg-blue-50 rounded p-2 border border-blue-200">
              <span className="text-xs text-blue-500">Q3</span>
              <p className="font-mono font-medium text-blue-800">{String(d.q3)}</p>
            </div>
          </div>
          <div className="bg-green-50 rounded p-2 border border-green-200 text-center">
            <span className="text-xs text-green-500">Median</span>
            <p className="font-mono font-semibold text-green-800">{String(d.median)}</p>
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span>Whiskers: {String(d.lower_whisker)} - {String(d.upper_whisker)}</span>
            <span className="text-red-600 font-medium">{String(d.outlier_count)} outliers</span>
          </div>
        </div>
      </div>
    );
  }

  if (chart.chart_type === 'grouped_bar') {
    return <GroupedBarCard chart={chart} />;
  }

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <h4 className="text-sm font-medium text-gray-700 mb-3">{chart.title}</h4>
      <pre className="text-xs text-gray-600 overflow-auto">{JSON.stringify(chart.data, null, 2)}</pre>
    </div>
  );
}

function formatTask(task: string): string {
  return task.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function missingRecommendation(pct: number): string {
  if (pct < 5) return 'Simple imputation may suffice';
  if (pct <= 30) return 'Evaluate before imputation';
  return 'Consider dropping or using unknown category';
}

function typeColor(type: string): string {
  const map: Record<string, string> = {
    numeric: 'bg-blue-100 text-blue-700',
    categorical: 'bg-green-100 text-green-700',
    boolean: 'bg-purple-100 text-purple-700',
    datetime: 'bg-orange-100 text-orange-700',
    text: 'bg-gray-100 text-gray-700',
    id_like: 'bg-red-100 text-red-700',
    constant: 'bg-yellow-100 text-yellow-700',
    unknown: 'bg-gray-100 text-gray-500',
  };
  return map[type] || 'bg-gray-100 text-gray-600';
}

const STEP_LABELS: Record<string, string> = {
  handle_missing: 'Handle Missing',
  label_encode: 'Label Encoding',
  one_hot_encode: 'One-Hot Encoding',
  drop_column: 'Drop Column',
  scale: 'Scaling',
  handle_outlier: 'Handle Outlier',
};

const STEP_COLORS: Record<string, string> = {
  handle_missing: 'bg-red-100 text-red-700',
  label_encode: 'bg-blue-100 text-blue-700',
  one_hot_encode: 'bg-purple-100 text-purple-700',
  drop_column: 'bg-gray-100 text-gray-700',
  scale: 'bg-green-100 text-green-700',
  handle_outlier: 'bg-amber-100 text-amber-700',
};

function PreprocessingCard({ preview }: { preview: import('../types').PreprocessingPreview }) {
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex items-center gap-2">
        <span className={`text-xs px-2 py-0.5 rounded font-medium ${STEP_COLORS[preview.step_type] || 'bg-gray-100 text-gray-600'}`}>
          {STEP_LABELS[preview.step_type] || preview.step_type}
        </span>
        <span className="text-sm font-medium text-gray-800">{preview.column}</span>
        <span className="text-xs text-gray-400 ml-auto">{preview.method}</span>
      </div>
      <div className="p-4 space-y-3">
        <p className="text-sm text-gray-600">{preview.reason}</p>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-xs font-medium text-gray-500 mb-1">Before</p>
            <div className="bg-red-50 border border-red-100 rounded p-2">
              {preview.before_sample.map((v, i) => (
                <span key={i} className="inline-block text-xs bg-white border border-red-200 rounded px-1.5 py-0.5 mr-1 mb-1 text-red-700">
                  {v === null ? 'null' : String(v)}
                </span>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-500 mb-1">After</p>
            <div className="bg-green-50 border border-green-100 rounded p-2">
              {preview.after_sample.map((v, i) => (
                <span key={i} className="inline-block text-xs bg-white border border-green-200 rounded px-1.5 py-0.5 mr-1 mb-1 text-green-700">
                  {String(v)}
                </span>
              ))}
            </div>
          </div>
        </div>

        <p className="text-xs text-gray-500 bg-gray-50 rounded px-3 py-2">{preview.summary}</p>
      </div>
    </div>
  );
}

function GroupedBarCard({ chart }: { chart: ChartDataType }) {
  if (!chart.data || chart.data.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">{chart.title}</h4>
        <p className="text-xs text-gray-400">No data available</p>
      </div>
    );
  }

  const firstRow = chart.data[0];
  const groupKeys = Object.keys(firstRow).filter(k => k !== 'name');

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <h4 className="text-sm font-medium text-gray-700 mb-3">{chart.title}</h4>
      <ResponsiveContainer width="100%" height={Math.max(250, chart.data.length * 40)}>
        <BarChart data={chart.data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-30} textAnchor="end" height={60} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend />
          {groupKeys.map((key, i) => (
            <Bar key={key} dataKey={key} fill={COLORS[i % COLORS.length]} radius={[4, 4, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
