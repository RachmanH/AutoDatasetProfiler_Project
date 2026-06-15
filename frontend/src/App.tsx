import { useState } from 'react';
import UploadPage from './components/UploadPage';
import PreviewPage from './components/PreviewPage';
import ResultDashboard from './components/ResultDashboard';
import ResearchPRDPage from './components/ResearchPRDPage';
import type { UploadResponse, AnalyzeResponse } from './types';

type Step = 'upload' | 'preview' | 'results' | 'research';

function App() {
  const [step, setStep] = useState<Step>('upload');
  const [uploadData, setUploadData] = useState<UploadResponse | null>(null);
  const [analyzeData, setAnalyzeData] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = (data: UploadResponse) => {
    setUploadData(data);
    setStep('preview');
    setError(null);
  };

  const handleAnalyze = (analyze: AnalyzeResponse) => {
    setAnalyzeData(analyze);
    setStep('results');
    setError(null);
  };

  const handleResearch = () => {
    setStep('research');
    setError(null);
  };

  const handleReset = () => {
    setStep('upload');
    setUploadData(null);
    setAnalyzeData(null);
    setError(null);
  };

  const steps: Step[] = ['upload', 'preview', 'results', 'research'];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-semibold text-gray-900 cursor-pointer" onClick={handleReset}>
            AutoDataset Profiler
          </h1>
          <div className="flex gap-2 text-sm">
            {steps.map((s, i) => (
              <span
                key={s}
                className={`px-3 py-1 rounded-full ${
                  step === s
                    ? 'bg-blue-600 text-white'
                    : i < steps.indexOf(step)
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-400'
                }`}
              >
                {i + 1}. {s.charAt(0).toUpperCase() + s.slice(1)}
              </span>
            ))}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {step === 'upload' && <UploadPage onUpload={handleUpload} onError={setError} />}
        {step === 'preview' && uploadData && (
          <PreviewPage
            uploadData={uploadData}
            onAnalyze={handleAnalyze}
            onError={setError}
            onBack={handleReset}
          />
        )}
        {step === 'results' && analyzeData && (
          <ResultDashboard
            analyzeData={analyzeData}
            onReset={handleReset}
            onResearch={handleResearch}
          />
        )}
        {step === 'research' && analyzeData && (
          <ResearchPRDPage
            analyzeData={analyzeData}
            onBack={() => setStep('results')}
          />
        )}
      </main>
    </div>
  );
}

export default App;
