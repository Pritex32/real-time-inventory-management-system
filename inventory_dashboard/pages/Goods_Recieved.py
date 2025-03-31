from http import cookies
import streamlit as st
import pandas as pd

from streamlit_option_menu import option_menu
from datetime import datetime,timedelta ,date 
import numpy as np
from streamlit_cookies_manager import EncryptedCookieManager
import json
import time

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
       
  



from supabase import create_client, client
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
        supabase = get_supabase_client()
        
        if not supabase:
            st.error("❌ Supabase client is not initialized!")
            return pd.DataFrame()

        # ✅ Fetch data from Supabase
        response = supabase.table("goods_received").select("*").execute()
        
        if response.data:  # ✅ Check if response has data
            return pd.DataFrame(response.data)
        else:
            st.warning("⚠️ No data found in Supabase!")
            return pd.DataFrame()

    except Exception as e:
        st.error(f"🚨 Error fetching data: {e}")
        return pd.DataFrame()

# ✅ Add a refresh button



st.subheader("📦 REAL TIME INVENTORY MANAGEMENT SYSTEM")
# ✅ Add a refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()  # ✅ Clear cached data
    st.rerun() # ✅ Force rerun of the app

# Display inventory log


# Insert interface


# lets put them in options
with st.sidebar:
    selected = option_menu(
        menu_title=('Options'),
        options=["Home page","Add Goods", "Delete",'Calculations',"Filter","Reports"],
        icons=["house", "plus-circle", "trash", "calculator","bar-chart-line"],
        default_index=0
    )


if selected == "Home page":
    st.success("✅ Welcome to the Inventory Dashboard!")
    df = fetch_data_from_supabase()
    if not df.empty:
        st.write(df) # Display the full dataframe
        st.write('Last ten rows ',df.tail(10)) 
    


# add sections

if selected == "Add Goods":
    st.subheader("📦 Add Goods Received")

    # ✅ Input Fields
    date = st.date_input("📅 Enter the date (YYYY-MM-DD)")
    items = st.text_input("🛒 Item")
    category = st.text_input("📂 Category")
    quantity = st.number_input("📊 Quantity", min_value=0, value=0)
    cost = st.number_input("💰 Cost", min_value=0, value=0)
    requested_quantity = st.number_input("📌 Request Quantity", min_value=0, value=0)
    supplier = st.text_input("🏢 Supplier")
    remark = st.text_input("📝 Remark")

    if st.button("➕ Add"):
        try:
            # ✅ Initialize Supabase client
            supabase = get_supabase_client()
            
            if not supabase:
                st.error("❌ Supabase client is not initialized!")
            else:
                # ✅ Insert Data into Supabase
                response = (
                    supabase.table("goods_received")
                    .insert({
                        "date": str(date),  # Convert to string for compatibility
                        "items": items,
                        "category": category,
                        "quantity": quantity,
                        "cost": cost,
                        "requested_quantity": requested_quantity,
                        "supplier": supplier,
                        "remark": remark,
                    })
                    .execute()
                )

                # ✅ Check if insert was successful
                if response.data:
                    st.success("✅ Goods Added Successfully!")
                else:
                    st.warning("⚠️ Failed to add goods. Please try again.")

        except Exception as e:
            st.error(f"🚨 Error adding goods: {e}")


# Delete Section


  ## to create delete button
def delete_requisition(req_id):
    try:
        # ✅ Initialize Supabase client
        supabase = get_supabase_client()
        
        if not supabase:
            st.error("❌ Supabase client is not initialized!")
            return
        
        # ✅ Delete the record from Supabase
        response = (
            supabase.table("goods_received")
            .delete()
            .eq("good_received_id", req_id)
            .execute()
        )

        # ✅ Check if deletion was successful
        if response.data:
            st.success(f"✅ Item with ID {req_id} deleted successfully!")
        else:
            st.warning(f"⚠️ No record found with ID {req_id}")

    except Exception as e:
        st.error(f"🚨 Error deleting item: {e}")

# ✅ Streamlit UI for Deleting an Item
if selected == "Delete":
    st.subheader("🗑️ Delete an Item")

    req_id = st.number_input("🔢 Enter the Serial Number", format="%d", step=1, min_value=1)

    if st.button("🗑️ Delete"):
        delete_requisition(req_id)






# calculations
def get_item_aggregation(items, start_date, end_date, aggregation):
    try:
        # ✅ Initialize Supabase client
        supabase = get_supabase_client()
        
        if not supabase:
            st.error("❌ Supabase client is not initialized!")
            return None

        # ✅ Fetch data from Supabase table
        response = (
            supabase.table("goods_received")
            .select("quantity")
            .eq("items", items)
            .gte("date", str(start_date))  # Convert date to string format
            .lte("date", str(end_date))
            .execute()
        )

        # ✅ Extract data
        if response.data:
            df = pd.DataFrame(response.data)

            # ✅ Perform aggregation
            if aggregation == "SUM":
                return df["quantity"].sum()
            elif aggregation == "MAX":
                return df["quantity"].max()
            elif aggregation == "MIN":
                return df["quantity"].min()
            elif aggregation == "AVG":
                return df["quantity"].mean()
        else:
            return 0  # Return 0 if no matching records found

    except Exception as e:
        st.error(f"🚨 Error fetching data: {e}")
        return None

# ✅ Streamlit UI for Calculations
if selected == "Calculations":
    st.subheader("📊 Table Manipulations")

    # Input for item name
    items = st.text_input("🔍 Enter Item Name (e.g., diesel, fuel, paper)")

    # Select aggregation type
    aggregation = st.selectbox("📊 Select Aggregation Type", ["SUM", "MAX", "MIN", "AVG"])

    # Date range input
    start_date = st.date_input("📅 Start Date")
    end_date = st.date_input("📅 End Date")

    if st.button("📈 Get Aggregated Quantity"):
        if items and start_date and end_date and aggregation:
            result = get_item_aggregation(items, start_date, end_date, aggregation)
        
            if result is not None:
                st.success(f"✅ {aggregation} quantity of '{items}' from {start_date} to {end_date}: {result:.2f}")
            else:
                st.warning("⚠️ No data found for the selected criteria.")
        else:
            st.warning("⚠️ Please fill in all fields.")





# filter for with each columns
# Function to filter inventory log by column
def filter_inventory_log(filter_column, filter_value):
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("goods_received")
            .select("*")
            .ilike(filter_column, f"%{filter_value}%")  # Case-insensitive filtering
            .execute()
        )
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error fetching filtered data: {e}")
        return pd.DataFrame()

# Function to filter by date range
def filter_by_date(start_date, end_date):
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("goods_received")
            .select("*")
            .gte("date", str(start_date))
            .lte("date", str(end_date))
            .execute()
        )
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return pd.DataFrame()

# Function to filter by item and date
def filter_by_item_and_date(items, start_date, end_date):
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("goods_received")
            .select("*")
            .eq("items", items)
            .gte("date", str(start_date))
            .lte("date", str(end_date))
            .execute()
        )
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return pd.DataFrame()

# Streamlit interface
if "selected" in locals() and selected == "Filter":
    st.title("🔍 Filter Options")

    filter_option = st.selectbox("📌 Select Filter Type", ["Filter by Date", "Filter by Item & Date"])

    if filter_option == "Filter by Date":
        st.subheader("📆 Filter Items by Date")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")

        if st.button("Apply Date Filter"):
            if start_date and end_date:
                filtered_df = filter_by_date(start_date, end_date)
                if not filtered_df.empty:
                    st.dataframe(filtered_df)
                else:
                    st.warning("⚠️ No results found for the selected date range.")

    elif filter_option == "Filter by Item & Date":
        st.subheader("📦 Filter Items by Item & Date")
        items = st.text_input("Enter Item Name")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")

        if st.button("Apply Item & Date Filter"):
            if items and start_date and end_date:
                filtered_df = filter_by_item_and_date(items, start_date, end_date)
                if not filtered_df.empty:
                    st.dataframe(filtered_df)
                else:
                    st.warning(f"⚠️ No results found for '{items}' in the selected date range.")





# Reports

# Function to get total quantity per item within a date range
def get_total_quantity_per_item(start_date, end_date):
    try:
        supabase = get_supabase_client()

        # Query Supabase table
        response = (
            supabase.table("goods_received")
            .select("items, quantity")
            .gte("date", str(start_date))
            .lte("date", str(end_date))
            .execute()
        )

        # Check if response contains data
        if response.data:
            df = pd.DataFrame(response.data)

            # Ensure 'quantity' is numeric
            df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")

            # Perform aggregation
            total_quantity_per_item = df.groupby("items")["quantity"].sum().reset_index()
            total_quantity_per_item = total_quantity_per_item.sort_values(by="quantity", ascending=False)

            return total_quantity_per_item
        else:
            return pd.DataFrame()

    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return pd.DataFrame()

# Streamlit UI for Reports section
if "selected" in locals() and selected == 'Reports':  
    st.subheader("📊 Goods Report - Total Quantity Per Item")

    # Date range filter
    st.sidebar.subheader("📅 Select Date Range")
    start_date = st.sidebar.date_input("Start Date") 
    end_date = st.sidebar.date_input("End Date")

    if st.sidebar.button("Apply Filter"):
        if start_date and end_date:
            df = get_total_quantity_per_item(start_date, end_date)
            
            if not df.empty:
                st.subheader(f"📊 Total Quantity by Items from {start_date} to {end_date}")
                st.dataframe(df)

                # Download as CSV
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download CSV", data=csv_data, file_name="total_quantity_per_item.csv", mime="text/csv")
            else:
                st.warning("No data available for the selected date range!")

