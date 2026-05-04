#!/bin/bash
# Usage: ./export_results.sh <target_name>
# Example: ./export_results.sh pacemaker_run1

TARGET=$1
FILE="results/audit_results.xlsx"

python3 -c "
import sqlite3, openpyxl, sys, os

target = '$TARGET'
db_path = '/workspaces/seclab-taskflows/.data/repo_context.db'
file = '$FILE'

db = sqlite3.connect(db_path)
c = db.cursor()
c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
tables = [t[0] for t in c.fetchall()]

# Load existing or create new
if os.path.exists(file):
    wb = openpyxl.load_workbook(file)
else:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

ws = wb.create_sheet(title=target[:31])

for table in tables:
    c.execute(f'SELECT * FROM {table}')
    rows = c.fetchall()
    cols = [d[0] for d in c.description]
    ws.append([f'--- {table} ---'])
    ws.append(cols)
    for row in rows:
        ws.append(list(row))
    ws.append([])

wb.save(file)
print(f'Saved {target} to {file}')
db.close()
"
