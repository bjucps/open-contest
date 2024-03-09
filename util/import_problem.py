#!/usr/bin/python3

import json
import os
import os.path
import sys
import shutil

def copy_file(filename):
    if not os.path.isfile(os.path.join(source_dir, output_folder, filename)):
        print(f'Input test file {filename} has no corresponding output file... aborting.')
        sys.exit(1)
    
    shutil.copyfile(os.path.join(source_dir, input_folder, filename),
                     os.path.join(problem_dir_db, 'input', f'in{num_tests}.txt'))

    shutil.copyfile(os.path.join(source_dir, output_folder, filename),
                     os.path.join(problem_dir_db, 'output', f'out{num_tests}.txt'))


if len(sys.argv) != 7:
    print('Usage: import_problem.py <db-dir> <source-problem-dir> <input-data-folder> <output-data-folder> <sample-prefix> <judge-prefix>')
    print('\nExample: import_problem.py db 2024/Advising input output sample judge')
    sys.exit(1)

db_dir = sys.argv[1]
source_dir = sys.argv[2]
input_folder = sys.argv[3]
output_folder = sys.argv[4]
sample_prefix = sys.argv[5]
judge_prefix = sys.argv[6]

if not (os.path.isdir(source_dir) and os.path.isdir(os.path.join(source_dir, input_folder)) and os.path.isdir(os.path.join(source_dir, output_folder))):
    print("Cannot find files to import")
    sys.exit(1)

print(f"Importing {source_dir}...")
problem_title = os.path.basename(source_dir)
problem_dir_db = os.path.join(db_dir, "problems", problem_title)
problem_file = os.path.join(problem_dir_db, "problem.json")
if os.path.isdir(problem_dir_db):
    print("Updating existing problem...")
    with open(problem_file) as prob_file:
        problem = json.load(prob_file)
else:
    os.makedirs(problem_dir_db)
    os.makedirs(os.path.join(problem_dir_db, "input"))
    os.makedirs(os.path.join(problem_dir_db, "output"))
    problem = {
        'id': f"prob-{problem_title}",
        'title': problem_title,
        "description": "",
        "statement": "",
        "input": "",
        "output": "",
        "constraints": "",
        "samples": 0,
        "tests": 0,
        "timelimit": "5"
    }

num_samples = 0
num_tests = 0

for filename in os.listdir(os.path.join(source_dir, input_folder)):
    if filename.startswith(sample_prefix):
        copy_file(filename)
        num_samples += 1
        num_tests += 1

for filename in os.listdir(os.path.join(source_dir, input_folder)):
    if filename.startswith(judge_prefix):
        copy_file(filename)
        num_tests += 1

if num_samples == 0:
    print('Warning: No sample test data found')

if num_tests == num_samples:
    print('Warning: No hidden judge data found')

problem['samples'] = num_samples
problem['tests'] = num_tests
with open(problem_file, "w") as prob_file:
    prob_file.write(json.dumps(problem, indent=2))

