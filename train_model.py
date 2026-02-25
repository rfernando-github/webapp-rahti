"""Train the CardioRisk Decision Tree model and save as pickle + metadata JSON."""
import json
import pickle
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, classification_report, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

# ── Load data ──
df = pd.read_csv('../Health Screening Data.csv', index_col=0)
print(f'Loaded {len(df):,} records')

# ── Preprocessing (same filters as export_figures.py) ──
df_clean = df.copy()
bp_filter = ((df_clean['ap_hi'] >= 90) & (df_clean['ap_hi'] <= 250) &
             (df_clean['ap_lo'] >= 40) & (df_clean['ap_lo'] <= 150) &
             (df_clean['ap_hi'] > df_clean['ap_lo']))
hw_filter = ((df_clean['height'] >= 100) & (df_clean['height'] <= 220) &
             (df_clean['weight'] >= 30) & (df_clean['weight'] <= 200))
df_clean = df_clean[bp_filter & hw_filter]
print(f'After cleaning: {len(df_clean):,} records')

# ── Features & target ──
feature_columns = ['AgeinYr', 'gender', 'BMI', 'ap_hi', 'ap_lo',
                   'cholesterol', 'gluc', 'smoke', 'alco', 'active']
X = df_clean[feature_columns]
y = df_clean['cardio']
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ── Train Decision Tree ──
model = DecisionTreeClassifier(
    max_depth=5, min_samples_split=10, min_samples_leaf=5,
    criterion='gini', random_state=42
)
model.fit(X_train, y_train)

# ── Evaluate ──
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
roc_auc = roc_auc_score(y_test, y_proba)

print(f'\nTest Accuracy: {accuracy:.4f}')
print(f'Precision:     {precision:.4f}')
print(f'Recall:        {recall:.4f}')
print(f'F1 Score:      {f1:.4f}')
print(f'ROC AUC:       {roc_auc:.4f}')

# ── Save model ──
with open('model.pkl', 'wb') as f:
    pickle.dump(model, f)
print('\nSaved model.pkl')

# ── Save metadata ──
feature_importances = dict(zip(feature_columns,
                               [round(float(x), 4) for x in model.feature_importances_]))
metadata = {
    'model_type': 'DecisionTreeClassifier',
    'hyperparameters': {
        'max_depth': 5,
        'min_samples_split': 10,
        'min_samples_leaf': 5,
        'criterion': 'gini',
        'random_state': 42
    },
    'feature_columns': feature_columns,
    'metrics': {
        'accuracy': round(float(accuracy), 4),
        'precision': round(float(precision), 4),
        'recall': round(float(recall), 4),
        'f1_score': round(float(f1), 4),
        'roc_auc': round(float(roc_auc), 4)
    },
    'feature_importances': feature_importances,
    'dataset': {
        'total_records': len(df),
        'records_after_cleaning': len(df_clean),
        'training_samples': len(X_train),
        'test_samples': len(X_test)
    },
    'training_date': datetime.now().isoformat()
}

with open('model_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
print('Saved model_metadata.json')
