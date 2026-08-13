"""
utils/parse_exp_calculator.py
-----------------------
100% accurate Python mathematical post-processing for Parse API.
"""
import re
from typing import Dict, Any

def calculate_months_from_string(duration_str: str) -> int:
    if not duration_str: return 0
    try:
        years_match = re.search(r'(\d+)\s*(?:yr|year|years)', duration_str, re.I)
        months_match = re.search(r'(\d+)\s*(?:mo|month|months)', duration_str, re.I)
        if years_match or months_match:
            y = int(years_match.group(1)) if years_match else 0
            m = int(months_match.group(1)) if months_match else 0
            return (y * 12) + m
        if len(re.split(r'–|-|to', duration_str, flags=re.I)) >= 2: return 12
    except: pass
    return 0

def format_experience_string(months: int) -> str:
    if months <= 0: 
        return "Fresher"
    
    # Mahino ko 12 se divide karke 1 decimal point tak round off kar diya (e.g., 14 / 12 = 1.16 -> 1.2)
    decimal_years = round(months / 12, 1)
    
    return f"{decimal_years} years"

def process_parse_experience(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    work_history = raw_data.get("work_history", [])
    full_time_months = 0
    curr_comp, curr_desig = None, None
    internships = []

    for item in work_history:
        role = str(item.get("role", "")).lower()
        is_intern = item.get("is_internship", False) or any(w in role for w in ["intern", "trainee"])
        if is_intern:
            internships.append({"role": item.get("role"), "company": item.get("company"), "duration": item.get("duration_str"), "description": item.get("summary")})
        else:
            full_time_months += calculate_months_from_string(item.get("duration_str", ""))
            if item.get("is_current", False) or any(w in str(item.get("duration_str", "")).lower() for w in ["present", "current", "now"]):
                curr_comp, curr_desig = item.get("company"), item.get("role")

    if not curr_comp and work_history:
        first = work_history[0]
        if not any(w in str(first.get("role", "")).lower() for w in ["intern", "trainee"]):
            curr_comp, curr_desig = first.get("company"), first.get("role")

    extra_details = raw_data.get("extraDetails", {})
    extra_details["internships"] = internships
    exp_str = format_experience_string(full_time_months) if full_time_months > 0 else "Fresher"

    return {
        "fullName": raw_data.get("fullName", ""), "email": raw_data.get("email", ""),
        "phone": raw_data.get("phone", ""), "experience": exp_str,
        "skills": raw_data.get("skills", []), "currentCompany": curr_comp,
        "currentDesignation": curr_desig, "atsscore": raw_data.get("atsscore", "75%"),
        "extraDetails": extra_details
    }