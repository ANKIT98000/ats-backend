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

logger = logging.getLogger(__name__)# File ke naam se error logger banaya

# Temporary In-Memory Database (Job track karne ke liye)
BULK_DB = {}

async def process_candidates_one_by_one(batch_id: str, payload: Dict[str, Any]):
    """Background task jo 1-1 karke candidates ko process karega."""
    print(f"\n⚙️ [BULK PROCESS] Background Job Started for Batch: {batch_id}")
    
    # 1. Extract Job Details dynamically
    job_details = payload.get("job_details", {})
    # Payload se 'job_details' wala object nikala. Agar na ho toh empty {} le liya
    jd_text = f"Title: {job_details.get('title', '')}\n" \
              f"Description: {job_details.get('description', '')}\n" \
              f"Criteria: {json.dumps(job_details.get('hiringCriteria', []))}"
    # AI ko bhejane ke liye Title, Description aur Criteria ko jod kar ek single lamba Paragraph (String) bana diya

    # 2. Extract Candidates from flexible JSON structure
    candidates = [] # Ek khali list banayi jisme saare candidates daalenge.
    for key, value in payload.items():
        if key == "job_details":
            continue
        if isinstance(value, list):
            candidates.extend(value)
            # Agar frontend ne array ["cand1", "cand2"] bheja hai, toh usko hamari list me jod do.
        elif isinstance(value, dict):
            candidates.append(value)
            # Agar dictionary format me bheja hai, toh usko list me append kar do.

    total_candidates = len(candidates)
    print(f"📦 [BULK PROCESS] Total Candidates Found: {total_candidates}")

    # Update DB with total count
    BULK_DB[batch_id]["total"] = total_candidates

    # 3. Process 1-by-1
    for index, cand in enumerate(candidates, start=1):
        # enumerate hume candidate ke sath uska number (1, 2, 3...) bhi de deta hai
        cand_id = cand.get("resumeId", str(uuid.uuid4()))
        # Agar resumeId na ho, toh khud ka ek naya (uuid) bana lo.
        cand_name = cand.get("fullName", f"Unknown_{index}")
        # Candidate ka naam nikalo print karne ke liye
        
        print(f"\n🔄 [BULK PROCESS] Processing {index}/{total_candidates} -> Candidate: {cand_name}")
        
        try:
            # Run the heavy AI task in a separate thread so the server doesn't freeze
            score_result = await asyncio.to_thread(execute_jd_score_pipeline, cand, jd_text)
            
            # Save success result
            BULK_DB[batch_id]["results"].append({
                "resumeId": cand_id,
                "fullName": cand_name,
                "status": "SUCCESS",
                "evaluation": score_result
            })
            print(f"✅ [BULK PROCESS] Finished {cand_name} -> Score: {score_result.get('ats_score')}/100")
            
        except Exception as e:
            # Save error result if candidate fails
            BULK_DB[batch_id]["results"].append({
                "resumeId": cand_id,
                "fullName": cand_name,
                "status": "ERROR",
                "message": str(e)
            })# Agar API error aa gaya, toh server crash nahi hoga. Wo us error ko list me save kar dega taaki frontend ko pata chal sake.
            print(f"❌ [BULK PROCESS] Failed for {cand_name} -> Error: {str(e)}")
        
        # Increase processed count and wait 1 sec to protect HuggingFace API Limits
        BULK_DB[batch_id]["processed"] += 1
        await asyncio.sleep(1)

    # Job is finally complete!
    BULK_DB[batch_id]["is_completed"] = True
    print(f"\n🎉 [BULK PROCESS] Batch {batch_id} Processing 100% Completed!\n")