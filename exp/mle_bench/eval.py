#!/usr/bin/env python3
import os
import glob
import shutil
import json
from datetime import datetime

def find_latest_submission_files():
    """
    Find the latest submission.csv files in all mlebench* directories
    """
    outputs_dir = "/data/cyx/openlens-ai/outputs"
    mlebench_dirs = glob.glob(os.path.join(outputs_dir, "mlebench*"))
    
    # Dictionary to store the latest file for each competition ID
    latest_by_competition = {}
    
    for mlebench_dir in mlebench_dirs:
        # Search for all submission.csv files in the directory
        submission_pattern = os.path.join(mlebench_dir, "**/submission.csv")
        found_files = glob.glob(submission_pattern, recursive=True)
        
        for file_path in found_files:
            # Extract competition ID from directory name
            competition_id_list = os.path.basename(mlebench_dir).split('-')[2:-1]
            competition_id = '-'.join(competition_id_list)
            
            # If this competition ID is not in our dictionary or this file is newer, update
            if (competition_id not in latest_by_competition or 
                os.path.getmtime(file_path) > os.path.getmtime(latest_by_competition[competition_id]["submission_path"])):
                latest_by_competition[competition_id] = {
                    "competition_id": competition_id,
                    "submission_path": file_path,
                    "mlebench_dir": mlebench_dir
                }
    
    # Convert dictionary to list
    return list(latest_by_competition.values())

def create_evaluation_directory():
    """
    Create the evaluation directory if it doesn't exist
    """
    eval_dir = "/data/cyx/openlens-ai/outputs/mlebench_eval"
    os.makedirs(eval_dir, exist_ok=True)
    return eval_dir

def copy_files_to_eval_dir(submission_files, eval_dir):
    """
    Copy all CSV and JSON files to the evaluation directory
    """
    # Create a JSONL file for mlebench grade command
    jsonl_path = os.path.join(eval_dir, "submissions.jsonl")
    
    with open(jsonl_path, "w") as jsonl_file:
        for submission in submission_files:
            # Copy the submission CSV file
            submission_filename = f"{submission['competition_id']}_submission.csv"
            dest_path = os.path.join(eval_dir, submission_filename)
            shutil.copy2(submission["submission_path"], dest_path)
            
            # Create a JSON entry for the JSONL file
            json_entry = {
                "competition_id": submission["competition_id"],
                "submission_path": dest_path
            }
            jsonl_file.write(json.dumps(json_entry) + "\n")
    
    return jsonl_path

def main():
    print("Finding latest submission files...")
    submission_files = find_latest_submission_files()
    
    if not submission_files:
        print("No submission files found!")
        return
    
    print(f"Found {len(submission_files)} submission files:")
    for submission in submission_files:
        print(f"  - {submission['competition_id']}: {submission['submission_path']}")
    
    print("\nCreating evaluation directory...")
    eval_dir = create_evaluation_directory()
    
    print("Copying files to evaluation directory...")
    jsonl_path = copy_files_to_eval_dir(submission_files, eval_dir)
    
    print(f"\nAll files copied to {eval_dir}")
    print(f"JSONL file for grading: {jsonl_path}")
    print("\nYou can now run the following command to grade the submissions:")
    print(f"mlebench grade {jsonl_path}")

if __name__ == "__main__":
    main()
