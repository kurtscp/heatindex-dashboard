"""
HeatWatch - Analytics Engine
Computes statistics, chart data, and auto-generated insights from the preprocessed dataset.
"""

import pandas as pd
import numpy as np
from scipy import stats


def compute_metric_cards(df):
    """
    Compute the 4 metric summary card values for the main dashboard.
    Returns dict with card data.
    """
    # Determine the most recent complete year (has data for all 12 months or is the latest full year)
    year_counts = df.groupby('year')['month'].nunique()
    complete_years = year_counts[year_counts == 12].index.tolist()
    
    if complete_years:
        latest_year = max(complete_years)
    else:
        latest_year = df['year'].max()
    
    base_year = df['year'].min()

    # Card 1: Average Heat Index (latest complete year)
    latest_avg_hi = df[df['year'] == latest_year]['computed_heat_index'].mean()
    base_avg_hi = df[df['year'] == base_year]['computed_heat_index'].mean()
    avg_hi_diff = latest_avg_hi - base_avg_hi

    # Card 2: Total Danger Days (latest complete year)
    latest_danger_days = int(df[df['year'] == latest_year]['is_danger_day'].sum())
    base_danger_days = int(df[df['year'] == base_year]['is_danger_day'].sum())
    danger_days_diff = latest_danger_days - base_danger_days

    # Card 3: Peak recorded heat index
    peak_idx = df['computed_heat_index'].idxmax()
    peak_hi = df.loc[peak_idx, 'computed_heat_index']
    peak_date = df.loc[peak_idx, 'time']
    if hasattr(peak_date, 'strftime'):
        peak_date_str = peak_date.strftime('%B %d, %Y')
    else:
        peak_date_str = str(peak_date)

    # Card 4: Riskiest month historically
    monthly_avg = df.groupby('month')['computed_heat_index'].mean()
    riskiest_month_num = monthly_avg.idxmax()
    riskiest_month_avg = monthly_avg.max()
    month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April',
                   5: 'May', 6: 'June', 7: 'July', 8: 'August',
                   9: 'September', 10: 'October', 11: 'November', 12: 'December'}
    riskiest_month_name = month_names.get(riskiest_month_num, str(riskiest_month_num))

    return {
        "avg_hi": {
            "title": "Average Heat Index",
            "value": f"{latest_avg_hi:.1f}\u00b0C",
            "subtitle": f"{chr(8593) if avg_hi_diff >= 0 else chr(8595)} {'+' if avg_hi_diff >= 0 else ''}{avg_hi_diff:.1f}\u00b0C vs {base_year}",
            "year": latest_year,
        },
        "danger_days": {
            "title": "Total Danger Days",
            "value": str(latest_danger_days),
            "subtitle": f"{chr(8593) if danger_days_diff >= 0 else chr(8595)} {'+' if danger_days_diff >= 0 else ''}{danger_days_diff} days vs {base_year}",
            "year": latest_year,
        },
        "peak_hi": {
            "title": "Peak Heat Index",
            "value": f"{peak_hi:.1f}\u00b0C",
            "subtitle": peak_date_str,
        },
        "riskiest_month": {
            "title": "Riskiest Month",
            "value": riskiest_month_name,
            "subtitle": f"Avg {riskiest_month_avg:.1f}\u00b0C historically",
        },
    }


def compute_danger_days_per_year(df):
    """Bar chart data: danger day counts per year with El Nino flags."""
    yearly = df.groupby('year').agg(
        danger_days=('is_danger_day', 'sum'),
        el_nino=('el_nino_year', 'first'),
        enso_condition=('enso_condition', 'first'),
    ).reset_index()
    
    # Linear regression trend line
    x = yearly['year'].values.astype(float)
    y = yearly['danger_days'].values.astype(float)
    if len(x) >= 2:
        slope, intercept, _, _, _ = stats.linregress(x, y)
        yearly['trend'] = slope * x + intercept
        trend_slope = slope
    else:
        yearly['trend'] = y
        trend_slope = 0

    return yearly.to_dict('records'), trend_slope


def compute_monthly_comparison(df, year1, year2):
    """Dual-line chart data: monthly average HI for two selected years."""
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    data1 = df[df['year'] == year1].groupby('month')['computed_heat_index'].mean()
    data2 = df[df['year'] == year2].groupby('month')['computed_heat_index'].mean()

    result = {
        'months': month_names,
        'year1': year1,
        'year2': year2,
        'values1': [round(data1.get(m, 0), 2) if m in data1.index else None for m in range(1, 13)],
        'values2': [round(data2.get(m, 0), 2) if m in data2.index else None for m in range(1, 13)],
    }
    return result


def compute_key_insights(df):
    """Auto-generate the 4 key insights for the dashboard panel."""
    insights = []

    # Insight 1: Highest Recorded Heat Index
    peak_idx = df['computed_heat_index'].idxmax()
    max_hi = df.loc[peak_idx, 'computed_heat_index']
    peak_date = df.loc[peak_idx, 'time']
    if hasattr(peak_date, 'strftime'):
        max_date = peak_date.strftime('%B %d, %Y')
    else:
        max_date = str(peak_date)
        
    insights.append({
        "title": "Highest Heat Index",
        "text": f"The maximum recorded heat index was {max_hi:.1f}°C, which occurred on {max_date}.",
    })

    # Insight 2: Total Danger Days
    total_danger_days = int(df['is_danger_day'].sum())
    first_year = df['year'].min()
    last_year = df['year'].max()
    insights.append({
        "title": "Total Danger Days",
        "text": f"There have been {total_danger_days} days where the heat index reached the danger level (≥42°C) between {first_year} and {last_year}.",
    })

    # Insight 3: Average Heat Gap
    avg_gap = df['hi_gap'].mean()
    insights.append({
        "title": "Average Heat Gap",
        "text": f"On average, high humidity makes the perceived heat index {avg_gap:.1f}°C hotter than the actual measured temperature.",
    })

    # Insight 4: Highest Danger Year
    yearly_danger = df.groupby('year')['is_danger_day'].sum()
    if not yearly_danger.empty and yearly_danger.max() > 0:
        worst_year = yearly_danger.idxmax()
        worst_count = int(yearly_danger.max())
        insights.append({
            "title": "Highest Danger Year",
            "text": f"The year {worst_year} experienced the most extreme heat, with a total of {worst_count} recorded danger days.",
        })
    else:
        insights.append({
            "title": "No Danger Years",
            "text": "There are no years in the current dataset that recorded danger-level heat index days.",
        })

    return insights


def compute_annual_trend(df):
    """Annual average heat index trend with linear regression."""
    yearly = df.groupby('year')['computed_heat_index'].mean().reset_index()
    yearly.columns = ['year', 'avg_hi']

    x = yearly['year'].values.astype(float)
    y = yearly['avg_hi'].values
    slope, intercept, r_value, _, _ = stats.linregress(x, y)
    yearly['trend'] = slope * x + intercept

    return {
        'years': yearly['year'].tolist(),
        'avg_hi': [round(v, 2) for v in yearly['avg_hi'].tolist()],
        'trend': [round(v, 2) for v in yearly['trend'].tolist()],
        'slope': round(slope, 4),
        'r_squared': round(r_value ** 2, 4),
    }


def compute_earliest_danger_day(df):
    """Earliest calendar day per year that reached Danger level."""
    danger_df = df[df['danger_category'].isin(['Danger', 'Extreme Danger'])]
    earliest = danger_df.groupby('year')['day_of_year'].min().reset_index()
    earliest.columns = ['year', 'earliest_doy']

    # Convert day_of_year to a readable date label
    labels = []
    for _, row in earliest.iterrows():
        try:
            date = pd.Timestamp(year=int(row['year']), month=1, day=1) + pd.Timedelta(days=int(row['earliest_doy']) - 1)
            labels.append(date.strftime('%b %d'))
        except Exception:
            labels.append(f"Day {int(row['earliest_doy'])}")
    earliest['label'] = labels

    # Check for years with no danger days
    all_years = sorted(df['year'].unique())
    result = []
    for y in all_years:
        match = earliest[earliest['year'] == y]
        if len(match) > 0:
            result.append({
                'year': int(y),
                'day_of_year': int(match.iloc[0]['earliest_doy']),
                'label': match.iloc[0]['label'],
                'has_danger': True,
            })
        else:
            result.append({
                'year': int(y),
                'day_of_year': None,
                'label': 'None',
                'has_danger': False,
            })

    return result


def compute_hi_gap_trend(df):
    """Temperature vs Heat Index gap data per year."""
    yearly = df.groupby('year').agg(
        avg_temp=('temperature_2m_mean', 'mean'),
        avg_hi=('computed_heat_index', 'mean'),
        avg_gap=('hi_gap', 'mean'),
    ).reset_index()

    return {
        'years': yearly['year'].tolist(),
        'avg_temp': [round(v, 2) for v in yearly['avg_temp'].tolist()],
        'avg_hi': [round(v, 2) for v in yearly['avg_hi'].tolist()],
        'avg_gap': [round(v, 2) for v in yearly['avg_gap'].tolist()],
    }


def compute_danger_calendar(df):
    """Heatmap calendar: year x month grid with danger severity."""
    cat_order = {'Normal': 0, 'Caution': 1, 'Extreme Caution': 2, 'Danger': 3, 'Extreme Danger': 4}

    years = sorted(df['year'].unique())
    months = list(range(1, 13))
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    pivot_data = []
    for y in years:
        row = {'year': int(y)}
        for m in months:
            subset = df[(df['year'] == y) & (df['month'] == m)]
            if len(subset) == 0:
                row[month_names[m - 1]] = {
                    'severity': -1,
                    'category': 'No Data',
                    'danger_days': 0,
                    'peak_hi': 0,
                }
            else:
                max_cat = subset['danger_category'].map(cat_order).max()
                cat_name = [k for k, v in cat_order.items() if v == max_cat][0]
                row[month_names[m - 1]] = {
                    'severity': int(max_cat),
                    'category': cat_name,
                    'danger_days': int(subset['is_danger_day'].sum()),
                    'peak_hi': round(float(subset['computed_heat_index'].max()), 1),
                    'avg_hi': round(float(subset['computed_heat_index'].mean()), 1),
                }
        pivot_data.append(row)

    return pivot_data, month_names


def compute_top_dangerous_weeks(df):
    """Top 5 historically most dangerous weeks."""
    weekly = df.groupby('week_of_year').agg(
        avg_hi=('computed_heat_index', 'mean'),
        total_days=('is_danger_day', 'count'),
        danger_days=('is_danger_day', 'sum'),
    ).reset_index()

    weekly['danger_probability'] = (weekly['danger_days'] / weekly['total_days'] * 100).round(1)
    weekly['avg_hi'] = weekly['avg_hi'].round(1)

    def get_week_category(avg_hi):
        if avg_hi >= 52:
            return 'Extreme Danger'
        elif avg_hi >= 42:
            return 'Danger'
        elif avg_hi >= 33:
            return 'Extreme Caution'
        elif avg_hi >= 27:
            return 'Caution'
        return 'Normal'

    weekly['category'] = weekly['avg_hi'].apply(get_week_category)

    # Sort by danger probability descending
    weekly = weekly.sort_values('danger_probability', ascending=False).head(5).reset_index(drop=True)

    results = []
    for i, row in weekly.iterrows():
        wk = int(row['week_of_year'])
        start_day = (wk - 1) * 7 + 1
        end_day = start_day + 6
        try:
            start_date = pd.Timestamp(year=2024, month=1, day=1) + pd.Timedelta(days=start_day - 1)
            end_date = pd.Timestamp(year=2024, month=1, day=1) + pd.Timedelta(days=end_day - 1)
            week_range = f"{start_date.strftime('%b %d')} \u2013 {end_date.strftime('%b %d')}"
        except Exception:
            week_range = f"Week {wk}"

        results.append({
            'rank': i + 1,
            'week_range': week_range,
            'avg_hi': float(row['avg_hi']),
            'danger_probability': float(row['danger_probability']),
            'category': row['category'],
        })

    return results


def get_available_years(df):
    """Get list of available years in the dataset."""
    return sorted(df['year'].unique().tolist())
