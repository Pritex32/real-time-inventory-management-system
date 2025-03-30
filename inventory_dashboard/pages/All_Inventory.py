from http import cookies
import streamlit as st
import pandas as pd
import psycopg2
from streamlit_option_menu import option_menu
from datetime import datetime,timedelta ,date
from streamlit_cookies_manager import EncryptedCookieManager
from Home import check_access 
import json
import time

st.set_page_config()
cookies = EncryptedCookieManager(prefix="inventory_app_", password="your_secret_key_here")


def check_access(required_role=None):
    """Ensures the user is logged in and has the correct role. Shows a loading spinner while fetching cookies."""

    # Show a spinner while waiting for cookies to be ready
    if not cookies.ready():
        with st.spinner("🔄 Fetching session cookies... Please wait."):
            time.sleep(2)  # Short delay to allow UI to update before rerunning
        st.rerun()  # Restart script after waiting

    # Restore session from cookies if missing
    if "logged_in" not in st.session_state or not st.session_state.get("logged_in", False):
        if cookies.get("logged_in") == "True":
            st.session_state.logged_in = True
            user_data = cookies.get("user")

            if user_data and user_data != "{}":  # Ensure user data is not empty
                try:
                    st.session_state.user = json.loads(user_data)
                    time.sleep(1)  # Small delay to prevent UI flickering
                    st.rerun()  # Force rerun after restoring session
                except json.JSONDecodeError:
                    st.session_state.user = None
                    st.error("⚠️ Corrupted user session. Please log in again.")
                    st.stop()
        else:
            st.warning("⚠️ You must log in to access this page.")
            st.stop()

    # Ensure user session is valid
    if "user" not in st.session_state or not isinstance(st.session_state.user, dict) or not st.session_state.user:
        st.error("🚫 Invalid user session. Please log in again.")
        st.stop()

    # Check role access if required_role is specified
    user_role = st.session_state.user.get("role", None)
    if required_role and user_role != required_role:
        st.error("🚫 Unauthorized Access! You don't have permission to view this page.")
        st.stop()


# Ensure session state is initialized to prevent errors
if "user" not in st.session_state:
    st.session_state.user = {}  # Initialize as an empty dictionary

# 🔹 **Check Access for Inventory Role**
check_access(required_role="Inventory")






# connecting to supabase

from supabase import create_client
# supabase configurations
def get_supabase_client():
    supabase_url = 'https://bpxzfdxxidlfzvgdmwgk.supabase.co' # Your Supabase project URL
    supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJweHpmZHh4aWRsZnp2Z2Rtd2drIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI3NjM0MTQsImV4cCI6MjA1ODMzOTQxNH0.vQq2-VYCJyTQDq3QN2mJprmmBR2w7HMorqBuzz43HRU'
    supabase = create_client(supabase_url, supabase_key)
    return supabase  # Make sure to return the client

# Initialize Supabase client
supabase = get_supabase_client() # use this to call the supabase database

@st.cache_resource(ttl=600)
def fetch_data_from_supabase():
    """Fetch data from Supabase with caching and error handling."""
    try:
        supabase = get_supabase_client()  # Ensure we have a working client
        if not supabase:
            raise ValueError("Supabase client is not initialized!")  # Additional safety check
        
        response = supabase.table("inventory_log").select("*").execute()
        
        if hasattr(response, "data") and response.data:  
            return pd.DataFrame(response.data)
        else:
            st.warning("❌ No data found in Supabase!")
            return pd.DataFrame()

    except Exception as e:
        st.error(f"🚨 Error fetching data: {str(e)}")
        return pd.DataFrame()


st.subheader("📦 REAL TIME INVENTORY MANAGEMENT SYSTEM")

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()  # ✅ Clear cached data
    st.rerun() # ✅ Force rerun of the app


# Streamlit UI


# Display inventory log


# Insert interface


# lets put them in options
with st.sidebar:
    selected = option_menu(
        menu_title=('Options'),
        options=["Home page","Add Inventory", "Delete",'Calculations',"Filter","Reports"],
        icons=["house", "plus-circle", "trash", "calculator","bar-chart-line"],
        default_index=0
    )


if selected == "Home page":
     st.success("✅ Welcome to the Inventory Dashboard!")
     df = fetch_data_from_supabase()
     if not df.empty:
        st.write(df) # Display the full dataframe
        st.write('Last ten rows ',df.tail(10)) 
    
# Add item section

# Function to Get the Last Closing Stock
# Function to Get Last Closing Stock
# ✅ Function to Get Last Closing Stock
def get_last_closing_stock():
    try:
        response = (
            supabase.table("inventory_log")
            .select("closing_stock")
            .order("inventory_id", desc=True)
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]["closing_stock"]  # Return last closing stock
        return 0  # Default to 0 if no previous record exists

    except Exception as e:
        st.error(f"❌ Error fetching last closing stock: {e}")
        return 0


# ✅ Function to Insert Inventory Log (Without inserting `closing_stock`)
def insert_inventory_log(item, date, stock_in, return_item, stock_out):
    try:
        # Step 1: Get last closing stock
        last_closing_stock = get_last_closing_stock()

        # Step 2: Insert new record into Supabase (DO NOT insert `closing_stock`)
        response = (
            supabase.table("inventory_log")
            .insert({
                "item": item,
                "date": date.isoformat(),
                "open_stock": last_closing_stock,  # Store previous closing stock as open stock
                "stock_in": stock_in,
                "return_item": return_item,
                "stock_out": stock_out
            })
            .execute()
        )

        if response.data:
            inventory_id = response.data[0]["inventory_id"]
            st.success(f"✅ Item added successfully! ID: {inventory_id} 🎉")
        else:
            st.error("❌ Failed to insert inventory log.")

    except Exception as e:
        st.error(f"❌ Error inserting record: {e}")


# ✅ Streamlit UI for Adding Inventory
if "selected" in locals() and selected == "Add Inventory":
    st.subheader("➕ Add New Inventory")

    # Get last closing stock
    last_closing_stock = get_last_closing_stock()

    # User Inputs
    item = st.text_input('Item Name')
    date = st.date_input("Date", value=datetime.today())
    open_stock = st.number_input("Opening Stock", value=last_closing_stock, min_value=0, step=1, disabled=True)
    stock_in = st.number_input("Stock In", value=0, min_value=0, step=1)
    return_item = st.number_input("Returned Items", value=0, min_value=0, step=1)
    stock_out = st.number_input("Stock Out", value=0, min_value=0, step=1)

    # Submit Button
    if st.button("➕ Add Inventory Log"):
        insert_inventory_log(item, date, stock_in, return_item, stock_out)








#




## to delete inventory
if selected == "Delete":
    st.subheader("🗑️ Delete Inventory Log Entry")

    # Input for Inventory ID
    inventory_id = st.number_input("Enter Inventory Log ID to Delete", min_value=1, step=1)

    def delete_inventory_log(inventory_id):
        try:
            # Check if the ID exists before attempting deletion
            response = (
                supabase.table("inventory_log")
                .select("*")
                .eq("inventory_id", inventory_id)
                .execute()
            )

            if response.data:  # If record exists, proceed with deletion
                delete_response = (
                    supabase.table("inventory_log")
                    .delete()
                    .eq("inventory_id", inventory_id)
                    .execute()
                )
                
                st.success(f"✅ Inventory Log ID {inventory_id} deleted successfully! 🗑️")
            else:
                st.warning(f"⚠️ Inventory Log ID {inventory_id} not found!")

        except Exception as e:
            st.error(f"❌ Error deleting record: {e}")

    # Add delete button
    if st.button("Delete Record"):
        if inventory_id:
            delete_inventory_log(inventory_id)
        else:
            st.warning("⚠️ Please enter a valid Inventory ID to delete!")











def get_item_aggregation(item, start_date, end_date, column, aggregation):
    try:
        response = supabase.rpc(
            "calculate_item_aggregation",
            {
                "p_item": item,
                "p_start_date": start_date.isoformat(),
                "p_end_date": end_date.isoformat(),
                "p_column": column,
                "p_aggregation": aggregation
            }
        ).execute()

        if response.data is not None:
            return response.data
        else:
            return 0  # Return 0 if no data found

    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return None
# Streamlit UI
if selected == "Calculations":
    st.subheader("📊 Item Aggregation by Column")

    # Select item
    item = st.text_input("Enter Item Name (e.g., diesel, fuel, paper)")

    # Select column to aggregate
    column = st.selectbox("📌 Select Column to Aggregate", ["stock_in", "return_item", "stock_out", "closing_stock"])

    # Select aggregation type
    aggregation = st.selectbox("📊 Select Aggregation Type", ["SUM", "MAX", "MIN", "AVG"])

    # Date range input
    start_date = st.date_input("📅 Start Date")
    end_date = st.date_input("📅 End Date")

    if st.button("🔍 Get Aggregated Value"):
        if item and start_date and end_date and aggregation and column:
            result = get_item_aggregation(item, start_date, end_date, column, aggregation)

            if result is not None:
                st.success(f"✅ {aggregation} of '{column}' for '{item}' from {start_date} to {end_date}: {result}")
        else:
            st.warning("⚠️ Please fill in all fields.")









# Filtering
# filtering functions

def filter_inventory_log(filter_column, filter_value):
    try:
        # Query Supabase
        response = supabase.table("inventory_log").select("*").eq(filter_column, filter_value).execute()

        # Convert response to DataFrame
        if response.data:
            return pd.DataFrame(response.data)
        else:
            return pd.DataFrame()  # Return empty DataFrame if no results

    except Exception as e:
        st.error(f"❌ Error fetching filtered data: {e}")
        return pd.DataFrame()


# function to filter by date
def filter_by_date(start_date, end_date):
    try:
        response = (
            supabase.table("inventory_log")
            .select("*")
            .gte("date", str(start_date))
            .lte("date", str(end_date))
            .execute()
        )

        if response.data:
            return pd.DataFrame(response.data)
        else:
            return pd.DataFrame()

    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return pd.DataFrame()



# function to filter by date and item

def filter_by_item_and_date(item, start_date, end_date):
    try:
        response = (
            supabase.table("inventory_log")
            .select("*")
            .eq("item", item)
            .gte("date", str(start_date))
            .lte("date", str(end_date))
            .execute()
        )

        if response.data:
            return pd.DataFrame(response.data)
        else:
            return pd.DataFrame()

    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return pd.DataFrame()











# streamlit code
# Streamlit App
# Streamlit App
if selected == "Filter":
    st.subheader("🔍 Filter Inventory Log")

    # Select Filter Type
    filter_option = st.selectbox("Select Filter Type", ["Filter by Column", "Filter by Date", "Filter by Item & Date"])

    if filter_option == "Filter by Column":
        filter_column = st.selectbox("📌 Select Column to Filter By", 
                                     ["item", "stock_in", "details", "return_item", "closing_stock"])
        filter_value = st.text_input(f"Enter {filter_column} Value:")

        if st.button("🔎 Apply Filter"):
            if filter_value:
                filtered_df = filter_inventory_log(filter_column, filter_value)

                if not filtered_df.empty:
                    st.success(f"✅ Filter Applied Successfully!")
                    st.dataframe(filtered_df)
                else:
                    st.warning(f"⚠️ No records found for {filter_column} = {filter_value}")
            else:
                st.warning("⚠️ Please enter a filter value.")

    elif filter_option == "Filter by Date":
        st.subheader("Filter by Date")
        start_date = st.date_input("Start Date", date.today() - timedelta(days=30))  # Fixed
        end_date = st.date_input("End Date", date.today())  # Fixed

        if st.button("Apply Date Filter"):
            if start_date and end_date:
                filtered_df = filter_by_date(start_date, end_date)

                if not filtered_df.empty:
                    st.success("✅ Date Filter Applied Successfully!")
                    st.dataframe(filtered_df)
                else:
                    st.warning("⚠️ No results found for the selected date range.")

    elif filter_option == "Filter by Item & Date":
        st.subheader("Filter by Item & Date")
        item = st.text_input("Enter Item Name (e.g., diesel, fuel, paper)")
        
        # Correct way to get today's date and subtract 30 days
        start_date = st.date_input("Start Date", date.today() - timedelta(days=30))  # Fixed
        end_date = st.date_input("End Date", date.today())  # Fixed

        if st.button("Apply Item & Date Filter"):
            if item and start_date and end_date:
                filtered_df = filter_by_item_and_date(item, start_date, end_date)

                if not filtered_df.empty:
                    st.success(f"✅ Filter Applied for '{item}' from {start_date} to {end_date}")
                    st.dataframe(filtered_df)
                else:
                    st.warning(f"⚠️ No results found for '{item}' in the selected date range.")







# filter by date and item






# filter by date and item only

# Date range input








# Reports
# this function will generate sum of each column base on the time period  selected
def get_summary_report(time_period, start_date, end_date):
    try:
        # ✅ Convert dates to string format
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        # 🔹 Fetch raw data from Supabase
        response = supabase.table("inventory_log") \
            .select("date, item, stock_in, return_item, stock_out, closing_stock") \
            .gte("date", start_date_str) \
            .lte("date", end_date_str) \
            .execute()

        # ✅ Check if there is an error
        if hasattr(response, "error") and response.error:
            st.error(f"❌ Supabase Error: {response.error}")
            return pd.DataFrame()

        # ✅ Check if response.data exists
        if not hasattr(response, "data") or not response.data:
            st.warning("⚠️ No data returned from Supabase.")
            return pd.DataFrame()

        # ✅ Convert response data to DataFrame
        df = pd.DataFrame(response.data)

        # ✅ Ensure 'date' is in datetime format
        df["date"] = pd.to_datetime(df["date"])

        # ✅ Time Truncation Mapping
        time_trunc_map = {
            "Weekly": "W",
            "Monthly": "M",
            "Yearly": "Y"
        }

        if time_period not in time_trunc_map:
            st.error("❌ Invalid time period selected!")
            return pd.DataFrame()

        # ✅ Aggregate Data
        df_summary = (
            df.groupby([pd.Grouper(key="date", freq=time_trunc_map[time_period]), "item"])
            .agg(
                total_stock_in=("stock_in", "sum"),
                total_returned=("return_item", "sum"),
                total_stock_out=("stock_out", "sum"),
                total_closing_stock=("closing_stock", "sum"),
            )
            .reset_index()
        )

        # ✅ Rename 'date' column to 'period'
        df_summary.rename(columns={"date": "period"}, inplace=True)

        return df_summary

    except Exception as e:
        st.error(f"❌ Error fetching summary report: {e}")
        return pd.DataFrame()

# 🔹 Streamlit UI
if selected == "Reports":
    st.subheader("📊 Inventory Summary Reports")

    # Select Report Type
    report_type = st.selectbox("📆 Select Report Type", ["Weekly", "Monthly", "Yearly"])

    # Select Date Range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("📅 Start Date", datetime.today().replace(day=1))
    with col2:
        end_date = st.date_input("📅 End Date", datetime.today())

    if st.button("📈 Generate Report"):
        if start_date > end_date:
            st.error("❌ Start date cannot be after end date!")
        else:
            summary_df = get_summary_report(report_type, start_date, end_date)

            if not summary_df.empty:
                st.success(f"✅ {report_type} Report Generated Successfully!")
                st.dataframe(summary_df)
            else:
                st.warning(f"⚠️ No data found for the selected date range.")
