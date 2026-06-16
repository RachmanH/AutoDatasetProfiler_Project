# AutoDataset Profiler

AutoDataset Profiler is a web application that helps users — especially students, data science beginners, and Kaggle dataset users — quickly understand tabular datasets before moving to the modeling stage.

Upload a CSV or XLSX file (max 20 MB), and the system will automatically analyze the dataset structure, detect column types, identify data quality issues, generate EDA visualizations, and provide LLM-powered insights including ML task suggestions, preprocessing recommendations, and methodological warnings.

> **Positioning:** Dataset Reader + Basic EDA Dashboard + LLM Dataset Understanding
>
> This is **not** an AutoML tool, model trainer, code executor, or notebook generator.

---

## Features

- **Dataset Upload** — Drag-and-drop CSV/XLSX files with validation (format, size, empty check)
- **Data Preview** — 5-row preview with file metadata (rows, columns, size)
- **Column Type Detection** — Automatic detection of numeric, categorical, boolean, datetime, text, and ID-like columns
- **Data Quality Check** — Missing values, duplicate rows, constant columns, high-cardinality columns, and ID-like column detection
- **EDA Visualizations** — Bar charts, histograms, scatter plots, boxplots, and grouped bar charts (both static and LLM-recommended dynamic charts)
- **Dataset Fingerprint** — Compact JSON summary sent to the LLM (raw data is never sent)
- **LLM-Powered Insights** — Dataset understanding, domain guessing, target column candidates, ML task suggestions, preprocessing recommendations, and methodological warnings via integrated LLM
- **Rule-Based Task Suggestion** — Automatic ML task suggestion (binary/multiclass classification, regression, count regression, clustering candidate)
- **Preprocessing Previews** — Before/after previews for each LLM-suggested preprocessing step (missing value handling, encoding, scaling, outlier treatment, etc.)
- **Research PRD Generator** — LLM-powered research title suggestions, task suggestions, research questions, and full PRD markdown generation for academic use
- **Graceful Degradation** — If the LLM is unavailable, the basic EDA dashboard still renders normally

---

## Tech Stack

### Frontend

| Technology | Purpose |
|---|---|
| React 19 | UI framework |
| Vite 8 | Build tool and dev server |
| TypeScript 6 | Type safety |
| Tailwind CSS 4 | Utility-first styling |
| Recharts 3 | Chart visualizations |
| Axios | HTTP client |

### Backend

| Technology | Purpose |
|---|---|
| FastAPI | REST API framework |
| Python 3.11+ | Data processing runtime |
| pandas | Tabular data parsing and analysis |
| numpy | Numerical computations |
| Pydantic | Request/response validation and LLM output validation |
| openpyxl | XLSX file support |
| requests | LLM API client |
| python-dotenv | Environment variable management |

---

## Project Structure

```
PemroUAS/
├── backend/
│   ├── services/
│   │   ├── chart_data.py       # EDA chart generation (static + LLM-dynamic)
│   │   ├── fingerprint.py      # Dataset fingerprint builder
│   │   ├── llm.py              # LLM integration + JSON validation
│   │   ├── parser.py           # CSV/XLSX file parser
│   │   ├── preprocessing.py    # Preprocessing step previews
│   │   ├── profiler.py         # Column type detection & profiling
│   │   ├── research.py         # Research PRD suggestions & generation
│   │   └── task_suggestion.py  # Rule-based ML task suggestion
│   ├── uploads/                # Temporary uploaded files
│   ├── .env                    # Environment variables (not committed)
│   ├── .env.example            # Environment variable template
│   ├── config.py               # App configuration
│   ├── main.py                 # FastAPI app & API endpoints
│   ├── models.py               # Pydantic models
│   ├── storage.py              # In-memory dataset storage with TTL
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── UploadPage.tsx      # File upload with drag-and-drop
│   │   │   ├── PreviewPage.tsx     # Dataset preview & target selection
│   │   │   ├── ResultDashboard.tsx # Full EDA dashboard
│   │   │   └── ResearchPRDPage.tsx # Research PRD generator
│   │   ├── App.tsx             # Main app with step-based navigation
│   │   ├── api.ts              # API client functions
│   │   ├── types.ts            # TypeScript type definitions
│   │   ├── main.tsx            # Entry point
│   │   └── index.css           # Global styles
│   ├── package.json
│   └── vite.config.ts
└── prd.md                      # Product Requirements Document
```

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **LLM API Key** — Required for LLM-powered features (the app works without it but LLM insights will be unavailable)

### Backend Setup

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Create a virtual environment and activate it:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # venv\Scripts\activate   # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and fill in your LLM API key:

   ```env
   LLM_API_KEY=your_api_key_here
   LLM_MODEL=your_model_name
   LLM_URL=your_llm_endpoint_url
   ```

5. Start the backend server:

   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`.

### Frontend Setup

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Start the development server:

   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:5173`.

   > The Vite dev server proxies `/api` requests to the backend at `http://localhost:8000`.

---

## API Endpoints

### Upload Dataset

```
POST /api/datasets/upload
Content-Type: multipart/form-data
```

Upload a CSV or XLSX file (max 20 MB). Returns dataset metadata and a 5-row preview.

### Analyze Dataset

```
POST /api/datasets/analyze
Content-Type: application/json
```

```json
{
  "dataset_id": "ds_abc123",
  "target_column": "Survived"  // optional
}
```

Performs full profiling, generates EDA charts, calls the LLM, and returns the complete analysis.

### LLM Dataset Understanding

```
POST /api/llm/dataset-understanding
Content-Type: application/json
```

```json
{
  "dataset_id": "ds_abc123",
  "dataset_fingerprint": { ... }
}
```

Standalone endpoint to get LLM insights for a dataset fingerprint.

### Research Suggestions

```
POST /api/research/suggestions
Content-Type: application/json
```

Returns LLM-generated research title suggestions, task suggestions, and research questions.

### Generate Research PRD

```
POST /api/research/generate-prd
Content-Type: application/json
```

Generates a full research PRD in Markdown format based on user selections and dataset analysis.

---

## How It Works

```
Upload Dataset (CSV/XLSX)
       ↓
  File Validation
       ↓
  pandas Parser
       ↓
  Dataset Profiling
  (column types, missing values, duplicates, etc.)
       ↓
  Dataset Fingerprint (compact JSON)
       ↓
  LLM API
  (understanding, task suggestion, preprocessing, warnings)
       ↓
  EDA Dashboard + LLM Insights
```

1. User uploads a CSV or XLSX file
2. Backend validates format, size, and content
3. Parser reads the dataset and generates a preview
4. Profiler analyzes each column (type detection, stats, missing values)
5. A **dataset fingerprint** (compact JSON summary) is generated
6. The fingerprint is sent to the LLM for semantic understanding
7. LLM output is validated (JSON parsing, column name verification, schema validation)
8. Results are displayed in an interactive dashboard with charts and insights

---

## Screenshots

### Upload Page
Upload your dataset via drag-and-drop or file picker.

### Preview Page
View dataset metadata, 5-row preview, and select a target column.

### Result Dashboard
Explore summary cards, data quality checks, column profiles, EDA charts, LLM insights, ML task suggestions, preprocessing recommendations, and methodological warnings.

### Research PRD Page
Get LLM-generated research title suggestions and generate a complete research PRD document.

---

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `LLM_API_KEY` | *(empty)* | API key for LLM provider (required for LLM features) |
| `LLM_MODEL` | *(configurable)* | LLM model name |
| `LLM_URL` | *(configurable)* | LLM API endpoint URL |
| `MAX_FILE_SIZE_MB` | `20` | Maximum upload file size |
| `DATASET_TTL_SECONDS` | `3600` | Dataset expiry time in memory (1 hour) |

---

## Key Design Decisions

- **LLM receives only the dataset fingerprint** — raw data is never sent to the LLM for security and efficiency
- **Robust JSON parsing** — 3 fallback strategies for parsing truncated or malformed LLM responses
- **Column name validation** — any column names hallucinated by the LLM are automatically filtered out
- **Graceful degradation** — if the LLM fails, the basic EDA dashboard still renders with all charts and data quality checks
- **Primary task suggestion** — merges LLM and rule-based results, preferring LLM when available with valid output
- **Dynamic charts** — the LLM can recommend specific charts with exact column names, which the backend renders alongside standard EDA charts
- **In-memory storage** — datasets are stored in memory with automatic TTL-based cleanup (no database required)

---

## Testing Datasets

The following datasets are recommended for testing:

| Dataset | Target | Expected Task |
|---|---|---|
| Titanic | Survived | Binary Classification |
| House Prices | SalePrice | Regression |
| Iris | Species | Multiclass Classification |
| Mall Customer | *(none)* | Clustering Candidate |
| Breast Cancer | diagnosis | Binary Classification |

---

## License

This project was developed as a university final assignment (UAS - Ujian Akhir Semester).
