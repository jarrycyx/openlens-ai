python -m openlens_ai.build_graph \
    --question "What is the prediction precision of AKI in ICU patients when dynamically predicting each day based on the past two days of historical data?" \
    --dataset-path "datasets/mimic-iv-icu" \
    --thread-id "pred_aki_dy_mimic_icu_csv" \
    --email "dzdzzd@126.com"

python -m openlens_ai.build_graph \
    --question "What is the prediction precision of AKI in ICU patients when dynamically predicting each day based on the past two days of historical data?" \
    --dataset-path "datasets/eicu-demo" \
    --thread-id "pred_aki_dy_eicu_demo" \
    --email "dzdzzd@126.com"

python -m openlens_ai.build_graph \
    --question "What is the prediction precision of AKI in ICU patients when dynamically predicting each day based on the past two days of historical data?" \
    --dataset-path "datasets/nanjing" \
    --thread-id "pred_aki_dy_nanjing" \
    --email "dzdzzd@126.com"

python -m openlens_ai.build_graph \
    --question "What is the average ICU length of stay for patients with sepsis?" \
    --dataset-path "datasets/mimic-iv-icu" \
    --thread-id "los_sepsis_dy_mimic_icu_csv" \
    --email "dzdzzd@126.com"

python -m openlens_ai.build_graph \
    --question "What is the average ICU length of stay for patients with sepsis?" \
    --dataset-path "datasets/eicu-demo" \
    --thread-id "los_sepsis_eicu_demo" \
    --email "dzdzzd@126.com"
