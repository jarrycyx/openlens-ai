# File Analysis Report


## File Content Samples
### datasets/eicu-demo/carePlanGoal.csv
**Summary:** The `carePlanGoal.csv` file records care plan goals for ICU patients, including categories (e.g., Infection/Labs, Cardiovascular), values (e.g., "Normal electrolytes"), statuses, and active status at discharge, indexed by patient and time offset. (249 characters)
**First 10 lines:**
```
cplgoalid,patientunitstayid,cplgoaloffset,cplgoalcategory,cplgoalvalue,cplgoalstatus,activeupondischarge
2287240,1318254,800,Infection/Labs,Normal electrolytes,Active,True
2287241,1318254,800,Infection/Labs,Absence of sepsis,Active,True
2287239,1318254,800,Infection/Labs,Stable Hgb and Hct,Active,True
2287237,1318254,800,Cardiovascular,Vital signs within normal parameters,Active,True
2370651,1318254,36,Cardiovascular,Vital signs within normal parameters,Active,False
2287238,1318254,800,Pulmonary,Pulse oximetry within ordered parameters,Active,True
2370650,1318254,36,Infection/Labs,Absence of sepsis,Active,False
2243077,1351888,1022,Cardiovascular,Vital signs within normal parameters,Active,True
2243076,1351888,1022,Cardiovascular,Hemodynamically stable within ordered parameters,Active,True
```
**Random 10 lines:**
```
6049857,3116577,3732,Infection/Labs,Absence of fever,Active,False
5312433,2635557,273,Fluid Balance/Treatments,"",Active,False
5352935,2616371,2078,Neurologic,"",Active,False
8226746,3079543,5859,Pulmonary,Pulse oximetry within ordered parameters,Active,True
1580172,1034813,561,Patient-Family,Identify patient/family needs,Progressing towards goal,False
5642167,2602528,4516,Other,"",Active,True
5666198,2574532,2444,Pulmonary,"",Active,False
7125937,3035601,3563,Infection/Labs,Stable Hgb and Hct,Active,False
5376918,2595334,6043,Fluid Balance/Treatments,"",Active,False
8228302,3037894,308,Patient-Family,"",Active,False
```

### datasets/eicu-demo/carePlanCareProvider.csv
**Summary:** This file logs care providers assigned to patients, tracking their specialties, roles (managing/consulting), intervention categories, timing within the care plan, and active status upon discharge, linked by unique provider and patient stay identifiers.
**First 10 lines:**
```
cplcareprovderid,patientunitstayid,careprovidersaveoffset,providertype,specialty,interventioncategory,managingphysician,activeupondischarge
1124435,149713,11,"",family practice,I,Managing,True
1196330,157016,2,"",obstetrics/gynecology,I,Managing,True
1115508,165840,26,"",internal medicine,I,Managing,True
1153793,174826,49,"",critical care medicine (CCM),"",Managing,True
1135321,174956,3,"",cardiology,Unknown,Managing,True
1168507,185821,170,"",surgery-trauma,"",Managing,True
1177389,202294,3,"",internal medicine,"",Managing,True
1204257,210642,3,"",hospitalist,"",Managing,False
1187279,223303,5,"",internal medicine,"",Managing,True
```
**Random 10 lines:**
```
6694410,1811733,9516,"",gastroenterology,I,Consulting,True
2318089,532223,114,"",cardiology,Unknown,Consulting,False
1121643,167093,44,"",hospitalist,"",Managing,True
1950100,379119,14452,"","",Unknown,Consulting,False
6187583,1687744,99,"",hospitalist,IV,Managing,True
8073160,2216546,2,"",internal medicine,"",Managing,False
8173282,2225847,39,"",surgery-cardiac,II,Managing,True
6326623,1718492,-117,"",oncology,Unknown,Consulting,True
8479181,2610399,61,"",internal medicine,"",Managing,True
8889589,2870678,6,"",hospitalist,II,Managing,True
```

### datasets/eicu-demo/hospital.csv
**Summary:** This CSV file contains hospital data with identifiers, bed size categories, teaching status, and geographic regions, providing information about various healthcare facilities across different regions.
**First 10 lines:**
```
hospitalid,numbedscategory,teachingstatus,region
56,<100,f,Midwest
58,100 - 249,f,Midwest
59,<100,f,Midwest
60,<100,f,Midwest
61,<100,f,Midwest
63,100 - 249,f,Midwest
66,100 - 249,f,Midwest
67,,f,Midwest
68,<100,f,Midwest
```
**Random 10 lines:**
```
79,>= 500,f,Midwest
188,>= 500,t,South
203,100 - 249,f,
204,100 - 249,f,Northeast
206,250 - 499,f,Northeast
224,100 - 249,f,South
248,100 - 249,f,Midwest
350,,f,
355,<100,f,Midwest
436,100 - 249,f,South
```

### datasets/eicu-demo/microLab.csv
**Summary:** This file contains microbiological laboratory test results documenting culture collection sites, identified organisms, and antibiotic sensitivity testing for ICU patients.
**First 10 lines:**
```
microlabid,patientunitstayid,culturetakenoffset,culturesite,organism,antibiotic,sensitivitylevel
840759,2597777,1343,"Sputum, Expectorated",mixed flora,"",""
840628,2597777,2723,"Sputum, Expectorated",mixed flora,"",""
833113,2608936,1,Bronchial Lavage,mixed flora,"",""
839342,2621338,22,"Sputum, Expectorated",gram negative rods,"",""
839341,2621338,22,"Sputum, Expectorated",gram positive cocci,"",""
833396,2628859,-10,Bronchial Lavage,mixed flora,"",""
840054,2635167,298,"Sputum, Expectorated",mixed flora,"",""
1552311,3046540,212,"Urine, Catheter Specimen",Other,"",""
1563049,3046540,-81,"Sputum, Tracheal Specimen",Other,meropenam,Sensitive
```
**Random 10 lines:**
```
1625993,3139532,503,Nasopharynx,no growth,"",""
1630192,3140049,-371,"Urine, Catheter Specimen",gram negative rods,Other,""
1610596,3140490,-156,"Sputum, Tracheal Specimen",mixed flora,"",""
1609524,3142950,-1073,Nasopharynx,Other,"",""
1579341,3148997,-30,"Urine, Voided Specimen",Escherichia coli,ciprofloxacin,Sensitive
1579333,3148997,-30,"Urine, Voided Specimen",Escherichia coli,levofloxacin,Sensitive
1630840,3152607,6,Nasopharynx,Other,"",""
1615229,3153894,178,"Blood, Venipuncture",no growth,"",""
1605170,3159826,-220,"Urine, Voided Specimen",Pseudomonas aeruginosa,gentamicin,Sensitive
1605176,3159826,-1245,"Blood, Venipuncture",no growth,"",""
```

### datasets/eicu-demo/nurseAssessment.csv
**Summary:** This CSV file records nursing assessment data for ICU patients, capturing hierarchical assessment categories (e.g., Cardiovascular|Edema), specific attributes, values (e.g., generalized, minimal), and timing offsets.
**First 10 lines:**
```
nurseassessid,patientunitstayid,nurseassessoffset,nurseassessentryoffset,cellattributepath,celllabel,cellattribute,cellattributevalue
57436984,1054428,13791,13819,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Cardiovascular|Edema|Edema,Edema,Edema,generalized
57483728,1036759,4075,4076,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Respiratory|Secretions|Secretions,Secretions,Secretions,minimal
57483729,1036759,4075,4076,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Respiratory|Secretions|Secretions,Secretions,Secretions,thin
57483730,1036759,4075,4076,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Respiratory|Secretions|Secretions,Secretions,Secretions,clear
57505995,1054428,18051,18065,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Cardiovascular|Pacemaker/AICD|Pacemaker/AICD,Pacemaker/AICD,Pacemaker/AICD,N/A
57515475,1014000,362,363,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Respiratory|Secretions|Secretions,Secretions,Secretions,minimal
57515476,1014000,362,363,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Respiratory|Secretions|Secretions,Secretions,Secretions,thick
57515477,1014000,362,363,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Respiratory|Secretions|Secretions,Secretions,Secretions,bloody
57515478,1014000,362,363,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Respiratory|Secretions|Secretions,Secretions,Secretions,cloudy
```
**Random 10 lines:**
```
109594720,1036759,2754,2822,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Respiratory|Breath Sounds|Right Lower,Breath Sounds,Right Lower,rhonchi
398101147,2553254,2776,2789,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Scores|Intervention|Pressure Sore Risk Interventions,Intervention,Pressure Sore Risk Interventions,turning schedule
461462164,3057805,297,323,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Neurologic|Pupils|Right,Pupils,Right,brisk
467996800,3116577,10031,10119,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Respiratory|Cough|Cough,Cough,Cough,non-productive
485007526,3086265,4630,4642,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Respiratory|Breath Sounds|Left Upper,Breath Sounds,Left Upper,rhonchi
495457551,3057806,38,52,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Scores|Braden Scale|Activity,Braden Scale,Activity,2. chairfast
511021623,3053511,29,169,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Cardiovascular|Pacemaker/AICD|Pacemaker/AICD,Pacemaker/AICD,Pacemaker/AICD,N/A
528940219,3047675,1725,1848,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Cardiovascular|Skin Color/Temp|Skin Color/Temp,Skin Color/Temp,Skin Color/Temp,normal
539072904,3079543,98,94,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Respiratory|Breath Sounds|Left Lower,Breath Sounds,Left Lower,diminished
560231610,3035600,1629,1637,flowsheet|Flowsheet Cell Labels|Nursing Assessment|Scores|Morse Fall Risk|Secondary Diagnosis,Morse Fall Risk,Secondary Diagnosis,yes
```

### datasets/eicu-demo/vitalAperiodic.csv
**Summary:** The file 'vitalAperiodic.csv' records aperiodic vital sign measurements for ICU patients, primarily non-invasive blood pressure (systolic, diastolic, mean) at specific time offsets, along with other hemodynamic parameters (PAOP, cardiac output, etc.) that are often missing.
**First 10 lines:**
```
vitalaperiodicid,patientunitstayid,observationoffset,noninvasivesystolic,noninvasivediastolic,noninvasivemean,paop,cardiacoutput,cardiacinput,svr,svri,pvr,pvri
3661418,141764,81,171,90,116,,,,,,,
3661424,141764,334,153,78,103,,,,,,,
3661417,141764,77,176,87,107,,,,,,,
3661419,141764,165,173,106,128,,,,,,,
3661421,141764,255,182,103,133,,,,,,,
3661420,141764,195,181,102,143,,,,,,,
3661422,141764,262,180,101,143,,,,,,,
3661423,141764,264,166,80,132,,,,,,,
5600905,141765,1393,156,85,127,,,,,,,
```
**Random 10 lines:**
```
3885918,166864,592,133,82,101,,,,,,,
7426444,216951,7320,199,92,131,,,,,,,
7283368,230427,289,87,51,64,,,,,,,
63115563,343093,12942,134,68,84,,,,,,,
76012479,375854,46567,144,125,130,,,,,,,
167776784,1067786,879,102,57,73,,,,,,,
215982815,1455088,691,119,44,52,,,,,,,
253230755,1835048,1448,138,58,87,,,,,,,
384572983,2980454,22,114,93,103,,,,,,,
408335930,3075813,6016,163,46,76,,,,,,,
```

### datasets/eicu-demo/patient.csv
**Summary:** The 'patient.csv' file stores comprehensive patient data including demographics, hospital/ICU stay details, admission/discharge events, clinical diagnoses, and physical measurements.
**First 10 lines:**
```
patientunitstayid,patienthealthsystemstayid,gender,age,ethnicity,hospitalid,wardid,apacheadmissiondx,admissionheight,hospitaladmittime24,hospitaladmitoffset,hospitaladmitsource,hospitaldischargeyear,hospitaldischargetime24,hospitaldischargeoffset,hospitaldischargelocation,hospitaldischargestatus,unittype,unitadmittime24,unitadmitsource,unitvisitnumber,unitstaytype,admissionweight,dischargeweight,unitdischargetime24,unitdischargeoffset,unitdischargelocation,unitdischargestatus,uniquepid
141764,129391,Female,87,Caucasian,59,91,"",157.50,23:36:00,-2258,"",2015,19:20:00,366,Home,Alive,Med-Surg ICU,13:14:00,ICU to SDU,2,stepdown/other,,,18:58:00,344,Home,Alive,002-1039
141765,129391,Female,87,Caucasian,59,91,"Rhythm disturbance (atrial, supraventricular)",157.50,23:36:00,-8,"",2015,19:20:00,2616,Home,Alive,Med-Surg ICU,23:44:00,Emergency Department,1,admit,46.50,45.00,13:14:00,2250,Step-Down Unit (SDU),Alive,002-1039
143870,131022,Male,76,Caucasian,68,103,"Endarterectomy, carotid",167.00,20:46:00,-1,Operating Room,2014,17:05:00,1218,Home,Alive,SICU,20:47:00,Operating Room,1,admit,77.50,79.40,10:00:00,793,Floor,Alive,002-12289
144815,131736,Female,34,Caucasian,56,82,"Overdose, other toxin, poison or drug",172.70,01:44:00,-23,Emergency Department,2015,21:05:00,1138,Other Hospital,Alive,Med-Surg ICU,02:07:00,Emergency Department,1,admit,60.30,60.70,20:48:00,1121,Other External,Alive,002-1116
145427,132209,Male,61,Caucasian,68,103,"GI perforation/rupture, surgery for",177.80,23:48:00,-10,Emergency Department,2014,15:41:00,5263,Home,Alive,SICU,23:58:00,Operating Room,1,admit,91.70,93.10,22:47:00,1369,Floor,Alive,002-12243
147306,133684,Female,55,Caucasian,63,95,"",157.50,23:23:55,-495,Operating Room,2015,17:48:00,610,Home,Alive,Med-Surg ICU,07:38:00,ICU to SDU,2,stepdown/other,,,17:48:00,610,Home,Alive,002-10241
147307,133684,Female,55,Caucasian,63,95,"Endarterectomy, carotid",157.50,23:23:55,-19,Operating Room,2015,17:48:00,1086,Home,Alive,Med-Surg ICU,23:42:00,Operating Room,1,admit,72.50,72.50,07:38:00,476,Step-Down Unit (SDU),Alive,002-10241
147784,134042,Female,60,Hispanic,67,109,"Coma/change in level of consciousness (for hepatic see GI, for diabetic see Endocrine, if related to cardiac arrest, see CV)",154.90,05:06:00,0,"",2015,23:08:00,3962,Home,Alive,Med-Surg ICU,05:06:00,Emergency Department,1,admit,95.60,97.60,20:47:00,2381,Floor,Alive,002-10424
148611,134686,Male,28,Caucasian,61,120,"Overdose, other toxin, poison or drug",182.90,18:02:00,-1,Emergency Department,2015,15:15:00,1272,Other,Alive,Med-Surg ICU,18:03:00,Emergency Department,1,admit,91.80,91.90,15:11:00,1268,Floor,Alive,002-10736
```
**Random 10 lines:**
```
281132,242279,Male,65,Caucasian,95,126,"Pneumonia, bacterial",180.30,18:10:00,0,Emergency Department,2014,17:45:00,5735,Home,Alive,Med-Surg ICU,18:10:00,Emergency Department,1,admit,86.60,83.60,15:48:00,2738,Floor,Alive,003-13187
1060026,786216,Female,79,Other/Unknown,197,477,"CHF, congestive heart failure",154.90,19:11:00,-17600,Floor,2014,19:20:00,9769,Death,Expired,Cardiac ICU,00:31:00,Floor,1,admit,67.80,,23:00:00,4229,Floor,Alive,009-10020
1211532,907098,Female,81,Caucasian,207,505,"",165.10,04:47:00,-515,Step-Down Unit (SDU),2014,00:23:00,661,Other Hospital,Alive,Med-Surg ICU,13:22:00,Step-Down Unit (SDU),1,stepdown/other,54.20,,00:21:00,659,Other Hospital,Alive,011-10034
1637431,1272502,Female,62,African American,256,647,"Sepsis, unknown",165.00,22:41:00,-153,"",2015,20:00:00,4006,Home,Alive,Med-Surg ICU,01:14:00,Emergency Department,1,admit,99.70,,22:27:00,1273,Floor,Alive,017-101374
2853358,2309782,Female,65,Caucasian,399,999,"Renal failure, acute",157.50,00:40:22,-250,Emergency Department,2014,21:27:00,5317,Skilled Nursing Facility,Alive,Med-Surg ICU,04:50:00,Emergency Department,1,admit,54.43,,00:27:00,2617,Floor,Alive,027-111437
2999209,2430117,Male,66,Caucasian,417,1019,"Endarterectomy, carotid",188.00,14:47:59,-580,"",2015,19:30:00,1143,Home,Alive,Med-Surg ICU,00:27:00,Recovery Room,1,admit,114.80,114.82,19:30:00,1143,Home,Alive,029-10005
3029353,2456095,Male,> 89,Caucasian,417,1019,"Sepsis, pulmonary",177.80,15:16:22,-143,"",2015,16:52:00,1393,Death,Expired,Med-Surg ICU,17:39:00,Emergency Department,1,admit,62.50,67.22,17:20:00,1421,Death,Expired,029-10037
3146276,2558178,Female,63,Caucasian,434,1051,"",,15:12:00,-1,"",2014,21:30:00,3257,Home,Alive,Med-Surg ICU,15:13:00,"",1,admit,,,15:14:00,1,Other ICU,Alive,031-10809
3153171,2563930,Male,84,Caucasian,435,1052,Burr hole placement,165.10,22:20:00,-1526,Operating Room,2015,21:27:00,9941,Home,Alive,Med-Surg ICU,23:46:00,Operating Room,1,admit,94.80,,17:50:00,8284,Floor,Alive,031-10188
3159558,2569222,Female,61,African American,437,1047,"Respiratory - medical, other",140.00,16:06:00,-20,Recovery Room,2015,01:18:00,16372,Home,Alive,Med-Surg ICU,16:26:00,Recovery Room,1,admit,49.70,,21:13:00,287,Telemetry,Alive,031-14167
```

### datasets/eicu-demo/carePlanEOL.csv
**Summary:** The file records end-of-life care plans for ICU patients, documenting timestamps for plan saving/discussion relative to ICU admission and their active status at discharge.
**First 10 lines:**
```
cpleolid,patientunitstayid,cpleolsaveoffset,cpleoldiscussionoffset,activeupondischarge
11340,1054428,304,0,True
24686,1593179,3992,0,True
34322,2592641,3998,0,True
35600,2611237,303,0,True
35303,2621948,987,0,True
35037,2630865,3296,0,False
33980,2630865,3462,0,True
35225,2635556,16603,0,True
34465,2635556,14320,0,False
```
**Random 10 lines:**
```
35002,2637542,3319,0,True
38935,2788588,7823,0,True
38755,2892404,41,-948,True
49439,3079543,4860,0,True
42846,3086265,4393,2950,True
47461,3086494,421,-1032,True
```

### datasets/eicu-demo/nurseCare.csv
**Summary:** The nurseCare.csv file records nursing care interventions for patients, including care types (e.g., Hygiene/ADLs, Equipment), timing offsets, and specific care details (e.g., oral care, air mattress). (244 characters)
**First 10 lines:**
```
nursecareid,patientunitstayid,celllabel,nursecareoffset,nursecareentryoffset,cellattributepath,cellattribute,cellattributevalue
20977673,1014000,Hygiene/ADLs,2151,2138,flowsheet|Flowsheet Cell Labels|Nursing Care|Hygiene/ADLs|Hygiene/ADLs|Hygiene/ADLs,Hygiene/ADLs,ADLs assist
20977674,1014000,Hygiene/ADLs,2151,2138,flowsheet|Flowsheet Cell Labels|Nursing Care|Hygiene/ADLs|Hygiene/ADLs|Hygiene/ADLs,Hygiene/ADLs,oral care
21023628,1034813,Equipment,1680,1694,flowsheet|Flowsheet Cell Labels|Nursing Care|Equipment|Equipment|Equipment,Equipment,air mattress
21023629,1034813,Equipment,1680,1694,flowsheet|Flowsheet Cell Labels|Nursing Care|Equipment|Equipment|Equipment,Equipment,heels floated
21023630,1034813,Equipment,1680,1694,flowsheet|Flowsheet Cell Labels|Nursing Care|Equipment|Equipment|Equipment,Equipment,sling
21031999,1054428,Equipment,14150,14328,flowsheet|Flowsheet Cell Labels|Nursing Care|Equipment|Equipment|Equipment,Equipment,air mattress
21032000,1054428,Equipment,14150,14328,flowsheet|Flowsheet Cell Labels|Nursing Care|Equipment|Equipment|Equipment,Equipment,heels floated
21032001,1054428,Equipment,14150,14328,flowsheet|Flowsheet Cell Labels|Nursing Care|Equipment|Equipment|Equipment,Equipment,therapeutic bed
21065063,1034813,Treatments,1185,1250,flowsheet|Flowsheet Cell Labels|Nursing Care|Respiratory|Treatments|Treatments,Treatments,"TCDB = Turn, Cough, Deep Breath"
```
**Random 10 lines:**
```
36235535,1034813,Safety,8145,8136,flowsheet|Flowsheet Cell Labels|Nursing Care|Safety|Safety|Precautions,Precautions,fall prevention measures
59543158,1015158,Safety,64,95,flowsheet|Flowsheet Cell Labels|Nursing Care|Safety|Safety|Assessment,Assessment,safety discussed with patient/family
291307943,3119186,Safety,767,767,flowsheet|Flowsheet Cell Labels|Nursing Care|Safety|Safety|Assessment,Assessment,safety risk assessed
331025218,3078650,Safety,3348,3356,flowsheet|Flowsheet Cell Labels|Nursing Care|Safety|Safety|Side Rails,Side Rails,X4
334174674,3046967,Restraints,712,1827,flowsheet|Flowsheet Cell Labels|Nursing Care|Restraints|Restraints|Restraint Education/Communication,Restraint Education/Communication,"patient rights, dignity, safety maintained"
340248653,3111371,Hygiene/ADLs,2322,2450,flowsheet|Flowsheet Cell Labels|Nursing Care|Hygiene/ADLs|Hygiene/ADLs|Hygiene/ADLs,Hygiene/ADLs,ADLs assist
360784322,3086265,Safety,17,146,flowsheet|Flowsheet Cell Labels|Nursing Care|Safety|Safety|Bed Position,Bed Position,brakes on
364475814,3098570,Safety,14,477,flowsheet|Flowsheet Cell Labels|Nursing Care|Safety|Safety|Assessment,Assessment,safety risk assessed
371762490,3078650,Nutrition,3186,3188,flowsheet|Flowsheet Cell Labels|Nursing Care|Nutrition|Nutrition|Nutrition,Nutrition,clear liquids
374752799,3154481,Activity,-3,75,flowsheet|Flowsheet Cell Labels|Nursing Care|Activity|Activity|Activity,Activity,HOB 30 degrees
```

### datasets/eicu-demo/customLab.csv
**Summary:** customLab.csv tracks patient-specific laboratory test results over time, storing diverse lab names, numeric/text values, and timing offsets relative to ICU admission. (498 characters)
**First 10 lines:**
```
customlabid,patientunitstayid,labotheroffset,labothertypeid,labothername,labotherresult,labothervaluetext
25451,243999,45,1,Creatinine w Est GFR,51.0000,51
25450,243999,450,1,GFR,"",>60
24747,267829,202,1,Vitamin B12,"",>1000
24653,267829,202,1,Iron,"",<10.0
24748,267829,202,1,Folate,"",>20.0
24654,267829,202,1,TIBC,319.0000,319
24746,267829,675,1,GFR,"",>60
30839,267829,202,3,Bleeding Time,7.5000,7.5
25673,276815,-120,1,B-Natriuretic Peptide  ,153.0000,153.0
```
**Random 10 lines:**
```
35540,276815,2085,3,"Heparin Anti-Xa, Unfract",.5800,0.58
35542,276815,1150,3,"Heparin Anti-Xa, Unfract",1.1000,1.10
24666,295916,-660,1,Globulin,3.6000,3.6
24658,295916,1010,1,Creatinine w GFR,46.0000,46
24665,295916,-660,1,Creatinine w GFR,45.0000,45
36149,301185,628,4,Influenza A,"",Negative
42069,411036,119,1,Pro BNP,127.0000,127
120153,2744115,5267,7,VE ,6.3700,6.37
120154,2744115,5267,7,sample type,"",Arterial
120141,2744115,3726,7,VE ,6.9600,6.96
```

### datasets/eicu-demo/infusiondrug.csv
**Summary:** This file tracks continuous intravenous drug infusions for ICU patients, recording the drug name (e.g., Magnesium), administration rate, timing relative to admission, and patient-specific details like weight.
**First 10 lines:**
```
infusiondrugid,patientunitstayid,infusionoffset,drugname,drugrate,infusionrate,drugamount,volumeoffluid,patientweight
40215081,1461035,768,Volume (mL) Magnesium  (ml/hr),25,"","","",""
38752780,1461035,648,Volume (mL) Magnesium  (ml/hr),25,"","","",""
36960718,1461035,-1812,Volume (mL) Magnesium  (ml/hr),25,"","","",""
38679313,1461035,-611,Volume (mL) Magnesium  (ml/hr),25.42,"","","",""
40681648,1461035,828,Volume (mL) Magnesium  (ml/hr),25,"","","",""
37790467,1461035,1068,Volume (mL) Magnesium  (ml/hr),25,"","","",""
36135179,1461035,108,Volume (mL) Magnesium  (ml/hr),25,"","","",""
40544162,1461035,-972,Volume (mL) Magnesium  (ml/hr),25,"","","",""
37048839,1461035,-672,Volume (mL) Magnesium  (ml/hr),25,"","","",""
```
**Random 10 lines:**
```
13271488,741996,13774,Norepinephrine (ml/hr),11.3,"","","",""
8571108,426975,1757,Norepinephrine (mcg/min),50,46.9,16,250,""
49572329,1985995,227,Propofol (ml/hr),14.28,"","","",""
13047553,578187,7107,Propofol (ml/hr),14.1,"","","",""
46379473,1998890,1239,Dexmedetomidine (ml/hr),6.97,"","","",""
58794568,2846485,12293,Propofol (),21.8,"","","",""
64782522,3098657,8177,Midazolam (mg/hr),15,30,25,50,""
65858394,3098657,1037,Midazolam (mg/hr),0,0,25,50,""
6863201,521456,22623,nimbex (mcg/kg/min),5,27,200,200,90
49510513,2193649,1191,Midazolam (ml/hr),0.2,"","","",""
```

### datasets/eicu-demo/carePlanGeneral.csv
**Summary:** The 'carePlanGeneral.csv' file documents patient-specific care plan items including clinical aspects (ventilation, medication, activity) with their status at discharge, organized by patient identifiers and categorized care groups.
**First 10 lines:**
```
cplgeneralid,patientunitstayid,activeupondischarge,cplitemoffset,cplgroup,cplitemvalue
3665765,174826,True,49,Ventilation,Spontaneous - adequate
3608330,174826,True,49,Care Limitation,Full therapy
3466711,174826,True,49,Stress Ulcer Prophylaxis,Proton pump inhibitor
3666045,174826,True,49,Airway,Not intubated/normal airway
3772790,174826,True,49,DVT Prophylaxis,Compression devices
3447072,223303,True,5,Stress Ulcer Prophylaxis,Not indicated
3593679,223303,True,5,Airway,Not intubated/normal airway
3765574,223303,True,5,Care Limitation,Full therapy
3827613,223303,True,5,DVT Prophylaxis,Compression devices
```
**Random 10 lines:**
```
55294145,3150018,True,16,DVT Prophylaxis,Drug therapy
45512460,2838819,True,80,Volume Status,Normovolemic - attempting to push volume status
4293957,272886,True,3419,Sedation,None
49183390,3021108,True,284,Acuity,Low
7043180,346379,True,734,Safety/Restraints,Assess fall risk
42878882,2595884,False,14,Activity,HOB 30 degrees
32553681,1733584,True,1353,DVT Prophylaxis,Drug therapy
36561616,2193649,False,1,Airway,Not intubated/normal airway
9238272,524799,True,5571,Ordered Protocols,Cerebral vasospasm prevention/therapy
36281217,2085136,False,38,Route-Status,NPO
```

### datasets/eicu-demo/vitalPeriodic.csv
**Summary:** This CSV file stores time-stamped periodic vital sign measurements (e.g., temperature, heart rate, blood pressure, oxygen saturation, ICP) for ICU patients, linked by unique identifiers and observation offsets.
**First 10 lines:**
```
vitalperiodicid,patientunitstayid,observationoffset,temperature,sao2,heartrate,respiration,cvp,etco2,systemicsystolic,systemicdiastolic,systemicmean,pasystolic,padiastolic,pamean,st1,st2,st3,icp
29524122,141765,1179,,,82,,,,,,,,,,,,,
29557845,141765,189,,97,76,30,,,,,,,,,,,,
29524442,141765,1169,,,84,,,,,,,,,,,,,
29513052,141765,1534,,,92,,,,,,,,,,,,,
29524600,141765,1164,,,86,,,,,,,,,,,,,
29558795,141765,159,,96,80,22,,,,,,,,,,,,
29511454,141765,1584,,,94,,,,,,,,,,,,,
29553160,141765,334,,96,76,29,,,,,,,,,,,,
29485816,141764,74,,,126,,,,,,,,,,0,-1.7,-1.7,
```
**Random 10 lines:**
```
202336808,375854,48714,,100,87,,,,,,,,,,,,,
524928448,1054428,21975,,96,98,19,,,,,,,,,,,,
626619026,1117947,12012,,96,62,19,,,,,,,,,-0.40000001,-1.92,-1.76,
1212258865,1748443,1840,,99,70,59,2,,,,,,,,0,50,50,
1306870019,2069695,2853,,95,73,25,,,,,,,,,,,,
1359859102,2114686,3351,,100,75,15,,,,,,,,,,,,
1493606551,2361839,3648,,96,51,12,13,,102,45,63,,,,0.30000001,-0.1,-0.55000001,
1440042357,2492731,2356,,94,108,25,,,,,,,,,,,,
1721853814,2739712,4226,,100,100,,,,,,,,,,,,,
2072148922,3242157,8370,,98,63,22,,,,,,,,,,,,
```

### datasets/eicu-demo/carePlanInfectiousDisease.csv
**Summary:** This file tracks patient-specific infectious disease care plans, documenting infection sites, assessment certainty, treatment approaches, and care plan status at discharge.
**First 10 lines:**
```
cplinfectid,patientunitstayid,activeupondischarge,cplinfectdiseaseoffset,infectdiseasesite,infectdiseaseassessment,responsetotherapy,treatment
3329,249328,True,1153,Urinary tract,Definite infection,"",""
3234,260860,False,1451,Urinary tract,Definite infection,"",""
1149,260860,True,2866,Urinary tract,Definite infection,"",""
255,260860,False,1451,Skin & Soft tissue,Definite infection,"",""
328,260860,True,2866,Skin & Soft tissue,Definite infection,"",""
3115,264276,True,3236,Lung,Definite infection,"",""
3103,272886,True,2314,Lung,Definite infection,"",""
5337,292154,True,91,Other,Definite infection,"",Directed
3048,294032,True,144,Lung,Definite infection,"",""
```
**Random 10 lines:**
```
90479,2580992,False,821,Lung,Possible infection,"",Empiric
99908,2589516,True,257,Lung,Definite infection,"",Directed
75465,2595771,True,441,Blood,Possible infection,"",""
102268,2597777,False,7287,Urinary tract,Definite infection,"",Directed
71983,2600767,True,1379,Urinary tract,Definite infection,"",""
73931,2600791,True,537,Lung,Definite infection,"",""
84957,2602528,True,1987,Lung,Definite infection,"",Empiric
101731,2607275,True,1183,Urinary tract,Definite infection,"",Directed
81313,2627574,True,2632,Urinary tract,Definite infection,"",Empiric
76483,2642496,True,100,Skin & Soft tissue,Possible infection,"",Prophylactic
```

### datasets/eicu-demo/respiratoryCharting.csv
**Summary:** The respiratoryCharting.csv file records time-stamped respiratory parameters for ICU patients, including ventilator settings, oxygen delivery values, tidal volumes, PEEP, and other respiratory measurements categorized by type.
**First 10 lines:**
```
respchartid,patientunitstayid,respchartoffset,respchartentryoffset,respcharttypecat,respchartvaluelabel,respchartvalue
107,184757,2922,2922,respFlowSettings,LPM O2,1
1108,187150,408,408,respFlowSettings,FiO2,80
10629,179269,117,117,respFlowSettings,LPM O2,6
13000,162502,3845,3845,respFlowSettings,LPM O2,25
13001,162502,3845,3845,respFlowSettings,FiO2,60
20619,229236,-5791,-5791,respFlowSettings,LPM O2,4
21034,202294,4168,4168,respFlowSettings,LPM O2,4
22035,173458,4,4,respFlowSettings,FiO2,30
24696,237983,1036,1036,respFlowSettings,FiO2,35
```
**Random 10 lines:**
```
19427170,791784,0,6,respFlowPtVentData,RR (patient),20
45564232,758325,151,160,respFlowPtVentData,Plateau Pressure,17
49355178,564216,5420,5432,respFlowPtVentData,Exhaled MV,11.7
94818270,1439835,1144,1144,respFlowCareData,Head of Bed Elevation,Yes
110580313,1567943,-109,-109,respFlowCareData,O2 Device,Bi-PAP
122576596,1625701,719,719,respFlowSettings,TV/kg IBW,4.3956
149009382,2038433,13806,13806,respFlowPtVentData,Peak Insp. Pressure,36
151564848,2199589,5165,5165,respFlowPtVentData,Mean Airway Pressure,14
180389097,2893929,1682,1682,respFlowSettings,Vent Rate,15
222815263,3099676,4440,4447,respFlowPtVentData,RR (patient),24
```

### datasets/eicu-demo/apacheApsVar.csv
**Summary:** The file 'apacheApsVar.csv' contains patient physiological and clinical measurements (vital signs, lab values, Glasgow Coma Scale components) used to calculate the Apache APS score for assessing illness severity in ICU patients.
**First 10 lines:**
```
apacheapsvarid,patientunitstayid,intubated,vent,dialysis,eyes,motor,verbal,meds,urine,wbc,temperature,respiratoryrate,sodium,heartrate,meanbp,ph,hematocrit,creatinine,albumin,pao2,pco2,bun,glucose,bilirubin,fio2
92788,141765,0,0,0,4,6,5,0,-1,10.2,36.2,39,139,88,108,-1,37.8,1.04,-1,-1,-1,28,61,-1,-1
8893,143870,0,0,0,4,6,5,0,-1,11.7,36.4,60,133,40,47,-1,34.1,1.14,-1,-1,-1,14,140,-1,-1
79585,144815,0,0,0,4,6,5,0,-1,7.9,36.7,6,141,131,61,-1,36.6,0.63,3.6,-1,-1,6,82,0.5,-1
203242,145427,0,0,0,4,6,5,0,-1,21.1,36.2,41,141,49,72,-1,40.4,1.05,-1,-1,-1,14,118,-1,-1
154681,147307,0,0,0,4,6,5,0,-1,-1,36.8,33,-1,115,107,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1
53115,147784,1,0,0,4,6,3,0,-1,12.6,36,53,142,109,130,7.38,40.9,0.54,2.8,76,81,17,151,0.7,60
2143574,148611,0,0,0,4,6,5,0,-1,7.3,36.2,45,142,105,108,-1,47.5,0.82,-1,-1,-1,7,112,-1,-1
119324,149433,0,0,0,-1,-1,-1,-1,-1,-1,-1,-1,-1,98,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1
53149,149713,0,0,0,4,6,4,0,-1,9.9,36.3,54,133,94,65,-1,38.7,0.61,3.8,-1,-1,11,97,0.5,-1
```
**Random 10 lines:**
```
142510,257802,0,0,0,3,6,4,0,1028.5056,-1,36.3,10,-1,94,65,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1
1979605,454240,0,0,0,4,6,5,0,1875.4848,3,37,31,140,118,53,-1,33.7,0.5,-1,-1,-1,6,185,-1,-1
185322,970328,1,1,0,4,6,5,0,730.1664,12.6,36.4,34,139,141,53,7.46,33.1,0.8,2.9,65,50,17,209,0.3,30
385589,1081887,0,0,0,4,6,5,0,1959.12,-1,37.1,24,-1,52,82,-1,-1,-1,-1,-1,-1,-1,169,-1,-1
507867,1629286,0,0,0,4,6,5,0,-1,8.4,36.9,36,139,96,102,-1,37.8,1.2,-1,-1,-1,19,234,-1,-1
806355,2215881,0,0,0,4,6,5,0,-1,-1,36.1,4,-1,33,113,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1
1137095,2707486,0,0,0,2,5,2,0,-1,-1,-1,25,-1,34,49,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1
966805,2714202,0,0,0,4,6,5,0,-1,14.4,37.1,9,138,117,67,-1,29.6,1,-1,-1,-1,9,170,-1,-1
1149505,2720598,0,0,0,1,1,1,0,6176.5632,18.6,36.2,41,145,122,127,-1,47.1,0.7,4.1,-1,-1,7,195,0.4,-1
1303895,3086494,0,0,0,4,6,5,0,938.6496,6.3,36.4,27,130,103,67,-1,27.6,0.91,2.2,-1,-1,14,96,25.5,-1
```

### datasets/eicu-demo/treatment.csv
**Summary:** The `treatment.csv` file records medical treatments administered to ICU patients, including unique treatment IDs, patient stay IDs, timing (offset), hierarchical treatment descriptions, and active status at discharge. (498 characters)
**First 10 lines:**
```
treatmentid,patientunitstayid,treatmentoffset,treatmentstring,activeupondischarge
9579899,242895,838,cardiovascular|arrhythmias|anticoagulant administration|low molecular weight heparin|enoxaparin,False
8788989,242895,512,cardiovascular|consultations|Cardiology consultation,False
10293108,242895,838,cardiovascular|non-operative procedures|external pacemaker,False
9017080,242895,70,pulmonary|vascular disorders|VTE prophylaxis|low molecular weight heparin|enoxaparin,False
9853526,242895,70,cardiovascular|consultations|Cardiology consultation,False
10361067,242895,1434,pulmonary|medications|bronchodilator|inhaled,True
8725224,242895,838,cardiovascular|consultations|Cardiology consultation,False
8518378,242895,512,pulmonary|medications|bronchodilator|inhaled,False
9102158,242895,1434,cardiovascular|non-operative procedures|diagnostic ultrasound of heart|transthoracic echocardiography,True
```
**Random 10 lines:**
```
11968087,350551,2766,neurologic|pain / agitation / altered mentation|analgesics,False
16997467,375854,17149,renal|electrolyte correction|electrolyte administration|oral,False
22894066,447543,257,pulmonary|consultations|Pulmonary/CCM consultation,False
33745839,1363755,16257,cardiovascular|hypertension|beta blocker|metoprolol,False
43230354,1441069,18,cardiovascular|arrhythmias|anticoagulant administration|low molecular weight heparin|enoxaparin,True
43228895,1483029,3365,pulmonary|medications|analgesics,True
60295556,2646210,3868,pulmonary|radiologic procedures / bronchoscopy|chest x-ray,True
68374899,3025797,26,oncology|procedures|surgical resection for cancer,False
70500964,3098657,8215,pulmonary|radiologic procedures / bronchoscopy|endotracheal tube,False
77050258,3132505,756,"gastrointestinal|radiology, diagnostic and procedures|CT scan|pelvis",False
```

### datasets/eicu-demo/respiratoryCare.csv
**Summary:** This file records respiratory care events and ventilator settings for patients, tracking airway management details, ventilation start/end times, and various ventilator parameters and limits.
**First 10 lines:**
```
respcareid,patientunitstayid,respcarestatusoffset,currenthistoryseqnum,airwaytype,airwaysize,airwayposition,cuffpressure,ventstartoffset,ventendoffset,priorventstartoffset,priorventendoffset,apneaparams,lowexhmvlimit,hiexhmvlimit,lowexhtvlimit,hipeakpreslimit,lowpeakpreslimit,hirespratelimit,lowrespratelimit,sighpreslimit,lowironoxlimit,highironoxlimit,meanairwaypreslimit,peeplimit,cpaplimit,setapneainterval,setapneatv,setapneaippeephigh,setapnearr,setapneapeakflow,setapneainsptime,setapneaie,setapneafio2
564013,147784,1188,2,"","","",,0,0,-361,542,"",,,,,,,,,,,,,,"","","","","","","",""
564012,147784,-61,1,"","","",,-361,0,0,0,"",,,,,,,,,,,,,,"","","","","","","",""
545261,165840,-63,1,"","","",,-363,0,0,0,"",,,,,,,,,,,,,,"","","","","","","",""
545262,165840,73,2,"","","",,0,0,-363,-227,"",,,,,,,,,,,,,,"","","","","","","",""
550472,187150,7293,2,"","","",,0,0,-522,7424,"",,,,,,,,,,,,,,"","","","","","","",""
550471,187150,-222,1,"","","",,-522,0,0,0,"",,,,,,,,,,,,,,"","","","","","","",""
545434,197617,6644,2,"","","",,0,0,-520,5803,"",,,,,,,,,,,,,,"","","","","","","",""
555630,197619,670,1,"","","",,310,0,0,0,"",,,,,,,,,,,,,,"","","","","","","",""
554522,198627,5580,2,"","","",,0,0,-290,5280,"",,,,,,,,,,,,,,"","","","","","","",""
```
**Random 10 lines:**
```
597471,426976,301,1,"","","",,-293,0,0,0,"",,,,,,,,,,,,,,"","","","","","","",""
1100656,876429,-23,1,"","","",,-748,0,0,0,"",,,,,,,,,,,,,,"","","","","","","",""
3060099,2081387,917,23,"","","",,0,0,0,0,"",,,,,,,,,,,,,,"","","","","","","",""
3239202,2124939,910,29,"","","",,0,0,0,0,"",,,,,,,,,,,,,,"","","","","","","",""
3092773,2154422,2848,4,"","",23,,0,0,0,0,"",,,,,,,,,,,,,,"","","","","","","",""
3781000,2740390,10718,25,"","","",,0,0,0,0,"",4.0000,,,,,,,,,,,,,"","","","","","","",""
4141046,3027284,6283,46,"","",Center,,0,0,-335,2159,"",,,,,,,,,,,,,,"","","","","","","",""
4141051,3027284,6702,51,"","",Center,,0,0,-335,2159,"",4.0000,,,,,,,,,,,,,"","","","","","","",""
6420356,3351763,2360,157,"","","",,0,0,0,0,"",2.0000,,,,,,,,,,,,,"","","","","","","",""
6448099,3352230,1948,135,"","","",,0,0,0,0,"",,,,,,,,,,,,,4.0000,"","","","","","","",""
```

### datasets/eicu-demo/intakeOutput.csv
**Summary:** This file tracks fluid intake, output, dialysis, and body weight measurements for ICU patients over time, enabling fluid balance monitoring and clinical assessment.
**First 10 lines:**
```
intakeoutputid,patientunitstayid,intakeoutputoffset,intaketotal,outputtotal,dialysistotal,nettotal,intakeoutputentryoffset,cellpath,celllabel,cellvaluenumeric,cellvaluetext
9314532,147307,-394,0.0000,0.0000,0.0000,0.0000,-394,flowsheet|Flowsheet Cell Labels|I&O|Weight|Bodyweight (lb),Bodyweight (lb),159.8000,159.8
9314533,147307,-394,0.0000,0.0000,0.0000,0.0000,-394,flowsheet|Flowsheet Cell Labels|I&O|Weight|Bodyweight (kg),Bodyweight (kg),72.5000,72.5
9319306,211715,1533,120.0000,0.0000,0.0000,120.0000,1533,flowsheet|Flowsheet Cell Labels|I&O|Intake (ml)|Generic Intake (ml)|P.O.,P.O.,120.0000,120
9319891,219981,6504,120.0000,0.0000,0.0000,120.0000,6504,flowsheet|Flowsheet Cell Labels|I&O|Intake (ml)|Generic Intake (ml)|P.O.,P.O.,120.0000,120
9319987,158057,624,0.0000,0.0000,0.0000,0.0000,624,flowsheet|Flowsheet Cell Labels|I&O|Weight|Bodyweight (lb),Bodyweight (lb),359.0000,359
9319988,158057,624,0.0000,0.0000,0.0000,0.0000,624,flowsheet|Flowsheet Cell Labels|I&O|Weight|Bodyweight (kg),Bodyweight (kg),162.8000,162.8
9320320,237983,5570,100.0000,0.0000,0.0000,100.0000,5570,flowsheet|Flowsheet Cell Labels|I&O|Intake (ml)|Generic Intake (ml)|P.O.,P.O.,100.0000,100
9322164,162841,2358,100.0000,75.0000,0.0000,25.0000,2358,flowsheet|Flowsheet Cell Labels|I&O|Intake (ml)|Crystalloids (ml)|Volume (mL)-potassium chloride 20 mEq/100mL IVPB premix,Volume (mL)-potassium chloride 20 mEq/100mL IVPB premix,100.0000,100
9322642,214497,1758,100.0000,1.0000,0.0000,99.0000,1758,flowsheet|Flowsheet Cell Labels|I&O|Intake (ml)|Generic Intake (ml)|P.O.,P.O.,100.0000,100
```
**Random 10 lines:**
```
10241953,222133,2725,360.0000,0.0000,0.0000,360.0000,2725,flowsheet|Flowsheet Cell Labels|I&O|Intake (ml)|Generic Intake (ml)|P.O.,P.O.,360.0000,360
48239085,640796,4516,0.0000,121.0000,0.0000,-121.0000,4663,flowsheet|Flowsheet Cell Labels|I&O|Output (ml)|Indwelling Catheter Output,Indwelling Catheter Output,111.0000,111
56357243,979241,8667,0.0000,125.0000,0.0000,-125.0000,8688,flowsheet|Flowsheet Cell Labels|I&O|Output (ml)|Urine,Urine,125.0000,125
123805503,1702184,3737,2701.0000,750.0000,0.0000,1951.0000,3737,flowsheet|Flowsheet Cell Labels|I&O|Output (ml)|Urine,Urine,750.0000,750
148190669,2103754,7327,0.0000,150.0000,0.0000,-150.0000,7327,flowsheet|Flowsheet Cell Labels|I&O|Output (ml)|URINE CATHETER,URINE CATHETER,150.0000,150
162211255,2416376,3861,0.0000,40.0000,0.0000,-40.0000,3861,flowsheet|Flowsheet Cell Labels|I&O|Output (ml)|URINE CATHETER,URINE CATHETER,40.0000,40
171352232,2720598,97,0.0000,62.0000,0.0000,-62.0000,97,flowsheet|Flowsheet Cell Labels|I&O|Output (ml)|Urine,Urine,62.0000,62
173986882,2724119,2682,0.0000,60.0000,0.0000,-60.0000,2682,flowsheet|Flowsheet Cell Labels|I&O|Output (ml)|Urine,Urine,60.0000,60
177815405,2980454,1362,300.0000,0.0000,0.0000,300.0000,1362,flowsheet|Flowsheet Cell Labels|I&O|Intake (ml)|Generic Intake (ml)|Oral Intake,Oral Intake,300.0000,300
178320210,2989641,5826,0.0000,350.0000,0.0000,-350.0000,5826,flowsheet|Flowsheet Cell Labels|I&O|Weight|Bodyweight (lb),Bodyweight (lb),132.9000,132.9
```

### datasets/eicu-demo/medication.csv
**Summary:** The 'medication.csv' file tracks medication orders and administrations for ICU patients, including drug names, dosages, administration routes, frequencies, timing offsets, and order statuses like cancellation.
**First 10 lines:**
```
medicationid,patientunitstayid,drugorderoffset,drugstartoffset,drugivadmixture,drugordercancelled,drugname,drughiclseqno,dosage,routeadmin,frequency,loadingdose,prn,drugstopoffset,gtc
7278819,141765,134,1396,No,No,WARFARIN SODIUM 5 MG PO TABS,2812,5 3,PO,,"",No,2739,0
9726266,141765,1,-188,No,No,5 ML VIAL : DILTIAZEM HCL 25 MG/5ML IV SOLN,182,15 3,IV,Once PRN,"",Yes,171,38
10293599,141765,115,856,No,No,ASPIRIN EC 81 MG PO TBEC,1820,81 3,PO,Daily,"",No,2739,0
10871534,141765,114,316,No,No,DILTIAZEM HCL 30 MG PO TABS,182,30 3,PO,Q6H SCH,"",No,2739,0
10128716,141765,115,856,No,No,LISINOPRIL 5 MG PO TABS,132,5 3,PO,Daily,"",No,2428,0
8580224,143870,17,1033,No,No,ASPIRIN EC 81 MG PO TBEC,1820,81 3,PO,Daily,"",No,1339,0
7019364,143870,4,-164,No,No,1 ML  -  DIPHENHYDRAMINE HCL 50 MG/ML IJ SOLN,4480,25 3,IV,Q15 Min PRN,"",Yes,-1,17
10899992,143870,4,-420,No,No,METOPROLOL TARTRATE 25 MG PO TABS,2102,25 3,PO,Once PRN,"",Yes,-1,0
8855227,143870,16,1033,No,No,CLOPIDOGREL BISULFATE 75 MG PO TABS,17539,75 3,PO,Daily,"",No,1339,0
```
**Random 10 lines:**
```
36883569,961295,156,135,No,No,magnesium sulfate,610,1 g,IVPB,as directed,"",Yes,1436,59
37161391,1063659,603,630,No,No,,926,50 ML,IV,,"",No,19523,59
89670407,2607275,627,627,Yes,No,,2073,2.5 MG,nebu,As needed,"",Yes,1170,14
108754194,3231363,12623,12634,Yes,No,,3660,40 mg,PO,daily9:  0900 for  dose(s),"",No,16856,56
13406720,249805,1,-452,Yes,No,,768,,IV,TITRATE,"",No,398,71
26591293,946151,3,-5019,No,No,fentaNYL (PF) 50 MCG/1 ML 2 ML INJ,25386,50 mcg,IV Push,ONCALL,"",No,-4979,2
55695854,1580986,1117,1159,No,No,ASPIRIN 81 MG PO CHEW,1820,81 MG,Oral,Daily,"",No,5231,2
36883320,979241,7819,7817,No,No,fentaNYL,25386,50 mcg,IV,Once,"",No,7818,2
47774070,1350881,1176,1157,No,No,nalOXone,1874,0.4 mg,IntraVENOUS,As needed,"",Yes,13207,9
59829930,1619343,-40,-119,No,No,,936,"1,000 ML",IV,,"",Yes,3503,59
```

### datasets/eicu-demo/apachePatientResult.csv
**Summary:** This file stores patient-specific Apache scoring results, including predicted vs. actual ICU/hospital mortality and length of stay, acute physiology scores, and physician intervention data.
**First 10 lines:**
```
apachepatientresultsid,patientunitstayid,physicianspeciality,physicianinterventioncategory,acutephysiologyscore,apachescore,apacheversion,predictedicumortality,actualicumortality,predictediculos,actualiculos,predictedhospitalmortality,actualhospitalmortality,predictedhospitallos,actualhospitallos,preopmi,preopcardiaccath,ptcawithin24h,unabridgedunitlos,unabridgedhosplos,actualventdays,predventdays,unabridgedactualventdays
31917,141765,hospitalist,Unknown,23,47,IV,8.2471913877810981E-3,ALIVE,0.722231399105669,1.5625,3.7319948856373762E-2,ALIVE,2.88170958065951,1.8222,0,0,0,1.5625,1.8222,,,
31918,141765,hospitalist,Unknown,23,47,IVa,0.01231145545549805,ALIVE,1.37480651018718,1.5625,3.5813944311032138E-2,ALIVE,3.17392534799226,1.8222,0,0,0,1.5625,1.8222,,,
21398,143870,family practice,Unknown,43,60,IVa,1.5706796732545089E-2,ALIVE,3.0216711758903,0.5506,0.02893216261220858,ALIVE,6.03262662378308,0.8465,0,0,0,0.5506,0.8465,,,
21397,143870,family practice,Unknown,43,60,IV,1.7738751589020281E-2,ALIVE,3.00652209166107,0.5506,0.02820647395637314,ALIVE,5.9552924047471,0.8465,0,0,0,0.5506,0.8465,,,
181,144815,internal medicine,I,25,25,IV,1.8341987534681509E-3,ALIVE,0.592445507010167,0.7784,4.2529613427439049E-3,ALIVE,2.19629430867699,0.8063,0,0,0,0.7784,0.8063,,,
182,144815,internal medicine,I,25,25,IVa,2.1330459623421791E-3,ALIVE,0.806311151992014,0.7784,3.6191129716436361E-3,ALIVE,2.20761389953117,0.8063,0,0,0,0.7784,0.8063,,,
106474,145427,surgery-trauma,Unknown,26,37,IV,9.514384325165182E-3,ALIVE,3.18810856928262,0.9506,2.1406808566348679E-2,ALIVE,10.9306412988452,3.6618,0,0,0,0.9506,3.6618,,,
106475,145427,surgery-trauma,Unknown,26,37,IVa,7.5555085721478212E-3,ALIVE,3.50354022395167,0.9506,1.6063934736413411E-2,ALIVE,10.3832369083441,3.6618,0,0,0,0.9506,3.6618,,,
133082,147307,unknown,Unknown,15,20,IV,1.6086431260178809E-3,ALIVE,0.674527080624368,0.3305,2.5136105741046101E-3,ALIVE,0.758865344255698,0.7674,0,0,0,0.3305,0.7674,,,
```
**Random 10 lines:**
```
3312398,363006,unknown,Unknown,14,14,IV,3.1102404555357769E-3,ALIVE,5.17094804509169,2.0791,5.0505027213677434E-3,ALIVE,8.41100574896794,2.2938,0,0,0,2.0791,2.2938,,,
263128,755774,Specialty Not Specified,Unknown,22,35,IVa,0.01216546290768661,ALIVE,3.50825627978807,2.109,2.9406714195596342E-2,ALIVE,9.49458200881176,5.7146,0,0,0,2.109,5.7146,,,
985890,1121034,family practice,Unknown,48,65,IV,7.9629586573941924E-2,ALIVE,4.95939630566709,10.1097,0.1575532314701952,ALIVE,10.8293339431366,18.1458,0,0,0,10.1097,18.1458,10,3.61328390403144,10
1807677,1749391,internal medicine,III,23,47,IV,2.4680824761358841E-2,ALIVE,4.74479645462328,2.693,6.8909092469981864E-2,ALIVE,9.42013972598838,3.3194,0,0,0,2.693,3.3194,1,2.18132654201974,1
1824820,1785418,unknown,II,26,31,IVa,1.0241511751713559E-2,ALIVE,2.72677142947412,2.6243,0.01958934186419603,ALIVE,7.55509150341348,4.9375,0,0,0,2.6243,4.9375,,,
2175570,2403083,critical care medicine (CCM),III,56,61,IVa,0.03639134827089175,ALIVE,3.00818926713719,0.7201,6.8285676888679717E-2,ALIVE,8.27385366626944,1.4319,0,0,0,0.7201,1.4319,,,
2674063,2740973,otolaryngology,I,33,33,IV,0.01009431559631002,ALIVE,3.83965951945583,1.0388,2.0164002375000711E-2,ALIVE,10.2799141795865,6.1063,0,0,0,1.0388,6.1063,,,
2600975,2794088,internal medicine,II,19,24,IVa,3.3907233857163668E-2,ALIVE,3.15590965754105,0.6923,7.9021192311249655E-2,ALIVE,6.09300208589157,11.8507,0,0,0,0.6923,11.8507,,,
3069372,3151890,Specialty Not Specified,III,37,48,IV,0.02370908190853779,ALIVE,3.70673244755775,0.5576,5.8990407617826403E-2,EXPIRED,10.0849026886583,4.2882,0,0,0,0.5576,4.2882,,,
3282568,3348292,hospitalist,II,55,79,IVa,0.1363786775096521,ALIVE,8.49756906222661,7.0729,0.3101063544378509,ALIVE,17.0629798929332,20.0257,0,0,0,7.0729,20.0257,3,3.11731976993542,3
```

### datasets/eicu-demo/lab.csv
**Summary:** This CSV file stores laboratory test results for ICU patients, including test names, numeric values, units, timing relative to ICU admission, and revision timestamps for various blood counts and chemistry tests.
**First 10 lines:**
```
labid,patientunitstayid,labresultoffset,labtypeid,labname,labresult,labresulttext,labmeasurenamesystem,labmeasurenameinterface,labresultrevisedoffset
437880563,1754323,-647,3,Hct,38.3000,38.3,%,%,-631
437880572,1754323,-647,3,platelets x 1000,181.0000,181,K/mcL,k/mm cu,-631
437880560,1754323,-647,3,RBC,4.8600,4.86,M/mcL,m/mm cu,-631
437880570,1754323,-647,3,-monos,8.7000,8.7,%,%,-631
437880571,1754323,-647,3,MCHC,30.4000,30.4,g/dL,%,-631
435917188,1754323,-207,3,WBC x 1000,14.3000,14.3  ,K/mcL,k/mm cu,-175
437880567,1754323,-647,3,WBC x 1000,5.4000,5.4  ,K/mcL,k/mm cu,-631
435917185,1754323,-207,3,Hct,32.5000,32.5,%,%,-175
437880566,1754323,-647,3,Hgb,11.6000,11.6,g/dL,g/dL,-631
```
**Random 10 lines:**
```
260615677,1118668,45,1,albumin,3.5000,3.5,g/dL,g/dL,98
461063571,1820689,-18226,7,Total CO2,26.0000,26,"",mmol/L,-18150
729537047,3027283,5708,1,bicarbonate,32.0000,32,mmol/L,MMOL/L,5744
45877980,175243,333,1,chloride,110.0000,110,mmol/L,mmol/L,364
744011900,3075813,4672,1,anion gap,11.0000,11.0,"","",4672
114270908,479455,1237,1,BUN,8.0000,8,mg/dL,mg/dL,1340
513696880,2016313,353,3,MPV,9.5000,9.5,fL,fL,383
425500203,1817131,-260,1,albumin,2.7000,2.7,g/dL,g/dL,-178
230022528,972933,-178,3,WBC x 1000,11.3000,11.3,K/mcL,th/uL,-156
432481460,1768638,10911,3,-lymphs,2.0000,2,%,%,11109
```

### datasets/eicu-demo/physicalExam.csv
**Summary:** This CSV file stores structured physical examination measurements and observations (like GCS scores, weight, vital signs) for ICU patients, timestamped by offset from admission, organized via hierarchical exam paths.
**First 10 lines:**
```
physicalexamid,patientunitstayid,physicalexamoffset,physicalexampath,physicalexamvalue,physicalexamtext
5276231,157427,1,notes/Progress Notes/Physical Exam/Physical Exam/Neurologic/GCS/Score/scored,scored,scored
5276232,157427,1,notes/Progress Notes/Physical Exam/Physical Exam Obtain Options/Performed - Structured,Performed - Structured,Performed - Structured
5276236,157427,1,notes/Progress Notes/Physical Exam/Physical Exam/Constitutional/Weight and I&O/Weight (kg)/Admission,Admission,86.2
5276237,157427,1,notes/Progress Notes/Physical Exam/Physical Exam/Constitutional/Weight and I&O/Weight (kg)/Current,Current,86.2
5276238,157427,1,notes/Progress Notes/Physical Exam/Physical Exam/Constitutional/Weight and I&O/Weight (kg)/Delta,Delta,0
5276239,157427,1,notes/Progress Notes/Physical Exam/Physical Exam/Neurologic/GCS/Motor Score/6,6,6
5276240,157427,1,notes/Progress Notes/Physical Exam/Physical Exam/Neurologic/GCS/Eyes Score/4,4,4
5276241,157427,1,notes/Progress Notes/Physical Exam/Physical Exam/Neurologic/GCS/Verbal Score/5,5,5
5278355,238463,19,notes/Progress Notes/Physical Exam/Physical Exam/Neurologic/GCS/Score/scored,scored,scored
```
**Random 10 lines:**
```
11850525,349481,10,notes/Progress Notes/Physical Exam/Physical Exam/Constitutional/Vital Sign and Physiological Data/O2 Sat%/O2 Sat% Lowest,O2 Sat% Lowest,100
83892449,2075278,-631,notes/Progress Notes/Physical Exam/Physical Exam/Neurologic/GCS/Motor Score/6,6,6
96320819,2898513,50,notes/Progress Notes/Physical Exam/Physical Exam/Constitutional/Vital Sign and Physiological Data/Resp Rate/Resp Current,Resp Current,24
104538508,2846485,4,notes/Progress Notes/Physical Exam/Physical Exam/Neurologic/GCS/Verbal Score/5,5,5
125054309,3060213,7258,notes/Progress Notes/Physical Exam/Physical Exam/Pulmonary/Auscultation/Wheezes/diffuse wheezing,diffuse wheezing,diffuse wheezing
134413978,3115505,82,notes/Progress Notes/Physical Exam/Physical Exam/Neurologic/GCS/Motor Score/6,6,6
152371954,3140152,977,notes/Progress Notes/Physical Exam/Physical Exam/Cardiovascular/Auscultation/Heart Sounds/S1/S1 normal,S1 normal,S1 normal
152622232,3159526,11519,notes/Progress Notes/Physical Exam/Physical Exam/Cardiovascular/Pulses/Normal/normal,normal,normal
154848579,3136745,6332,notes/Progress Notes/Physical Exam/Physical Exam/Constitutional/Vital Sign and Physiological Data/BP (diastolic)/BP (diastolic) Current,BP (diastolic) Current,70
157777560,3237226,45,notes/Progress Notes/Physical Exam/Physical Exam/Constitutional/Vital Sign and Physiological Data/BP (diastolic)/BP (diastolic) Highest,BP (diastolic) Highest,74
```

### datasets/eicu-demo/nurseCharting.csv
**Summary:** The nurseCharting.csv file documents nursing assessments, vital signs, observations, and interventions for patients during their hospital stay, with timestamps indicating when these were recorded.
**First 10 lines:**
```
nursingchartid,patientunitstayid,nursingchartoffset,nursingchartentryoffset,nursingchartcelltypecat,nursingchartcelltypevallabel,nursingchartcelltypevalname,nursingchartvalue
189336686,143870,-67,-67,Other Vital Signs and Infusions,"Eye, Ear, Nose, Throat Assessment",Value,WDL
187848155,143870,239,239,Other Vital Signs and Infusions,Gastrointestinal Assessment,Value,X
281610014,143870,433,433,Other Vital Signs and Infusions,Pain Assessment,Value,WDL
237860915,143870,433,433,Other Vital Signs and Infusions,Neurological Assessment,Value,WDL
265486190,143870,1108,1108,Vital Signs,Respiratory Rate,Respiratory Rate,15
250570336,143870,433,433,Vital Signs,O2 Saturation,O2 Saturation,95
138970043,143870,973,973,Vital Signs,Respiratory Rate,Respiratory Rate,16
273339764,143870,73,73,Vital Signs,Heart Rate,Heart Rate,41
286729710,143870,313,313,Vital Signs,O2 Saturation,O2 Saturation,98
```
**Random 10 lines:**
```
312189119,249328,4049,4073,Vital Signs,Invasive BP,Invasive BP Systolic,137
354645686,391704,36,48,Vital Signs,O2 Saturation,O2 Saturation,100
433534480,521456,37503,37518,Scores,Delirium Scale/Score,Delirium Score,N/A
490041524,827084,641,641,Vital Signs,Non-Invasive BP,Non-Invasive BP Diastolic,43
462143596,896028,4753,4824,Vital Signs,Invasive BP,Invasive BP Mean,88
655591079,1065859,366,366,Vital Signs,O2 Saturation,O2 Saturation,98
1296497856,1858620,4494,4543,Scores,Glasgow coma score,Verbal,4
1689423211,2335944,2809,2809,Vital Signs,Non-Invasive BP,Non-Invasive BP Diastolic,39
1554609380,2361839,12936,12936,Vital Signs,Temperature,Temperature (F),99.9
1772013577,2603071,3029,3029,Scores,Glasgow coma score,Verbal,5
```

### datasets/eicu-demo/note.csv
**Summary:** The 'note.csv' file stores metadata and content of comprehensive progress notes for patients, including note identifiers, patient stay IDs, timestamps, note types, system paths, and specific note values related to medical documentation settings and options.
**First 10 lines:**
```
noteid,patientunitstayid,noteoffset,noteenteredoffset,notetype,notepath,notevalue,notetext
3594780,157427,1,8,Comprehensive Progress,notes/Progress Notes/Admission Page One/Skip Screen Options 2/Include Past Medical History,Include Past Medical History,Include Past Medical History
3594785,157427,1,8,Comprehensive Progress,notes/Progress Notes/Assessment and Plan/View Options/System View,System View,SystemView
3594786,157427,1,8,Comprehensive Progress,notes/Progress Notes/Assessment and Plan/Include Rx/Include Rx,Include Rx,Include Rx
3594787,157427,1,8,Comprehensive Progress,notes/Shared/View and Save/Save Options/Print/Copies/Copies,Copies,1
3595514,238463,19,22,Comprehensive Progress,notes/Progress Notes/Assessment and Plan/View Options/System View,System View,SystemView
3595515,238463,19,22,Comprehensive Progress,notes/Shared/View and Save/Save Options/Print/Copies/Copies,Copies,1
3600679,174956,-3,1,Comprehensive Progress,notes/Progress Notes/Admission Page One/Enter surgery Information?/Yes,Yes,Yes
3600680,174956,-3,1,Comprehensive Progress,notes/Progress Notes/Assessment and Plan/View Options/System View,System View,SystemView
3600681,174956,-3,1,Comprehensive Progress,notes/Shared/View and Save/Save Options/Print/Copies/Copies,Copies,1
```
**Random 10 lines:**
```
9402432,387623,4,82,Admission,notes/Progress Notes/Admission Page One/Skip Screen Options 1/Include Review of Systems,Include Review of Systems,Include Review of Systems
10855438,399365,109,132,Admission,notes/Shared/View and Save/Save Options/Print/Copies/Copies,Copies,1
11888312,524799,17,44,Comprehensive Progress,notes/Progress Notes/Assessment and Plan/Include Rx/Include Rx,Include Rx,Include Rx
16174522,454240,112,122,Daily Progress,notes/Progress Notes/Assessment and Plan/View Options/System View,System View,SystemView
31832425,1439473,25,33,Admission,notes/Shared/View and Save/Save Options/Print/Copies/Copies,Copies,1
33596116,1544756,27,81,Admission,notes/Progress Notes/Allergies / Preadmission Medications/Pre-Admission Medications/Unknown,Unknown,Unknown
38746944,1687775,42,69,Admission,notes/Progress Notes/Assessment and Plan/View Options/System View,System View,SystemView
64882938,2692124,58,1131,Admission,notes/Progress Notes/Admission Page One/Skip Screen Options 1/Include Allergies and Pre-Admission Meds,Include Allergies and Pre-Admission Meds,Include Allergies and Pre-Admission Meds
87744944,3172946,1,7,Admission,notes/Progress Notes/Review Of Systems/Systems/Pulmonary/Dyspnea on Exertion/dyspnea on exertion,dyspnea on exertion,dyspnea on exertion
88669355,3223634,8,138,Admission,notes/Shared/View and Save/Save Options/Print/Copies/Copies,Copies,1
```

### datasets/eicu-demo/admissionDx.csv
**Summary:** This file stores detailed admission diagnoses for ICU patients, including hierarchical categorization paths, specific diagnosis names/descriptions, and timing offsets relative to admission, linked by unique patient stay identifiers. (498 characters)
**First 10 lines:**
```
admissiondxid,patientunitstayid,admitdxenteredoffset,admitdxpath,admitdxname,admitdxtext
7351978,2900423,162,admission diagnosis|Non-operative Organ Systems|Organ System|Cardiovascular,Cardiovascular,Cardiovascular
7351977,2900423,162,admission diagnosis|Was the patient admitted from the O.R. or went to the O.R. within 4 hours of admission?|No,No,No
7351979,2900423,162,"admission diagnosis|All Diagnosis|Non-operative|Diagnosis|Cardiovascular|Sepsis, pulmonary","Sepsis, pulmonary","Sepsis, pulmonary"
7745060,2902156,944,"admission diagnosis|All Diagnosis|Non-operative|Diagnosis|Cardiovascular|Rhythm disturbance (atrial, supraventricular)","Rhythm disturbance (atrial, supraventricular)","Rhythm disturbance (atrial, supraventricular)"
7745059,2902156,944,admission diagnosis|Non-operative Organ Systems|Organ System|Cardiovascular,Cardiovascular,Cardiovascular
7745058,2902156,944,admission diagnosis|Was the patient admitted from the O.R. or went to the O.R. within 4 hours of admission?|No,No,No
8251201,2903553,2,admission diagnosis|Non-operative Organ Systems|Organ System|Cardiovascular,Cardiovascular,Cardiovascular
8251200,2903553,2,admission diagnosis|Was the patient admitted from the O.R. or went to the O.R. within 4 hours of admission?|No,No,No
8251202,2903553,2,"admission diagnosis|All Diagnosis|Non-operative|Diagnosis|Cardiovascular|Sepsis, other","Sepsis, other","Sepsis, other"
```
**Random 10 lines:**
```
1348184,356949,78,admission diagnosis|All Diagnosis|Non-operative|Diagnosis|Metabolic/Endocrine|Diabetic ketoacidosis,Diabetic ketoacidosis,Diabetic ketoacidosis
4475015,1455088,22,admission diagnosis|Was the patient admitted from the O.R. or went to the O.R. within 4 hours of admission?|No,No,No
6204820,2093411,15,admission diagnosis|Was the patient admitted from the O.R. or went to the O.R. within 4 hours of admission?|No,No,No
5978751,2095984,85,"admission diagnosis|All Diagnosis|Non-operative|Diagnosis|Gastrointestinal|Bleeding, lower GI","Bleeding, lower GI","Bleeding, lower GI"
6900765,2558003,11,admission diagnosis|Was the patient admitted from the O.R. or went to the O.R. within 4 hours of admission?|No,No,No
6902478,2560585,13,admission diagnosis|Non-operative Organ Systems|Organ System|Cardiovascular,Cardiovascular,Cardiovascular
7478971,2678186,39,admission diagnosis|Non-operative Organ Systems|Organ System|Cardiovascular,Cardiovascular,Cardiovascular
7617282,2694459,5,admission diagnosis|Was the patient admitted from the O.R. or went to the O.R. within 4 hours of admission?|No,No,No
7657056,2754778,50,admission diagnosis|Additional APACHE  Information|PTCA done within 24 hours|none,none,none
7740364,2794087,539,admission diagnosis|Was the patient admitted from the O.R. or went to the O.R. within 4 hours of admission?|Yes,Yes,Yes
```

### datasets/eicu-demo/pastHistory.csv
**Summary:** The file documents patients' past medical histories by recording time offsets, note types, hierarchical categories (paths), and specific health conditions or events (values) during their ICU stay.
**First 10 lines:**
```
pasthistoryid,patientunitstayid,pasthistoryoffset,pasthistoryenteredoffset,pasthistorynotetype,pasthistorypath,pasthistoryvalue,pasthistoryvaluetext
990803,141765,7,12,Comprehensive Progress,notes/Progress Notes/Past History/Past History Obtain Options/No Health Problems,No Health Problems,NoHealthProblems
970059,143870,4,10,Comprehensive Progress,notes/Progress Notes/Past History/Past History Obtain Options/No Health Problems,No Health Problems,NoHealthProblems
1180401,144815,32,41,Comprehensive Progress,notes/Progress Notes/Past History/Past History Obtain Options/No Health Problems,No Health Problems,NoHealthProblems
1194998,145427,8,13,Comprehensive Progress,notes/Progress Notes/Past History/Past History Obtain Options/No Health Problems,No Health Problems,NoHealthProblems
896652,147307,53,56,Comprehensive Progress,notes/Progress Notes/Past History/Past History Obtain Options/No Health Problems,No Health Problems,NoHealthProblems
1261966,147784,10,20,Comprehensive Progress,notes/Progress Notes/Past History/Past History Obtain Options/Performed,Performed,Performed
1261967,147784,10,20,Comprehensive Progress,notes/Progress Notes/Past History/Organ Systems/Endocrine (R)/Non-Insulin Dependent Diabetes/medication dependent,medication dependent,medication dependent
1150985,148611,-93,-82,Comprehensive Progress,notes/Progress Notes/Past History/Past History Obtain Options/No Health Problems,No Health Problems,NoHealthProblems
1252461,149713,4,9,Comprehensive Progress,notes/Progress Notes/Past History/Past History Obtain Options/No Health Problems,No Health Problems,NoHealthProblems
```
**Random 10 lines:**
```
1608737,261520,18,121,Admission,notes/Progress Notes/Past History/Organ Systems/Cardiovascular (R)/Hypertension Requiring Treatment/hypertension requiring treatment,hypertension requiring treatment,hypertension requiring treatment
3449748,453764,2354,2456,Comprehensive Progress,notes/Progress Notes/Past History/Organ Systems/Pulmonary/COPD/COPD  - moderate,COPD  - moderate,COPD  - moderate
6080458,1062496,136,161,Admission,notes/Progress Notes/Past History/Organ Systems/Cardiovascular (R)/Valve disease/s/p AVR,s/p AVR,s/p AVR
6427652,1081610,2436,2437,Past History Edit,notes/Progress Notes/Past History/Organ Systems/Cardiovascular (R)/Arrhythmias/atrial fibrillation - chronic,atrial fibrillation - chronic,atrial fibrillation - chronic
10234756,1681068,58,67,Admission,notes/Progress Notes/Past History/Organ Systems/Cardiovascular (R)/Congestive Heart Failure/CHF,CHF,CHF
11225074,1823939,5122,5122,Follow-up Consultation/Other,notes/Progress Notes/Past History/Organ Systems/Pulmonary/COPD/COPD  - moderate,COPD  - moderate,COPD  - moderate
17366107,3001552,0,58,Admission,notes/Progress Notes/Past History/Organ Systems/Pulmonary/COPD/COPD  - no limitations,COPD  - no limitations,COPD  - no limitations
21268065,3136458,1115,1146,Comprehensive Progress,notes/Progress Notes/Past History/Organ Systems/Endocrine (R)/Hypothyroidism/hypothyroidism,hypothyroidism,hypothyroidism
21291588,3149953,804,816,Comprehensive Progress,notes/Progress Notes/Past History/Organ Systems/Neurologic/Dementia/dementia,dementia,dementia
21770145,3239262,7662,7664,Past History Edit,notes/Progress Notes/Past History/Organ Systems/Cardiovascular (R)/Myocardial Infarction/MI - date unknown,MI - date unknown,MI - date unknown
```

### datasets/eicu-demo/allergy.csv
**Summary:** This CSV file logs patient allergies during ICU stays, recording drug/non-drug allergy names, types, timestamps, and entry details for each patient.
**First 10 lines:**
```
allergyid,patientunitstayid,allergyoffset,allergyenteredoffset,allergynotetype,specialtytype,usertype,rxincluded,writtenineicu,drugname,allergytype,allergyname,drughiclseqno
357144,243097,2549,2552,Comprehensive Progress,eCM Primary,THC Nurse,True,True,"",Non Drug,penicillins,
442253,243097,1288,1294,Comprehensive Progress,eCM Primary,THC Nurse,True,True,CODEINE PHOSPHATE,Drug,CODEINE PHOSPHATE,1721
357143,243097,2549,2552,Comprehensive Progress,eCM Primary,THC Nurse,True,True,CODEINE PHOSPHATE,Drug,CODEINE PHOSPHATE,1721
329929,243097,21,28,Admission,eCM Primary,THC Nurse,True,True,"",Non Drug,penicillins,
363374,243097,3988,3989,Comprehensive Progress,eCM Primary,THC Nurse,True,True,CODEINE PHOSPHATE,Drug,CODEINE PHOSPHATE,1721
442254,243097,1288,1294,Comprehensive Progress,eCM Primary,THC Nurse,True,True,"",Non Drug,penicillins,
363375,243097,3988,3989,Comprehensive Progress,eCM Primary,THC Nurse,True,True,"",Non Drug,penicillins,
329928,243097,21,28,Admission,eCM Primary,THC Nurse,True,True,CODEINE PHOSPHATE,Drug,CODEINE PHOSPHATE,1721
234874,244477,30,273,Admission,eCM Primary,THC Nurse,True,True,VALSARTAN,Drug,VALSARTAN,12204
```
**Random 10 lines:**
```
496204,371003,42,55,Admission,eCM Primary,THC Nurse,True,True,PENICILLIN G BENZATHINE,Drug,PENICILLIN G BENZATHINE,3941
1100786,1098048,727,729,Daily Progress,eCM Primary,Other,False,True,"",Non Drug,HALOGENATED,
1111139,1099398,1367,1369,Daily Progress,eCM Primary,Other,False,True,TRAMADOL HCL,Drug,TRAMADOL HCL,8317
1104710,1105687,693,693,Daily Progress,eCM Primary,Other,False,True,CELEBREX,Drug,CELEBREX,18979
1836272,1794248,1326,1330,Comprehensive Progress,eCM Primary,THC Nurse,False,True,"",Non Drug,SULFA'S,
1892426,1830188,24,33,Admission,eCM Primary,THC Nurse,True,True,"",Non Drug,telmisartan,
2320025,1979528,77,101,Admission,eCM Primary,THC Nurse,True,True,LISINOPRIL,Drug,LISINOPRIL,132
2501466,2521021,127,136,Admission,eCM Primary,THC Nurse,True,True,LEVAQUIN,Drug,LEVAQUIN,12383
3971470,3149953,804,816,Comprehensive Progress,eCM Primary,Attending Physician,False,False,PENICILLIN G BENZATHINE,Drug,PENICILLIN G BENZATHINE,3941
3977408,3156122,-81,-70,Admission,eCM Primary,Attending Physician,True,False,IODINE,Drug,IODINE,752
```

### datasets/eicu-demo/apachePredVar.csv
**Summary:** This CSV file contains clinical variables and outcomes for ICU patients, designed for predicting mortality and other outcomes using Apache II and SAPS3 scores, demographics, physiology, comorbidities, and treatment data. (499 chars)
**First 10 lines:**
```
apachepredvarid,patientunitstayid,sicuday,saps3day1,saps3today,saps3yesterday,gender,teachtype,region,bedcount,admitsource,graftcount,meds,verbal,motor,eyes,age,admitdiagnosis,thrombolytics,diedinhospital,aids,hepaticfailure,lymphoma,metastaticcancer,leukemia,immunosuppression,cirrhosis,electivesurgery,activetx,readmit,ima,midur,ventday1,oobventday1,oobintubday1,diabetes,managementsystem,var03hspxlos,pao2,fio2,ejectfx,creatinine,dischargelocation,visitnumber,amilocation,day1meds,day1verbal,day1motor,day1eyes,day1pao2,day1fio2
4004,141765,1,0,0,0,1,0,3,12,8,3,0,5,6,4,87,RHYTHATR,0,0,0,0,0,0,0,0,0,,0,0,0,0,0,0,0,0,1,0,-1,-1,-1,1.04,4,1,-1,0,5,6,4,-1,-1
8047,143870,1,0,0,0,0,0,3,14,1,3,0,5,6,4,76,S-CAROTEND,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,-1,-1,-1,1.14,4,1,-1,0,5,6,4,-1,-1
1798882,144815,1,0,0,0,1,0,3,8,8,3,0,5,6,4,34,ODOTHER,0,0,0,0,0,0,0,0,0,,0,0,0,0,0,0,0,0,1,0,-1,-1,-1,0.63,8,1,-1,0,5,6,4,-1,-1
1485310,145427,1,0,0,0,0,0,3,14,1,3,0,5,6,4,61,S-GIPERFOR,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,-1,-1,-1,1.05,4,1,-1,0,5,6,4,-1,-1
27991,147307,1,0,0,0,1,0,3,43,1,3,0,5,6,4,55,S-CAROTEND,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1,0,-1,-1,-1,-1,4,1,-1,0,5,6,4,-1,-1
12167,147784,1,0,0,0,1,0,3,30,8,3,0,3,6,4,60,COMA,0,0,0,0,0,0,0,0,0,,1,0,0,0,0,1,1,1,1,0,76,60,-1,0.54,4,1,-1,0,3,6,4,76,60
2100906,148611,1,0,0,0,0,0,3,8,8,3,0,5,6,4,28,ODOTHER,0,0,0,0,0,0,0,0,0,,0,0,0,0,0,0,0,0,1,0,-1,-1,-1,0.82,4,1,-1,0,5,6,4,-1,-1
1795240,149433,1,0,0,0,1,0,3,14,8,3,-1,-1,-1,-1,34,"",0,0,0,0,0,0,0,0,0,,0,0,0,0,0,0,0,0,1,0,-1,-1,-1,-1,4,1,-1,-1,-1,-1,-1,-1,-1
311,149713,1,0,0,0,1,0,3,9,8,3,0,4,6,4,,AMI,0,0,0,0,0,0,0,0,0,,0,0,0,0,0,0,0,0,1,0,-1,-1,-1,0.61,4,1,2,0,4,6,4,-1,-1
```
**Random 10 lines:**
```
1117185,1093888,1,0,0,0,0,0,3,11,8,3,0,5,6,4,78,SEPSISPULM,0,0,0,0,0,0,0,0,0,,1,0,0,0,0,0,0,0,1,0,-1,-1,-1,1.6,4,1,-1,0,5,6,4,-1,-1
1423418,1101375,1,0,0,0,1,0,3,20,8,3,1,-1,-1,-1,79,ICH,0,0,0,0,0,0,0,0,0,,1,0,0,0,1,1,1,0,1,0,-1,-1,-1,-1,7,1,-1,1,-1,-1,-1,-1,-1
2327943,1154605,1,0,0,0,1,0,3,15,4,3,0,2,5,2,76,PNEUMBACT,0,0,0,0,0,0,0,0,0,,1,1,0,0,1,1,0,0,1,0,166,75,-1,-1,6,2,-1,0,2,5,2,166,75
330461,1620780,1,0,0,0,1,0,3,5,8,3,0,4,6,3,57,DHNKA,0,0,0,0,0,0,0,0,0,,0,0,0,0,0,0,0,1,1,0,-1,-1,-1,1.4,4,1,-1,0,4,6,3,-1,-1
2297438,1661775,1,0,0,0,1,0,3,7,7,3,0,5,6,4,75,CP-UNK,0,0,0,0,0,0,0,0,0,,0,0,0,0,0,0,0,1,1,0,-1,-1,-1,1.17,4,1,-1,0,5,6,4,-1,-1
1002962,2565400,1,0,0,0,0,0,3,26,4,3,0,5,6,4,51,"",0,0,0,0,0,0,0,0,0,,0,0,0,0,0,0,0,0,1,0,-1,-1,-1,1,4,1,-1,0,5,6,4,-1,-1
968026,2848336,1,0,0,0,0,0,3,53,4,3,0,5,6,4,51,PANCRITIS,0,0,0,0,0,0,0,0,0,,0,0,0,0,0,0,0,0,1,0,-1,-1,-1,-1,8,1,-1,0,5,6,4,-1,-1
1282039,2866893,1,0,0,0,0,0,3,17,4,3,0,4,5,3,46,SEPSISGI,0,0,0,0,0,0,0,0,0,,0,0,0,0,0,0,0,0,1,0,-1,-1,-1,1.35,4,1,-1,0,4,5,3,-1,-1
733335,3098570,1,0,0,0,0,0,3,12,8,3,0,1,1,1,57,PNEUMOTHER,0,0,0,0,0,0,0,0,0,,1,0,0,0,1,1,1,0,1,0,-1,-1,-1,0.93,4,1,-1,0,1,1,1,-1,-1
1852647,3148506,1,0,0,0,0,0,3,13,1,3,0,1,1,1,54,S-CABG,0,0,0,0,0,0,0,0,0,1,1,0,1,0,1,1,1,0,1,0,157,40,55,0.67,4,1,-1,0,1,1,1,157,40
```

### datasets/eicu-demo/admissiondrug.csv
**Summary:** The file `admissiondrug.csv` documents medications administered to ICU patients, including drug names, dosages, administration times, provider details, and clinical context (e.g., note types, specialties) to support clinical care and research. (496 characters)
**First 10 lines:**
```
admissiondrugid,patientunitstayid,drugoffset,drugenteredoffset,drugnotetype,specialtytype,usertype,rxincluded,writtenineicu,drugname,drugdosage,drugunit,drugadmitfrequency,drughiclseqno
1373386,281479,420,444,Daily Progress,eCM Primary,THC Physician,False,True,NOVOLOG                                                                                                                                                                                                                                                        ,0.0000, , ,20769
1917810,281479,24,31,Admission,eCM Primary,THC Nurse,True,True,NOVOLOG                                                                                                                                                                                                                                                        ,0.0000, , ,20769
2118524,292154,242,243,Daily Progress,eCM Primary,Other,False,True,ALLOPURINOL                                                                                                                                                                                                                                                    ,0.0000, , ,1100
1984925,292154,53,69,Admission,eCM Primary,THC Nurse,False,True,DILTIAZEM 24HR CD                                                                                                                                                                                                                                              ,0.0000, , ,182
2118526,292154,242,243,Daily Progress,eCM Primary,Other,False,True,CALCIUM CARBONATE                                                                                                                                                                                                                                              ,0.0000, , ,1163
1984920,292154,53,69,Admission,eCM Primary,THC Nurse,False,True,ALLOPURINOL                                                                                                                                                                                                                                                    ,0.0000, , ,1100
2118525,292154,242,243,Daily Progress,eCM Primary,Other,False,True,ASPIRIN                                                                                                                                                                                                                                                        ,0.0000, , ,1820
1984924,292154,53,69,Admission,eCM Primary,THC Nurse,False,True,CLONIDINE                                                                                                                                                                                                                                                      ,0.0000, , ,36550
2118529,292154,242,243,Daily Progress,eCM Primary,Other,False,True,COUMADIN                                                                                                                                                                                                                                                       ,0.0000, , ,2812
```
**Random 10 lines:**
```
2219088,391704,53,77,Admission,eCM Primary,THC Nurse,True,True,LANTUS                                                                                                                                                                                                                                                         ,0.0000, , ,22025
7375365,1735220,959,999,Initial Consultation/Other,critical care medicine (CCM),THC Physician,False,False,PREDNISONE                                                                                                                                                                                                                                                     ,0.0000, , ,2879
6376264,1823442,45,67,Admission,eCM Primary,THC Nurse,True,True,COREG                                                                                                                                                                                                                                                          ,0.0000, , ,13795
6695282,1837638,-69,-40,Admission,eCM Primary,THC Nurse,True,True,COREG                                                                                                                                                                                                                                                          ,0.0000, , ,13795
6802524,1855917,7,10,Re-Admission,eCM Primary,THC Nurse,True,True,GLUCOPHAGE                                                                                                                                                                                                                                                     ,0.0000, , ,4763
6730145,1855917,1602,1606,Comprehensive Progress,eCM Primary,THC Nurse,True,True,PRILOSEC                                                                                                                                                                                                                                                       ,0.0000, , ,4673
11735938,2619844,193,213,Admission,eCM Primary,THC Nurse,True,True,PROTONIX                                                                                                                                                                                                                                                       ,0.0000, , ,22008
11053380,2629735,-84,51,Admission,eCM Primary,THC Nurse,True,True,LASIX                                                                                                                                                                                                                                                          ,0.0000, , ,3660
13618733,2687268,31,61,Admission,eCM Primary,THC Nurse,True,True,PRILOSEC                                                                                                                                                                                                                                                       ,0.0000, , ,4673
18378066,3156122,2824,2834,Comprehensive Progress,eCM Primary,Attending Physician,False,False,CRESTOR                                                                                                                                                                                                                                                        ,0.0000, , ,25009
```

### datasets/eicu-demo/diagnosis.csv
**Summary:** This file tracks ICU patient diagnoses, recording each diagnosis's description, medical code (ICD-9), timing relative to ICU admission, priority level, and whether it was active at discharge, linked to specific patient stays.
**First 10 lines:**
```
diagnosisid,patientunitstayid,activeupondischarge,diagnosisoffset,diagnosisstring,icd9code,diagnosispriority
7607199,346380,False,5028,cardiovascular|ventricular disorders|hypertension,"401.9, I10",Other
7570429,346380,False,685,neurologic|altered mental status / pain|change in mental status,"780.09, R41.82",Major
7705483,346380,True,5035,cardiovascular|shock / hypotension|hypotension,"458.9, I95.9",Major
7848601,346380,True,5035,neurologic|altered mental status / pain|schizophrenia,"295.90, F20.9",Major
7451475,346380,False,5028,pulmonary|disorders of vasculature|pulmonary embolism|thrombus,"415.19, I26.99",Major
7839760,346380,False,5028,cardiovascular|shock / hypotension|hypotension,"458.9, I95.9",Major
7194271,346380,True,5035,renal|disorder of kidney|acute renal failure,"584.9, N17.9",Primary
6926969,346380,True,5035,general|other syndromes|syncope,"780.2, R55",Major
7517655,346380,False,5028,neurologic|misc|Parkinson's disease,"332.0, G20",Major
```
**Random 10 lines:**
```
44224659,3159526,False,16203,gastrointestinal|malnutrition|protein-calorie malnutrition,"263.9, E46",Major
43547950,3097587,False,782,infectious diseases|chest/pulmonary infections|pneumonia|hospital acquired (not ventilator-associated),"486, J18.9",Major
34018153,2764328,True,117,infectious diseases|systemic/other infections|sepsis|severe,"995.92, R65.20",Primary
10765079,564216,False,6299,pulmonary|respiratory failure|pulmonary aspiration,"507.0, J69.0",Major
23016084,1657457,True,-24,general|other syndromes|syncope,"780.2, R55",Other
8947633,472811,False,3509,cardiovascular|vascular disorders|hypertension|controlled,"401.9, I10",Other
11681410,930706,True,18,cardiovascular|chest pain / ASHD|acute coronary syndrome|acute myocardial infarction (with ST elevation),"410.90, I21.3",Primary
44265066,3136459,False,7495,pulmonary|pulmonary infections|pneumonia,"486, J18.9",Other
35571772,3098657,False,8215,cardiovascular|shock / hypotension|signs and symptoms of sepsis (SIRS),995.90,Other
30566071,2595334,False,61,cardiovascular|ventricular disorders|acute pulmonary edema|due to hypertension,"428.1, 402.91, I11.0, I50.1",Major
```

### datasets/eicu-demo/.f1a_cache/file_summary_cache.json
**Summary:** No summary available
**First 10 lines:**
```
{
  "/data/cyx/openlens-ai/datasets/eicu-demo/admissionDx.csv": {
    "mtime": 1760863079.3453543,
    "summary": "This file stores detailed admission diagnoses for ICU patients, including hierarchical categorization paths, specific diagnosis names/descriptions, and timing offsets relative to admission, linked by unique patient stay identifiers. (498 characters)"
  },
  "/data/cyx/openlens-ai/datasets/eicu-demo/admissiondrug.csv": {
    "mtime": 1760863077.5153718,
    "summary": "The file `admissiondrug.csv` documents medications administered to ICU patients, including drug names, dosages, administration times, provider details, and clinical context (e.g., note types, specialties) to support clinical care and research. (496 characters)"
  },
  "/data/cyx/openlens-ai/datasets/eicu-demo/allergy.csv": {
```
**Random 10 lines:**
```
    "summary": "This CSV file logs patient allergies during ICU stays, recording drug/non-drug allergy names, types, timestamps, and entry details for each patient."
  "/data/cyx/openlens-ai/datasets/eicu-demo/apacheApsVar.csv": {
    "mtime": 1760863077.4833722,
  },
    "summary": "The 'note.csv' file stores metadata and content of comprehensive progress notes for patients, including note identifiers, patient stay IDs, timestamps, note types, system paths, and specific note values related to medical documentation settings and options."
    "summary": "This CSV file records nursing assessment data for ICU patients, capturing hierarchical assessment categories (e.g., Cardiovascular|Edema), specific attributes, values (e.g., generalized, minimal), and timing offsets."
  },
  },
  },
    "summary": "This CSV file stores time-stamped periodic vital sign measurements (e.g., temperature, heart rate, blood pressure, oxygen saturation, ICP) for ICU patients, linked by unique identifiers and observation offsets."
```

