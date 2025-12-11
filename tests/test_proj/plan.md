# Experiment Plan

Objective: What are the temporal patterns of vital sign deterioration preceding cardiac arrest events in critical care settings?

Sub Tasks:


# SUBTASK01
 ### **Subtask 1: Cardiac Arrest Cohort Identification and Event Timing**

**Input Specifications:**
- **Source datasets:** `patient.csv`, `apachePredVar.csv`, `apachePatientResult.csv`
- **Required variables:** 
  - From `patient.csv`: `patientunitstayid`, `age`, `gender`, `unittype`, `hospitaldischargestatus`
  - From `apachePredVar.csv`: `patientunitstayid`, `admitdiagnosis`, `diedinhospital`, `age`, `gender`
  - From `apachePatientResult.csv`: `patientunitstayid`, `actualhospitalmortality`, `actualiculos`
- **Preprocessing steps:** 
  - Merge datasets on `patientunitstayid`
  - Filter for patients with cardiac arrest admission diagnoses (ICD-9 codes: 427.5, 995.91, 427.1, 427.41, 427.42)
  - Exclude patients with missing discharge status or timing information
  - Define cardiac arrest events as patients with admission diagnosis indicating cardiac arrest OR hospital mortality due to cardiac arrest

**Output Specifications:**
- **Format:** CSV file named `cardiac_arrest_cohort.csv`
- **Key artifacts:**
  - `patientunitstayid` (unique identifier)
  - `arrest_event_time` (time of cardiac arrest event)
  - `arrest_type` (primary diagnosis category)
  - `patient_age`, `gender`, `icu_type`
  - `time_to_arrest` (time from ICU admission to arrest event)
  - `survival_status` (binary: survived/died)
- **Quality constraints:** Ensure no duplicate patient IDs, realistic time-to-arrest values (0-168 hours), exclude survival rates > 0.999 or = 0

**Execution Protocol:**
1. Execute Python script: `python identify_cardiac_arrest_cohort.py`
2. Dependencies: Python 3.10+, pandas==1.5.0, numpy==1.24.0
3. Runtime conditions: 4GB RAM, < 10 minutes execution time
4. Command: `python identify_cardiac_arrest_cohort.py --input-dir=data --output=cardiac_arrest_cohort.csv`

**Validation Checks:**
- **Expected runtime:** < 10 minutes
- **Sample output verification:** First 5 rows should show valid cardiac arrest patients with complete timing information
- **Error handling:** Retry if memory allocation fails, handle missing ICD-9 codes gracefully
- **Data leak prevention:** Use only admission-time data for cohort definition, avoid post-arrest variables in initial identification


# SUBTASK02
 ### **Subtask 2: Vital Sign Time Series Extraction Around Arrest Events**

**Input Specifications:**
- **Source datasets:** `vitalPeriodic.csv`, `vitalAperiodic.csv`, `cardiac_arrest_cohort.csv` (from Subtask 1)
- **Required variables:**
  - From vital files: `patientunitstayid`, `observationoffset`, all vital sign columns (heartrate, sao2, systemicsystolic, systemicdiastolic, systemicmean, temperature, respiration)
  - From cohort: `arrest_event_time`, `patientunitstayid`
- **Preprocessing steps:**
  - Merge vital sign data with cardiac arrest cohort
  - Create time windows: 24 hours before arrest (-1440 to 0 minutes relative to arrest)
  - Handle missing data: linear interpolation for gaps < 30 minutes, forward fill for larger gaps
  - Exclude vital signs with > 50% missing data in the 24-hour window
  - Convert all vital signs to consistent units (mmHg for BP, °C for temperature, % for SpO2)

**Output Specifications:**
- **Format:** CSV file named `vital_signs_arrest_window.csv`
- **Key artifacts:**
  - `patientunitstayid`, `time_relative_to_arrest` (minutes)
  - Vital sign measurements at each time point
  - `data_quality_score` (percentage of valid measurements in window)
  - `measurement_frequency` (average time between measurements)
- **Quality constraints:** Ensure vital sign values within clinical ranges (HR: 20-200 bpm, BP: 40-300 mmHg, SpO2: 50-100%), exclude unrealistic patterns

**Execution Protocol:**
1. Execute Python script: `python extract_vital_signs_arrest_window.py`
2. Dependencies: Python 3.10+, pandas==1.5.0, scipy==1.10.0
3. Runtime conditions: 8GB RAM, < 30 minutes execution time
4. Command: `python extract_vital_signs_arrest_window.py --cohort=cardiac_arrest_cohort.csv --vital-dir=vital_data --output=vital_signs_arrest_window.csv`

**Validation Checks:**
- **Expected runtime:** < 30 minutes
- **Sample output verification:** Each patient should have 24-hour time series with vital signs at regular intervals
- **Error handling:** Handle missing offset values, validate time window boundaries
- **Data leak prevention:** Use only pre-arrest vital signs, ensure no post-arrest data contamination


# SUBTASK03
 ### **Subtask 3: Temporal Pattern Analysis and Statistical Modeling**

**Input Specifications:**
- **Source datasets:** `vital_signs_arrest_window.csv` (from Subtask 2), `cardiac_arrest_cohort.csv` (from Subtask 1)
- **Required variables:**
  - Time series vital sign data with `time_relative_to_arrest`
  - Patient demographics and arrest characteristics
  - Vital signs: heartrate, sao2, systemicsystolic, systemicmean, temperature, respiration
- **Preprocessing steps:**
  - Calculate vital sign trends using linear regression slopes over rolling windows (1, 2, 4, 6 hours)
  - Compute deterioration rates (change per hour) for each vital sign
  - Create composite deterioration scores (weighted sum of abnormal vital signs)
  - Identify critical deterioration thresholds based on clinical literature
  - Normalize vital signs by patient baseline (first 2 hours of observation)

**Output Specifications:**
- **Format:** JSON file named `temporal_patterns_results.json` and CSV file `deterioration_metrics.csv`
- **Key artifacts:**
  - Time-to-event analysis for each vital sign (when deterioration begins)
  - Statistical significance testing (p-values, confidence intervals)
  - Effect sizes (Cohen's d) for vital sign changes
  - Optimal prediction windows (hours before arrest with highest predictive power)
  - Temporal pattern classifications (early vs late deterioration patterns)
- **Quality constraints:** Ensure statistical validity (p-values < 0.05 with proper multiple testing correction), effect sizes within reasonable ranges, prevent AUROC > 0.98 or < 0.5

**Execution Protocol:**
1. Execute Python script: `python analyze_temporal_patterns.py`
2. Dependencies: Python 3.10+, pandas==1.5.0, numpy==1.24.0, scipy==1.10.0, lifelines==0.27.0
3. Runtime conditions: 16GB RAM, < 45 minutes execution time
4. Command: `python analyze_temporal_patterns.py --vital-data=vital_signs_arrest_window.csv --cohort=cardiac_arrest_cohort.csv --output=temporal_patterns_results.json`

**Validation Checks:**
- **Expected runtime:** < 45 minutes
- **Sample output verification:** JSON should contain statistically significant temporal patterns with proper confidence intervals
- **Error handling:** Handle statistical edge cases, validate time series completeness
- **Data leak prevention:** Use only pre-arrest data for pattern analysis, ensure temporal ordering is maintained


# SUBTASK04
 ### **Subtask 4: Manuscript Figure Generation and Visualization**

**Input Specifications:**
- **Source datasets:** `temporal_patterns_results.json` (from Subtask 3), `vital_signs_arrest_window.csv` (from Subtask 2)
- **Required variables:**
  - Statistical results from temporal analysis
  - Individual patient vital sign trajectories
  - Summary statistics and pattern classifications
  - Patient demographic and clinical characteristics
- **Preprocessing steps:**
  - Aggregate individual patient data into population-level trends
  - Create color-coded trajectory groups based on deterioration patterns
  - Normalize time series for visualization purposes
  - Generate summary statistics for figure annotations
  - Prepare high-resolution graphics suitable for publication

**Output Specifications:**
- **Format:** High-resolution PNG/PDF files and Python source code
- **Key artifacts:**
  - **Figure 1:** Population-level vital sign trajectories (6-panel plot showing HR, BP, SpO2, RR, Temp trends)
  - **Figure 2:** Individual patient trajectory examples (4-6 representative cases)
  - **Figure 3:** Temporal pattern classification heatmap
  - **Figure 4:** Deterioration timeline infographic
  - **Figure 5:** Statistical significance and effect size visualization
  - Python script: `generate_manuscript_figures.py` for reproducible figure generation
- **Quality constraints:** Ensure publication-quality resolution (300 DPI), consistent color schemes, proper axis labels, statistical annotations, prevent misleading visual representations

**Execution Protocol:**
1. Execute Python script: `python generate_manuscript_figures.py`
2. Dependencies: Python 3.10+, matplotlib==3.7.0, seaborn==0.12.0, pandas==1.5.0
3. Runtime conditions: 8GB RAM, < 20 minutes execution time
4. Command: `python generate_manuscript_figures.py --results=temporal_patterns_results.json --vital-data=vital_signs_arrest_window.csv --output-dir=figures`

**Validation Checks:**
- **Expected runtime:** < 20 minutes
- **Sample output verification:** All figure files should be generated with proper dimensions and clarity
- **Error handling:** Handle missing data gracefully, ensure consistent figure styling
- **Reproducibility:** Save figure generation script and all parameters for reproducible research

Expected Result: Comprehensive experimental plan addressing temporal patterns of vital sign deterioration preceding cardiac arrest events, including cohort identification, vital sign extraction, statistical analysis, and manuscript figure generation. The plan will produce a cardiac arrest cohort dataset, vital sign time series data around arrest events, statistical analysis results of temporal deterioration patterns, and publication-quality figures for manuscript submission.