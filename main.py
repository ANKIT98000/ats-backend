"""
main.py
--------
FastAPI REST application exposing Parse API, Single JD Score API, and Bulk JD Score APIs.
"""
import json
import uuid
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status, BackgroundTasks,APIRouter
from fastapi.middleware.cors import CORSMiddleware

# this 2 import for one resume jd_score
# from schemas.jd_score_schema import JDScoreRequest
# from services.jd_score_service import execute_jd_score_pipeline



from utils.parse_extractor import extract_text_for_parsing
from services.parse_service import execute_parse_pipeline
from utils.file_manager import save_uploaded_zip, cleanup_old_folders
from services.bulk_parse_service import process_zip_background,BULK_PARSE_DB

from prompts.parse_prompts import PARSE_PROMPT
from config.settings import llm
from fastapi.responses import FileResponse
import os


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
    print(f" [API HIT] POST /api/v1/parse-resume")
    print(f" Received File: {resume.filename}")
    print("="*50)
    
    try:
        file_content = await resume.read()
        resume_text = extract_text_for_parsing(resume.filename, file_content)
        
        if not resume_text:
            raise HTTPException(status_code=400, detail="Empty document.")

        # Service se data nikalna
        final_response = execute_parse_pipeline(resume_text, resume_id=resume_id)

        #  YAHAN HAI NAYA PRINT LOGIC: Frontend ko jane wala JSON print karna
        print("\n [RESPONSE] Sending this JSON Data to Frontend:")
        print(json.dumps(final_response, indent=4))
        print("="*50 + "\n")

        return final_response

    except Exception as exc:
        print(f" [ERROR] Parse API Failed: {str(exc)}")
        logger.error(f"Endpoint /parse-resume failed: {str(exc)}")
        raise HTTPException(status_code=500, detail="Internal Parse Error.")

# ==========================================
# API 2: JD SCORE ENDPOINT
# ==========================================
# @app.post("/api/v1/score-resume", status_code=status.HTTP_200_OK)
# async def score_resume_endpoint(request: JDScoreRequest):
#     print("\n" + "="*50)
#     print(f" [API HIT] POST /api/v1/score-resume")
#     print("="*50)
    
#     try:
#         evaluation = execute_jd_score_pipeline(
#             resume_data=request.resume_data,
#             job_description=request.job_description
#         )
        
#         final_response = {"success": True, "evaluation": evaluation}
        
#         #  JD Score ka response bhi print karwa diya
#         print("\n [RESPONSE] Sending this JD Score JSON Data to Frontend:")
#         print(json.dumps(final_response, indent=4))
#         print("="*50 + "\n")
        
#         return final_response

#     except Exception as exc:
#         print(f" [ERROR] JD Score API Failed: {str(exc)}")
#         logger.error(f"Endpoint /score-resume failed: {str(exc)}")
#         raise HTTPException(status_code=500, detail="Internal JD Score Error.")



    


# ==========================================
# NAYI API 3: START BULK JOB 
# ==========================================
@app.post("/api/v1/jd-bulk-score/start")
async def start_bulk_score(payload: BulkJDScoreRequest, background_tasks: BackgroundTasks):
    """Frontend is API par apna 100+ candidates wala JSON bhejega."""
    print("\n" + "="*50)
    print(f" [API HIT] POST /api/v1/jd-bulk-score/start")
    
    batch_id = str(uuid.uuid4())
    
    # Database initialization
    BULK_DB[batch_id] = {
        "total": len(payload.applications),  #  Pydantic ka fayda! Seedha array ki length yahan mil gayi
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
    
    print(f" [RESPONSE] Returning Batch ID to frontend immediately: {batch_id}")
    print("="*50 + "\n")
    return response


# ==========================================
# NAYI API 4: GET BULK RESULTS (1-BY-1 CHECK)
# ==========================================
@app.get("/api/v1/bulk-score/results/{batch_id}")
async def get_bulk_results(batch_id: str):
    """Frontend is naye API par Batch ID bhej kar check karega ki kitne process hue."""
    print(f" [API HIT] GET /api/v1/bulk-score/results/{batch_id}")
    
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
    print(f" [API HIT] POST /api/v1/generate-questions")
    print("="*50)
    
    try:
        # Call the new service
        final_response = generate_interview_questions(request)
        
        # Print output in terminal for debugging
        print("\n [RESPONSE] Sending Interview Questions to Frontend:")
        print(json.dumps(final_response, indent=4)[:500] + "\n... (truncated for terminal) ...")
        print("="*50 + "\n")
        
        return final_response

    except Exception as exc:
        print(f" [ERROR] Interview Questions API Failed: {str(exc)}")
        logger.error(f"Endpoint /generate-questions failed: {str(exc)}")
        raise HTTPException(status_code=500, detail=str(exc))
# ==========================================================
# NAYI API 6: parse zip file (BULK RESUME PARSE)
# ==========================================================

# --- ROUTE 1: UPLOAD ZIP ---
@app.post("/api/v1/parse-bulk/upload")
async def upload_bulk_resumes(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    print(f" [API HIT] POST /api/v1/parse-bulk/upload")
    
    # Security: Sirf ZIP allow karo
    if not file.filename.endswith('.zip'):
        return {"success": False, "message": "Only .zip files are allowed!"}

    bulk_id = str(uuid.uuid4())
    file_bytes = await file.read()
    
    # 1. Hard disk me save karo
    job_folder, zip_path = save_uploaded_zip(bulk_id, file_bytes)
    
    # 2. Database (Dictionary) initialize karo
    BULK_PARSE_DB[bulk_id] = {
        "status": "PENDING",
        "total": 0,
        "processed": 0,
        "results": []
    }
    
    # 3. Background me ZIP kholne aur parse karne bhej do
    background_tasks.add_task(process_zip_background, bulk_id, job_folder, zip_path)
    
    # 4. Background me 24 ghante purane kachre ki safai bhi check karwa lo
    background_tasks.add_task(cleanup_old_folders, 24)

    return {
        "success": True,
        "message": "ZIP Uploaded. Processing started.",
        "bulkId": bulk_id
    }

# --- ROUTE 2: GET LIVE STATUS ---
@app.get("/api/v1/parse-bulk/status/{bulk_id}")
async def get_bulk_parse_status(bulk_id: str):
    print(f" [API HIT] GET /api/v1/parse-bulk/status/{bulk_id}")
    
    data = BULK_PARSE_DB.get(bulk_id)
    if not data:
        return {"success": False, "message": "Invalid bulkId or job expired."}
        
    return {
        "success": True,
        "bulkId": bulk_id,
        "data": data
    }
# ============================================================
#  api 7 : only for testing ("Dry Run" ya "Payload Debugging")
# =============================================================
@app.post("/api/v1/parse-debug/ai-payload")
async def debug_ai_payload(file: UploadFile = File(...)):
    print(f" [DEBUG API] Extracting payload & tokens for: {file.filename}")
    
    try:
        # 1. PDF/DOCX se bytes nikalo
        file_bytes = await file.read()
        
        # 2. Raw text nikalo
        resume_text = extract_text_for_parsing(file.filename, file_bytes)
        
        # 3. Text ko truncate karo
        truncated_text = resume_text[:8000]
        
        # 4. Exact prompt generate karo
        exact_prompt_sent_to_ai = PARSE_PROMPT.format(resume_text=truncated_text)
        
        # 5.  TOKEN ESTIMATION LOGIC
        total_chars = len(exact_prompt_sent_to_ai)
        total_words = len(exact_prompt_sent_to_ai.split())
        estimated_tokens = int(total_chars / 4) # Industry standard formula
        
        return {
            "success": True,
            "filename": file.filename,
            "stats": {
                "extracted_length_chars": len(resume_text),
                "truncated_length_chars": len(truncated_text)
            },
            "token_analysis": {
                "total_words_in_prompt": total_words,
                "estimated_tokens": estimated_tokens,
                "warning": "High Token Cost Risk!" if estimated_tokens > 4000 else "Safe Token Limit."
            },
            "raw_extracted_text": resume_text, 
            "exact_prompt_for_ai": exact_prompt_sent_to_ai 
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Debug Failed: {str(e)}"
        }
# ===============================================================
# api B: for testing only (jo responce llm se aa rha h ...)
# ===============================================================
@app.post("/api/v1/parse-debug/ai-response")
async def debug_ai_raw_response(file: UploadFile = File(...)):
    """
    Yeh API strictly debug karne ke liye hai.
    Upload PDF -> AI will read it -> Returns the EXACT RAW STRING the AI outputs.
    """
    print(f"\n [DEBUG API] Fetching RAW AI Response for: {file.filename}")
    
    try:
        # 1. PDF File ke bytes read karo
        file_bytes = await file.read()
        
        # 2. PDF se raw text nikalo
        resume_text = extract_text_for_parsing(file.filename, file_bytes)
        
        # 3. Limit the text (token bachane ke liye)
        truncated_text = resume_text[:8000]
        
        # 4.Sirf Prompt aur LLM ko jod rahe hain (Pydantic Parser hata diya)
        raw_chain = PARSE_PROMPT | llm 
        
        print(" [AI MODEL] Waiting for Model to reply...")
        
        # 5. Model ko call lagayi
        ai_response = raw_chain.invoke({"resume_text": truncated_text})
        
        # 6. AI ne jo lamba string bheja (with markdown ```json tags), wo nikal liya
        raw_output_text = ai_response.content
        
        print(" [DEBUG API] Raw response received successfully!\n")
        
        # 7. Seedha Frontend/Postman ko bhej diya
        return {
            "success": True,
            "filename": file.filename,
            "message": "Yeh AI ka kachha response hai, bina kisi validation ya formatting ke.",
            "raw_ai_response": raw_output_text 
        }
        
    except Exception as e:
        print(f" [DEBUG API ERROR] {str(e)}")
        return {
            "success": False,
            "error_message": str(e)
        }

#=====================================================================
# api for testing (to access temp folder)
#=====================================================================
@app.get("/api/v1/parse-debug/list-temp-files")
async def list_temp_files():
    """
    Yeh API server ke andar ghuskar check karegi ki temp_resumes_data 
    folder mein kaun kaun si files/resumes abhi zinda hain.
    """
    TEMP_DIR = "./temp_resumes_data"
    print(" [DEBUG API] Scanning temporary file system...")
    
    # Agar folder hi nahi bana, toh bata do
    if not os.path.exists(TEMP_DIR):
        return {
            "success": True, 
            "message": "Abhi tak koi ZIP upload nahi hui hai. Folder khali hai."
        }
        
    system_data = {}
    
    # Folder ke andar ghuso
    for folder_name in os.listdir(TEMP_DIR):
        folder_path = os.path.join(TEMP_DIR, folder_name)
        
        # Sirf directories ko check karo (bulk_ids)
        if os.path.isdir(folder_path):
            extracted_dir = os.path.join(folder_path, "extracted")
            resumes = []
            
            # Agar ZIP extract ho chuki hai, toh files ka naam nikal lo
            if os.path.exists(extracted_dir):
                for root, _, files in os.walk(extracted_dir):
                    for file in files:
                        resumes.append(file)
                        
            system_data[folder_name] = {
                "total_resumes_found": len(resumes),
                "resume_names": resumes
            }
            
    return {
        "success": True,
        "active_bulk_batches": len(system_data),
        "server_folder_path": TEMP_DIR,
        "data": system_data
    }