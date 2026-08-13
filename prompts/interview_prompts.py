"""
prompts/interview_prompts.py
----------------------------
LangChain prompts for generating dynamic Interview Questions.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from schemas.interview_schema import InterviewLLMResponse

interview_parser = PydanticOutputParser(pydantic_object=InterviewLLMResponse)

INTERVIEW_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an Expert Technical and HR Recruiter Panel.
Your task is to generate highly relevant interview questions based on the provided Job Description, Hiring Criteria, and specific Interview Rounds.

RULES:
1. You must generate EXACTLY {num_questions} questions for EACH valid interview stage provided.
2. The questions must be perfectly aligned with the target stage (e.g., Technical questions for Technical rounds, HR questions for HR rounds,etc).
3. Do not provide paragraph answers. You MUST provide 3 to 4 strict bullet points under 'expected_answer_points' that an interviewer should look for in a candidate's response.
4. Align the difficulty level with the Job Description requirements and with exp .

RULES:
1. You must generate EXACTLY {num_questions} questions for EACH valid interview stage provided.
2. The questions must be perfectly aligned with the target stage.
3. Do not provide paragraph answers. You MUST provide 3 to 4 strict bullet points under 'expected_answer_points'.
4. CRITICAL: Classify the 'difficulty' (Easy, Medium, Hard). The difficulty MUST be relative to the experience requested in the Job Description. (e.g., an 'Easy' question for a 5-year Senior role should be highly technical, not a basic fresher question).
5. CRITICAL: Classify the 'category' strictly as either "Technical", "Functional", "Behavioral", or "Leadership".
Return strictly valid JSON matching the schema without markdown code fences.

{format_instructions}"""),
    ("human", """
Job Details:
{job_details}

Hiring Criteria (Focus Areas):
{hiring_criteria}

Required Interview Stages:
{stages}

Generate exactly {num_questions} questions for each of the stages listed above.
""")
]).partial(format_instructions=interview_parser.get_format_instructions())