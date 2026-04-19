from rag.llm import generate, get_model


def extract_form16_data(text):
    client = get_model()

    prompt = f"""
You are a tax document parser.

Extract the following details from the given Form 16 text:

- Employee Name
- PAN
- Employer Name
- Assessment Year
- Total Salary
- Gross Income
- Taxable Income
- Deductions (80C, 80D, etc.)
- TDS (Tax Deducted at Source)

Return STRICT JSON format like:

{{
  "employee_name": "",
  "pan": "",
  "employer_name": "",
  "assessment_year": "",
  "total_salary": "",
  "gross_income": "",
  "taxable_income": "",
  "deductions": {{
    "80C": "",
    "80D": ""
  }},
  "tds": ""
}}

Text:
{text}
"""

    response = generate(client, prompt)

    return response