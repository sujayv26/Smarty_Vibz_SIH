import pandas as pd
from datetime import date

data = [
    {"date": date(2026, 8, 30), "discipline": "Piping", "activity_description": "Started erection of XX-101 spool", "status": "Started", "equipment_tag": "XX-101", "location": "Area B", "reported_by": "Supervisor A"},
    {"date": date(2026, 8, 30), "discipline": "Civil", "activity_description": "Foundation A1 concrete pouring in progress", "status": "In Progress", "equipment_tag": "A1", "location": "Area C", "reported_by": "Supervisor B"},
    {"date": date(2026, 8, 29), "discipline": "Mechanical", "activity_description": "Pump P-101 installation completed", "status": "Completed", "equipment_tag": "P-101", "location": "Pump House", "reported_by": "Supervisor C"},
    {"date": date(2026, 8, 30), "discipline": "Electrical", "activity_description": "Cable pulling for substation delayed due to rain", "status": "Delayed", "equipment_tag": "SUB-1", "location": "Substation", "reported_by": "Supervisor D"},
]

df = pd.DataFrame(data)
df.to_excel("sample_progress.xlsx", index=False)
print("Sample progress Excel created successfully")