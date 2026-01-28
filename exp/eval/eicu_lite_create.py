import os
import pandas as pd
from pathlib import Path
import random

SOURCE_DIR = Path('datasets/eicu')
TARGET_DIR = Path('datasets/eicu20k')
NUM_PATIENTS = 20000

def select_patients():
    patient_df = pd.read_csv(SOURCE_DIR / 'patient.csv')
    
    random.seed(42)
    selected_ids = random.sample(patient_df['patientunitstayid'].tolist(), NUM_PATIENTS)
    selected_ids_set = set(selected_ids)
    
    patient_subset = patient_df[patient_df['patientunitstayid'].isin(selected_ids_set)]
    
    return selected_ids_set, patient_subset

def process_file(filepath, selected_ids_set):
    df = pd.read_csv(filepath)
    
    if 'patientunitstayid' in df.columns:
        df_subset = df[df['patientunitstayid'].isin(selected_ids_set)]
        return df_subset
    else:
        return df

def main():
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    selected_ids_set, patient_subset = select_patients()
    patient_subset.to_csv(TARGET_DIR / 'patient.csv', index=False)
    print(f"Created {TARGET_DIR / 'patient.csv'} with {len(patient_subset)} patients")
    
    csv_files = sorted([f for f in SOURCE_DIR.glob('*.csv') if f.name != 'patient.csv'])
    
    for csv_file in csv_files:
        try:
            df_subset = process_file(csv_file, selected_ids_set)
            df_subset.to_csv(TARGET_DIR / csv_file.name, index=False)
            print(f"Created {TARGET_DIR / csv_file.name} with {len(df_subset)} rows")
        except Exception as e:
            print(f"Error processing {csv_file.name}: {e}")
    
    print(f"\nSuccessfully created eICU 20k dataset in {TARGET_DIR}")

if __name__ == '__main__':
    main()
