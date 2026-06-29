# HeatWatch — Metro Manila Heat Index Dashboard

Flask-based web app for analyzing, visualizing, and predicting heat index patterns for Metro Manila using Open-Meteo ERA5 data.

## Quick Start

### Prerequisites
- Python 3.8+
- Git

### Setup

```bash
git clone <your-repo-url>
cd "HEATINDEX DASHBOARD"

python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Run

```bash
python main/app.py
```

Open `http://127.0.0.1:5000/` → upload the dataset at `rawData/raw_manila_heatindex_2015_2026.csv` → Proceed to Dashboard.

---

## Project Structure

```
├── main/
│   └── app.py              # Flask entry point & all routes
├── frontend/
│   ├── base.html           # Shared layout template
│   ├── upload.html         # File upload page
│   ├── dashboard.html      # Main analytics dashboard
│   ├── historical.html     # Historical trend charts
│   ├── calendar.html       # Danger calendar heatmap
│   ├── predictor.html      # ML predictor & forecast
│   └── static/             # CSS, JS, assets
├── backend/
│   ├── preprocessing.py    # CSV cleaning & feature engineering
│   ├── analytics.py        # Chart data & insight computations
│   └── predictor.py        # Decision Tree classifier + regression forecasting
├── rawData/
│   └── raw_manila_heatindex_2015_2026.csv   # Default dataset
└── requirements.txt
```

---

## Features

| Page | Description |
|------|-------------|
| **Dashboard** | Metric cards, danger days bar chart, monthly HI comparison, key insights |
| **Historical** | Annual HI trend, earliest danger day per year, hidden heat gap |
| **Calendar** | Year × month heatmap of peak danger category per period |
| **Predictor** | Date + ENSO → danger category prediction; linear regression forecast to 2028 |

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| `POST` | `/upload` | Upload CSV, runs preprocessing + model training |
| `GET` | `/api/monthly-comparison?year1=&year2=` | Monthly HI data for two years |
| `POST` | `/api/predict` | Predict danger level for `{day, month, year, enso_condition}` |
| `GET` | `/download-csv` | Download cleaned dataset |
| `GET` | `/reset` | Clear session and return to upload |
