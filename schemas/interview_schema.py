"""
schemas/interview_schema.py
---------------------------
Defines strict Pydantic schemas for the Interview Question Generation API.
"""
from typing import List, Optional , Literal
from pydantic import BaseModel, Field

# ---- REQUEST SCHEMAS (Frontend se aane wala data) ----
class JobDetails(BaseModel):
    title: str
    description: str

class InterviewStage(BaseModel):
    stageName: str
    sequence: int

class HiringCriteria(BaseModel):
    criteriaName: str
    weight: int

class InterviewQuestionRequest(BaseModel):
    jobId: str = Field(..., description="Unique job identifier")
    questionCount: int = Field(default=10, description="Total questions needed per round")
    job_details: JobDetails
    interview_stages: List[InterviewStage]
    hiringCriteria: List[HiringCriteria]

# ---- RESPONSE SCHEMAS (AI se aane wala format) ----
class QuestionDetail(BaseModel):
    question_number: int
    question_text: str = Field(..., description="The interview question text")
    expected_answer_points: List[str] = Field(..., description="3-4 strict bullet points for the expected answer")
    difficulty: Literal["Easy", "Medium", "Hard"] = Field(..., description="Difficulty scaled based on JD experience requirement. e.g. A 5-year experienced candidate's 'Easy' is tougher than a Fresher's 'Easy'.")
    category: Literal["Technical", "Functional", "Behavioral", "Leadership"] = Field(..., description="The category of the question.")

class RoundDetail(BaseModel):
    stageName: str
    sequence: int
    questions: List[QuestionDetail]

class InterviewLLMResponse(BaseModel):
    """The complete structure we want the AI to return."""
    rounds: List[RoundDetail]