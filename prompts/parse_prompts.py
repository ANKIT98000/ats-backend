"""
prompts/parse_prompts.py
-------------------------
LangChain prompts and parsers ONLY for Resume Parsing API.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from schemas.parse_schema import RawParsedDataSchema

parse_parser = PydanticOutputParser(pydantic_object=RawParsedDataSchema)

PARSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a High-Precision Resume Extraction Engine. Extract data with 100% accuracy.

CRITICAL EXTRACTION RULES:
1. STRICT ACADEMIC EDUCATION ONLY: Extract ONLY formal academic degrees (B.Tech, 12th, etc.) from Education sections.
2. PROJECTS (A TO Z): Extract EVERY SINGLE project into 'extraDetails.projects'.
3. GIT REPOS & LINKS: Ensure 'githubRepo' and 'liveLink' contain valid full URL strings.
4. WORK HISTORY: Put every job/internship in 'work_history'. Set 'is_internship' TRUE if it's an intern/trainee role.
5. Ensure no hallucination. Output strictly valid JSON matching the schema below.

{format_instructions}"""),
    ("human", "RESUME TEXT:\n{resume_text}")
]).partial(format_instructions=parse_parser.get_format_instructions())