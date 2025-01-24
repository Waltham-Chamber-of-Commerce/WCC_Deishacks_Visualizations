# Import required libraries
import plotly as pl  # Import plotly for data visualization
import streamlit as st  # Import streamlit for web app creation

# Set the default template for plotly graphs, otherwise some features of the sankey diagrams won't display properly on the streamlit page
pl.io.templates.default = 'plotly'

# Configure the default Streamlit page layout - full width with collapsed sidebar
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

# Initialize workbookGraphs in session state if it doesn't exist
# This list will store graphs added to the workbook
if 'workbookGraphs' not in st.session_state:
    st.session_state['workbookGraphs'] = []

# Create page objects for different sections of the app
workbook = st.Page("Workbook.py")  # Create workbook page
home = st.Page("Home.py")  # Create home page (where visualizations are created)

# Set up navigation between pages
navigate = st.navigation([home, workbook])  # Create navigation with home and workbook pages
navigate.run()  # Execute the navigation system
