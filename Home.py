# imports section
import pandas as pd
import numpy as np
import plotly as pl
import streamlit as st 
import plotly.express as px
import re


#Function to add any chart to the page, and account for the click interactivity
def addChartToPage(fig):
    #Keep track of all current graphs
    if fig not in st.session_state['currentGraphs']:
        st.session_state['currentGraphs'].append(fig)
    
    #Display the graph
    chart = st.plotly_chart(fig, on_select="rerun", selection_mode=["points"])

    # If points are selected on the chart (clicked on)
    if chart['selection']['points']:
        for point in chart['selection']['points']:
            # Get hover template from first or second trace (fallback for heatmaps because of the way they are implemented)
            printout = fig.data[0].hovertemplate
            if (printout == None):
                printout = fig.data[1].hovertemplate
                
            with st.container():
                # Clean up the hover template format so that it works with the .format command from python
                printout = printout.replace("%{", "{")
                printout = printout.replace("<extra></extra>", "")
                printout = printout.replace("<br>", " ")
                
                # Find all variables in the template (anything between {} brackets)
                listOfVariables = re.findall("{(?:[^{}])*}", printout)
                
                # Process each variable in the template
                for initialVar in listOfVariables:
                    var = initialVar[1:-1]  # Remove brackets
                    
                    # Handle formatting qualifiers (e.g., :.2f)
                    try:
                        index = var.index(":")
                        qualifier = var[index:]
                        var = var[:index]
                    except:
                        qualifier = ""
                        var = var
                    
                    # Special handling for marker size and custom data, because they are treated differently in the hoverdata
                    if var == "marker.size":
                        var = "marker_size"
                    if "customdata" in var:
                        data = point["customdata"][int(var[-2:-1])]
                    else:
                        data = point[var]
                    
                    # Format the data and replace in template
                    formatting = ("{" + qualifier + "}")
                    final = formatting.format(data)
                    printout = printout.replace(initialVar, final)
                    
                # Display the formatted hover text as a printout beneath the graph
                st.write(printout)
                

    #If the figure hasn't been added to the workbook, display a button to allow users to add the graph
    if fig not in st.session_state['workbookGraphs']:
        if st.button("Add this graph to the workbook", key = fig):
            st.session_state['workbookGraphs'].append(fig)
            st.write("Graph added!")
    else:
        st.write("This graph is in the workbook!")



#Set a plotly default, which is necessary for the sankey graph to display correctly on streamlit
pl.io.templates.default = 'plotly'



#Title with custom formatting
st.markdown("<p style='text-align: center; font-size: 3em; font-weight: bold; color: #003478; margin-bottom: 0.5em; line-height: 1.2;'>Waltham Chamber of Commerce : Advanced Visualization Creator<p>", unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.5em; font-weight: bold; color: #003478; margin-bottom: 1.5em; line-height: 1.1; font-style: italic;">Created by: Rowan Scassellati, Caitlyn Pennie, Isabel Roseth, George Yan, and Jimkelly Percine</p>', unsafe_allow_html=True)
st.html(
    '''
    <style>
    hr {
        border: none;
        height: 2px;
        /* Set the hr color */
        color: #003478;  /* old IE */
        background-color: #003478;  /* Modern Browsers */
        margin-bottom: 0px;
        margin-top: 0px;
    }
    </style>
    '''
)
st.divider() #Divider with custom CSS styling

#Increase the size of the buttons and select options
tabs_font_css = """
<style>
div[class*="stCheckbox"] label p {
  font-size: 20px;
}

div[class*="stMultiSelect"] label p {
  font-size: 20px;
}

div[class*="stNumberInput"] label p {
  font-size: 20px;
}

div[class*="stTextInput"] label p {
  font-size: 20px;
}

div[class*="stRadio"] label p {
  font-size: 20px;

}

div[class*="stSelectbox"] label p {
  font-size: 20px;
}

div[data-testid="stExpander"] details summary p{
    font-size: 20px;
    font-weight: bold;
}
</style>
"""
st.write(tabs_font_css, unsafe_allow_html=True)

#Display the whole text in the "What type of visualizations should be generated?" multiselect button, rather than cutting them off
st.markdown("""
    <style>
        .stMultiSelect [data-baseweb=select] span{
            max-width: 500px;
        }
    </style>
    """, unsafe_allow_html=True)

#Initial state to upload the data file
if 'dataFile' not in st.session_state:
    st.markdown('<p style="font-size: 20px; ">In order to get started, please add the excel file that contains the correctly formatted Waltham Chamber of Commerce data</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("In order to get started, please add the excel file that contains the correctly formatted Waltham Chamber of Commerce data", label_visibility="collapsed")
else:
    uploaded_file = st.session_state['dataFile']

if uploaded_file is None:
    st.session_state['checkFile'] = True

def findPairings(dateRemoved = None):
    dateNamePairing = st.session_state['dateNamePairing']
    temp_df = st.session_state['originalDF'].copy()
    mappingPairs = {}
    for ind in dateNamePairing.index:
        mappingPairs[dateNamePairing.loc[ind]['Date']] = dateNamePairing.loc[ind]

    st.session_state['Unknown Dates'] = []
    eventName = []
    nonMemberPrice = []
    memberPrice = []
    for ind in temp_df.index:
        date = temp_df.loc[ind]['Timestamp']
        if date in mappingPairs:
            eventName.append(mappingPairs[date].iloc[1])
            nonMemberPrice.append(mappingPairs[date].iloc[2])
            memberPrice.append(mappingPairs[date].iloc[3])
        else:
            if date not in st.session_state['Unknown Dates']:
                st.session_state['Unknown Dates'].append(date)
            eventName.append(None)
            nonMemberPrice.append(None)
            memberPrice.append(None)
    temp_df['eventName'] = eventName
    temp_df['nonMemberPrice'] = nonMemberPrice
    temp_df['memberPrice'] = memberPrice

    temp_df.dropna(subset=['eventName'], inplace=True)
    st.session_state['df'] = temp_df


st.markdown("""
<style>
h3 {
    text-align: center; 
    margin: auto;
    font-size: 3em; 
    font-weight: bold; 
    color: #003478; 
    margin-bottom: 1.5em; 
    line-height: 1.2; 
    font-style: italic;
}
</style>
""", unsafe_allow_html=True)


def updatePairingFile(date, title, eventMemberPrice, eventNonMemberPrice):
    currentDF = st.session_state['dateNamePairing']
    currentDF.loc[len(currentDF)] = [date, title, eventMemberPrice, eventNonMemberPrice]
    currentDF.to_excel('DateNamePairings.xlsx', index=False)
    st.session_state['dateNamePairing'] = currentDF
    findPairings(date)


#Process the data file once uploaded
if uploaded_file is not None and st.session_state['checkFile'] == True:
    st.session_state['dataFile'] = uploaded_file

    #Read the excel file and different sheets, using a faster calamine engine
    xls = pd.read_excel(uploaded_file, sheet_name=['Sheet1'])

    # Access individual sheets using sheet names
    temp_df = xls['Sheet1']

    temp_df["Is your organization a sponsor of this event?"] = temp_df["Is your organization a sponsor of this event?"].str.lower().map({'yes': True, 'no': False})
    temp_df["Is your organization a member of the Waltham Chamber of Commerce?"] = temp_df["Is your organization a member of the Waltham Chamber of Commerce?"].str.lower().map({'yes': True, 'no': False})
    temp_df['Timestamp'] = pd.to_datetime(temp_df['Timestamp']).dt.date

    dateNamePairing = pd.read_excel("DateNamePairings.xlsx", engine = 'calamine', sheet_name=['Sheet1'])['Sheet1']


    dateNamePairing['Date'] = pd.to_datetime(dateNamePairing['Date']).dt.date

    st.session_state['dateNamePairing'] = dateNamePairing

    


    st.session_state['checkFile'] = False
    st.session_state['currentGraphs'] = []
    st.session_state['originalDF'] = temp_df
    st.session_state['updatedMissingData'] = False
    findPairings()

    #Reload the page once everything has been processed so the prompt to input data is removed
    st.rerun()
    
print("Website reloaded!")



#Once the file has been uploaded, this will always run
if uploaded_file is not None and st.session_state['checkFile'] == False:
    df = st.session_state['df']
    st.dataframe(df)
    

    def calculateCost(row):
        if row['Is your organization a member of the Waltham Chamber of Commerce?']:
            return row["Number of attendees from your company?"] * row["memberPrice"]
        else:
            return row["Number of attendees from your company?"] * row["nonMemberPrice"]

    df['Cost'] = df.apply(calculateCost, axis=1)

    if st.session_state['updatedMissingData']:
        st.toast("Information submitted, thank you for updating the data!")
    st.session_state['updatedMissingData'] = False
    unknownDates = st.session_state['Unknown Dates']
    if (len(unknownDates) != 0):
        st.write("There are some dates needing updates!")
        for realDate in unknownDates:
            date = str(realDate)
            with st.form(date):
                title = st.text_input("If there was an event on " + date + ", please input the name of the event", value = "Event Name Here",key = "Title" + date)
                eventMemberPrice = st.number_input("Please input the price of the event for members", min_value=0, value=None, step=1, key = "Member" + date)
                eventNonMemberPrice = st.number_input("Please input the price of the event for nonmembers", min_value=0, value=None, step=1, key = "Nonmember" + date)
                notEvent = st.checkbox("If there was not a Waltham Chamber of Commerce event on that day, please click this box. Please note: This cannot be undone once submitted")
                submitButton = st.form_submit_button("Submit information")

                if submitButton:
                    if (eventMemberPrice != None and eventNonMemberPrice != None and title != "Event Name Here") or notEvent:
                        if notEvent:
                            updatePairingFile(realDate, None, None, None)
                        else:
                            updatePairingFile(realDate, title, eventMemberPrice, eventNonMemberPrice)
                        st.session_state['updatedMissingData'] = True
                        
                        st.rerun()
                    else:
                        st.write(":red[Some data has not been updated yet. Please update all fields and then submit again.]")

        # st.write(st.session_state['Unknown Dates'])
    barChart = px.bar(df, x="Timestamp", y="Number of attendees from your company?")
    addChartToPage(barChart)

    barChart2 = px.bar(df, x="eventName", y="Number of attendees from your company?")
    addChartToPage(barChart2)

    barChart3 = px.bar(df, x="eventName", y="Cost")
    addChartToPage(barChart3)


    grouped = df.groupby('eventName').sum(["Is your organization a member of the Waltham Chamber of Commerce?",  'Number of attendees from your company?', "Is your organization a sponsor of this event?", "Cost"])
    st.write(grouped)


    barChart4 = px.bar(grouped, x=grouped.index, y="Cost")
    addChartToPage(barChart4)

    barChart4 = px.bar(grouped, x=grouped.index, y="Number of attendees from your company?")
    addChartToPage(barChart4)


    grouped2 = df.groupby(["Is your organization a member of the Waltham Chamber of Commerce?", 'eventName']).sum(['Number of attendees from your company?'])
    grouped2.reset_index(inplace =True)
    grouped2["Is your organization a member of the Waltham Chamber of Commerce?"] = grouped2["Is your organization a member of the Waltham Chamber of Commerce?"].astype(str).str.lower().map({"true": 'Member', "false": 'Not a Member'})
    
    barPlot2 = px.bar(
    grouped2,
    x="eventName",
    y="Number of attendees from your company?",
    color="Is your organization a member of the Waltham Chamber of Commerce?", 
    title="Attendance by Membership Status",
    labels={
        "Number of attendees from your company?": "Number of Attendees",
        "Is your organization a member of the Waltham Chamber of Commerce?": "Membership Status",
        
    },
    text="Number of attendees from your company?", 
    )
    addChartToPage(barPlot2)
   

    col1, col2, col3 = st.columns(3, vertical_alignment="center")

    
    with col1:
        left_co, cent_co,last_co = st.columns([0.1,0.8,0.1])
        with cent_co:
            st.image("images/realWaltham1.jpeg")
        
        st.markdown('<div style="width: 100%; text-align: center;"> <a target="_self" href="#firstSection" style="text-align: center; margin: auto; font-size: 1.5em; font-weight: bold; color: #003478; margin-bottom: 1.5em; line-height: 1.1; font-style: italic;">Check out Visualizations about the Most Recent Event</a> </div>', unsafe_allow_html=True)

    with col2:
        left_co, cent_co,last_co = st.columns([0.1,0.8,0.1])
        with cent_co:
            st.image("images/realWaltham2.jpeg")
        st.markdown('<div style="width: 100%; text-align: center;"> <a target="_self" href="#secondSection" style="text-align: center; margin: auto; font-size: 1.5em; font-weight: bold; color: #003478; margin-bottom: 1.5em; line-height: 1.1; font-style: italic;">Check out Visualizations for the Top Performing Events</a> </div>', unsafe_allow_html=True)

    with col3:
        left_co, cent_co,last_co = st.columns([0.1,0.8,0.1])
        with cent_co:
            st.image("images/realWaltham3.jpeg")
        st.markdown('<div style="width: 100%; text-align: center;"> <a target="_self" href="#thirdSection" style="text-align: center; margin: auto; font-size: 1.5em; font-weight: bold; color: #003478; margin-bottom: 1.5em; line-height: 1.1; font-style: italic;">Check out Visualizations to see Recent Trends in Events</a> </div>', unsafe_allow_html=True)
    
    st.subheader("Most Recent Event Visualizations", anchor="firstSection")  
    st.subheader("Top Performing Events", anchor="secondSection")  

    pieCol1, pieCol2 = st.columns(2)
    with pieCol1:
        # Calculate revenue for each event by multiplying the number of attendees with the respective price
        df['Revenue'] = df.apply(lambda row: row['Number of attendees from your company?'] * row['memberPrice'] 
                            if row['Is your organization a member of the Waltham Chamber of Commerce?'] == True 
                            else row['Number of attendees from your company?'] * row['nonMemberPrice'], axis=1)

    # Group by event name and sum the revenue
        grouped_revenue = df.groupby('eventName')['Revenue'].sum().reset_index()

    # Sort the events by revenue in descending order and get the top 5
        top_5_revenue = grouped_revenue.sort_values(by='Revenue', ascending=False).head(5)

    # Create a pie chart for the top 5 events by revenue
        pie_chart = px.pie(
            top_5_revenue,
            names='eventName',
            values='Revenue',
            title='Top 5 Events by Revenue',
            labels={'Revenue': 'Revenue ($)', 'eventName': 'Event Name'},
        )

        addChartToPage(pie_chart)


    # top 5 events by attendance 
        grouped_attendance = df.groupby('eventName')['Number of attendees from your company?'].sum().reset_index()

        top_5_attendance = grouped_attendance.sort_values(by='Number of attendees from your company?', ascending=False).head(5)

        pie_chart = px.pie(
            top_5_attendance,
            names='eventName',
            values='Number of attendees from your company?',
            title='Top 5 Events by Attendance',
            labels={'Number of attendees from your company?': 'Number of Attendees', 'eventName': 'Event Name'},
        )
        
        addChartToPage(pie_chart)

    with pieCol2:
        # top 5 events by members

        df_members = df[df['Is your organization a member of the Waltham Chamber of Commerce?'] == True]

        grouped_members = df_members.groupby('eventName')['Number of attendees from your company?'].sum().reset_index()

        top_5_members = grouped_members.sort_values(by='Number of attendees from your company?', ascending=False).head(5)

        pie_chart_members = px.pie(
            top_5_members,
            names='eventName',
            values='Number of attendees from your company?',
            title='Top 5 Events by Members',
            labels={'Number of attendees from your company?': 'Number of Members', 'eventName': 'Event Name'},
        )
        addChartToPage(pie_chart_members)

        # top 5 events by non_members
        
        df_non_members = df[df['Is your organization a member of the Waltham Chamber of Commerce?'] == False]

        grouped_non_members = df_non_members.groupby('eventName')['Number of attendees from your company?'].sum().reset_index()

        top_5_members = grouped_non_members.sort_values(by='Number of attendees from your company?', ascending=False).head(5)

        pie_chart_non_members = px.pie(
            top_5_members,
            names='eventName',
            values='Number of attendees from your company?',
            title='Top 5 Events by Non - Members',
            labels={'Number of attendees from your company?': 'Number of Non - Members', 'eventName': 'Event Name'},
        )
        addChartToPage(pie_chart_non_members)
    
    st.subheader("Recent Event Trends", anchor="thirdSection")  