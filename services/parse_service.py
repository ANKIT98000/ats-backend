"""
services/parse_service.py
--------------------------
Core execution pipeline ONLY for Parse API.
"""
import uuid
import logging
from typing import Dict, Any, Optional
from config.settings import llm
from prompts.parse_prompts import PARSE_PROMPT, parse_parser
from utils.parse_exp_calculator import process_parse_experience

logger = logging.getLogger(__name__)

def execute_parse_pipeline(resume_text: str, resume_id: Optional[str] = None) -> Dict[str, Any]:
    print("🚀 [SERVICE] Initiating AI Resume Parsing Pipeline...")
    
    chain = PARSE_PROMPT | llm | parse_parser
    truncated_text = resume_text[:8000]
    
    try:
        print("⏳ [AI MODEL] Sending text to Qwen LLM. Please wait...")
        raw_parsed = chain.invoke({"resume_text": truncated_text})
        # Pydantic object ko dictionary me convert kiya
        raw_data = raw_parsed.model_dump()
        # 🛡️ THE TRAP DOOR: Check if AI flagged it as a fake/garbage document
        ats_score_str = str(raw_data.get("atsscore", "")).strip()
        if ats_score_str == "0%" or ats_score_str == "0":
            print("🚨 [SERVICE ALERT] Garbage Document Detected! Rejecting...")
            return {
                "resumeId": resume_id or str(uuid.uuid4()),
                "status": "FALSE",
                "message": "Resume was not proper. Please upload a valid document."
            }
        print("🧠 [AI MODEL] Data extracted! Passing to Python Math Engine...")
        accurate_parsed_data = process_parse_experience(raw_parsed.model_dump())
        
        print("✅ [SERVICE] 100% Accurate JSON Generated Successfully!\n")
        return {
            "resumeId": resume_id or str(uuid.uuid4()),
            "status": "SUCCESS",
            "parsedData": accurate_parsed_data
        }
    except Exception as exc:
        print(f"❌ [SERVICE ERROR] LLM Parsing Failed: {str(exc)}")
        logger.error(f"Parse API failure: {str(exc)}")
        raise RuntimeError(f"Failed to parse resume: {str(exc)}") from exc