"""Model Service + Feature Extractor + Explainability Module."""
import json
import pickle

import numpy as np


def load_model(model_path='model.pkl'):
    """Load the trained model from a pickle file."""
    with open(model_path, 'rb') as f:
        return pickle.load(f)


def load_metadata(metadata_path='model_metadata.json'):
    """Load model metadata from JSON."""
    with open(metadata_path, 'r') as f:
        return json.load(f)


def calculate_bmi(height_cm, weight_kg):
    """Feature Extractor: calculate BMI from height (cm) and weight (kg)."""
    height_m = height_cm / 100.0
    return round(weight_kg / (height_m ** 2), 2)


def prepare_features(form_data):
    """Extract and arrange features from form data into model input order.

    Feature order: AgeinYr, gender, BMI, ap_hi, ap_lo, cholesterol, gluc,
                   smoke, alco, active
    """
    age = int(form_data['age'])
    gender = int(form_data['gender'])
    height = float(form_data['height'])
    weight = float(form_data['weight'])
    bmi = calculate_bmi(height, weight)
    ap_hi = int(form_data['ap_hi'])
    ap_lo = int(form_data['ap_lo'])
    cholesterol = int(form_data['cholesterol'])
    gluc = int(form_data['gluc'])
    smoke = int(form_data['smoke'])
    alco = int(form_data['alco'])
    active = int(form_data['active'])

    features = np.array([[age, gender, bmi, ap_hi, ap_lo,
                          cholesterol, gluc, smoke, alco, active]])
    return features, bmi


def predict(model, features):
    """Return prediction label and class probabilities."""
    prediction = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]
    return {
        'prediction': int(prediction),
        'label': 'HIGH RISK' if prediction == 1 else 'LOW RISK',
        'probability_no_cvd': round(float(probabilities[0]) * 100, 1),
        'probability_cvd': round(float(probabilities[1]) * 100, 1),
    }


def get_feature_importance(model, feature_names=None):
    """Return sorted feature importance scores."""
    if feature_names is None:
        feature_names = ['AgeinYr', 'gender', 'BMI', 'ap_hi', 'ap_lo',
                         'cholesterol', 'gluc', 'smoke', 'alco', 'active']
    importances = model.feature_importances_
    pairs = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
    return [{'feature': name, 'importance': round(float(imp), 4)} for name, imp in pairs]


def get_decision_path(model, features, feature_names=None):
    """Extract the decision rules used for this specific prediction."""
    if feature_names is None:
        feature_names = ['AgeinYr', 'gender', 'BMI', 'ap_hi', 'ap_lo',
                         'cholesterol', 'gluc', 'smoke', 'alco', 'active']

    tree = model.tree_
    node_indicator = model.decision_path(features)
    node_indices = node_indicator.indices

    rules = []
    for node_id in node_indices:
        if tree.children_left[node_id] == tree.children_right[node_id]:
            # Leaf node
            continue
        feature_idx = tree.feature[node_id]
        threshold = tree.threshold[node_id]
        feature_name = feature_names[feature_idx]
        value = features[0, feature_idx]

        if value <= threshold:
            direction = '<='
        else:
            direction = '>'

        rules.append({
            'feature': feature_name,
            'threshold': round(float(threshold), 2),
            'value': round(float(value), 2),
            'direction': direction
        })

    return rules
