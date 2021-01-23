#!/usr/bin/python3

import sys
import json
import os.path

if len(sys.argv) != 2:
    print("Usage: python3 export_users.py <db-path>")
    sys.exit(1)

db_path = sys.argv[1]  

with open(os.path.join(db_path, 'users.json')) as f:
    users = json.loads(f.read())

for user in users:
    print(f"{user['username']},{user['password']}")
