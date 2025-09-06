---
name: prediction_reminders
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
- prediction
- predict
- dynamic
---

Reminders: 
- **Prevent Data Leakage:** Confirm that training, validation, and testing datasets are strictly separated, with no overlap in samples, time windows, or features. Verify that test data is never used—directly or indirectly—for model training, feature engineering, or hyperparameter tuning.
- **Validate and Fix Temporal Integrity:** For time-series or longitudinal data, ensure that no future information is used to predict past or present states (e.g., avoid “peeking ahead” into data that would not be available at the prediction time).
- **Validate and Fix Feature Engineering:** Verify that derived or engineered features are created using only information available at the time of prediction, and not using aggregated statistics from the entire dataset.
- **Prevent Unrealistic Results:** If the model produces unreasonable results (e.g., AUROC<=0.5, AUROC>0.98, Accuracy>0.98, Accuracy=0), investigate the cause (e.g. data leakage) and fix the issue.