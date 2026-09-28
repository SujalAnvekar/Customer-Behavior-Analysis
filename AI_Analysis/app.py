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

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    .main-header {
        padding: 10px 0 5px 0;
    }

    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .main-subtitle {
        font-size: 1rem;
        color: #6b7280;
        margin-bottom: 1.5rem;
    }

    .question-label {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 650;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }

    .sidebar-title {
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .sidebar-text {
        color: #64748b;
        font-size: 0.9rem;
        line-height: 1.5;
    }

    .footer {
        text-align: center;
        color: #94a3b8;
        font-size: 0.8rem;
        padding-top: 1rem;
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
        '<div class="sidebar-title">📊 Customer Intelligence</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="sidebar-text">
        AI-powered business analytics for understanding
        customer behavior, revenue, subscriptions and
        sales performance.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown("### Analytics Areas")

    st.markdown(
        """
        - Customer Behavior
        - Revenue Analysis
        - Product Categories
        - Customer Segments
        - Subscription Analysis
        - Location Performance
        - Purchase Patterns
        """
    )

    st.divider()

    st.markdown("### Analysis Process")

    st.markdown(
        """
        **1. Business Question**

        **2. AI Interpretation**

        **3. SQL Data Analysis**

        **4. Business Insight**
        """
    )

    st.divider()

    st.caption(
        "Powered by AI + SQL Server"
    )


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-header">',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="main-title">Customer Intelligence Dashboard</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="main-subtitle">
    Transform customer data into actionable business insights.
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# BUSINESS QUESTION
# =========================================================

st.markdown(
    '<div class="question-label">Business Question</div>',
    unsafe_allow_html=True
)

question = st.text_input(
    label="",
    placeholder="Ask a question about your customer data...",
    label_visibility="collapsed"
)


# =========================================================
# ANALYZE BUTTON
# =========================================================

analyze_clicked = st.button(
    "Analyze",
    type="primary",
    use_container_width=True
)


# =========================================================
# ANALYSIS
# =========================================================

if analyze_clicked:

    if not question.strip():

        st.warning(
            "Please enter a business question before starting the analysis."
        )

    else:

        with st.spinner(
            "Analyzing customer data..."
        ):

            result = analyze_question(
                question
            )

        # =================================================
        # SUCCESS
        # =================================================

        if result.get("success", False):

            st.divider()

            # =================================================
            # KEY METRICS
            # =================================================

            supporting_data = result.get(
                "supporting_data",
                []
            )

            if supporting_data:

                st.markdown(
                    '<div class="section-title">Key Metrics</div>',
                    unsafe_allow_html=True
                )

                metric_count = min(
                    len(supporting_data),
                    4
                )

                columns = st.columns(
                    metric_count
                )

                for index, item in enumerate(
                    supporting_data
                ):

                    label = item.get(
                        "label",
                        "Metric"
                    )

                    value = item.get(
                        "value",
                        "N/A"
                    )

                    with columns[
                        index % metric_count
                    ]:

                        st.metric(
                            label=label,
                            value=value
                        )


            # =================================================
            # BUSINESS RECOMMENDATION
            # =================================================

            if result.get(
                "has_recommendation",
                False
            ):

                recommendation = result.get(
                    "recommendation",
                    ""
                )

                if recommendation:

                    st.markdown(
                        '<div class="section-title">Business Recommendation</div>',
                        unsafe_allow_html=True
                    )

                    st.info(
                        recommendation
                    )


            # =================================================
            # SUPPORTING DATA
            # =================================================

            evidence = result.get(
                "evidence"
            )

            if evidence:

                st.markdown(
                    '<div class="section-title">Supporting Data</div>',
                    unsafe_allow_html=True
                )

                st.code(
                    evidence
                )


            # =================================================
            # TECHNICAL DETAILS
            # =================================================

            with st.expander(
                "View Technical Details"
            ):

                sql_data = result.get(
                    "sql"
                )

                diagnostic = result.get(
                    "diagnostic",
                    False
                )

                if sql_data:

                    st.markdown(
                        "**SQL Generated for Analysis**"
                    )

                    if diagnostic:

                        for index, query_data in enumerate(
                            sql_data,
                            start=1
                        ):

                            st.markdown(
                                f"**Analysis {index}:** "
                                f"{query_data.get(
                                    'purpose',
                                    'Business Analysis'
                                )}"
                            )

                            st.code(
                                query_data.get(
                                    "sql",
                                    ""
                                ),
                                language="sql"
                            )

                    else:

                        st.code(
                            sql_data,
                            language="sql"
                        )

                else:

                    st.caption(
                        "No SQL query was returned."
                    )


        # =================================================
        # ERROR
        # =================================================

        else:

            st.error(
                result.get(
                    "answer",
                    "The analysis could not be completed."
                )
            )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.markdown(
    """
    <div class="footer">
        Customer Intelligence Dashboard · AI-powered data analysis
    </div>
    """,
    unsafe_allow_html=True
)