"""
HeatWatch - Predictor Module
Decision Tree Classifier for danger category prediction
and Linear Regression for heat index trend forecasting.
"""

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder


class HeatWatchPredictor:
    """ML-backed prediction system for danger level and trend forecasting."""

    def __init__(self):
        self.classifier = None
        self.regressor = None
        self.label_encoder = LabelEncoder()
        self.enso_encoder = LabelEncoder()
        self.category_order = ['Normal', 'Caution', 'Extreme Caution', 'Danger', 'Extreme Danger']
        self.is_trained = False
        self.forecast_data = None
        self.historical_hi_lookup = {}

    def train(self, df):
        """Train both models on the cleaned dataset."""
        # Decision Tree Classifier
        train_df = df.dropna(subset=['danger_category']).copy()

        # Encode ENSO condition
        train_df['enso_encoded'] = self.enso_encoder.fit_transform(train_df['enso_condition'])

        # Encode target
        self.label_encoder.fit(self.category_order)
        train_df['target'] = self.label_encoder.transform(train_df['danger_category'])

        features = ['day', 'month', 'year', 'enso_encoded']
        X = train_df[features].values
        y = train_df['target'].values

        self.classifier = DecisionTreeClassifier(
            max_depth=10,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
        )
        self.classifier.fit(X, y)

        # Linear Regression for Forecasting
        yearly = df.groupby('year')['computed_heat_index'].mean().reset_index()
        yearly.columns = ['year', 'avg_hi']

        X_reg = yearly['year'].values.reshape(-1, 1)
        y_reg = yearly['avg_hi'].values

        self.regressor = LinearRegression()
        self.regressor.fit(X_reg, y_reg)

        self.historical_years = yearly['year'].tolist()
        self.historical_avg_hi = [round(v, 2) for v in yearly['avg_hi'].tolist()]

        # Build historical lookup table for Month + ENSO based on actual data
        lookup_df = train_df.groupby(['month', 'enso_condition'])['computed_heat_index'].mean().reset_index()
        for _, row in lookup_df.iterrows():
            self.historical_hi_lookup[(int(row['month']), row['enso_condition'])] = row['computed_heat_index']

        # Compute forecast through 2028
        forecast_years = list(range(int(yearly['year'].min()), 2029))
        forecast_values = self.regressor.predict(np.array(forecast_years).reshape(-1, 1))

        # Compute confidence interval using residuals
        y_pred_hist = self.regressor.predict(X_reg)
        residuals = y_reg - y_pred_hist
        std_err = np.std(residuals)

        self.forecast_data = {
            'years': forecast_years,
            'values': [round(float(v), 2) for v in forecast_values.tolist()],
            'upper': [round(float(v + 1.96 * std_err), 2) for v in forecast_values.tolist()],
            'lower': [round(float(v - 1.96 * std_err), 2) for v in forecast_values.tolist()],
            'slope': round(float(self.regressor.coef_[0]), 4),
            'historical_end_year': int(yearly['year'].max()),
        }
        
        self.historical_end_year = int(yearly['year'].max())

        # Find projected year when average crosses 42 degrees C
        crossing_year = None
        for yr, val in zip(forecast_years, forecast_values):
            if val >= 42:
                crossing_year = yr
                break
        self.forecast_data['crossing_year'] = crossing_year

        self.is_trained = True

    def predict(self, day, month, year, enso_condition):
        """
        Predict danger category for a given date and ENSO condition.
        Returns dict with prediction results.
        """
        if not self.is_trained:
            return {"error": "Model not trained yet"}

        # Encode ENSO condition
        try:
            enso_encoded = self.enso_encoder.transform([enso_condition])[0]
        except ValueError:
            enso_encoded = self.enso_encoder.transform(["Neutral"])[0]

        features = np.array([[day, month, year, enso_encoded]])
        
        # Predict category
        predicted_idx = self.classifier.predict(features)[0]
        predicted_category = self.label_encoder.inverse_transform([predicted_idx])[0]

        # Predict probabilities
        probabilities = self.classifier.predict_proba(features)[0]
        max_prob = float(max(probabilities)) * 100

        # Predict heat index using historical lookup based on Month and ENSO condition
        # If the exact combo isn't in historical data, fallback to month average, then general average
        exact_match = self.historical_hi_lookup.get((month, enso_condition))
        if exact_match is not None:
            base_hi = exact_match
        else:
            # Fallback to month average across all conditions if specific ENSO condition missing
            month_matches = [v for k, v in self.historical_hi_lookup.items() if k[0] == month]
            base_hi = sum(month_matches) / len(month_matches) if month_matches else 35.0
            
        # Add a slight trend factor based on the regression slope
        trend_adjustment = float(self.regressor.coef_[0]) * (year - self.historical_end_year)
        predicted_hi = base_hi + max(0, trend_adjustment) # only apply upward trend

        # Health advisory based on category
        advisories = {
            'Normal': 'No significant heat risk. Normal outdoor activities are safe.',
            'Caution': 'Fatigue possible with prolonged exposure. Stay hydrated and take breaks during outdoor physical activity.',
            'Extreme Caution': 'Heat cramps and exhaustion possible. Limit prolonged outdoor exposure, especially during midday hours.',
            'Danger': 'Heat cramps and exhaustion likely. Heat stroke is possible. Avoid prolonged outdoor activities. Seek air-conditioned spaces.',
            'Extreme Danger': 'Heat stroke is highly likely. This is a life-threatening condition. Stay indoors. Cancel all outdoor activities.',
        }

        return {
            'category': predicted_category,
            'probability': round(max_prob, 1),
            'predicted_hi': round(predicted_hi, 1),
            'advisory': advisories.get(predicted_category, ''),
        }

    def get_forecast_data(self):
        """Return forecast chart data."""
        if not self.is_trained:
            return None
        return self.forecast_data

    def get_recommendations(self):
        """Return 3 data-backed recommendation cards."""
        if not self.is_trained:
            return []

        slope = self.forecast_data['slope']
        crossing = self.forecast_data['crossing_year']

        return [
            {
                'title': 'Schools & Universities',
                'text': f'Consider completing in-person classes before late April. At the current trend rate of +{slope:.2f}\u00b0C/year, May heat index levels will increasingly exceed Danger thresholds. Shift to online delivery during the April 24 \u2013 May 14 peak danger window.',
                'stat': f'+{slope:.2f}\u00b0C/year trend',
            },
            {
                'title': 'Outdoor Workers',
                'text': 'DOLE and labor agencies should pre-announce heat advisories aligned with historical danger windows, specifically the first two weeks of May. El Nino years require enhanced protocols.',
                'stat': 'Peak danger: May 1\u201314',
            },
            {
                'title': 'Public Health',
                'text': f'Ensure hospitals and clinics are ready with heat stroke supplies before the hottest weeks of the year. {"The average heat index is expected to reach the 42°C danger level by " + str(crossing) if crossing else "The heat trend is still going up"}. Focus on crowded neighborhoods with few trees or parks.',
                'stat': f'Projected 42°C avg: {crossing if crossing else "Beyond 2028"}',
            },
        ]
