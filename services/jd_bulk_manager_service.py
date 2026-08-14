"""
services/bulk_service.py
-------------------------
Handles bulk processing of 100+ candidates in the background.
Processes them 1-by-1 and stores the results securely.
"""
import uuid
import json
import asyncio
import logging
from typing import Dict, Any
from services.jd_score_service import execute_jd_score_pipeline

logger = logging.getLogger(__name__) # File ke naam se error logger banaya

# Temporary In-Memory Database (Job track karne ke liye)
BULK_DB = {}

async def process_candidates_one_by_one(batch_id: str, payload: Dict[str, Any]):
    """Background task jo 1-1 karke applications ko process karega."""
    print(f"\n [BULK PROCESS] Background Job Started for Batch: {batch_id}")
    
    # 1. Extract Job Details dynamically
    job_details = payload.get("job_details", {})
    
    # Hiring Criteria ko AI ke padhne layak string me convert kiya
    criteria_list = job_details.get("hiringCriteria", [])
    criteria_strings = [f"{c.get('criteriaName')} (Weight: {c.get('weight')})" for c in criteria_list if isinstance(c, dict)]
    criteria_text = ", ".join(criteria_strings) if criteria_strings else "None"

    jd_text = f"Title: {job_details.get('title', '')}\n" \
              f"Description: {job_details.get('description', '')}\n" \
              f"Criteria: {criteria_text}"

    # 2. Extract Applications directly (Naye strict schema ke hisaab se)
    applications = payload.get("applications", [])
    
    total_applications = len(applications)
    print(f" [BULK PROCESS] Total Applications Found: {total_applications}")

    # Update DB with total count
    BULK_DB[batch_id]["total"] = total_applications

    # 3. Process 1-by-1
    for index, app in enumerate(applications, start=1):
        # Naye schema me resumeId ki jagah applicationId hai
        app_id = app.get("applicationId", str(uuid.uuid4()))
        app_name = app.get("fullName", f"Unknown_{index}")
        
        print(f"\n[BULK PROCESS] Processing {index}/{total_applications} -> Candidate: {app_name}")
        
        try:
            # Run the heavy AI task in a separate thread so the server doesn't freeze
            score_result = await asyncio.to_thread(execute_jd_score_pipeline, app, jd_text)
            
            # Save success result
            BULK_DB[batch_id]["results"].append({
                "applicationId": app_id, # Updated key
                "fullName": app_name,
                "status": "SUCCESS",
                "evaluation": score_result
            })
            
            # AI ab actual exact match score de raha hoga jo ATS rubric par based hai
            print(f" [BULK PROCESS] Finished {app_name} -> Score: {score_result.get('ats_score', 'N/A')}")
            
        except Exception as e:
            # Save error result if candidate fails
            BULK_DB[batch_id]["results"].append({
                "applicationId": app_id, # Updated key
                "fullName": app_name,
                "status": "ERROR",
                "message": str(e)
            })
            print(f"[BULK PROCESS] Failed for {app_name} -> Error: {str(e)}")
        
        # Increase processed count and wait 1 sec to protect HuggingFace API Limits
        BULK_DB[batch_id]["processed"] += 1
        await asyncio.sleep(1)

    # Job is finally complete!
    BULK_DB[batch_id]["is_completed"] = True
    print(f"\n [BULK PROCESS] Batch {batch_id} Processing 100% Completed!\n")