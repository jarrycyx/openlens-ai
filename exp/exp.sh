python -m openlens_ai.build_graph \
    --question "What is the prediction precision of AKI in ICU patients when dynamically predicting each day based on the past two days of historical data?" \
    --dataset-path "datasets/mimic" \
    --thread-id "pred_aki_dy_mimic" \
    --email "dzdzzd@126.com"

python -m openlens_ai.build_graph \
    --question "What is the prediction precision of AKI in ICU patients when dynamically predicting each day based on the past two days of historical data?" \
    --dataset-path "datasets/eicu" \
    --thread-id "pred_aki_dy_eicu" \
    --email "dzdzzd@126.com"