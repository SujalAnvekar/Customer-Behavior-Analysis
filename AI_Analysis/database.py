# import pyodbc

# server = "LAPTOP-12GALTT6\\SQLEXPRESS01"
# database = "Customer_behavior"
# username = "LAPTOP-12GALTT6\\Sujal Anvekar"
# password = ""


# def get_customer_metrics():

#     try:
#         conn = pyodbc.connect(
#             "Driver={SQL Server};"
#             f"SERVER={server};"
#             f"DATABASE={database};"
#             f"UID={username};"
#             f"PWD={password};"
#             "Trusted_Connection=yes;"
#         )

#         print("Database connected successfully!")

#         crs = conn.cursor()

#         # Total customers
#         crs.execute("SELECT COUNT(*) FROM customer_table")
#         total_customers = crs.fetchone()[0]

#         # Total revenue
#         crs.execute("""
#             SELECT SUM(purchase_amt)
#             FROM customer_table
#         """)
#         total_revenue = crs.fetchone()[0]

#         # Average purchase
#         crs.execute("""
#             SELECT AVG(purchase_amt)
#             FROM customer_table
#         """)
#         average_purchase = crs.fetchone()[0]

#         crs.close()
#         conn.close()

#         return {
#             "total_customers": total_customers,
#             "total_revenue": total_revenue,
#             "average_purchase": average_purchase
#         }

#     except Exception as e:
#         print("Database error:", e)
#         return None


# def get_revenue_by_category():

#     try:
#         conn = pyodbc.connect(
#             "Driver={SQL Server};"
#             f"SERVER={server};"
#             f"DATABASE={database};"
#             f"UID={username};"
#             f"PWD={password};"
#             "Trusted_Connection=yes;"
#         )

#         crs = conn.cursor()

#         crs.execute("""
#                 SELECT
#         category,
#         COUNT(*) AS purchase_count,
#         SUM(purchase_amt) AS total_revenue,
#         AVG(purchase_amt) AS average_purchase
#     FROM customer_table
#     GROUP BY category
#     ORDER BY total_revenue DESC
#         """)

#         results = crs.fetchall()

#         crs.close()
#         conn.close()

#         return results

#     except Exception as e:
#         print("Category analysis error:", e)
#         return None


# def subscription_analysis():
#     try:
#         conn = pyodbc.connect(
#                     "Driver={SQL Server};"
#                     f"SERVER={server};"
#                     f"DATABASE={database};"
#                     f"UID={username};"
#                     f"PWD={password};"
#                     "Trusted_Connection=yes;"
#                 )
        
#         crs = conn.cursor()
#         crs.execute("""
#                 SELECT
#                 subscription_status,
#                 COUNT(*) AS customer_count,
#                 SUM(purchase_amt) AS total_revenue,
#                 AVG(purchase_amt) AS average_purchase
#             FROM customer_table
#             GROUP BY subscription_status
#             ORDER BY total_revenue DESC
#             """)

#         results=crs.fetchall()
#         crs.close()
#         conn.close()
#         return results
#     except Exception as err:
#             print("Subscription analysis error")
#             return None
        
# def get_location_analysis():

#     try:
#         conn = pyodbc.connect(
#             "Driver={SQL Server};"
#             f"SERVER={server};"
#             f"DATABASE={database};"
#             f"UID={username};"
#             f"PWD={password};"
#             "Trusted_Connection=yes;"
#         )

#         crs = conn.cursor()

#         crs.execute("""
#             SELECT
#                 location,
#                 COUNT(*) AS purchase_count,
#                 SUM(purchase_amt) AS total_revenue,
#                 AVG(purchase_amt) AS average_purchase
#             FROM customer_table
#             GROUP BY location
#             ORDER BY total_revenue DESC
#         """)

#         results = crs.fetchall()

#         crs.close()
#         conn.close()

#         return results

#     except Exception as e:
#         print("Location analysis error:", e)
#         return None


# def get_customer_segment():
#      try:
#         conn = pyodbc.connect(
#                 "Driver={SQL Server};"
#                 f"SERVER={server};"
#                 f"DATABASE={database};"
#                 f"UID={username};"
#                 f"PWD={password};"
#                 "Trusted_Connection=yes;"
#                   )
          
#         crs = conn.cursor()
#         crs.execute("""SELECT
#                 CASE
#                     WHEN previous_purchases = 1 THEN 'New'
#                     WHEN previous_purchases BETWEEN 2 AND 10 THEN 'Returning'
#                     ELSE 'Loyal'
#                 END AS customer_segment,
#                 COUNT(*) AS customer_count,
#                 SUM(purchase_amt) AS total_revenue,
#                 AVG(purchase_amt) AS average_purchase
#             FROM customer_table
#             GROUP BY
#                 CASE
#                     WHEN previous_purchases = 1 THEN 'New'
#                     WHEN previous_purchases BETWEEN 2 AND 10 THEN 'Returning'
#                     ELSE 'Loyal'
#                 END
#             ORDER BY total_revenue DESC""")

#         results=crs.fetchall()
#         crs.close()
#         conn.close()
#         return results
#      except Exception as err:
#           print("Customer Analysis Error",err)
#           return None
     

# # Test the functions
# if __name__ == "__main__":

#     metrics = get_customer_metrics()

#     if metrics:
#         print("\nCustomer Metrics:")
#         print(metrics)

#     category_data = get_revenue_by_category()

#     if category_data:
#         print("\nRevenue by Category:")

#         for row in category_data:
#             print(row)

#     subscription_data=subscription_analysis()
#     if subscription_data:
#         print("\nSubscriptions Analysis:")

#         for row in subscription_data:
#                     print(row)

#     location_data = get_location_analysis()

#     if location_data:
#         print("\nLocation Analysis:")
#         for row in location_data:
#             print(row)

#     customer_segment=get_customer_segment()

#     if customer_segment:
#          print("\nCustomer Segment Analysis")
#          for row in customer_segment:
#               print(row)


import pyodbc

server = "LAPTOP-12GALTT6\\SQLEXPRESS01"
database = "Customer_behavior"
username = "LAPTOP-12GALTT6\\Sujal Anvekar"
password = ""


def get_connection():
    return pyodbc.connect(
        "Driver={SQL Server};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "Trusted_Connection=yes;"
    )


# ============================================================
# GENERIC SQL QUERY FUNCTION
# ============================================================

def execute_query(sql):

    # Remove unnecessary spaces
    sql = sql.strip()

    # Only SELECT queries are allowed
    if not sql.lower().startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")

    # Block dangerous SQL commands
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

    # Allow only the intended table
    if "customer_table" not in sql_lower:
        raise ValueError(
            "Query must use the customer_table table."
        )

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(sql)

        # Get column names
        columns = [column[0] for column in cursor.description]

        # Get rows
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "columns": columns,
            "rows": rows
        }

    except Exception as e:

        print("SQL execution error:", e)

        return None


# ============================================================
# EXISTING ANALYSIS FUNCTIONS
# ============================================================

def get_customer_metrics():

    try:

        conn = get_connection()
        crs = conn.cursor()

        crs.execute("SELECT COUNT(*) FROM customer_table")
        total_customers = crs.fetchone()[0]

        crs.execute("""
            SELECT SUM(purchase_amt)
            FROM customer_table
        """)
        total_revenue = crs.fetchone()[0]

        crs.execute("""
            SELECT AVG(purchase_amt)
            FROM customer_table
        """)
        average_purchase = crs.fetchone()[0]

        crs.close()
        conn.close()

        return {
            "total_customers": total_customers,
            "total_revenue": total_revenue,
            "average_purchase": average_purchase
        }

    except Exception as e:

        print("Database error:", e)

        return None


def get_revenue_by_category():

    try:

        conn = get_connection()
        crs = conn.cursor()

        crs.execute("""
            SELECT
                category,
                COUNT(*) AS purchase_count,
                SUM(purchase_amt) AS total_revenue,
                AVG(purchase_amt) AS average_purchase
            FROM customer_table
            GROUP BY category
            ORDER BY total_revenue DESC
        """)

        results = crs.fetchall()

        crs.close()
        conn.close()

        return results

    except Exception as e:

        print("Category analysis error:", e)

        return None


def subscription_analysis():

    try:

        conn = get_connection()
        crs = conn.cursor()

        crs.execute("""
            SELECT
                subscription_status,
                COUNT(*) AS customer_count,
                SUM(purchase_amt) AS total_revenue,
                AVG(purchase_amt) AS average_purchase
            FROM customer_table
            GROUP BY subscription_status
            ORDER BY total_revenue DESC
        """)

        results = crs.fetchall()

        crs.close()
        conn.close()

        return results

    except Exception as e:

        print("Subscription analysis error:", e)

        return None


def get_location_analysis():

    try:

        conn = get_connection()
        crs = conn.cursor()

        crs.execute("""
            SELECT
                location,
                COUNT(*) AS purchase_count,
                SUM(purchase_amt) AS total_revenue,
                AVG(purchase_amt) AS average_purchase
            FROM customer_table
            GROUP BY location
            ORDER BY total_revenue DESC
        """)

        results = crs.fetchall()

        crs.close()
        conn.close()

        return results

    except Exception as e:

        print("Location analysis error:", e)

        return None


def get_customer_segment():

    try:

        conn = get_connection()
        crs = conn.cursor()

        crs.execute("""
            SELECT
                CASE
                    WHEN previous_purchases = 1
                        THEN 'New'

                    WHEN previous_purchases BETWEEN 2 AND 10
                        THEN 'Returning'

                    ELSE 'Loyal'
                END AS customer_segment,

                COUNT(*) AS customer_count,
                SUM(purchase_amt) AS total_revenue,
                AVG(purchase_amt) AS average_purchase

            FROM customer_table

            GROUP BY
                CASE
                    WHEN previous_purchases = 1
                        THEN 'New'

                    WHEN previous_purchases BETWEEN 2 AND 10
                        THEN 'Returning'

                    ELSE 'Loyal'
                END

            ORDER BY total_revenue DESC
        """)

        results = crs.fetchall()

        crs.close()
        conn.close()

        return results

    except Exception as e:

        print("Customer Analysis Error:", e)

        return None


# ============================================================
# TEST GENERIC QUERY
# ============================================================

if __name__ == "__main__":

    test_query = """
        SELECT TOP 5
            category,
            SUM(purchase_amt) AS total_revenue
        FROM customer_table
        GROUP BY category
        ORDER BY total_revenue DESC
    """

    result = execute_query(test_query)

    if result:

        print("\nColumns:")
        print(result["columns"])

        print("\nResults:")

        for row in result["rows"]:
            print(row)

    else:

        print("Query failed.")