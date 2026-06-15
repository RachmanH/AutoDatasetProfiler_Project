import { useState } from 'react';
import { analyzeDataset } from '../api';
import type { UploadResponse, AnalyzeResponse } from '../types';

interface Props {
  uploadData: UploadResponse;
  onAnalyze: (analyze: AnalyzeResponse) => void;
  onError: (msg: string) => void;
  onBack: () => void;
}

export default function PreviewPage({ uploadData, onAnalyze, onError, onBack }: Props) {
  const [targetColumn, setTargetColumn] = useState('');
  const [loading, setLoading] = useState(false);
  const columns = uploadData.preview.length > 0 ? Object.keys(uploadData.preview[0]) : [];

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const analyze = await analyzeDataset(uploadData.dataset_id, targetColumn || undefined);
      onAnalyze(analyze);
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      onError(detail || (e instanceof Error ? e.message : 'Analysis failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={onBack} className="mb-4 text-sm text-gray-500 hover:text-gray-700">
        &larr; Upload different file
      </button>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <InfoCard label="File" value={uploadData.filename} />
        <InfoCard label="Size" value={`${uploadData.file_size_mb} MB`} />
        <InfoCard label="Rows" value={uploadData.rows.toLocaleString()} />
        <InfoCard label="Columns" value={uploadData.columns.toString()} />
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden mb-6">
        <h3 className="px-4 py-3 text-sm font-medium text-gray-700 border-b border-gray-200 bg-gray-50">
          Preview (first 5 rows)
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                {columns.map((col) => (
                  <th key={col} className="px-3 py-2 text-left font-medium text-gray-600 whitespace-nowrap">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {uploadData.preview.map((row, i) => (
                <tr key={i} className="border-b border-gray-100 last:border-0">
                  {columns.map((col) => (
                    <td key={col} className="px-3 py-2 text-gray-700 whitespace-nowrap max-w-[200px] truncate">
                      {row[col] == null ? <span className="text-gray-300 italic">null</span> : String(row[col])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex items-end gap-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Target Column (optional)
          </label>
          <select
            value={targetColumn}
            onChange={(e) => setTargetColumn(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          >
            <option value="">-- Auto-detect --</option>
            {columns.map((col) => (
              <option key={col} value={col}>{col}</option>
            ))}
          </select>
        </div>

        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Analyzing...
            </span>
          ) : (
            'Analyze Dataset'
          )}
        </button>
      </div>

      {loading && (
        <p className="mt-3 text-sm text-gray-500">
          Profiling dataset, generating charts, and requesting LLM insight...
        </p>
      )}
    </div>
  );
}

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 px-4 py-3">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-lg font-semibold text-gray-900 truncate">{value}</p>
    </div>
  );
}
