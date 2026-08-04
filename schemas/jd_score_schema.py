"""
schemas/jd_score_schema.py
---------------------
Defines strict Pydantic schemas for JD Scoring API.
"""
from typing import List
from pydantic import BaseModel, Field

class JDScoreRequest(BaseModel):
    """Request payload schema for Single JD scoring endpoint."""
    resume_data: dict = Field(..., description="Parsed resume JSON data")
    job_description: str = Field(..., description="Target job description text")

class JDScoreResponseSchema(BaseModel):
    """Schema representing the JD evaluation response."""
    jd_score: int = Field(..., description="EXACT JD MATCH PERCENTAGE (0 to 100). Be ruthless. 100 means perfect, 20 means very poor fit.")
    matching_skills: List[str] = Field(..., description="Skills from resume that strictly match the JD.")
    missing_skills: List[str] = Field(..., description="Core skills required in JD but completely missing in Resume.")
    short_verdict: str = Field(..., description="Harsh and honest 2-line verdict explaining exactly WHY the score was given.")