"""
main.py
--------
FastAPI REST application exposing Parse API, Single JD Score API, and Bulk JD Score APIs.
"""
import json
import uuid
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# this 2 import for one resume jd_score
# from schemas.jd_score_schema import JDScoreRequest
# from services.jd_score_service import execute_jd_score_pipeline



from utils.parse_extractor import extract_text_for_parsing
from services.parse_service import execute_parse_pipeline


from services.jd_bulk_manager_service import BULK_DB, process_candidates_one_by_one
from schemas.jd_score_schema import BulkJDScoreRequest

from schemas.interview_schema import InterviewQuestionRequest
from services.interview_service import generate_interview_questions

# from config.settings import FRONTEND_URL

logger = logging.getLogger(__name__)

app = FastAPI(title="Resume Parse & Bulk JD Score API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=[FRONTEND_URL],
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "healthy"}

# ==========================================
# API 1: PARSE ENDPOINT
# ==========================================
@app.post("/api/v1/parse-resume", status_code=status.HTTP_200_OK)
async def parse_resume_endpoint(
    resume: UploadFile = File(...),
    resume_id: Optional[str] = Form(default=None)
):
    print("\n" + "="*50)
    print(f"🌐 [API HIT] POST /api/v1/parse-resume")
    print(f"📁 Received File: {resume.filename}")
    print("="*50)
    
    try:
        file_content = await resume.read()
        resume_text = extract_text_for_parsing(resume.filename, file_content)
        
        if not resume_text:
            raise HTTPException(status_code=400, detail="Empty document.")

        # Service se data nikalna
        final_response = execute_parse_pipeline(resume_text, resume_id=resume_id)

        # 🚀 YAHAN HAI NAYA PRINT LOGIC: Frontend ko jane wala JSON print karna
        print("\n📤 [RESPONSE] Sending this JSON Data to Frontend:")
        print(json.dumps(final_response, indent=4))
        print("="*50 + "\n")

        return final_response

    except Exception as exc:
        print(f"❌ [ERROR] Parse API Failed: {str(exc)}")
        logger.error(f"Endpoint /parse-resume failed: {str(exc)}")
        raise HTTPException(status_code=500, detail="Internal Parse Error.")

# ==========================================
# API 2: JD SCORE ENDPOINT
# ==========================================
# @app.post("/api/v1/score-resume", status_code=status.HTTP_200_OK)
# async def score_resume_endpoint(request: JDScoreRequest):
#     print("\n" + "="*50)
#     print(f"🌐 [API HIT] POST /api/v1/score-resume")
#     print("="*50)
    
#     try:
#         evaluation = execute_jd_score_pipeline(
#             resume_data=request.resume_data,
#             job_description=request.job_description
#         )
        
#         final_response = {"success": True, "evaluation": evaluation}
        
#         # 🚀 JD Score ka response bhi print karwa diya
#         print("\n📤 [RESPONSE] Sending this JD Score JSON Data to Frontend:")
#         print(json.dumps(final_response, indent=4))
#         print("="*50 + "\n")
        
#         return final_response

#     except Exception as exc:
#         print(f"❌ [ERROR] JD Score API Failed: {str(exc)}")
#         logger.error(f"Endpoint /score-resume failed: {str(exc)}")
#         raise HTTPException(status_code=500, detail="Internal JD Score Error.")



    


# ==========================================
# NAYI API 3: START BULK JOB 
# ==========================================
@app.post("/api/v1/jd-bulk-score/start")
async def start_bulk_score(payload: BulkJDScoreRequest, background_tasks: BackgroundTasks):
    """Frontend is API par apna 100+ candidates wala JSON bhejega."""
    print("\n" + "="*50)
    print(f"🚀 [API HIT] POST /api/v1/jd-bulk-score/start")
    
    batch_id = str(uuid.uuid4())
    
    # Database initialization
    BULK_DB[batch_id] = {
        "total": len(payload.applications),  # 🔥 Pydantic ka fayda! Seedha array ki length yahan mil gayi
        "processed": 0,
        "is_completed": False,
        "results": []
    }

    # Background processing chalu kar di! 
    # (payload.model_dump() isliye lagaya taaki service ko wapas Dictionary format mile)
    background_tasks.add_task(process_candidates_one_by_one, batch_id, payload.model_dump())

    response = {
        "success": True,
        "message": "Bulk processing started in the background. Use the batchId to check status.",
        "batchId": batch_id
    }
    
    print(f"📤 [RESPONSE] Returning Batch ID to frontend immediately: {batch_id}")
    print("="*50 + "\n")
    return response


# ==========================================
# NAYI API 4: GET BULK RESULTS (1-BY-1 CHECK)
# ==========================================
@app.get("/api/v1/bulk-score/results/{batch_id}")
async def get_bulk_results(batch_id: str):
    """Frontend is naye API par Batch ID bhej kar check karega ki kitne process hue."""
    print(f"📡 [API HIT] GET /api/v1/bulk-score/results/{batch_id}")
    
    if batch_id not in BULK_DB:
        raise HTTPException(status_code=404, detail="Batch ID not found or expired.")
    
    # Return the live status!
    return BULK_DB[batch_id]



# ==========================================
# NAYI API 5: GENERATE INTERVIEW QUESTIONS
# ==========================================
@app.post("/api/v1/generate-questions", status_code=status.HTTP_200_OK)
async def generate_questions_endpoint(request: InterviewQuestionRequest):
    print("\n" + "="*50)
    print(f"🌐 [API HIT] POST /api/v1/generate-questions")
    print("="*50)
    
    try:
        # Call the new service
        final_response = generate_interview_questions(request)
        
        # Print output in terminal for debugging
        print("\n📤 [RESPONSE] Sending Interview Questions to Frontend:")
        print(json.dumps(final_response, indent=4)[:500] + "\n... (truncated for terminal) ...")
        print("="*50 + "\n")
        
        return final_response

    except Exception as exc:
        print(f"❌ [ERROR] Interview Questions API Failed: {str(exc)}")
        logger.error(f"Endpoint /generate-questions failed: {str(exc)}")
        raise HTTPException(status_code=500, detail=str(exc))