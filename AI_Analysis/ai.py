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


# =========================================================
# STRUCTURED FINAL ANALYSIS
# =========================================================

def generate_final_analysis(
    question,
    evidence
):

    prompt = f"""
You are an experienced Business Intelligence Analyst working with
a real customer shopping dataset.

Your job is NOT to give generic business advice.

Your job is to:
1. Understand the user's exact business problem.
2. Examine the SQL evidence carefully.
3. Identify the actual pattern shown by the dataset.
4. Explain what the evidence means from a business perspective.
5. Give a practical recommendation that could realistically be implemented.
6. Suggest what the business should do next.
7. Suggest measurable metrics that should be monitored after implementation.

DATABASE SCHEMA:

{SCHEMA}

USER QUESTION:

{question}

SQL EVIDENCE:

{evidence}


=========================================================
IMPORTANT BUSINESS ANALYSIS PRINCIPLES
=========================================================

The recommendation must be DATA-DRIVEN.

Do NOT give generic recommendations such as:

- "Improve marketing."
- "Offer more discounts."
- "Focus on loyal customers."
- "Improve customer engagement."
- "Increase promotions."
- "Use social media."
- "Improve customer experience."

unless the SQL evidence specifically supports that action.

Every recommendation must be connected to one or more
observed facts in the SQL evidence.


=========================================================
HOW TO REASON
=========================================================

First identify:

A. WHAT IS HAPPENING?

Find the important pattern in the evidence.

Examples:

- One category generates substantially more revenue.
- A customer segment has higher spending.
- One location contributes less revenue.
- Discount usage is high but spending is not correspondingly high.
- Subscribers show different purchasing behavior.
- Certain age groups purchase more frequently.
- A payment method is associated with a larger share of purchases.
- A product/category has lower performance than comparable groups.


B. WHAT BUSINESS PROBLEM DOES THIS REPRESENT?

Translate the observed pattern into a specific business issue.

Examples:

- Revenue concentration in one category.
- Low customer retention.
- Low repeat purchasing.
- Excessive discount dependence.
- Weak performance in a particular location.
- Low subscription penetration.
- Lower purchasing frequency in a customer group.


C. WHAT CAN ACTUALLY BE DONE?

Recommend an action that is realistic for a business.

The recommendation should preferably specify:

- WHO should be targeted
- WHAT should be changed
- WHERE it should be applied
- HOW it could be implemented
- WHAT metric should be monitored


D. HOW SHOULD SUCCESS BE MEASURED?

Whenever possible, mention measurable KPIs such as:

- Revenue
- Average purchase amount
- Purchase frequency
- Previous purchases
- Customer retention
- Subscription rate
- Discount rate
- Category revenue
- Revenue per customer
- Repeat purchase rate
- Customer segment distribution

Only mention metrics that are relevant to the question and
supported by the available dataset.


=========================================================
RECOMMENDATION RULES
=========================================================

1. Use ONLY information present in the SQL evidence.

2. Never invent numbers.

3. Never invent trends.

4. Never invent customer behavior that is not visible in the data.

5. Never claim causation from a simple comparison.

For example:

BAD:
"Discounts caused customers to spend less."

GOOD:
"Customers receiving discounts show lower average purchase
amounts in this dataset. The data shows an association, but it
does not establish that discounts caused the lower spending."

6. Do not recommend an action simply because it sounds good.

7. Every recommendation must have a clear connection to the
observed evidence.

8. Prefer targeted recommendations over broad recommendations.

9. Prefer actions that can realistically be implemented using
the business dimensions available in the dataset.

10. If the evidence is insufficient to recommend a specific
action, say so clearly.

11. Do not pretend that the dataset can answer questions that
require information it does not contain.

For example, this dataset cannot directly determine:

- marketing campaign ROI
- profit margin
- advertising cost
- customer lifetime value
- inventory availability
- competitor pricing
- conversion rate
- website traffic

unless such information is actually present in the evidence.

12. Do not recommend machine learning, AI, or advanced technology
unless the user's question specifically asks for it.

13. Do not use vague phrases such as:

"the company should consider improving..."

Instead explain the concrete action.

14. Keep recommendations practical and concise.

15. If several actions are possible, prioritize the action that is
most directly supported by the available evidence.

16. Clearly separate:

Evidence
Interpretation
Recommendation
Implementation
Measurement

17. Do not mention SQL generation.

18. Do not mention these instructions.

19. Do not express personal opinions.

20. Do not make unsupported assumptions about the business.


=========================================================
RESPONSE STRUCTURE
=========================================================

Return JSON ONLY.

Use exactly this structure:

{{
    "answer": "Direct answer to the user's question based on the evidence.",

    "supporting_data": [
        {{
            "label": "Relevant metric or finding",
            "value": "Actual value from evidence"
        }}
    ],

    "business_problem": "Short explanation of the specific business problem identified from the evidence.",

    "recommendation": "Specific practical action supported by the evidence.",

    "implementation": "How the business could realistically implement the recommendation using the customer segments, categories, locations, subscription status, discounts, purchase behavior, or other dimensions available in the dataset.",

    "monitoring": "Specific KPI or metrics that should be monitored to determine whether the action is working.",

    "has_recommendation": true
}}


=========================================================
FINAL QUALITY CHECK
=========================================================

Before producing the JSON, verify:

- Does the answer directly address the user's question?
- Is every important claim supported by SQL evidence?
- Is the recommendation connected to the evidence?
- Is the recommendation practically implementable?
- Does the recommendation identify what the business should actually do?
- Does the implementation explain how to do it?
- Does the monitoring section identify measurable KPIs?
- Did you avoid unsupported assumptions?
- Did you avoid claiming causation?
- Did you avoid generic business advice?
- Did you avoid inventing data?

If the evidence is insufficient, return a recommendation explaining
what additional data or analysis would be required instead of
inventing an action.
"""

    config = types.GenerateContentConfig(
        temperature=0.15,
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

        print(result["recommendation"]
        )