python -m openlens_ai.main \
    --question "What are the temporal patterns of vital sign deterioration preceding cardiac arrest events in critical care settings?" \
    --dataset-path "datasets/eicu-demo" \
    --thread-id "pred_aki_trend_eicu_demo" \
    --notify-email "dzdzzd@126.com" \
    --interrupt-after-subgraph "none" \
    --language "eng" \
    --domain "medical" \
    --config "config.toml" \
    --e2e-test