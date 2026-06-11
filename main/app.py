"""
HeatWatch - Flask Application
Main entry point with all routes for the Heat Index Analytics Dashboard.
"""

import os
import sys
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify

# Point to the root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from backend.preprocessing import preprocess_csv
from backend.analytics import (
    compute_metric_cards,
    compute_danger_days_per_year,
    compute_monthly_comparison,
    compute_key_insights,
    compute_annual_trend,
    compute_earliest_danger_day,
    compute_hi_gap_trend,
    compute_danger_calendar,
    compute_top_dangerous_weeks,
    get_available_years,
)
from backend.predictor import HeatWatchPredictor

# Resolve templates and static folder locations dynamically
template_dir = os.path.join(ROOT_DIR, 'templates') if os.path.exists(os.path.join(ROOT_DIR, 'templates')) else os.path.join(ROOT_DIR, 'frontend')
static_dir = os.path.join(ROOT_DIR, 'static') if os.path.exists(os.path.join(ROOT_DIR, 'static')) else os.path.join(ROOT_DIR, 'frontend', 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = 'heatwatch-secret-key-2026'

# Global state
cleaned_data = None
cleaning_summary = None
predictor_model = None


def is_data_loaded():
    """Check if data has been loaded and processed."""
    return cleaned_data is not None


# Routes

@app.route('/')
def index():
    """Landing page with file upload."""
    if is_data_loaded():
        return redirect(url_for('dashboard'))
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload():
    """Handle CSV file upload and run preprocessing pipeline."""
    global cleaned_data, cleaning_summary, predictor_model

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.lower().endswith('.csv'):
        return jsonify({'error': 'Only .csv files are accepted. Please upload a valid CSV file.'}), 400

    try:
        # Read file content
        content = file.read().decode('utf-8')

        # Run preprocessing pipeline
        cleaned_data, cleaning_summary = preprocess_csv(content)

        # Train the ML predictor
        predictor_model = HeatWatchPredictor()
        predictor_model.train(cleaned_data)

        return jsonify({
            'success': True,
            'summary': cleaning_summary,
            'redirect': url_for('dashboard'),
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500


@app.route('/reset')
def reset():
    """Reset the application state and return to upload page."""
    global cleaned_data, cleaning_summary, predictor_model
    cleaned_data = None
    cleaning_summary = None
    predictor_model = None
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    """Main dashboard page."""
    if not is_data_loaded():
        return redirect(url_for('index'))

    metrics = compute_metric_cards(cleaned_data)
    danger_days, trend_slope = compute_danger_days_per_year(cleaned_data)
    
    years = get_available_years(cleaned_data)
    default_year1 = years[0]
    default_year2 = years[-1]
    
    monthly = compute_monthly_comparison(cleaned_data, default_year1, default_year2)
    insights = compute_key_insights(cleaned_data)

    return render_template('dashboard.html',
                           metrics=metrics,
                           danger_days=json.dumps(danger_days),
                           trend_slope=trend_slope,
                           monthly=json.dumps(monthly),
                           insights=insights,
                           years=years,
                           default_year1=default_year1,
                           default_year2=default_year2,
                           cleaning_summary=cleaning_summary)


@app.route('/historical')
def historical():
    """Historical trends page."""
    if not is_data_loaded():
        return redirect(url_for('index'))

    annual_trend = compute_annual_trend(cleaned_data)
    earliest_danger = compute_earliest_danger_day(cleaned_data)
    hi_gap = compute_hi_gap_trend(cleaned_data)

    return render_template('historical.html',
                           annual_trend=json.dumps(annual_trend),
                           earliest_danger=json.dumps(earliest_danger),
                           hi_gap=json.dumps(hi_gap))


@app.route('/calendar')
def calendar():
    """Danger calendar page."""
    if not is_data_loaded():
        return redirect(url_for('index'))

    calendar_data, month_names = compute_danger_calendar(cleaned_data)
    top_weeks = compute_top_dangerous_weeks(cleaned_data)

    return render_template('calendar.html',
                           calendar_data=json.dumps(calendar_data),
                           month_names=json.dumps(month_names),
                           top_weeks=top_weeks)


@app.route('/predictor')
def predictor_page():
    """Predictor page."""
    if not is_data_loaded():
        return redirect(url_for('index'))

    forecast = predictor_model.get_forecast_data() if predictor_model else None
    recommendations = predictor_model.get_recommendations() if predictor_model else []

    return render_template('predictor.html',
                           forecast=json.dumps(forecast),
                           recommendations=recommendations)


@app.route('/api/monthly-comparison')
def api_monthly_comparison():
    """API endpoint for dynamic dual-line chart updates."""
    if not is_data_loaded():
        return jsonify({'error': 'No data loaded'}), 400

    year1 = request.args.get('year1', type=int)
    year2 = request.args.get('year2', type=int)

    if not year1 or not year2:
        return jsonify({'error': 'Both year1 and year2 parameters required'}), 400

    data = compute_monthly_comparison(cleaned_data, year1, year2)
    return jsonify(data)


@app.route('/api/predict', methods=['POST'])
def api_predict():
    """API endpoint for danger level prediction."""
    if not is_data_loaded() or not predictor_model:
        return jsonify({'error': 'Model not ready'}), 400

    data = request.get_json()
    day = data.get('day', 1)
    month = data.get('month', 1)
    year = data.get('year', 2026)
    enso = data.get('enso_condition', 'Neutral')

    result = predictor_model.predict(day, month, year, enso)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
