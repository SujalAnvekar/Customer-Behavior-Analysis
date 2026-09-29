import os
import json
import time

from dotenv import load_dotenv
from google import genai

from database import execute_query


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not configured in the .env file."
    )


# =========================================================
# GEMINI CLIENT
# =========================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# GEMINI MODELS
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
Table: customer_table

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

Important:

- purchase_amt represents purchase amount / revenue.
- There is NO customer_segment column.
- Customer segment must be derived using:
    New      = previous_purchases = 1
    Returning = previous_purchases BETWEEN 2 AND 10
    Loyal     = previous_purchases > 10
- Do not invent columns.
- Do not use a date column because the dataset does not contain one.
"""


# =========================================================
# DIAGNOSTIC KEYWORDS
# =========================================================

diagnostic_words = [
    "why",
    "reason",
    "reasons",
    "factor",
    "factors",
    "driver",
    "drivers",
    "cause",
    "causes",
    "impact",
    "influence",
    "explain",
    "explanation",
    "difference",
    "differ",
    "lower",
    "higher",
    "decline",
    "increase",
    "decrease",
    "performing differently"
]


# =========================================================
# GEMINI CALL
# =========================================================

def call_gemini(
    prompt,
    response_schema=None,
    temperature=0.1
):

    last_error = None

    for model in AI_MODELS:

        for attempt in range(2):

            try:

                config = {
                    "temperature": temperature,
                    "response_mime_type": "application/json"
                }

                if response_schema:
                    config["response_schema"] = response_schema

                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config
                )

                text = response.text.strip()

                return json.loads(text)

            except Exception as e:

                last_error = e

                error_text = str(e).lower()

                # Retry temporary service failures
                if (
                    "503" in error_text
                    or "unavailable" in error_text
                    or "timeout" in error_text
                ):
                    time.sleep(1)
                    continue

                # Try next model for quota / model issues
                if (
                    "429" in error_text
                    or "quota" in error_text
                    or "resource_exhausted" in error_text
                    or "not found" in error_text
                    or "404" in error_text
                ):
                    break

                # Other errors
                break

    raise RuntimeError(
        f"Gemini request failed: {last_error}"
    )


# =========================================================
# SQL VALIDATION
# =========================================================

def validate_sql(sql):

    if not sql:
        return False, "SQL query is empty."

    sql = sql.strip()

    sql_lower = sql.lower()

    # Must be SELECT
    if not sql_lower.startswith("select"):
        return False, "Only SELECT queries are allowed."

    # Block multiple statements
    if ";" in sql:
        return False, "Multiple SQL statements are not allowed."

    # Block SQL comments
    if "--" in sql or "/*" in sql or "*/" in sql:
        return False, "SQL comments are not allowed."

    # Required table
    if "customer_table" not in sql_lower:
        return False, "Query must use customer_table."

    # Block dangerous operations
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

    for keyword in forbidden_keywords:

        if keyword in sql_lower:

            return False, (
                f"Unsafe SQL query detected: "
                f"{keyword.strip()}"
            )

    return True, ""


# =========================================================
# FORMAT SQL RESULT
# =========================================================

def format_result(result):

    if not result:
        return ""

    columns = result.get("columns", [])
    rows = result.get("rows", [])

    if not columns or not rows:
        return "No data returned."

    lines = []

    for row in rows:

        values = []

        for column, value in zip(columns, row):

            values.append(
                f"{column}={value}"
            )

        lines.append(
            " | ".join(values)
        )

    return "\n".join(lines)


# =========================================================
# NORMAL QUESTION → SQL
# =========================================================

def generate_normal_query(question):

    prompt = f"""
You are a SQL analyst working with Microsoft SQL Server.

Your task is to convert the user's business question into ONE
accurate SQL SELECT query.

DATABASE SCHEMA:
{SCHEMA}

USER QUESTION:
{question}

RULES:

1. Generate only one SELECT query.
2. Use only customer_table.
3. Do not modify data.
4. Do not invent columns.
5. Use purchase_amt for revenue or spending.
6. Use appropriate aggregation such as:
   SUM, AVG, COUNT, MIN, MAX.
7. Return only the information required to answer the question.
8. Do not return unrelated columns or metrics.
9. Do not use dates.
10. For customer segments, derive the segment using previous_purchases:
      New = previous_purchases = 1
      Returning = previous_purchases BETWEEN 2 AND 10
      Loyal = previous_purchases > 10
11. Use SQL Server syntax.
12. Do not add SQL comments.
13. Do not use multiple statements.
14. If the question asks for the highest/lowest category,
    location, item, segment, etc., return the relevant result.
15. Keep the query focused and minimal.

Return JSON only:

{{
    "can_answer": true,
    "sql": "SELECT ...",
    "reason": "Short explanation of what the query calculates."
}}

If the question cannot be answered from the available columns,
return:

{{
    "can_answer": false,
    "sql": "",
    "reason": "Explain why the available data is insufficient."
}}
"""

    return call_gemini(
        prompt,
        response_schema={
            "type": "OBJECT",
            "properties": {
                "can_answer": {
                    "type": "BOOLEAN"
                },
                "sql": {
                    "type": "STRING"
                },
                "reason": {
                    "type": "STRING"
                }
            },
            "required": [
                "can_answer",
                "sql",
                "reason"
            ]
        }
    )


# =========================================================
# DIAGNOSTIC PLAN
# =========================================================

def generate_diagnostic_plan(question):

    prompt = f"""
You are a senior business data analyst.

The user is asking a diagnostic business question.

DATABASE SCHEMA:
{SCHEMA}

USER QUESTION:
{question}

Your job is to identify the SMALL NUMBER of SQL analyses
needed to investigate the question using actual data.

Rules:

1. Generate no more than 8 SQL SELECT queries.
2. Every query must use customer_table.
3. Every query must be directly relevant to the question.
4. Do not collect unrelated metrics.
5. Do not dump the entire database.
6. Do not invent columns.
7. Use purchase_amt for revenue/spending.
8. Do not use dates.
9. Customer segments must be derived from previous_purchases.
10. Queries must be Microsoft SQL Server compatible.
11. No INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, EXEC, etc.
12. No SQL comments.
13. Do not make causal claims.
14. Investigate measurable differences and associations only.
15. Keep each query focused.

Return JSON only:

{{
    "can_answer": true,
    "queries": [
        {{
            "purpose": "What this query investigates",
            "sql": "SELECT ..."
        }}
    ]
}}

If the question cannot reasonably be investigated from this
dataset, return:

{{
    "can_answer": false,
    "queries": []
}}
"""

    return call_gemini(
        prompt,
        response_schema={
            "type": "OBJECT",
            "properties": {
                "can_answer": {
                    "type": "BOOLEAN"
                },
                "queries": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "purpose": {
                                "type": "STRING"
                            },
                            "sql": {
                                "type": "STRING"
                            }
                        },
                        "required": [
                            "purpose",
                            "sql"
                        ]
                    }
                }
            },
            "required": [
                "can_answer",
                "queries"
            ]
        }
    )


# =========================================================
# FINAL BUSINESS ANALYSIS
# =========================================================

def generate_final_analysis(
    question,
    evidence,
    diagnostic=False
):

    prompt = f"""
You are a professional business analyst.

Answer the user's question using ONLY the SQL evidence provided.

DATABASE SCHEMA:
{SCHEMA}

USER QUESTION:
{question}

SQL EVIDENCE:
{evidence}

IMPORTANT PRINCIPLE:

SQL calculates the evidence.
You interpret the evidence.
Do not invent information.

RULES:

1. Answer the exact question asked.
2. Be concise and business-focused.
3. Do not provide unrelated metrics.
4. Do not dump the SQL results into the answer.
5. Do not mention database implementation unless necessary.
6. Do not invent facts.
7. If the evidence does not support a conclusion, clearly say that
   the available data is insufficient.
8. Never claim causation from observational data.
9. For "why" questions, discuss measurable differences or
   associations only.
10. If a recommendation is requested, base it only on the evidence.
11. Do not provide a recommendation unless the user explicitly asks
    how to improve, increase, reduce, optimize, grow, or what action
    should be taken.
12. Do not provide a general summary.
13. Do not repeat the same information unnecessarily.

KEY METRICS RULE:

Supporting metrics are OPTIONAL.

Return supporting_data ONLY when separate metric cards materially
improve the answer.

If the answer itself already contains the required value,
normally return supporting_data as an empty list.

Examples of desired behavior:

- "Which category has the highest revenue?"
  → Answer with the category and revenue.
  → supporting_data should normally be empty.

- "What is the average purchase amount?"
  → Answer with the average purchase amount.
  → supporting_data should normally be empty.

- "Do subscribers spend more?"
  → A comparison between subscribers and non-subscribers may be useful
    as supporting_data.

- "Why is Clothing different?"
  → Only directly relevant evidence should be returned.

Do NOT return unrelated metrics simply because they are available.

Return JSON only:

{{
    "answer": "Direct business answer",
    "supporting_data": [
        {{
            "label": "Relevant metric",
            "value": "Value"
        }}
    ],
    "recommendation": "",
    "has_recommendation": false
}}

For recommendations:

{{
    "answer": "Evidence-based answer",
    "supporting_data": [],
    "recommendation": "Specific evidence-based recommendation",
    "has_recommendation": true
}}
"""

    return call_gemini(
        prompt,
        response_schema={
            "type": "OBJECT",
            "properties": {
                "answer": {
                    "type": "STRING"
                },
                "supporting_data": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "label": {
                                "type": "STRING"
                            },
                            "value": {
                                "type": "STRING"
                            }
                        },
                        "required": [
                            "label",
                            "value"
                        ]
                    }
                },
                "recommendation": {
                    "type": "STRING"
                },
                "has_recommendation": {
                    "type": "BOOLEAN"
                }
            },
            "required": [
                "answer",
                "supporting_data",
                "recommendation",
                "has_recommendation"
            ]
        }
    )


# =========================================================
# MAIN ANALYSIS FUNCTION
# =========================================================

def analyze_question(question):

    question = question.strip()

    if not question:

        return {
            "success": False,
            "answer": "",
            "supporting_data": [],
            "recommendation": "",
            "has_recommendation": False,
            "sql": "",
            "evidence": "",
            "diagnostic": False,
            "error": "Please enter a question."
        }

    try:

        # =================================================
        # DETERMINE QUESTION TYPE
        # =================================================

        question_lower = question.lower()

        is_diagnostic = any(
            word in question_lower
            for word in diagnostic_words
        )


        # =================================================
        # NORMAL QUESTION
        # =================================================

        if not is_diagnostic:

            generated = generate_normal_query(
                question
            )

            if not generated.get("can_answer"):

                return {
                    "success": False,
                    "answer": "",
                    "supporting_data": [],
                    "recommendation": "",
                    "has_recommendation": False,
                    "sql": "",
                    "evidence": "",
                    "diagnostic": False,
                    "error": generated.get(
                        "reason",
                        "The question cannot be answered from the available data."
                    )
                }

            sql = generated.get("sql", "").strip()

            valid, validation_error = validate_sql(sql)

            if not valid:

                return {
                    "success": False,
                    "answer": "",
                    "supporting_data": [],
                    "recommendation": "",
                    "has_recommendation": False,
                    "sql": sql,
                    "evidence": "",
                    "diagnostic": False,
                    "error": validation_error
                }

            # =============================================
            # EXECUTE SQL
            # =============================================

            result = execute_query(sql)

            if result is None:

                return {
                    "success": False,
                    "answer": "",
                    "supporting_data": [],
                    "recommendation": "",
                    "has_recommendation": False,
                    "sql": sql,
                    "evidence": "",
                    "diagnostic": False,
                    "error": "Unable to execute the SQL query."
                }

            evidence = format_result(result)

            if not evidence:

                return {
                    "success": False,
                    "answer": "",
                    "supporting_data": [],
                    "recommendation": "",
                    "has_recommendation": False,
                    "sql": sql,
                    "evidence": "",
                    "diagnostic": False,
                    "error": "No data was returned for this question."
                }

            # =============================================
            # FINAL ANSWER
            # =============================================

            final_result = generate_final_analysis(
                question,
                evidence,
                diagnostic=False
            )

            return {
                "success": True,
                "answer": final_result.get(
                    "answer",
                    ""
                ),
                "supporting_data": final_result.get(
                    "supporting_data",
                    []
                ),
                "recommendation": final_result.get(
                    "recommendation",
                    ""
                ),
                "has_recommendation": final_result.get(
                    "has_recommendation",
                    False
                ),
                "sql": sql,
                "evidence": evidence,
                "diagnostic": False
            }


        # =================================================
        # DIAGNOSTIC QUESTION
        # =================================================

        plan = generate_diagnostic_plan(
            question
        )

        if not plan.get("can_answer"):

            return {
                "success": False,
                "answer": "",
                "supporting_data": [],
                "recommendation": "",
                "has_recommendation": False,
                "sql": "",
                "evidence": "",
                "diagnostic": True,
                "error": "The available data is not sufficient to investigate this question."
            }

        queries = plan.get(
            "queries",
            []
        )

        if not queries:

            return {
                "success": False,
                "answer": "",
                "supporting_data": [],
                "recommendation": "",
                "has_recommendation": False,
                "sql": "",
                "evidence": "",
                "diagnostic": True,
                "error": "No relevant analysis could be generated."
            }


        # =================================================
        # EXECUTE DIAGNOSTIC QUERIES
        # =================================================

        evidence_blocks = []
        sql_blocks = []

        for index, query_info in enumerate(
            queries,
            start=1
        ):

            sql = query_info.get(
                "sql",
                ""
            ).strip()

            purpose = query_info.get(
                "purpose",
                f"Analysis {index}"
            )

            valid, validation_error = validate_sql(
                sql
            )

            if not valid:

                continue

            result = execute_query(sql)

            if result is None:

                continue

            formatted = format_result(
                result
            )

            if not formatted:

                continue

            sql_blocks.append(
                f"-- {purpose}\n{sql}"
            )

            evidence_blocks.append(
                f"Analysis: {purpose}\n"
                f"{formatted}"
            )


        # =================================================
        # CHECK WHETHER ANY EVIDENCE EXISTS
        # =================================================

        if not evidence_blocks:

            return {
                "success": False,
                "answer": "",
                "supporting_data": [],
                "recommendation": "",
                "has_recommendation": False,
                "sql": "",
                "evidence": "",
                "diagnostic": True,
                "error": "No usable evidence was returned from the database."
            }


        evidence = "\n\n".join(
            evidence_blocks
        )

        combined_sql = "\n\n".join(
            sql_blocks
        )


        # =================================================
        # FINAL DIAGNOSTIC ANSWER
        # =================================================

        final_result = generate_final_analysis(
            question,
            evidence,
            diagnostic=True
        )

        return {
            "success": True,
            "answer": final_result.get(
                "answer",
                ""
            ),
            "supporting_data": final_result.get(
                "supporting_data",
                []
            ),
            "recommendation": final_result.get(
                "recommendation",
                ""
            ),
            "has_recommendation": final_result.get(
                "has_recommendation",
                False
            ),
            "sql": combined_sql,
            "evidence": evidence,
            "diagnostic": True
        }


    except Exception as e:

        return {
            "success": False,
            "answer": "",
            "supporting_data": [],
            "recommendation": "",
            "has_recommendation": False,
            "sql": "",
            "evidence": "",
            "diagnostic": False,
            "error": str(e)
        }


# =========================================================
# COMMAND LINE MODE
# =========================================================

if __name__ == "__main__":

    print("=" * 50)
    print(" AI CUSTOMER BEHAVIOR ANALYZER")
    print(" Powered by Gemini + SQL Server")
    print("=" * 50)

    while True:

        question = input(
            "\nAsk your question: "
        ).strip()

        if not question:
            continue

        if question.lower() in [
            "exit",
            "quit"
        ]:
            break

        print("\nAnalyzing question...")

        result = analyze_question(
            question
        )

        if result.get("success"):

            print("\nANSWER")
            print("-" * 40)
            print(
                result.get(
                    "answer",
                    ""
                )
            )

            supporting_data = result.get(
                "supporting_data",
                []
            )

            if supporting_data:

                print("\nKEY METRICS")
                print("-" * 40)

                for metric in supporting_data:

                    print(
                        f"{metric.get('label')}: "
                        f"{metric.get('value')}"
                    )

            if result.get(
                "has_recommendation",
                False
            ):

                print("\nRECOMMENDATION")
                print("-" * 40)
                print(
                    result.get(
                        "recommendation",
                        ""
                    )
                )

            print("\nGenerated SQL:")
            print("-" * 40)
            print(
                result.get(
                    "sql",
                    ""
                )
            )

        else:

            print("\nERROR")
            print("-" * 40)
            print(
                result.get(
                    "error",
                    "Unknown error."
                )
            )