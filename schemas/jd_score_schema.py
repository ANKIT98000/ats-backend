"""
schemas/jd_score_schema.py
---------------------
Defines strict Pydantic schemas for JD Scoring API.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# only for 1 resume.

# class JDScoreRequest(BaseModel):
#     """Request payload schema for Single JD scoring endpoint."""
#     resume_data: dict = Field(..., description="Parsed resume JSON data")
#     job_description: str = Field(..., description="Target job description text")


# ---- REQUEST SCHEMAS (Frontend se aane wala data) ----

# 1. Hiring Criteria (Strict weight aur name)

class HiringCriteria(BaseModel):
    criteriaName: str = Field(..., min_length=2, description="Name of the criteria")
    weight: int = Field(..., description="Weightage of the criteria")

# 2. Job Details (Title aur Description required hain)

class JobDetails(BaseModel):
    title: str = Field(..., min_length=2, description="Job title")
    description: str = Field(..., min_length=10, description="Job description (Must not be empty)")
    hiringCriteria: List[HiringCriteria] = Field(default_factory=list, description="Criteria for scoring")

# 3. Application Data (Har resume ka structure)

class ApplicationData(BaseModel):
    applicationId: str = Field(..., description="Unique ID for the application")
    fullName: str = Field(..., description="Candidate's full name")
    skills: List[str] = Field(default_factory=list, description="Array of candidate skills")
    experience: str = Field(..., description="Experience string, e.g., '1.2 years'")
    currentDesignation: Optional[str] = Field(default="", description="Current job role")
    currentCompany: Optional[str] = Field(default="", description="Current company")
    extraDetails: Dict[str, Any] = Field(default_factory=dict, description="Any extra parsed data")


# 4. Main Request Model (Bulk API ka Bouncer)
class BulkJDScoreRequest(BaseModel):
    job_details: JobDetails = Field(..., description="Job details and criteria")
    # min_length=1 lagaya hai taaki array khali na ho (kam se kam 1 application aani chahiye)
    applications: List[ApplicationData] = Field(..., min_length=1, description="List of applications to process")

# ---- RESPONSE SCHEMAS (AI se aane wala format) ----


class JDScoreResponseSchema(BaseModel):
    """Schema representing the JD evaluation response."""
    jd_score: int = Field(..., description="EXACT JD MATCH PERCENTAGE (0 to 100). Be ruthless. 100 means perfect, 20 means very poor fit.")
    matching_skills: List[str] = Field(..., description="Skills from resume that strictly match the JD.")
    missing_skills: List[str] = Field(..., description="Core skills required in JD but completely missing in Resume.")
    short_verdict: str = Field(..., description="Harsh and honest 2-line verdict explaining exactly WHY the score was given.")