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
    ("system", """
CRITICAL ATS SCORING RUBRIC & GARBAGE CHECK:
1. GARBAGE/FAKE DOCUMENT CHECK: If the text provided is a recipe, an essay, random letters, or clearly NOT a candidate's resume/CV, you MUST set "atsscore" exactly to "0%" and leave all other lists empty.
2. STRICT HOLISTIC GRADING (For Valid Resumes): Evaluate the resume strictly and assign a score based on these tiers:
   - 20% to 40% (Poor): Missing basic contact info, terrible formatting, or extremely vague 1-line experiences.
   - 41% to 65% (Average): Standard resume. Lists daily duties but lacks quantifiable impact/metrics. Most resumes fall here.
   - 66% to 80% (Good): Well-structured, clear skills section, and includes some metrics/achievements in the experience.
   - 81% to 95% (Exceptional): Contains highly quantifiable achievements (e.g., "Increased revenue by 30%"), links to portfolios/GitHub, and perfect formatting.
3. REALITY CHECK: Be ruthless. Do NOT hand out 80%+ easily. Only the absolute best resumes deserve a high score.

You are a High-Precision Resume Extraction Engine. Extract data with 100% accuracy.

CRITICAL EXTRACTION RULES:
1. STRICT ACADEMIC EDUCATION ONLY: Extract ONLY formal academic degrees (B.Tech, 12th, etc.) from Education sections.
2. PROJECTS (A TO Z): Extract EVERY SINGLE project into 'extraDetails.projects'.
3. GIT REPOS & LINKS: Ensure 'githubRepo' and 'liveLink' contain valid full URL strings.
4. WORK HISTORY: Put every job/internship in 'work_history'. Set 'is_internship' TRUE if it's an intern/trainee role.
5. Ensure no hallucination. Output strictly valid JSON matching the schema below.

{format_instructions}"""),
    ("human", "RESUME TEXT:\n{resume_text}")
]).partial(format_instructions=parse_parser.get_format_instructions())