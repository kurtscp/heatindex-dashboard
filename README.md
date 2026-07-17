![HeatWatch Banner](https://capsule-render.vercel.app/api?type=rect&color=0:da3633,100:e3872d&height=12)

<div align="center">
  <h1>HeatWatch</h1>
  <p><strong>Philippines Heat Index Dashboard</strong></p>

  <p>
    <a href="#quick-start">View Dashboard</a>
    ·
    <a href="https://github.com/your-username/heatwatch/issues">Report Bug</a>
    ·
    <a href="https://github.com/your-username/heatwatch/issues">Request Feature</a>
  </p>
</div>

---

## About

**HeatWatch** is a Flask-based web application for analyzing, visualizing, and predicting historical heat index data across the Philippines. Upload any CSV dataset with daily weather observations — the system automatically cleans the data, computes heat index using the **PAGASA-adopted Rothfusz regression**, classifies danger levels, trains a machine learning predictor, and generates a full interactive analytics dashboard.

> [!NOTE]
> HeatWatch is data-source agnostic. While it was initially developed with [Open-Meteo ERA5](https://open-meteo.com/) exports, it works with **any CSV** that follows the required column format described below.

## ✨ Key Features

- 📊 **Interactive Dashboard** — Metric cards, danger day bar charts, and year-over-year monthly heat index comparison with dynamic selectors.
- 📈 **Historical Trends** — Annual average heat index trend with linear regression, earliest danger day per year, and temperature vs. heat index gap analysis.
- 🗓️ **Danger Calendar** — Year × month heatmap showing peak danger severity, plus a ranked table of the top 5 historically most dangerous weeks.
- 🤖 **ML Predictor** — Decision Tree classifier for danger level prediction given any date + ENSO condition, plus a linear regression forecast with 95% confidence intervals.
- 🧹 **Automated Preprocessing** — Handles metadata headers, duplicate removal, missing value imputation (linear interpolation), outlier flagging, and ENSO tagging — all before you see a single chart.
- 📥 **Export** — Download the cleaned, feature-engineered CSV for your own analysis.

---

## 📐 Formulas & Classification

### Heat Index Calculation

HeatWatch uses the **NOAA Rothfusz regression equation** — the same algorithm officially adopted by **PAGASA** (Philippine Atmospheric, Geophysical, and Astronomical Services Administration).

**Step 1:** Convert temperature from Celsius to Fahrenheit.

```
T_F = T_C × (9/5) + 32
```

**Step 2:** Compute an initial simple estimate:

```
HI = 0.5 × (T_F + 61.0 + ((T_F − 68.0) × 1.2) + (RH × 0.094))
```

**Step 3:** If HI ≥ 80°F, apply the full Rothfusz regression:

```
HI = −42.379
   + 2.04901523 × T
   + 10.14333127 × RH
   − 0.22475541 × T × RH
   − 0.00683783 × T²
   − 0.05481717 × RH²
   + 0.00122874 × T² × RH
   + 0.00085282 × T × RH²
   − 0.00000199 × T² × RH²
```

**Step 4:** Apply adjustments:
- If **RH < 13%** and **80°F ≤ T ≤ 112°F** → subtract a low-humidity correction.
- If **RH > 85%** and **80°F ≤ T ≤ 87°F** → add a high-humidity correction.

**Step 5:** Convert the result back to Celsius.

### PAGASA Danger Level Classification

| Category | Heat Index Range | Health Risk |
|:---|:---|:---|
| 🟢 **Normal** | Below 27°C | No significant risk |
| 🟡 **Caution** | 27°C – 32°C | Fatigue possible with prolonged exposure |
| 🟠 **Extreme Caution** | 33°C – 41°C | Heat cramps and exhaustion possible |
| 🔴 **Danger** | 42°C – 51°C | Heat cramps/exhaustion likely; heat stroke possible |
| ⛔ **Extreme Danger** | 52°C and above | Heat stroke imminent |

---

## 📋 CSV Data Format

Your CSV file **must** follow the structure below for the dashboard to process it correctly. The first few rows may contain metadata (latitude, longitude, etc.) — the system automatically skips those and looks for the header row starting with `time`.

### Required Columns

| Column | Description | Unit | Example |
|:---|:---|:---|:---|
| `time` | Date of observation | `YYYY-MM-DD` | `2024-05-15` |
| `temperature_2m_mean` | Daily mean temperature at 2m | °C | `29.4` |
| `temperature_2m_max` | Daily max temperature at 2m | °C | `34.1` |
| `temperature_2m_min` | Daily min temperature at 2m | °C | `25.8` |
| `precipitation_sum` | Total daily precipitation | mm | `0.0` |
| `relative_humidity_2m_max` | Daily max relative humidity at 2m | % | `89` |
| `relative_humidity_2m_mean` | Daily mean relative humidity at 2m | % | `74` |
| `wind_speed_10m_max` | Daily max wind speed at 10m | km/h | `18.5` |

> [!IMPORTANT]
> Column names **may include units in parentheses** — e.g., `temperature_2m_mean (°C)`. The system automatically strips units and normalizes names to snake_case.

### Example CSV

```csv
latitude,longitude,elevation,utc_offset_seconds,timezone,timezone_abbreviation
14.586995,121.002785,9.0,0,GMT,GMT

time,temperature_2m_mean (°C),temperature_2m_max (°C),temperature_2m_min (°C),precipitation_sum (mm),relative_humidity_2m_max (%),relative_humidity_2m_mean (%),wind_speed_10m_max (km/h)
2024-01-01,25.2,29.5,21.8,0.0,71.3,71.0,18.1
2024-01-02,25.5,30.4,22.7,0.1,70.6,71.8,15.3
2024-01-03,25.9,29.6,22.5,0.0,71.8,72.6,11.1
```

> [!TIP]
> You can export this exact format from [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) by selecting the daily variables listed above. However, any CSV matching this column structure will work.

### What Gets Computed Automatically

The preprocessing pipeline generates these derived columns:

| Derived Column | Description |
|:---|:---|
| `computed_heat_index` | Heat index in °C (Rothfusz regression) |
| `danger_category` | PAGASA classification (Normal → Extreme Danger) |
| `is_danger_day` | `1` if Danger or Extreme Danger, else `0` |
| `hi_gap` | Difference: heat index − actual temperature |
| `season` | Philippine season (Dry / Wet / Cool Dry) |
| `enso_condition` | El Niño / La Niña / Neutral (mapped by year) |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **pip** (Python package manager)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-username/heatwatch.git
cd heatwatch

# 2. Create a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Run

```bash
python main/app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser → upload your CSV file → **Proceed to Dashboard**.

> [!TIP]
> A sample dataset is included at `rawData/raw_manila_heatindex_2015_2026.csv` for testing.

---

## 📂 Project Structure

```
heatwatch/
├── main/
│   └── app.py                  # Flask entry point & all routes
├── frontend/
│   ├── base.html               # Shared layout (navbar, footer)
│   ├── upload.html             # File upload with progress animation
│   ├── dashboard.html          # Main analytics dashboard
│   ├── historical.html         # Historical trend charts
│   ├── calendar.html           # Danger calendar heatmap
│   ├── predictor.html          # ML predictor & forecast chart
│   └── static/
│       ├── css/style.css       # Custom dark theme styles
│       └── js/main.js          # Shared utilities
├── backend/
│   ├── preprocessing.py        # CSV cleaning & feature engineering
│   ├── analytics.py            # Chart data & insight computations
│   └── predictor.py            # Decision Tree + Linear Regression
├── rawData/                    # Sample datasets
├── assets/                     # Logo & favicon assets
└── requirements.txt
```

## 🔌 API Endpoints

| Method | Route | Description |
|:---|:---|:---|
| `POST` | `/upload` | Upload CSV → runs preprocessing + model training |
| `GET` | `/api/monthly-comparison?year1=&year2=` | Monthly heat index data for two years |
| `POST` | `/api/predict` | Predict danger level for `{day, month, year, enso_condition}` |
| `GET` | `/download-csv` | Download the cleaned, feature-engineered dataset |
| `GET` | `/reset` | Clear session and return to upload page |

---

## 🛠️ Built With

- [Flask](https://flask.palletsprojects.com/) — Web framework
- [Pandas](https://pandas.pydata.org/) & [NumPy](https://numpy.org/) — Data processing
- [scikit-learn](https://scikit-learn.org/) — Machine learning (Decision Tree, Linear Regression)
- [SciPy](https://scipy.org/) — Statistical analysis
- [Plotly.js](https://plotly.com/javascript/) — Interactive charts
- [Bootstrap 5](https://getbootstrap.com/) — Responsive layout

---

<div align="center">
  <p>© 2026 <a href="https://www.linkedin.com/in/kurtcruz">Kurt Cruz</a>. All rights reserved.</p>
</div>
