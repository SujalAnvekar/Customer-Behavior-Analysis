import streamlit as st

from ai import analyze_question


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Customer Behavior Analyzer",
    page_icon="📊",
    layout="wide"
)


# =========================================================
# HEADER
# =========================================================

st.title("📊 AI Customer Behavior Analyzer")

st.write(
    "Ask questions about customer behavior, sales, "
    "subscriptions, locations, categories and segments."
)

st.divider()


# =========================================================
# QUESTION
# =========================================================

question = st.text_input(
    "Ask your question",
    placeholder="Example: Which category has the highest revenue?"
)


# =========================================================
# ANALYZE
# =========================================================

if st.button(
    "🔍 Analyze",
    type="primary"
):

    if not question.strip():

        st.warning(
            "Please enter a question."
        )

    else:

        with st.spinner(
            "Analyzing actual customer data..."
        ):

            result = analyze_question(
                question
            )

        # =================================================
        # ANSWER
        # =================================================

        if result.get("success", False):

            st.subheader(
                "🤖 Answer"
            )

            st.write(
                result.get(
                    "answer",
                    "No answer generated."
                )
            )

            # =============================================
            # SUPPORTING DATA
            # =============================================

            supporting_data = result.get(
                "supporting_data",
                []
            )

            if supporting_data:

                st.subheader(
                    "📊 Supporting Information"
                )

                columns = st.columns(
                    min(len(supporting_data), 4)
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
                        index % len(columns)
                    ]:

                        st.metric(
                            label,
                            value
                        )

            # =============================================
            # RECOMMENDATION
            # =============================================

            if result.get(
                "has_recommendation",
                False
            ):

                recommendation = result.get(
                    "recommendation",
                    ""
                )

                if recommendation:

                    st.subheader(
                        "💡 Recommendation"
                    )

                    st.info(
                        recommendation
                    )

            # =============================================
            # TECHNICAL DETAILS
            # =============================================

            with st.expander(
                "🔧 Technical Details"
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
                        "**SQL Query / Queries**"
                    )

                    if diagnostic:

                        for index, query_data in enumerate(
                            sql_data,
                            start=1
                        ):

                            st.markdown(
                                f"**Analysis {index}: "
                                f"{query_data.get('purpose', 'Analysis')}**"
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

                evidence = result.get(
                    "evidence"
                )

                if evidence:

                    st.markdown(
                        "**Database Evidence**"
                    )

                    st.code(
                        evidence
                    )

        else:

            st.error(
                result.get(
                    "answer",
                    "Something went wrong."
                )
            )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "AI Customer Behavior Analyzer • "
    "Python • Gemini • SQL Server"
)