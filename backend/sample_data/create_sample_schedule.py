import pandas as pd
from datetime import date

data = [
    {"activity_code": "CIV-3011", "activity_name": "Construct Foundation A1", "discipline": "Civil", "wbs": "CIV.30.11", "planned_start": date(2026, 8, 1), "planned_finish": date(2026, 8, 15)},
    {"activity_code": "CIV-3012", "activity_name": "Construct Foundation A2", "discipline": "Civil", "wbs": "CIV.30.12", "planned_start": date(2026, 8, 10), "planned_finish": date(2026, 8, 25)},
    {"activity_code": "CIV-3021", "activity_name": "Erect Structural Steel Grid 1", "discipline": "Civil", "wbs": "CIV.30.21", "planned_start": date(2026, 8, 20), "planned_finish": date(2026, 9, 10)},
    {"activity_code": "PIP-1023", "activity_name": "Erect Line 24-XX-101", "discipline": "Piping", "wbs": "PIP.10.23", "planned_start": date(2026, 8, 15), "planned_finish": date(2026, 8, 30)},
    {"activity_code": "PIP-1027", "activity_name": "Install Support for XX-101", "discipline": "Piping", "wbs": "PIP.10.27", "planned_start": date(2026, 8, 10), "planned_finish": date(2026, 8, 20)},
    {"activity_code": "PIP-1042", "activity_name": "Inspect XX-101", "discipline": "Piping", "wbs": "PIP.10.42", "planned_start": date(2026, 9, 1), "planned_finish": date(2026, 9, 5)},
    {"activity_code": "PIP-1050", "activity_name": "Hydrotest Line XX-101", "discipline": "Piping", "wbs": "PIP.10.50", "planned_start": date(2026, 9, 5), "planned_finish": date(2026, 9, 10)},
    {"activity_code": "MEC-2011", "activity_name": "Install Pump P-101", "discipline": "Mechanical", "wbs": "MEC.20.11", "planned_start": date(2026, 8, 25), "planned_finish": date(2026, 9, 5)},
    {"activity_code": "MEC-2012", "activity_name": "Align Pump P-101", "discipline": "Mechanical", "wbs": "MEC.20.12", "planned_start": date(2026, 9, 5), "planned_finish": date(2026, 9, 10)},
    {"activity_code": "MEC-2021", "activity_name": "Install Compressor C-101", "discipline": "Mechanical", "wbs": "MEC.20.21", "planned_start": date(2026, 9, 1), "planned_finish": date(2026, 9, 15)},
    {"activity_code": "ELE-4011", "activity_name": "Cable Pulling for Substation SUB-1", "discipline": "Electrical", "wbs": "ELE.40.11", "planned_start": date(2026, 8, 20), "planned_finish": date(2026, 9, 5)},
    {"activity_code": "ELE-4012", "activity_name": "Terminate Cables SUB-1", "discipline": "Electrical", "wbs": "ELE.40.12", "planned_start": date(2026, 9, 5), "planned_finish": date(2026, 9, 15)},
    {"activity_code": "ELE-4021", "activity_name": "Install MCC Panel MCC-1", "discipline": "Electrical", "wbs": "ELE.40.21", "planned_start": date(2026, 8, 25), "planned_finish": date(2026, 9, 10)},
    {"activity_code": "INS-5011", "activity_name": "Install Instrument Tubing", "discipline": "Instrumentation", "wbs": "INS.50.11", "planned_start": date(2026, 9, 1), "planned_finish": date(2026, 9, 20)},
    {"activity_code": "INS-5012", "activity_name": "Calibrate Transmitters", "discipline": "Instrumentation", "wbs": "INS.50.12", "planned_start": date(2026, 9, 15), "planned_finish": date(2026, 9, 30)},
    {"activity_code": "PIP-1060", "activity_name": "Erect Line 24-XX-102", "discipline": "Piping", "wbs": "PIP.10.60", "planned_start": date(2026, 8, 20), "planned_finish": date(2026, 9, 5)},
    {"activity_code": "PIP-1065", "activity_name": "Install Support for XX-102", "discipline": "Piping", "wbs": "PIP.10.65", "planned_start": date(2026, 8, 15), "planned_finish": date(2026, 8, 25)},
    {"activity_code": "CIV-3031", "activity_name": "Construct Foundation B1", "discipline": "Civil", "wbs": "CIV.30.31", "planned_start": date(2026, 8, 15), "planned_finish": date(2026, 8, 30)},
]

df = pd.DataFrame(data)
df.to_excel("sample_schedule.xlsx", index=False)
print("Sample schedule created successfully")