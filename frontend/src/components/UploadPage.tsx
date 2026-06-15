import { useState, useRef, useCallback } from 'react';
import { uploadDataset } from '../api';
import type { UploadResponse } from '../types';

interface Props {
  onUpload: (data: UploadResponse) => void;
  onError: (msg: string) => void;
}

export default function UploadPage({ onUpload, onError }: Props) {
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(async (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !['csv', 'xlsx'].includes(ext)) {
      onError('Unsupported file format. Please upload CSV or XLSX.');
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      onError('File size exceeds 20 MB limit.');
      return;
    }

    setLoading(true);
    try {
      const data = await uploadDataset(file);
      onUpload(data);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Upload failed';
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      onError(detail || msg);
    } finally {
      setLoading(false);
    }
  }, [onUpload, onError]);

  return (
    <div className="max-w-lg mx-auto mt-16">
      <h2 className="text-2xl font-semibold text-gray-900 text-center mb-2">
        Upload Your Dataset
      </h2>
      <p className="text-gray-500 text-center mb-8">
        CSV or XLSX, max 20 MB
      </p>

      <div
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
          dragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const file = e.dataTransfer.files[0];
          if (file) handleFile(file);
        }}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />

        {loading ? (
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-600">Uploading and parsing...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <svg className="w-12 h-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="text-gray-600">
              Drag & drop your file here, or <span className="text-blue-600 font-medium">browse</span>
            </p>
            <p className="text-sm text-gray-400">Supported: .csv, .xlsx</p>
          </div>
        )}
      </div>
    </div>
  );
}
