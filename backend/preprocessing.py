"""
HeatWatch - Data Preprocessing Pipeline
Implements PRD Section 2.3: Full cleaning, transformation, and feature engineering
for the Open-Meteo ERA5 raw CSV dataset.
"""

import pandas as pd
import numpy as np
from io import StringIO


# ENSO Year Reference (PRD Table 6)
ENSO_MAP = {
    2015: "Neutral",
    2016: "El Nino",
    2017: "La Nina",
    2018: "Neutral",
    2019: "El Nino",
    2020: "La Nina",
    2021: "La Nina",
    2022: "La Nina",
    2023: "El Nino",
    2024: "El Nino",
    2025: "Neutral",
    2026: "Neutral",
}


def classify_danger(hi_celsius):
    """Classify heat index into PAGASA danger categories."""
    if hi_celsius >= 52:
        return "Extreme Danger"
    elif hi_celsius >= 42:
        return "Danger"
    elif hi_celsius >= 33:
        return "Extreme Caution"
    elif hi_celsius >= 27:
        return "Caution"
    else:
        return "Normal"


def compute_heat_index(temp_f, rh):
    """
    Compute heat index using the NOAA Rothfusz regression equation.
    Input: temperature in Fahrenheit, relative humidity in percent.
    Output: heat index in Fahrenheit.
    """
    # Simple formula for low HI cases
    hi = 0.5 * (temp_f + 61.0 + ((temp_f - 68.0) * 1.2) + (rh * 0.094))

    if hi >= 80:
        # Full Rothfusz regression
        hi = (
            -42.379
            + 2.04901523 * temp_f
            + 10.14333127 * rh
            - 0.22475541 * temp_f * rh
            - 0.00683783 * temp_f ** 2
            - 0.05481717 * rh ** 2
            + 0.00122874 * temp_f ** 2 * rh
            + 0.00085282 * temp_f * rh ** 2
            - 0.00000199 * temp_f ** 2 * rh ** 2
        )

        # Adjustment for low humidity
        if rh < 13 and 80 <= temp_f <= 112:
            adjustment = ((13 - rh) / 4) * np.sqrt((17 - abs(temp_f - 95.0)) / 17)
            hi -= adjustment
        # Adjustment for high humidity
        elif rh > 85 and 80 <= temp_f <= 87:
            adjustment = ((rh - 85) / 10) * ((87 - temp_f) / 5)
            hi += adjustment

    return hi


def celsius_to_fahrenheit(c):
    return c * 9.0 / 5.0 + 32.0


def fahrenheit_to_celsius(f):
    return (f - 32.0) * 5.0 / 9.0


def get_season(month):
    """Map month to Philippine season."""
    if month in [3, 4, 5]:
        return "Dry"
    elif month in [6, 7, 8, 9, 10, 11]:
        return "Wet"
    else:
        return "Cool Dry"


def preprocess_csv(file_content):
    """
    Full preprocessing pipeline for the raw Open-Meteo CSV.
    
    Args:
        file_content: string content of the uploaded CSV file
        
    Returns:
        tuple: (cleaned_df, summary_dict)
    """
    summary = {
        "rows_before": 0,
        "rows_after": 0,
        "duplicates_removed": 0,
        "missing_values_imputed": 0,
        "outliers_flagged": 0,
    }

    # Step 1: Parse CSV - skip metadata header (first 3 lines)
    lines = file_content.strip().split('\n')
    
    # Find the actual header row (contains 'time')
    header_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('time'):
            header_idx = i
            break
    
    csv_data = '\n'.join(lines[header_idx:])
    df = pd.read_csv(StringIO(csv_data))
    
    summary["rows_before"] = len(df)

    # Step 2: Rename columns to clean snake_case
    rename_map = {}
    for col in df.columns:
        clean = col.strip()
        # Remove units in parentheses
        if '(' in clean:
            clean = clean[:clean.index('(')].strip()
        # Convert to snake_case
        clean = clean.replace(' ', '_').lower()
        rename_map[col] = clean
    
    df.rename(columns=rename_map, inplace=True)

    # Step 3: Type conversion - time to datetime
    df['time'] = pd.to_datetime(df['time'], format='mixed')

    # Step 4: Timezone correction - UTC to Asia/Manila (UTC+8)
    df['time'] = df['time'] + pd.Timedelta(hours=8)

    # Step 5: Remove duplicates
    dupes_before = len(df)
    df = df.drop_duplicates(subset=['time'], keep='first')
    summary["duplicates_removed"] = dupes_before - len(df)

    # Step 6: Missing value imputation
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Count NaN before imputation
    nan_count = df[numeric_cols].isna().sum().sum()
    
    # Fill precipitation NaN with 0
    if 'precipitation_sum' in df.columns:
        df['precipitation_sum'] = df['precipitation_sum'].fillna(0)
    
    # Linear interpolation for temperature and humidity columns
    interp_cols = [c for c in numeric_cols if c != 'precipitation_sum']
    for col in interp_cols:
        df[col] = df[col].interpolate(method='linear')
    
    # Fill any remaining edge NaN with forward/backward fill
    df[numeric_cols] = df[numeric_cols].ffill().bfill()
    
    summary["missing_values_imputed"] = int(nan_count)

    # Step 7: Outlier flagging
    outlier_mask = pd.Series(False, index=df.index)
    
    temp_cols = [c for c in df.columns if 'temperature' in c]
    for col in temp_cols:
        outlier_mask |= (df[col] < 15) | (df[col] > 45)
    
    humidity_cols = [c for c in df.columns if 'humidity' in c]
    for col in humidity_cols:
        outlier_mask |= (df[col] < 20)
    
    summary["outliers_flagged"] = int(outlier_mask.sum())

    # Step 8: Compute heat index (NOAA Rothfusz)
    temp_col = 'temperature_2m_mean'
    rh_col = 'relative_humidity_2m_max'
    
    hi_values = []
    for _, row in df.iterrows():
        temp_c = row[temp_col]
        rh = row[rh_col]
        temp_f = celsius_to_fahrenheit(temp_c)
        hi_f = compute_heat_index(temp_f, rh)
        hi_c = fahrenheit_to_celsius(hi_f)
        hi_values.append(round(hi_c, 2))
    
    df['computed_heat_index'] = hi_values

    # Step 9: Danger category classification
    df['danger_category'] = df['computed_heat_index'].apply(classify_danger)

    # Step 10: Derived columns
    df['day'] = df['time'].dt.day
    df['month'] = df['time'].dt.month
    df['year'] = df['time'].dt.year
    df['day_of_year'] = df['time'].dt.dayofyear
    df['week_of_year'] = df['time'].dt.isocalendar().week.astype(int)
    df['season'] = df['month'].apply(get_season)

    # Step 11: ENSO mapping
    df['enso_condition'] = df['year'].map(ENSO_MAP).fillna("Neutral")
    df['el_nino_year'] = (df['enso_condition'] == "El Nino").astype(int)

    # Hidden heat gap
    df['hi_gap'] = df['computed_heat_index'] - df['temperature_2m_mean']

    # Is danger day flag
    df['is_danger_day'] = df['danger_category'].isin(["Danger", "Extreme Danger"]).astype(int)

    # Sort by date
    df = df.sort_values('time').reset_index(drop=True)

    summary["rows_after"] = len(df)

    return df, summary
