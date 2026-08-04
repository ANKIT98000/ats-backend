"""
services/jd_score_service.py
-----------------------
Core execution pipeline ONLY for JD Scoring API.
"""
import json
import logging
from typing import Dict, Any
from config.settings import llm
from prompts.jd_score_prompts import JD_SCORE_PROMPT, jd_score_parser

logger = logging.getLogger(__name__)

def execute_jd_score_pipeline(resume_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    print("🎯 [SERVICE] Initiating STRICT JD Matching Pipeline...")
    chain = JD_SCORE_PROMPT | llm | jd_score_parser

    try:
        print("⏳ [AI MODEL] Comparing Candidate with JD via Qwen LLM. Please wait...")
        score_result = chain.invoke({
            "resume_data": json.dumps(resume_data),
            "job_description": job_description[:2000]
        })
        
        # Yahan update kiya h: score_result.jd_score
        print(f"✅ [SERVICE] JD Score Generated Successfully: {score_result.jd_score}% Match\n")
        return score_result.model_dump()
    except Exception as exc:
        print(f"❌ [SERVICE ERROR] JD Score Evaluation Failed: {str(exc)}")
        logger.error(f"JD Score service failure: {str(exc)}")
        raise RuntimeError("Failed to generate JD score.") from exc