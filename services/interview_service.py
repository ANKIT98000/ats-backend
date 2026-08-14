"""
services/interview_service.py
-----------------------------
Core execution pipeline for generating Interview Questions.
"""
import json
import logging
from config.settings import llm
from schemas.interview_schema import InterviewQuestionRequest
from prompts.interview_prompts import INTERVIEW_PROMPT, interview_parser

logger = logging.getLogger(__name__)

def generate_interview_questions(request_data: InterviewQuestionRequest) -> dict:
    print("🎯 [SERVICE] Initiating Interview Question Generation Pipeline...")
    
    # 1. Filter out blank or inactive stages (toggleButton = False)
    valid_stages = []
    for stage in request_data.interview_stages:
        # Check if name is valid AND toggleButton is True
        if stage.stageName and stage.stageName.strip() != "" and stage.toggleButton is True:
            valid_stages.append({
                "stageName": stage.stageName.strip(), 
                "sequence": stage.sequence,
                "stageDescription": stage.stageDescription # Description AI ko bhejenge
            })
            
    if not valid_stages:
        raise ValueError("No active interview stages provided. Please enable at least one stage.")

    print(f"✅ [SERVICE] Valid Stages Found: {[s['stageName'] for s in valid_stages]}")

    # 2. Format Input Data for AI
    job_details_str = f"Title: {request_data.job_details.title}\nDescription: {request_data.job_details.description}"
    hiring_criteria_str = json.dumps([c.model_dump() for c in request_data.hiringCriteria])
    stages_str = json.dumps(valid_stages)

    # 3. Create the AI Chain
    chain = INTERVIEW_PROMPT | llm | interview_parser

    try:
        print(f"⏳ [AI MODEL] Generating {request_data.questionCount} questions per round. Please wait...")
        
        # 4. Invoke LLM

        ai_response = chain.invoke({
            "num_questions": request_data.questionCount,
            "job_details": job_details_str,
            "hiring_criteria": hiring_criteria_str,
            "stages": stages_str
        })
        
        final_result = {
            "success": True,
            "jobId": request_data.jobId,
            "total_stages_processed": len(valid_stages),
            "rounds": ai_response.model_dump()["rounds"]
        }
        
        print("🎉 [SERVICE] Interview Questions Generated Successfully!\n")
        return final_result

    except Exception as exc:
        print(f"❌ [SERVICE ERROR] Question Generation Failed: {str(exc)}")
        logger.error(f"Interview Question service failure: {str(exc)}")
        raise RuntimeError("Failed to generate interview questions.") from exc