from http import cookies
import streamlit as st

import pandas as pd
from streamlit_option_menu import option_menu
from datetime import date, datetime
from Home import check_access 
from streamlit_cookies_manager import EncryptedCookieManager
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


# Add your inventory-related features here
 



from supabase import create_client
# supabase configurations
def get_supabase_client():
    supabase_url = 'https://bpxzfdxxidlfzvgdmwgk.supabase.co' # Your Supabase project URL
    supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJweHpmZHh4aWRsZnp2Z2Rtd2drIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI3NjM0MTQsImV4cCI6MjA1ODMzOTQxNH0.vQq2-VYCJyTQDq3QN2mJprmmBR2w7HMorqBuzz43HRU'
    supabase = create_client(supabase_url, supabase_key)
    return supabase  # Make sure to return the client

# Initialize Supabase client
supabase = get_supabase_client() # use this to call the supabase database

@st.cache_data(ttl=600)
def fetch_data_from_supabase():
    """Fetch data from Supabase with caching and error handling."""
    try:
        supabase = get_supabase_client()  # Ensure we have a working client
        if not supabase:
            raise ValueError("Supabase client is not initialized!")  # Additional safety check
        
        response = supabase.table("req").select("*").execute()
        
        if hasattr(response, "data") and response.data:  
            return pd.DataFrame(response.data)
        else:
            st.warning("❌ No data found in Supabase!")
            return pd.DataFrame()

    except Exception as e:
        st.error(f"🚨 Error fetching data: {str(e)}")
        return pd.DataFrame()


st.subheader("REAL TIME INVENTORY MANAGEMENT SYSTEM")



# ✅ Add a refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()  # ✅ Clear cached data
    st.rerun()  # ✅ Force rerun of the app


# 🔹 Fetch and display data


   
# Sidebar menu
with st.sidebar:
    selected = option_menu(
        menu_title=('Options'),
        options=["Home page","Add", "Delete","Calculations","Filter","Reports"],
        icons=["house", "plus-circle", "trash", "calculator","bar-chart-line"],
        default_index=0
    )





# Function to filter the entire table based on date range
def filter_by_date(start_date, end_date):
    try:
        supabase = get_supabase_client()
        response = supabase.table("req").select("*").gte("date", start_date).lte("date", end_date).execute()

        if hasattr(response, "data") and response.data:
            return pd.DataFrame(response.data)
        else:
            st.warning("❌ No records found within the selected date range.")
            return pd.DataFrame()

    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()


# filter functions

def filter_by_item_and_date(item, start_date, end_date):
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("req")
            .select("*")
            .eq("item", item)
            .gte("date", start_date)
            .lte("date", end_date)
            .execute()
        )

        if hasattr(response, "data") and response.data:
            return pd.DataFrame(response.data)
        else:
            st.warning("❌ No records found for this item in the selected date range.")
            return pd.DataFrame()

    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()




## this is to make the df  to be on the home page

if selected == "Home page": 
    df = fetch_data_from_supabase()
    st.success("✅ Welcome to the Inventory Dashboard!")
    if not df.empty:
        st.write(df) # Display the full dataframe
        st.write('Last ten rows ',df.tail(10)) 


   




 

## this is when you click on the add buttion its gives you function where you can add daily requisitions 
# Function to add a requisition using Supabase RPC
def add_requisition(id, date, item, category, details, location, quantity, requested_by, issued_by, remark):
    try:
        supabase = get_supabase_client()  # Ensure Supabase connection

        # Call the RPC function
        response = supabase.rpc("add_requisition", {
            "id": id,
            "date": date.strftime("%Y-%m-%d"),  # Convert date to string
            "item": item,
            "category": category,
            "details": details,
            "location": location,
            "quantity": quantity,
            "requested_by": requested_by,
            "issued_by": issued_by,
            "remark": remark
        }).execute()

        if "error" in response:
            st.error(f"❌ Error adding requisition: {response['error']['message']}")
        else:
            st.success("✅ Requisition added successfully!")

    except Exception as e:
        st.error(f"❌ Error adding requisition: {e}")

# Streamlit UI
if selected == "Add":
    st.subheader("➕ Add Daily Requisition")
    
    id = st.number_input("Serial Number", step=1)
    date = st.date_input("Enter the requisition date (YYYY-MM-DD)")
    item = st.text_input("Item")
    category = st.text_input("Category")
    details = st.text_input("Enter details")
    location = st.text_input("Location item is used")
    quantity = st.number_input("Quantity", step=1,value=0,min_value=0)
    requested_by = st.text_input("Requested by")
    issued_by = st.text_input("Issued by")
    remark = st.text_input("Remark")

    if st.button("Add Requisition"):
        if id and item and category and quantity > 0:
            add_requisition(id, date, item, category, details, location, quantity, requested_by, issued_by, remark)
        else:
            st.warning("⚠️ Please fill in all required fields correctly.")



# Delete Section
# Function to delete requisition
def delete_requisition(req_id):
    """Deletes a requisition from Supabase based on the serial number."""
    try:
        supabase = get_supabase_client()  # Ensure Supabase connection
        
        # First, check if the requisition exists
        check_response = supabase.table("req").select("id").eq("id", req_id).execute()
        
        if not check_response.data:
            st.warning(f"⚠️ No requisition found with ID {req_id}. Deletion aborted.")
            return
        
        # Proceed with deletion
        response = supabase.table("req").delete().eq("id", req_id).execute()
       
        
        # ✅ Check response correctly
        if response.data:
            st.success(f"✅ Requisition with ID {req_id} has been deleted successfully.")
        else:
            st.error("❌ Deletion failed. Record may not exist or deletion is restricted.")

    except Exception as e:
        st.error(f"❌ Error deleting requisition: {e}")

# Streamlit UI for deletion
if selected == "Delete":
    st.subheader("🗑️ Delete a Requisition")

    req_id = st.number_input("Enter the requisition ID", min_value=1, step=1)

    if st.button("Delete Requisition"):
        delete_requisition(req_id)  # Call the function


## calculations











def get_item_aggregation(item, start_date, end_date, aggregation):
    try:
        supabase = get_supabase_client()  # Ensure Supabase connection
        
        response = supabase.rpc(
            "aggregate_quantity",  # Call the Supabase stored function
            {
                "item_name": item,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "agg_type": aggregation.lower(),  # Ensure lowercase for SQL compatibility
            },
        ).execute()

        # Extract the data properly
        if isinstance(response, dict) and "data" in response:
            result = response["data"]
        elif isinstance(response, list):  # Some Supabase responses return lists
            result = response[0] if response else None
        else:
            result = response  # If it's already an int

        return result if result is not None else 0  # Return 0 if no data found

    except Exception as e:
        st.error(f"Supabase Response: {response}")

        return None





# Calculations

if selected == "Calculations":
    st.subheader("Table Manipulations")

    # Select item
    item = st.text_input("Enter Item Name (e.g., diesel, fuel, paper)")

    # Select aggregation type
    aggregation = st.selectbox("Select Aggregation Type", ["SUM", "MAX", "MIN", "AVG",'COUNT'])

    # Date range input
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")

    if st.button("Get Aggregated Quantity"):
        if item and start_date and end_date and aggregation:
            result = get_item_aggregation(item, start_date, end_date, aggregation)

            if result is not None:
                st.success(f"{aggregation} quantity of '{item}' from {start_date} to {end_date}: {result}")
        else:
            st.warning("⚠️ Please fill in all fields.")



# filter for with each columns

def filter_inventory_log(filter_column, filter_value):
    try:
        supabase = get_supabase_client()

        text_columns = ["item", "category", "details", "location", "requested_by", "issued_by", "remark"]
        numeric_columns = ["id", "quantity"]
        date_columns = ["date"]

        # Use appropriate filtering method
        if filter_column in text_columns:
            response = supabase.table("req").select("*").ilike_all_of(filter_column, f"%{filter_value}%").execute() # i change the ilike to ilike_all_of and it worked.
        elif filter_column in numeric_columns:
            response = supabase.table("req").select("*").eq(filter_column, int(filter_value)).execute()
        elif filter_column in date_columns:
            response = supabase.table("req").select("*").eq(filter_column, filter_value).execute()
        else:
            st.error(f"❌ Unsupported column: {filter_column}")
            return pd.DataFrame()

        if hasattr(response, "data") and response.data:
            return pd.DataFrame(response.data)
        else:
            st.warning(f"⚠️ No records found for {filter_column} = {filter_value}")
            return pd.DataFrame()

    except ValueError:
        st.error(f"❌ Invalid input for column '{filter_column}'")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Supabase API Error: {str(e)}")
        return pd.DataFrame()


    
if selected == "Filter":
    st.subheader("🔍 Filter By Columns")

    # Select Column to Filter
    filter_column = st.selectbox("📌 Select Column to Filter By", 
                                 ["id", "date", "item", "category", "details", 
                                  "location", "quantity", "requested_by", "issued_by", "remark"])

    # User Input for Filter Value
    filter_value = st.text_input(f"Enter {filter_column} Value:")

    if st.button("🔎 Apply Filter"):
        if filter_value:
            filtered_df = filter_inventory_log(filter_column, filter_value)

            if not filtered_df.empty:
                st.success("✅ Filter Applied Successfully!")
                st.dataframe(filtered_df)
            else:
                st.warning(f"⚠️ No records found for {filter_column} = {filter_value}")
        else:
            st.warning("⚠️ Please enter a filter value.")


# filter by date and item only

# Date range input
    st.title("Requisitions Filter Options")

# Select filtering option
    filter_option = st.selectbox("Select Filter Type", ["Filter by Date", "Filter by Item & Date"])

    if filter_option == "Filter by Date":
        st.subheader("Filter Requisitions by Date")

        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")

    if st.button("Apply Date Filter"):
        if start_date and end_date:
            filtered_df = filter_by_date(start_date, end_date)

            if not filtered_df.empty:
                st.write("### Filtered Data")
                st.dataframe(filtered_df)
            else:
                st.warning("No results found for the selected date range.")

    elif filter_option == "Filter by Item & Date":
        st.subheader("Filter Requisitions by Item & Date")

        item = st.text_input("Enter Item Name (e.g., diesel, fuel, paper)")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        
        
        if st.button("Apply Item & Date Filter"):
            if item and start_date and end_date:
                filtered_df = filter_by_item_and_date(item, start_date, end_date)
                
                if not filtered_df.empty:
                    st.write(f"### Filtered Data for '{item}' from {start_date} to {end_date}")
                    st.dataframe(filtered_df)
                else:
                    st.warning(f"No results found for '{item}' in the selected date range.")
















# Reports

# Function to get total quantity per item within a date range
def get_summary_report(time_period, start_date, end_date):
    try:
        # Convert dates to string format
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        # Fetch raw data from Supabase
        response = supabase.table("inventory_log") \
            .select("date, item, stock_in, return_item, stock_out, closing_stock") \
            .gte("date", start_date_str) \
            .lte("date", end_date_str) \
            .execute()

        # ✅ Corrected error handling
        if hasattr(response, "data") and response.data:
            df = pd.DataFrame(response.data)
        else:
            st.error("❌ Supabase returned an empty response or an error occurred.")
            return pd.DataFrame()

        if df.empty:
            return pd.DataFrame()

        # Convert 'date' to datetime format
        df["date"] = pd.to_datetime(df["date"])

        # Define time grouping frequency
        time_trunc_map = {
            "Weekly": "W",
            "Monthly": "M",
            "Yearly": "Y"
        }

        if time_period not in time_trunc_map:
            st.error("❌ Invalid time period selected!")
            return pd.DataFrame()

        # Group and aggregate data
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

        # Rename 'date' column to 'period'
        df_summary.rename(columns={"date": "period"}, inplace=True)

        return df_summary

    except Exception as e:
        st.error(f"❌ Error fetching summary report: {str(e)}")
        return pd.DataFrame()

# 🔹 Streamlit UI for Reports
if "selected" in locals() and selected == "Reports":
    st.subheader("📊 Inventory Summary Reports")

    # Select Report Type
    report_type = st.selectbox("📆 Select Report Type", ["Weekly", "Monthly", "Yearly"])

    # Select Date Range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("📅 Start Date", date.today().replace(day=1))
    with col2:
        end_date = st.date_input("📅 End Date", date.today())

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
