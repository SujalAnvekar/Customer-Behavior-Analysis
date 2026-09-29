import streamlit as st

from ai import analyze_question


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Customer Intelligence | AI Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    /* =========================
       GLOBAL
       ========================= */

    .stApp {
        background-color: #f8fafc;
    }

    .main .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }


    /* =========================
       HEADER
       ========================= */

    .main-header {
        margin-bottom: 1.5rem;
    }

    .main-header h1 {
        font-size: 2.2rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.25rem;
    }

    .main-header p {
        font-size: 1rem;
        color: #6b7280;
        margin-top: 0;
    }


    /* =========================
       SECTION TITLES
       ========================= */

    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #111827;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }


    /* =========================
       QUESTION AREA
       ========================= */

    div[data-testid="stTextInput"] input {
        border: 1px solid #d1d5db;
        border-radius: 8px;
        padding: 0.7rem 0.9rem;
        font-size: 0.95rem;
        background-color: white;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 1px #2563eb;
    }


    /* =========================
       ANALYZE BUTTON
       ========================= */

    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        border: none;
        background-color: #2563eb;
        color: white;
        font-weight: 600;
        padding: 0.65rem 1rem;
    }

    div.stButton > button:hover {
        background-color: #1d4ed8;
        color: white;
    }


    /* =========================
       METRIC CARDS
       ========================= */

    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 1rem 1.1rem;
        min-height: 105px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    }

    .metric-label {
        color: #6b7280;
        font-size: 0.82rem;
        font-weight: 500;
        margin-bottom: 0.35rem;
    }

    .metric-value {
        color: #111827;
        font-size: 1.45rem;
        font-weight: 700;
        word-break: break-word;
    }


    /* =========================
       ANSWER BOX
       ========================= */

    .answer-box {
        background: white;
        border: 1px solid #e5e7eb;
        border-left: 4px solid #2563eb;
        border-radius: 10px;
        padding: 1.2rem 1.3rem;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
        color: #111827;
        line-height: 1.6;
        font-size: 1rem;
    }


    /* =========================
       SIDEBAR
       ========================= */

    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    .sidebar-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.25rem;
    }

    .sidebar-subtitle {
        font-size: 0.85rem;
        color: #6b7280;
        line-height: 1.5;
        margin-bottom: 1.5rem;
    }

    .sidebar-heading {
        font-size: 0.85rem;
        font-weight: 700;
        color: #374151;
        margin-top: 1.2rem;
        margin-bottom: 0.6rem;
    }

    .sidebar-item {
        font-size: 0.82rem;
        color: #4b5563;
        padding: 0.25rem 0;
    }


    /* =========================
       FOOTER
       ========================= */

    .footer {
        text-align: center;
        color: #9ca3af;
        font-size: 0.78rem;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #e5e7eb;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-title">Customer Intelligence</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="sidebar-subtitle">
            AI-powered customer analytics using natural-language
            questions, SQL Server and business-focused insights.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sidebar-heading">Analytics Areas</div>',
        unsafe_allow_html=True
    )

    analytics_areas = [
        "Customer Behavior",
        "Revenue Analysis",
        "Product Categories",
        "Customer Segments",
        "Subscription Analysis",
        "Location Performance",
        "Purchase Patterns"
    ]

    for area in analytics_areas:
        st.markdown(
            f'<div class="sidebar-item">• {area}</div>',
            unsafe_allow_html=True
        )

    st.markdown(
        '<div class="sidebar-heading">Analysis Process</div>',
        unsafe_allow_html=True
    )

    process_steps = [
        "1. Business Question",
        "2. AI Interpretation",
        "3. SQL Data Analysis",
        "4. Business Insight"
    ]

    for step in process_steps:
        st.markdown(
            f'<div class="sidebar-item">{step}</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    st.markdown(
        """
        <div style="
            font-size:0.78rem;
            color:#9ca3af;
            line-height:1.5;
        ">
            Powered by AI + SQL Server
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# MAIN HEADER
# =========================================================

st.markdown(
    """
    <div class="main-header">
        <h1>Customer Intelligence Dashboard</h1>
        <p>
            Transform customer data into actionable business insights.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# QUESTION INPUT
# =========================================================

question = st.text_input(
    "Question",
    placeholder="Ask a question about your customer data...",
    label_visibility="collapsed"
)


# =========================================================
# ANALYZE
# =========================================================

analyze_clicked = st.button(
    "Analyze",
    use_container_width=True
)


# =========================================================
# ANALYSIS
# =========================================================

if analyze_clicked:

    if not question.strip():

        st.warning("Please enter a question.")

    else:

        with st.spinner("Analyzing your question..."):

            try:
                result = analyze_question(question.strip())

            except Exception as e:
                result = {
                    "success": False,
                    "answer": "",
                    "supporting_data": [],
                    "recommendation": "",
                    "has_recommendation": False,
                    "sql": "",
                    "evidence": "",
                    "error": str(e)
                }

        # =================================================
        # SUCCESS
        # =================================================

        if result.get("success"):

            answer = result.get("answer", "").strip()

            supporting_data = result.get(
                "supporting_data",
                []
            )

            recommendation = result.get(
                "recommendation",
                ""
            ).strip()

            has_recommendation = result.get(
                "has_recommendation",
                False
            )

            # =============================================
            # BUSINESS ANSWER
            # =============================================

            st.markdown(
                '<div class="section-title">Business Answer</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
                <div class="answer-box">
                    {answer}
                </div>
                """,
                unsafe_allow_html=True
            )


            # =============================================
            # KEY METRICS
            # Only shown when AI explicitly returns them
            # =============================================

            if supporting_data:

                st.markdown(
                    '<div class="section-title">Key Metrics</div>',
                    unsafe_allow_html=True
                )

                valid_metrics = []

                for metric in supporting_data:

                    if not isinstance(metric, dict):
                        continue

                    label = str(
                        metric.get("label", "")
                    ).strip()

                    value = str(
                        metric.get("value", "")
                    ).strip()

                    if label and value:
                        valid_metrics.append(
                            (label, value)
                        )

                if valid_metrics:

                    columns = st.columns(
                        min(len(valid_metrics), 4)
                    )

                    for index, (label, value) in enumerate(
                        valid_metrics
                    ):

                        with columns[index % len(columns)]:

                            st.markdown(
                                f"""
                                <div class="metric-card">
                                    <div class="metric-label">
                                        {label}
                                    </div>
                                    <div class="metric-value">
                                        {value}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )


            # =============================================
            # RECOMMENDATION
            # Only shown when requested
            # =============================================

            if has_recommendation and recommendation:

                st.markdown(
                    '<div class="section-title">Business Recommendation</div>',
                    unsafe_allow_html=True
                )

                st.info(recommendation)


            # =============================================
            # TECHNICAL DETAILS
            #
            # Raw SQL/evidence are NOT displayed as a
            # normal dashboard section.
            # =============================================

            sql = result.get("sql", "")
            evidence = result.get("evidence", "")

            if sql or evidence:

                with st.expander("Technical Details"):

                    if sql:

                        st.markdown("**Generated SQL**")

                        st.code(
                            sql,
                            language="sql"
                        )

                    if evidence:

                        st.markdown("**Internal Evidence**")

                        st.code(
                            evidence,
                            language="text"
                        )


        # =================================================
        # FAILURE
        # =================================================

        else:

            error_message = result.get(
                "error",
                "Unable to analyze the question."
            )

            st.error(error_message)


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">
        Customer Intelligence • AI + SQL Analytics
    </div>
    """,
    unsafe_allow_html=True
)