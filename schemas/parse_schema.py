"""
schemas/parse_schema.py
------------------------
Defines Pydantic schemas ONLY for structured resume parsing API.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class EducationDetailSchema(BaseModel):
    degree: Optional[str] = Field("", description="AUTHENTIC ACADEMIC DEGREE ONLY.")
    institution: Optional[str] = Field("", description="College, University, or School name")
    year: Optional[str] = Field("", description="Passing year or academic session")
    score: Optional[str] = Field("", description="CGPA, Percentage, or Grade")

class ProjectDetailSchema(BaseModel):
    title: Optional[str] = Field("", description="Exact Name or title of the project")
    duration: Optional[str] = Field("", description="Duration or timeline of the project")
    description: Optional[str] = Field("", description="Complete detailed summary")
    githubRepo: Optional[str] = Field("", description="EXACT URL LINK to GitHub/GitLab.")
    liveLink: Optional[str] = Field("", description="EXACT URL LINK to live demo.")

class CertificationDetailSchema(BaseModel):
    name: Optional[str] = Field("", description="Name of the certification")
    link: Optional[str] = Field("", description="URL link to the certificate")

class WorkHistoryItemSchema(BaseModel):
    role: Optional[str] = Field("", description="Job Title or Role name")
    company: Optional[str] = Field("", description="Company name")
    duration_str: Optional[str] = Field("", description="Exact date range string")
    is_internship: bool = Field(False, description="TRUE if role contains Intern/Trainee.")
    is_current: bool = Field(False, description="TRUE if duration ends with Present/Now.")
    summary: Optional[str] = Field("", description="Work responsibilities description")

class ExtraDetailsSchema(BaseModel):
    education: List[EducationDetailSchema] = Field(default_factory=list)
    internships: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[CertificationDetailSchema] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    # portfolioLinks: List[str] = Field(default_factory=list)
    projects: List[ProjectDetailSchema] = Field(default_factory=list)

class RawParsedDataSchema(BaseModel):
    fullName: Optional[str] = Field("", description="Full name of candidate")
    email: Optional[str] = Field("", description="Email address")
    phone: Optional[str] = Field("", description="Phone or mobile number")
    skills: List[str] = Field(default_factory=list)
    work_history: List[WorkHistoryItemSchema] = Field(default_factory=list)
    atsscore: Optional[str] = Field("75%", description="General ATS readiness score")
    extraDetails: ExtraDetailsSchema = Field(default_factory=ExtraDetailsSchema)