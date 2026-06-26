import { useState, useEffect } from 'react';
import LandingPage from './components/LandingPage';
import UploadPage from './components/UploadPage';
import PreviewPage from './components/PreviewPage';
import ResultDashboard from './components/ResultDashboard';
import ResearchPRDPage from './components/ResearchPRDPage';
import type { UploadResponse, AnalyzeResponse } from './types';

type Step = 'landing' | 'upload' | 'preview' | 'results' | 'research';

const SS_STEP = 'adp_step';
const SS_UPLOAD = 'adp_upload';
const SS_ANALYZE = 'adp_analyze';

function readSession<T>(key: string): T | null {
  try {
    const v = sessionStorage.getItem(key);
    return v ? (JSON.parse(v) as T) : null;
  } catch {
    return null;
  }
}

function writeSession(key: string, value: unknown): void {
  try {
    sessionStorage.setItem(key, JSON.stringify(value));
  } catch {
    // quota exceeded — state won't survive refresh but app stays functional
  }
}

function getInitialState(): { step: Step; uploadData: UploadResponse | null; analyzeData: AnalyzeResponse | null } {
  const step = (sessionStorage.getItem(SS_STEP) as Step) || 'landing';
  const uploadData = readSession<UploadResponse>(SS_UPLOAD);
  const analyzeData = readSession<AnalyzeResponse>(SS_ANALYZE);

  if ((step === 'preview' || step === 'results' || step === 'research') && !uploadData)
    return { step: 'landing', uploadData: null, analyzeData: null };
  if ((step === 'results' || step === 'research') && !analyzeData)
    return { step: uploadData ? 'preview' : 'landing', uploadData, analyzeData: null };

  return { step, uploadData, analyzeData };
}

const initial = getInitialState();

function App() {
  const [step, setStep] = useState<Step>(initial.step);
  const [uploadData, setUploadData] = useState<UploadResponse | null>(initial.uploadData);
  const [analyzeData, setAnalyzeData] = useState<AnalyzeResponse | null>(initial.analyzeData);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { sessionStorage.setItem(SS_STEP, step); }, [step]);
  useEffect(() => {
    if (uploadData) writeSession(SS_UPLOAD, uploadData);
    else sessionStorage.removeItem(SS_UPLOAD);
  }, [uploadData]);
  useEffect(() => {
    if (analyzeData) writeSession(SS_ANALYZE, analyzeData);
    else sessionStorage.removeItem(SS_ANALYZE);
  }, [analyzeData]);

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
    sessionStorage.removeItem(SS_STEP);
    sessionStorage.removeItem(SS_UPLOAD);
    sessionStorage.removeItem(SS_ANALYZE);
    setStep('landing');
    setUploadData(null);
    setAnalyzeData(null);
    setError(null);
  };

  const appSteps: Step[] = ['upload', 'preview', 'results', 'research'];
  const isInApp = (step !== 'landing') as boolean;

  if (step === 'landing') {
    return <LandingPage onStart={() => setStep('upload')} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-semibold text-gray-900 cursor-pointer" onClick={handleReset}>
            AutoDataset Profiler
          </h1>
          {isInApp && (
            <div className="flex gap-2 text-sm">
              {appSteps.map((s, i) => (
                <span
                  key={s}
                  className={`px-3 py-1 rounded-full ${
                    step === s
                      ? 'bg-blue-600 text-white'
                      : i < appSteps.indexOf(step as Exclude<Step, 'landing'>)
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-400'
                  }`}
                >
                  {i + 1}. {s.charAt(0).toUpperCase() + s.slice(1)}
                </span>
              ))}
            </div>
          )}
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
