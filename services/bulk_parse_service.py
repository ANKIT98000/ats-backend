"""
services/bulk_parse_service.py
-------------------------------
Handles ZIP extraction and bulk resume parsing via AI.
"""
import zipfile
import os
import asyncio
from typing import Dict, Any

#  Tumhara Asli Extractor Import
from utils.parse_extractor import extract_text_for_parsing
from services.parse_service import execute_parse_pipeline

# In-Memory DB for Tracking Bulk Parse Jobs
BULK_PARSE_DB: Dict[str, Any] = {}

async def process_zip_background(bulk_id: str, job_folder: str, zip_path: str):
    print(f"\n [BULK PARSE] Job Started for: {bulk_id}")
    
    # 1. Extract ZIP file
    extract_folder = os.path.join(job_folder, "extracted")
    os.makedirs(extract_folder, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_folder)
    except Exception as e:
        BULK_PARSE_DB[bulk_id]["status"] = "FAILED"
        BULK_PARSE_DB[bulk_id]["message"] = f"Invalid ZIP file: {str(e)}"
        return

    # 2. Get all PDF/Doc files
    resume_files = []
    for root, _, files in os.walk(extract_folder):
        for file in files:
            # Sirf resumes wali extensions allow karenge
            if file.lower().endswith(('.pdf', '.docx', '.doc', '.txt')):
                resume_files.append(os.path.join(root, file))

    total_files = len(resume_files)
    BULK_PARSE_DB[bulk_id]["total"] = total_files
    print(f" [BULK PARSE] Found {total_files} resumes inside ZIP.")

    if total_files == 0:
        BULK_PARSE_DB[bulk_id]["status"] = "COMPLETED"
        BULK_PARSE_DB[bulk_id]["message"] = "No valid resumes found in ZIP."
        return

    BULK_PARSE_DB[bulk_id]["status"] = "PROCESSING"

    # 3. Parse One by One
    for index, file_path in enumerate(resume_files, start=1):
        file_name = os.path.basename(file_path)
        print(f"\n Processing {index}/{total_files}: {file_name}")
        
        try:
            #  NAYA LOGIC: Disk se file ko bytes me read karo
            with open(file_path, "rb") as f:
                file_bytes = f.read()
                
            # Tumhara apna function call kiya
            resume_text = extract_text_for_parsing(file_name, file_bytes) 
            
            # AI Parser ko bhejo (Separate thread me taaki server block na ho)
            parsed_result = await asyncio.to_thread(execute_parse_pipeline, resume_text)
            
            # Success hone par DB me entry daal do
            BULK_PARSE_DB[bulk_id]["results"].append({
                "fileName": file_name,
                "status": "SUCCESS",
                "data": parsed_result
            })
            print(f" [BULK PARSE] Successfully parsed: {file_name}")
            
        except Exception as e:
            # Error aane par server crash nahi hoga, fail status save hoga
            BULK_PARSE_DB[bulk_id]["results"].append({
                "fileName": file_name,
                "status": "ERROR",
                "message": str(e)
            })
            print(f" [BULK PARSE] Failed for {file_name}: {str(e)}")
            
        # Processed count badhao aur 1 second ka break lo (Rate Limit protect karne ke liye)
        BULK_PARSE_DB[bulk_id]["processed"] += 1
        await asyncio.sleep(1) 

    # Job is finally complete!
    BULK_PARSE_DB[bulk_id]["status"] = "COMPLETED"
    print(f" [BULK PARSE] Batch {bulk_id} 100% Completed!\n")