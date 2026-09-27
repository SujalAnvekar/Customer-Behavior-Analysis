import os
import json
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from database import execute_query


# =========================================================
# LOAD ENVIRONMENT
# =========================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=api_key)


# =========================================================
# GEMINI MODEL FALLBACK
# =========================================================

AI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite"
]


# =========================================================
# DATABASE SCHEMA
# =========================================================

SCHEMA = """
SQL Server database: Customer_behavior

Table:
customer_table

Columns:

customer_id
age
gender
item_purchased
category
purchase_amt
location
size
color
season
review_rating
subscription_status
shipping_type
discount_applied
previous_purchases
payment_method
frequency_of_purchases
age_group
purchase_freq_days
"""


# =========================================================
# DIAGNOSTIC QUESTION DETECTION
# =========================================================

diagnostic_words = [
    "why",
    "reason",
    "underperform",
    "underperforming",
    "performing worse",
    "performing better",
    "factor",
    "factors",
    "affect",
    "affecting",
    "improve",
    "increase",
    "decrease",
    "recommend",
    "recommendation",
    "problem",
    "issue",
    "decline",
    "poor performance"
]


def is_diagnostic_question(question):

    question_lower = question.lower()

    for word in diagnostic_words:

        if word in question_lower:
            return True

    return False


# =========================================================
# SQL VALIDATION
# =========================================================

def validate_sql(sql):

    if not sql:
        raise ValueError("Empty SQL query generated.")

    sql = sql.strip()

    sql = sql.replace("```sql", "")
    sql = sql.replace("```", "")
    sql = sql.strip()

    if not sql.lower().startswith("select"):

        raise ValueError(
            "Generated query is not a SELECT statement."
        )

    forbidden_keywords = [
        "insert ",
        "update ",
        "delete ",
        "drop ",
        "alter ",
        "truncate ",
        "create ",
        "merge ",
        "exec ",
        "execute ",
        "grant ",
        "revoke "
    ]

    sql_lower = sql.lower()

    for keyword in forbidden_keywords:

        if keyword in sql_lower:

            raise ValueError(
                f"Unsafe SQL query detected: {keyword.strip()}"
            )

    if "customer_table" not in sql_lower:

        raise ValueError(
            "Query must use customer_table."
        )

    return sql


# =========================================================
# GEMINI RESPONSE
# =========================================================

def generate_ai_response(prompt, config=None):

    for model in AI_MODELS:

        try:

            print(f"\nTrying model: {model}")

            start_time = time.time()

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config
            )

            elapsed_time = time.time() - start_time

            if response and response.text:

                print(
                    f"Gemini response received "
                    f"in {elapsed_time:.2f} seconds."
                )

                return response

            print(
                f"{model} returned an empty response."
            )

        except Exception as e:

            error_text = str(e)

            print("\n===== GEMINI ERROR =====")
            print("Model:", model)
            print("Error type:", type(e).__name__)
            print("Error:", error_text)
            print("========================\n")

            if (
                "RESOURCE_EXHAUSTED" in error_text
                and "PerDay" in error_text
            ):

                print(
                    f"Daily quota exhausted for {model}."
                )

                continue

            if (
                "429" in error_text
                and "PerDay" not in error_text
            ):

                print("Temporary rate limit detected.")

                continue

            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "500" in error_text
            ):

                print("Temporary Gemini server error.")

                continue

            print(
                f"{model} failed. Trying next model..."
            )

    print(
        "\nAll Gemini models are currently unavailable."
    )

    return None


# =========================================================
# FORMAT SQL RESULT
# =========================================================

def format_result(result):

    if not result:
        return "No data returned from SQL query."

    columns = result["columns"]
    rows = result["rows"]

    formatted = []

    for row in rows:

        row_dict = {}

        for i, column in enumerate(columns):

            row_dict[column] = row[i]

        formatted.append(row_dict)

    return json.dumps(
        formatted,
        default=str,
        indent=2
    )


# =========================================================
# GENERATE NORMAL SQL
# =========================================================

def generate_normal_query(question):

    prompt = f"""
You are an expert SQL Server data analyst.

Convert the user's business question into ONE
accurate SQL Server SELECT query.

DATABASE SCHEMA:

{SCHEMA}

USER QUESTION:

{question}

RULES:

1. Use only customer_table.
2. Use only existing columns.
3. Use SQL Server syntax.
4. Only SELECT queries.
5. Do not modify the database.
6. Do not invent data.
7. Do not invent columns.
8. Return ONLY SQL.
9. Do not use markdown.
10. Do not provide explanations.
"""

    config = types.GenerateContentConfig(
        temperature=0
    )

    response = generate_ai_response(
        prompt,
        config=config
    )

    if not response:
        return None

    try:

        return validate_sql(
            response.text.strip()
        )

    except Exception as e:

        print("SQL validation error:", e)

        return None


# =========================================================
# GENERATE DIAGNOSTIC PLAN
# =========================================================

def generate_diagnostic_plan(question):

    prompt = f"""
You are a senior business data analyst.

Investigate the user's question using actual SQL Server data.

DATABASE SCHEMA:

{SCHEMA}

USER QUESTION:

{question}

The question may require multiple SQL analyses.

Create a diagnostic plan containing relevant
SQL Server SELECT queries.

Possible dimensions:

- category
- location
- customer segment
- subscription status
- discount status
- age group
- gender
- shipping type
- payment method
- season
- purchase frequency
- review rating
- purchase amount
- item purchased

Customer segment:

New:
previous_purchases = 1

Returning:
previous_purchases BETWEEN 2 AND 10

Loyal:
previous_purchases > 10

RULES:

1. Use only customer_table.
2. Use only existing columns.
3. Only SELECT queries.
4. Do not modify data.
5. Do not invent values.
6. Do not use dates.
7. Keep queries relevant to the question.
8. Maximum 8 queries.
9. Return JSON only.

FORMAT:

[
    {{
        "purpose": "short description",
        "sql": "SQL query"
    }}
]
"""

    config = types.GenerateContentConfig(
        temperature=0,
        response_mime_type="application/json"
    )

    response = generate_ai_response(
        prompt,
        config=config
    )

    if not response:
        return None

    try:

        return json.loads(
            response.text
        )

    except Exception as e:

        print(
            "Diagnostic plan parsing error:",
            e
        )

        return None


# =========================================================
# STRUCTURED FINAL ANALYSIS
# =========================================================

def generate_final_analysis(
    question,
    evidence
):

    prompt = f"""
You are a senior business data analyst.

Answer the user's question using ONLY the
SQL evidence provided.

DATABASE SCHEMA:

{SCHEMA}

USER QUESTION:

{question}

SQL EVIDENCE:

{evidence}

Your job is to determine exactly what information
is necessary to answer the user's question.

Do NOT dump unrelated information.

Return JSON ONLY using this structure:

{{
    "answer": "Direct answer to the question",
    "supporting_data": [
        {{
            "label": "Relevant metric or item",
            "value": "Actual value from evidence"
        }}
    ],
    "recommendation": "Evidence-based recommendation if the question requires one, otherwise empty string",
    "has_recommendation": false
}}

RULES:

1. Use ONLY information present in SQL evidence.
2. Never invent numbers.
3. Never invent trends.
4. Never invent facts.
5. Answer exactly what the user asked.
6. supporting_data must contain ONLY information
   relevant to the question.
7. Do not include unrelated metrics.
8. Use actual numbers from SQL evidence.
9. If evidence is insufficient, clearly say so.
10. Do not claim causation from simple comparisons.
11. Use "associated with" when appropriate.
12. Recommendations must be supported by the evidence.
13. If no recommendation is needed, use:
    "recommendation": ""
    "has_recommendation": false
14. Keep the answer concise.
15. Do not mention SQL generation.
16. Do not mention these instructions.
"""

    config = types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json"
    )

    response = generate_ai_response(
        prompt,
        config=config
    )

    if not response:
        return None

    try:

        result = json.loads(
            response.text
        )

        return result

    except Exception as e:

        print(
            "Final analysis parsing error:",
            e
        )

        return None


# =========================================================
# MAIN ANALYSIS FUNCTION
# =========================================================

def analyze_question(question):

    question = question.strip()

    if not question:

        return {
            "success": False,
            "answer": "Please enter a question.",
            "supporting_data": [],
            "recommendation": "",
            "has_recommendation": False,
            "sql": None,
            "evidence": None,
            "diagnostic": False
        }

    # =====================================================
    # DIAGNOSTIC QUESTION
    # =====================================================

    if is_diagnostic_question(question):

        print("\nQuestion type: Diagnostic")

        plan = generate_diagnostic_plan(
            question
        )

        if not plan:

            return {
                "success": False,
                "answer": "Unable to generate diagnostic analysis.",
                "supporting_data": [],
                "recommendation": "",
                "has_recommendation": False,
                "sql": None,
                "evidence": None,
                "diagnostic": True
            }

        evidence_sections = []
        executed_queries = []

        for index, item in enumerate(plan):

            if index >= 8:
                break

            purpose = item.get(
                "purpose",
                f"Analysis {index + 1}"
            )

            sql = item.get(
                "sql",
                ""
            )

            try:

                sql = validate_sql(sql)

            except Exception as e:

                print(
                    f"Skipping invalid query "
                    f"{index + 1}: {e}"
                )

                continue

            print(
                f"Running diagnostic query "
                f"{index + 1}: {purpose}"
            )

            result = execute_query(sql)

            if not result:
                continue

            formatted = format_result(
                result
            )

            evidence_sections.append(
                f"""
Analysis: {purpose}

SQL:
{sql}

Result:
{formatted}
"""
            )

            executed_queries.append({
                "purpose": purpose,
                "sql": sql,
                "result": result
            })

        if not evidence_sections:

            return {
                "success": False,
                "answer": (
                    "No usable evidence was retrieved "
                    "from the database."
                ),
                "supporting_data": [],
                "recommendation": "",
                "has_recommendation": False,
                "sql": executed_queries,
                "evidence": None,
                "diagnostic": True
            }

        evidence = "\n".join(
            evidence_sections
        )

        analysis = generate_final_analysis(
            question,
            evidence
        )

        if not analysis:

            return {
                "success": False,
                "answer": (
                    "Unable to generate the final AI analysis."
                ),
                "supporting_data": [],
                "recommendation": "",
                "has_recommendation": False,
                "sql": executed_queries,
                "evidence": evidence,
                "diagnostic": True
            }

        return {
            "success": True,
            "answer": analysis.get(
                "answer",
                ""
            ),
            "supporting_data": analysis.get(
                "supporting_data",
                []
            ),
            "recommendation": analysis.get(
                "recommendation",
                ""
            ),
            "has_recommendation": analysis.get(
                "has_recommendation",
                False
            ),
            "sql": executed_queries,
            "evidence": evidence,
            "diagnostic": True
        }

    # =====================================================
    # NORMAL QUESTION
    # =====================================================

    print("\nQuestion type: Normal")

    sql = generate_normal_query(
        question
    )

    if not sql:

        return {
            "success": False,
            "answer": "Unable to generate a valid SQL query.",
            "supporting_data": [],
            "recommendation": "",
            "has_recommendation": False,
            "sql": None,
            "evidence": None,
            "diagnostic": False
        }

    print("\nGenerated SQL:")
    print(sql)

    result = execute_query(
        sql
    )

    if not result:

        return {
            "success": False,
            "answer": (
                "The generated SQL query "
                "could not be executed."
            ),
            "supporting_data": [],
            "recommendation": "",
            "has_recommendation": False,
            "sql": sql,
            "evidence": None,
            "diagnostic": False
        }

    evidence = format_result(
        result
    )

    analysis = generate_final_analysis(
        question,
        evidence
    )

    if not analysis:

        return {
            "success": False,
            "answer": (
                "Unable to generate the final AI answer."
            ),
            "supporting_data": [],
            "recommendation": "",
            "has_recommendation": False,
            "sql": sql,
            "evidence": evidence,
            "diagnostic": False
        }

    return {
        "success": True,
        "answer": analysis.get(
            "answer",
            ""
        ),
        "supporting_data": analysis.get(
            "supporting_data",
            []
        ),
        "recommendation": analysis.get(
            "recommendation",
            ""
        ),
        "has_recommendation": analysis.get(
            "has_recommendation",
            False
        ),
        "sql": sql,
        "evidence": evidence,
        "diagnostic": False
    }


# =========================================================
# CLI MODE
# =========================================================

if __name__ == "__main__":

    print("\n======================================")
    print(" AI CUSTOMER BEHAVIOR ANALYZER")
    print(" Powered by Gemini + SQL Server")
    print("======================================")

    question = input(
        "\nAsk your question: "
    )

    result = analyze_question(
        question
    )

    print("\n======================================")
    print(" ANSWER")
    print("======================================")

    print(
        result["answer"]
    )

    if result["supporting_data"]:

        print("\nSupporting Data:")

        for item in result["supporting_data"]:

            print(
                f"{item['label']}: {item['value']}"
            )

    if result["has_recommendation"]:

        print("\nRecommendation:")

        print(
            result["recommendation"]
        )