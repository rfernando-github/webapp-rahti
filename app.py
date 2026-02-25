"""Flask application for CardioRisk Predictor (API Layer) — Rahti-ready."""
import os

from flask import Flask, render_template, request

from model_service import (get_decision_path, get_feature_importance,
                           load_metadata, load_model, predict,
                           prepare_features)
from validators import validate_input

app = Flask(__name__)

# Load model and metadata at startup
model = load_model('model.pkl')
metadata = load_metadata('model_metadata.json')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict_route():
    form_data = request.form.to_dict()

    # Validate input
    errors = validate_input(form_data)
    if errors:
        return render_template('index.html', errors=errors, form_data=form_data)

    # Extract features and predict
    features, bmi = prepare_features(form_data)
    result = predict(model, features)
    result['bmi'] = bmi

    # Explainability
    result['feature_importance'] = get_feature_importance(model)
    result['decision_path'] = get_decision_path(model, features)

    return render_template('result.html', result=result, form_data=form_data)


@app.route('/about')
def about():
    return render_template('about.html', metadata=metadata)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
