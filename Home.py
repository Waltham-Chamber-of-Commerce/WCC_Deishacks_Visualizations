# imports section
import pandas as pd
import numpy as np
import plotly as pl

import matplotlib.pyplot as plt
import os
import xarray as xr

import streamlit as st 
import matplotlib
import mpld3
import streamlit.components.v1 as components
import matplotlib as mpl
from matplotlib import cm
from matplotlib import colors
import datetime
import plotly.graph_objects as go
import statistics
import plotly.express as px
from plotly.subplots import make_subplots
import re
from io import BytesIO




# Manual dictionary mapping engagement types to their categories, no longer actively used
# Used to standardize and group different types of career center activities
engagementMapping = {
    'Appointment':  'Appointment',
    'Group Appointment':  'Appointment',
    'Career Fair':  'Career Fair',
    'Drop-In/Chat':  'Drop-In/Chat',
    'Employer On-Site':  'Employer Activity ',
    'Employer Partner Event':  'Employer Activity ',
    'Employer Site Visit':  'Employer Activity ',
    'Trek':  'Employer Activity ',
    'OCI':  'Employer Activity ',
    'Info Session':  'Employer Activity ',
    'Career Course':  'Career Course ',
    'Hiration':  'Hiration ',
    'Networking':  'Networking Event',
    'Mentor Meetup':  'Networking Event',
    'Speaker/Panel':  'Networking Event',
    'Type Focus':  'Type Focus ',
    'Hiatt Funding':  'Hiatt Funding',
    'Virtual Session':  'Workshop/Event',
    'Classroom Presentation':  'Workshop/Event',
    'Club Presentation':  'Workshop/Event',
    'Orientation':  'Workshop/Event',
    'Workshop':  'Workshop/Event',
    'Employment Toolkit':  'Online Resource ',
    'Forage':  'Online Resource ',
    'Rise Together':  'Rise Together',
    'WOW':  'Do not Include',
    'Completed Handshake Profile':  'Do not Include',
    'Alumni Interview Coaching':  'Do not Include',
    'BIX Review':  'Do not Include',
    'Career Closet':  'Do not Include',
    'CIC Career Fair':  'Do not Include',
    'Club Support':  'Do not Include',
    'HS Employer Review':  'Do not Include',
    'HS Interview Review':  'Do not Include',
    'Library Book':  'Do not Include',
    'LinkedIn Photobooth':  'Do not Include',
    'Mentor Program':  'Do not Include',
    'Micro-internships':  'Do not Include',
    'Other':  'Do not Include',
    'Wisdom Wanted Ad':  'Do not Include',
    'appointment':  'Appointment',
    'Employer On-site':  'Employer Activity ',
    'HS Job Review':  'Do not Include',
}



###Helper Functions###


#Standardizes semester formatting in the dataset
#Handles special cases like Winter terms and FY notation
def clean_semesters(row):
    string = row['Semester']
    if "Winter" in string:
        string = "Winter 20" + str((int(string[-3:-1]) - 1))
    if "(FY" in string:
        string = string[:string.rfind('(')-1]
    if "FAll" in string:
        string = "Fall" + string[4:]
    return string

# Converts semester strings into numerical values for sorting
#     Base year is 2017, each year has 4 terms
#     Returns numerical value and updates mapping dictionary
def create_semester_value(str, map):
        date = int(str[-4:])
        num = (date - 2017) * 4 + 1
        if "Fall" in str:
            num += 1
        if "Winter"in str:
            num += 2
        if "Spring" in str:
            num += -1
        if "Summer" in str:
            num += 0
        map[num] = str
        return num

# Creates normalized semester values relative to graduation date
#     Used for tracking student progress through their academic career
def create_aggregated_semester_value(str, graduationSemester):
        if graduationSemester in [0, 'nan', 'None', np.nan]:
            return -9999
        date = int(str[-4:])
        gradYear = (int(graduationSemester[-4:]) - 2021)
        if "Fall" in graduationSemester:
            gradYear += 1
        num = (date - 2017) * 4 + 1
        if "Fall" in str:
            num += 1
        if "Winter"in str:
            num += 2
        if "Spring" in str:
            num += -1
        if "Summer" in str:
            num += 0
        num -= (gradYear *4)
        return num

#Calculates the semester based on the semester number
def create_semester_value_from_number(num, map):
        year = str(int(num/4) + 2017)
        if num%4 == 1:
            year = "Summer " + year
        if num%4 == 2:
            year = "Fall " + year
        if num%4 == 3:
            year = "Winter " + year
        if num%4 == 0:
            year = "Spring " + year
        
        map[num] = year
        return num

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

import streamlit as st
import pandas as pd
from io import StringIO

#Set a plotly default, which is necessary for the sankey graph to display correctly on streamlit
pl.io.templates.default = 'plotly'



#Title with custom formatting
st.markdown("<p style='text-align: center; font-size: 3em; font-weight: bold; color: #003478; margin-bottom: 0.5em; line-height: 1.2;'>Hiatt Career Center -- Advanced Visualization Creator<p>", unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.5em; font-weight: bold; color: #003478; margin-bottom: 1.5em; line-height: 1.1; font-style: italic;">Created By: Rowan Scassellati and Jon Schlesinger</p>', unsafe_allow_html=True)
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
    st.markdown('<p style="font-size: 20px; ">In order to get started, please add the excel file that contains the correctly formatted Hiatt data</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("In order to get started, please add the excel file that contains the correctly formatted Hiatt data", label_visibility="collapsed")
else:
    uploaded_file = st.session_state['dataFile']

if uploaded_file is None:
    st.session_state['checkFile'] = True




#Process the data file once uploaded
if uploaded_file is not None and st.session_state['checkFile'] == True:
    st.session_state['dataFile'] = uploaded_file

    #Read the excel file and different sheets, using a faster calamine engine
    xls = pd.read_excel(uploaded_file, engine = 'calamine', sheet_name=['Data', 'Demographics', 'Event Groupings', 'Event Rankings', 'Majors and Minors', 'Majors and Minors Groupings', 'Graduate Emails'])

    # Access individual sheets using sheet names
    data_df = xls['Data']
    demographics = xls['Demographics']
    groupings = xls['Event Groupings']
    rankings = xls['Event Rankings']
    majors = xls['Majors and Minors']
    majorsGroupings = xls['Majors and Minors Groupings']
    graduateEmails = xls['Graduate Emails']

    
    

    #Bits of data cleaning to account for inconsistencies in the data
    data_df['Semester'] = data_df['Semester'].str.strip()


    originalEngagementMapping = {}
    groupings['Event Type Name'] = groupings['Event Type Name'].str.lower()
    data_df['Event Type Name'] = data_df['Event Type Name'].str.lower()


    #Create a mapping for the event type groupings
    for ind in groupings.index:
        originalEngagementMapping[groupings['Event Type Name'][ind]] = groupings['Event Type Summarized\r\nIn order to ignore this event, use "Do not Include"'][ind]


    def engagement_categories(row):
        return originalEngagementMapping[row['Event Type Name']]
    data_df['Engagement Type'] = data_df.apply(engagement_categories, axis=1)

    #Ignore all categories marked as "Do not Include"
    data_df = data_df.drop(data_df[data_df['Engagement Type'] == 'Do not Include'].index)

    eventRankings = {}

    #Create a mapping for the ranking of the events
    for ind in rankings.index:
        eventRankings[rankings['Types of Event Groupings\r\nDO NOT MODIFY -- PULLS FROM EVENT GROUPINGS TAB!'][ind]] = rankings['Ranked Importance of Events'][ind]
    def ranking_events(row):
        return eventRankings[row['Engagement Type']]
     
    #Add to the dataframe the rankings for each event
    data_df['Event Ranking from User'] = data_df.apply(ranking_events, axis=1)

    rankings = rankings.sort_values(['Ranked Importance of Events'], ascending=[True])
    rankedEngagementList = list(rankings['Types of Event Groupings\r\nDO NOT MODIFY -- PULLS FROM EVENT GROUPINGS TAB!'])
    
    #Create a list that is sorted based on the ranked importance of each event
    st.session_state['RankedEngagementList'] = [x for x in rankedEngagementList if "Do not Include" not in x]

    #Bits of data cleaning to account for inconsistencies in the data
    demographics['Email'] = demographics['Email'].str.lower()
    data_df['Email'] = data_df['Email'].str.lower()

    #Create and use a mapping to figure out the garduation date of all students
    gradMapping = {np.nan: None}
    for ind in demographics.index:
        gradMapping[demographics['Email'][ind]] = demographics['Expected Completion Period'][ind]

    
    def gMap(email):
        if email in gradMapping:
           return gradMapping[email]
        else:
            return np.nan

    data_df['Graduation_Semester'] = data_df.apply(lambda x: gMap(x.Email), axis = 1)

    #Create a list of the graduation years, sort it, and save it to use for the "restrict by graduating class" option
    graduationYears = set(gradMapping.values())
    graduationYears = [s.strip()[-4:] for s in graduationYears if str(s) not in ['0', 'nan', 'None']]
    graduationYears = list(set(graduationYears))
    graduationYears.sort(reverse = True)
    graduationYears.insert(0, "Do not restrict by graduation year")
    st.session_state['Graduation List'] = graduationYears


    #Create and use a mapping to group the majors into their categories
    majorsGroupingsMapping = {}
    for ind in majorsGroupings.index:
        majorsGroupingsMapping[majorsGroupings['Types of Majors'][ind]] = majorsGroupings['Majors (Restricted List)'][ind]
    
    def majorsGroupingsMap(major):
        return majorsGroupingsMapping[major]
    
    majors['Majors'] = majors['Majors Name']
    majors['Majors Name'] = majors.apply(lambda x: majorsGroupingsMap(x.Majors), axis = 1)

    majors['Email'] = majors['Students Email - Institution'].str.lower()


    #Create a mapping that takes each email as a key and stores a list of all their majors
    majorsMapping = {np.nan: []}
    for ind in majors.index:
        email = majors['Email'][ind]
        if (email not in majorsMapping):
            majorsMapping[email] = [majors['Majors Name'][ind]]
        else:
            majorsMapping[email].extend([majors['Majors Name'][ind]])
    st.session_state['Majors Mapping'] = majorsMapping
    
    def majorsMap(email):
        if email not in majorsMapping:
            return "No Major Found"
        else:
            return majorsMapping[email]

    #Add each students major list to the dataframe
    data_df['Majors'] = data_df.apply(lambda x: majorsMap(x.Email), axis = 1)

    majorsList = sorted(set(majorsGroupings['Majors (Restricted List)']))
    st.session_state['Majors List'] = majorsList

    #Store default fine tuning states, so that they can be modified as desired without needing to be initialized repeatedly
    st.session_state['graphsGenerated'] = False
    st.session_state['df'] = data_df
    st.session_state['graduateEmails'] = graduateEmails
    st.session_state['checkFile'] = False
    st.session_state['sankeyColumns'] = 3
    st.session_state['sankeyLineWeight'] = 3
    st.session_state['neverEngagedBefore'] = False
    st.session_state['neverEngagedAgain'] = False
    st.session_state['scatterMinimumSize'] = 3
    st.session_state['majorsToInclude'] = []
    st.session_state['aggregatedScatter'] = "Do not aggregate (default)"
    st.session_state['scatterMaxPercentile'] = float(100.0)
    st.session_state['numbervspercent'] = False
    st.session_state['restrictByKnownGraduates'] = False
    st.session_state['downloadFile'] = False
    st.session_state['steppedColorbars'] = False
    st.session_state['numberOfColorDivisions'] = 5
    st.session_state['graduationYearToRestrictBy'] = "Do not restrict by graduation year"
    st.session_state['graphTypes'] = []
    st.session_state['advancedOptions'] = False

    st.session_state['restrictingDataOptions'] = False
    st.session_state['sankeyGraphOptions'] = False
    st.session_state['scatterPlotOptions'] = False
    st.session_state['otherOptions'] = False
    st.session_state['lineGraphEngagementOptions'] = ['Any Engagement']

    #Reload the page once everything has been processed so the prompt to input data is removed
    st.rerun()
    

#Once the file has been uploaded, this will always run
if uploaded_file is not None and st.session_state['checkFile'] == False:
    #These methods are necessary to use the session state keys for the later fine tuning buttons without breaking other things, if this doesn't happen it does not work properly
    def store_value(key):
        st.session_state[key] = st.session_state["_"+key]
    def load_value(key):
        st.session_state["_"+key] = st.session_state[key]


    #Allow the user to choose the graph types
    load_value("graphTypes")
    st.session_state['graphTypes'] = st.multiselect(
        "What type of visualizations should be generated?",
        ["Sequential Pathways of Student Engagements", "Engagement Relationships (Unique)", "Engagement Relationships (Total)", "First Engagements Data (Unique)", "First Engagements Data (Total)", "Return Rates Based on All Engagements", "Return Rates Based on First Engagements", "Rates of Unique Engagements", "Students with only 1 Engagement", "Total Engagement Percentages", "When Students Engaged with Hiatt"],
        key="_graphTypes", on_change=store_value, args=["graphTypes"]
    )
    
    #Function which allows the user to generate an excel file that they can download with the necessary data cleaning used by this program
    def downloadExcelFile(df):
        #Almost all of this code is mirrored below in this file, and as such for further clarity comments will be added in the below section
        #The general premise of this function is to perform all of the same data cleaning that normally happens before graphs are produced
        graduationYearToRestrictBy = st.session_state['graduationYearToRestrictBy']
        graphTypes = st.session_state['graphTypes']

        
        df = st.session_state['df'].copy()
        
        df['Unique ID'] = df.groupby(['Email']).ngroup()
        df['Semester'] = df.apply(clean_semesters, axis=1)

        def updatedRestrictByCohort(df, graduationYear):
            df.drop(df[
                (df['Graduation_Semester'] != 'Spring Semester ' + str(graduationYear)) &
                (df['Graduation_Semester'] != 'Summer Semester ' + str(graduationYear)) &
                (df['Graduation_Semester'] != 'GPS Spring Semester ' + str(graduationYear)) &
                (df['Graduation_Semester'] != 'GPS Fall Semester ' + str(graduationYear-1)) &
                (df['Graduation_Semester'] != 'Fall Semester ' + str(graduationYear-1))].index, inplace=True)
            return df
        def restrictByCohort(df, graduationYear):
            df.drop(df[
                ((df['Class Level'] != 'Senior') &
                (df['Class Level'] != 'Junior')  &
                (df['Class Level'] != 'Sophomore') &
                (df['Class Level'] != 'Freshman'))
                ].index, inplace=True)
            df.drop(df[((df['Semester'] == (str(graduationYear-1) + 'Fall')))].index, inplace=True)
            df.drop(df[((df['Class Level'] == 'Senior') & 
                    ((df['Semester'] != ('Summer ' + str(graduationYear-1))) & 
                    (df['Semester'] != ('Fall ' + str(graduationYear-1))) &
                    (df['Semester'] != ('Winter ' + str(graduationYear-1))) & 
                    (df['Semester'] != ('Spring ' + str(graduationYear)))))].index, inplace=True)
            df.drop(df[((df['Class Level'] == 'Junior') & 
                    ((df['Semester'] != ('Summer ' + str(graduationYear-2))) & 
                    (df['Semester'] != ('Fall ' + str(graduationYear-2))) &
                    (df['Semester'] != ('Winter ' + str(graduationYear-2))) & 
                    (df['Semester'] != ('Spring ' + str(graduationYear-1)))))].index, inplace=True)
            df.drop(df[((df['Class Level'] == 'Sophomore') & 
                    ((df['Semester'] != ('Summer ' + str(graduationYear-3))) & 
                    (df['Semester'] != ('Fall ' + str(graduationYear-3))) &
                    (df['Semester'] != ('Winter ' + str(graduationYear-3))) & 
                    (df['Semester'] != ('Spring ' + str(graduationYear-2)))))].index, inplace=True)
            df.drop(df[((df['Class Level'] == 'Freshman') & 
                ((df['Semester'] != ('Summer ' + str(graduationYear-4))) & 
                (df['Semester'] != ('Fall ' + str(graduationYear-4))) &
                (df['Semester'] != ('Winter ' + str(graduationYear-4))) & 
                (df['Semester'] != ('Spring ' + str(graduationYear-3)))))].index, inplace=True)
            return(df)



        if(graduationYearToRestrictBy != 'Do not restrict by graduation year'):
            df = updatedRestrictByCohort(df, int(graduationYearToRestrictBy))
            subtitle = "Graduating class of " + graduationYearToRestrictBy
        else:
            subtitle = "Data not restricted by graduating class"

        def event_sizes(row):
            return eventSize[row['Engagement Type']]


        eventSize = df.groupby('Engagement Type').count().to_dict(orient='dict')['Semester']
        df['Event Size'] = df.apply(event_sizes, axis=1)


        mapping = {}
        events = df.groupby('Engagement Type').count().to_dict(orient='dict')['Unique ID']
        sorted_events = sorted(events.items(), key=lambda x:x[1], reverse=True)
        sorted_events_dictionary = dict(sorted_events)
        
        x=0
        while x < len(sorted_events):
            mapping[sorted_events[x][0]] = x+1
            x +=1

        def ranked_events(row):
            return mapping[row['Engagement Type']]
        df['Ranked Events'] = df.apply(ranked_events, axis=1)

        originalEngagementList = st.session_state['RankedEngagementList']

        total = pd.DataFrame(index = originalEngagementList, columns=originalEngagementList)
        for col in total.columns:
            total[col].values[:] = 0

        majorsToInclude = set(st.session_state['majorsToInclude'])
        if len(majorsToInclude) > 0:
            to_delete = list()
            for id, row in df.iterrows():
                if not set(row.Majors).intersection(majorsToInclude):
                    to_delete.append(id)
            df.drop(to_delete, inplace=True)

            subtitle += ", only including students with majors in the following categories: " + ', '.join(majorsToInclude)
        else:
            if subtitle == "Data not restricted by graduating class":
                subtitle += " or students major"
            else:
                subtitle += ", data not restricted by students major"

        
        if st.session_state['restrictByKnownGraduates']:
            if subtitle != "Data not restricted by graduating class or students major":
                subtitle += "<br>Data also restricted to only include students known to have graduated"
            else:
                subtitle = "Data restricted to only include students known to have graduated, but not by students major or graduating class"
            
            graduateEmailsDF = st.session_state['graduateEmails']
            graduateEmailsList = graduateEmailsDF.values.flatten()
            df = df[df['Email'].isin(graduateEmailsList)]



        df = df.sort_values(['Unique ID', 'Events Start Date Date'], ascending=[True, True])
        df.reset_index(drop=True, inplace=True)
        
        
        #Unique section that may not be mirrored below
        graduateEmailsDF = st.session_state['graduateEmails']
        graduateEmailsList = graduateEmailsDF.values.flatten()
        #Calculate if the engagement is a students first engagement by checking if it is duplicated using pandas functions (for ease and speed)
        df['First Engagement?'] = df['Unique ID'].duplicated().map({True: "No", False: "Yes"})
        #Calculate if the engagement is a students last engagement by checking if it is duplicated earlier in the dataframe using pandas functions (for ease and speed)
        df['Last Engagement?'] = df['Unique ID'].duplicated(keep='last').map({True: "No", False: "Yes"})
        #Caclulate the number of engagements for each student using the groupby function
        df["Student's Number of Engagements"] = df.groupby('Unique ID')['Unique ID'].transform('count')
        #Add whether the student is a known graduate or not
        df["Known Graduate?"] = np.where(df['Email'].isin(graduateEmailsList), 'Graduate', 'Not Graduate')
        
        #Delete unwanted columns
        df.drop(['Unnamed: 16', 'Unnamed: 17', 'Unnamed: 18', 'Unnamed: 19', 'Email.1', 'Self-Reported Graduation Date', "Event Type Name", 'Medium', 'Event Originator', "Event Medium", "Host", "Event Ranking from User", "Event Size", "Ranked Events"], axis=1, inplace=True)
        #Add a column to display how the data is restricted
        df.insert(0, subtitle, None) 

        #Create an excel file from the dataframe that is returned by the file 
        def to_excel(df):
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='Sheet1', engine = 'xlsxwriter')
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']
            format1 = workbook.add_format({'num_format': '0.00'}) 
            worksheet.set_column('A:A', None, format1)  
            writer._save()
            processed_data = output.getvalue()
            return processed_data
        df_xlsx = to_excel(df)
        
        return df_xlsx
        



        
    #The following sections show all the options and add them to the website, using standard streamlit functions and sometimes providing restrictions (like max or min values) to attempt to ensure the program runs correctly
    st.divider()
    with st.expander("Show ways to restrict the data, which applies to all graphs"):
        st.divider()
        load_value("graduationYearToRestrictBy")
        st.selectbox("What graduating class should the data be from?", st.session_state['Graduation List'], key = "_graduationYearToRestrictBy", on_change=store_value, args=["graduationYearToRestrictBy"])
        load_value("majorsToInclude")
        st.multiselect("What majors should be included? Pulls from the graduation records, so it does not matter when a student declared", st.session_state['Majors List'], placeholder = "If left blank, will include all data", key = "_majorsToInclude", on_change=store_value, args=["majorsToInclude"])
        load_value("restrictByKnownGraduates")
        st.checkbox("Restrict data to only include students who are known to have graduated (data starts in 2021)", key = "_restrictByKnownGraduates", on_change=store_value, args=["restrictByKnownGraduates"])

    st.divider()
    with st.expander("Show fine tuning options for the scatter plots"):
        st.divider()
        load_value("scatterMinimumSize")
        st.number_input(label = "Minimum engagement size in all scatter Plots (based on number of engagements)", min_value=1, key = "_scatterMinimumSize", on_change=store_value, args=['scatterMinimumSize'],  format = "%d")
        load_value("scatterMaxPercentile")
        st.number_input(label = "Restrict maximum percentile for the color bar in scatter plots -- useful if one or two outliers are disrupting the full picture. Recommended to keep this number between 95-100.", min_value=1.0, max_value=100.0, format = "%f", key = "_scatterMaxPercentile", on_change=store_value, args=['scatterMaxPercentile'])
        load_value("numbervspercent")
        st.checkbox("Use total number for scatter plots (where appropriate) instead of percentage", key = "_numbervspercent", on_change=store_value, args=["numbervspercent"])
    st.divider()
    with st.expander("Show fine tuning options for the sankey diagram"):
        st.divider()
        load_value("sankeyColumns")
        st.number_input(label = "Number of columns in the Sankey Diagram", min_value=2, format = "%d", key = "_sankeyColumns", on_change=store_value, args=['sankeyColumns'])
        load_value("sankeyLineWeight")
        st.number_input(label = "Minimum line weight in the Sankey Diagram (number of engagements per line)", min_value=0, format = "%d", key = "_sankeyLineWeight", on_change=store_value, args=['sankeyLineWeight'])
        load_value("neverEngagedBefore")
        st.checkbox("Show Never Engaged Before in the Sankey Diagrams", key = "_neverEngagedBefore", on_change=store_value, args=['neverEngagedBefore'])
        load_value("neverEngagedAgain")
        st.checkbox("Show Never Engaged Again in the Sankey Diagrams", key = "_neverEngagedAgain", on_change=store_value, args=["neverEngagedAgain"])
    st.divider()
    with st.expander("Other options, including fine tuning options for multiple graph types and download features"):
        st.divider()
        load_value('aggregatedScatter')
        st.radio("Should the the x-axis for all scatter plots and the *When Students Engaged With Hiatt* graph be aggregated?", options = ["Do not aggregate (default)", "Aggregate by class year (Freshman Fall, Freshman Spring, ...)", "Aggregate by class year and semester (Freshman Year, Sophomore Year, ...)"], key = "_aggregatedScatter", on_change=store_value, args=["aggregatedScatter"])
        load_value('lineGraphEngagementOptions')
        st.multiselect("What engagements should be displayed on the 'When Students Engaged with Hiatt' line graph?", ['Any Engagement'] + st.session_state['RankedEngagementList'], key="_lineGraphEngagementOptions", on_change=store_value, args=['lineGraphEngagementOptions'])
        load_value('steppedColorbars')
        st.checkbox("Should colorbars be stepped (rather than a continuous color gradient) for all scatter plots and heat maps?", key="_steppedColorbars", on_change=store_value, args=['steppedColorbars'])
        load_value("numberOfColorDivisions")
        st.number_input(label = "If the colorbars are stepped, how many steps should there be?", min_value=1, format = "%d", key="_numberOfColorDivisions", on_change=store_value, args=['numberOfColorDivisions'])
        load_value("downloadFile")
        if st.checkbox("Enable the option to download the data file created by this code (useful for further exploration of data)", key = "_downloadFile", on_change=store_value, args = ['downloadFile']):
            #Print out the subtitle as a way to display how the data is restricted, to ensure a user doesn't accidentally restrict the data without realizing
            graduationYearToRestrictBy = st.session_state['graduationYearToRestrictBy']
            if(graduationYearToRestrictBy != 'Do not restrict by graduation year'):
                subtitle = "Graduating class of " + graduationYearToRestrictBy
            else:
                subtitle = "Data not restricted by graduating class"
            majorsToInclude = set(st.session_state['majorsToInclude'])
            if len(majorsToInclude) > 0:
                subtitle += ", only including students with majors in the following categories: " + ', '.join(majorsToInclude)
            else:
                if subtitle == "Data not restricted by graduating class":
                    subtitle += " or students major"
                else:
                    subtitle += ", data not restricted by students major"

            
            if st.session_state['restrictByKnownGraduates']:
                if subtitle != "Data not restricted by graduating class or students major":
                    subtitle += "<br>Data also restricted to only include students known to have graduated"
                else:
                    subtitle = "Data restricted to only include students known to have graduated, but not by students major or graduating class"
                
            st.write("For the Export File, " + subtitle)
            #Create another button to download the data -- in the current version of streamlit, there is not an efficient way to do this with just one button, because if so it will rerun the function to download the data each time and drastically slow down the program
            st.download_button(label='Download Cleaned Data',
                                        data=downloadExcelFile(st.session_state['df']),
                                        file_name= 'OUTPUT_DATA.xlsx')
    st.divider()    





    #The main function to generate all graphs, which runs when the generate button is pressed (as long as at least one graph is selected to generate)
    if st.button("Generate!") and uploaded_file is not None and len(st.session_state['graphTypes']) != 0:
        st.session_state['currentGraphs'] = []
        st.session_state['graphsGenerated'] = True
        graduationYearToRestrictBy = st.session_state['graduationYearToRestrictBy']
        graphTypes = st.session_state['graphTypes']

        #If the user wants a stpeed colorscale 
        def steppedColorscale(colorsList):
                from plotly.express.colors import sample_colorscale
                from sklearn.preprocessing import minmax_scale
                colorsRGB = [colors.to_rgb(c) for c in colorsList]
        
                colors_range = range(0, st.session_state['numberOfColorDivisions'])
                #Sample the colorscale to get the appropriate number of discrete colors
                discrete_colors = sample_colorscale(colorsRGB, minmax_scale(colors_range))

                steppedColorscale = []

                #Create a stepped color scale by adding the discrete colors to a list 100 times per color
                #(This doesn't truly change it from a color gradient, but to our eye there is no way to tell that it isn't)
                for i in range (0, st.session_state['numberOfColorDivisions']):
                    for notUsed in range (0, 100):
                        steppedColorscale.append(discrete_colors[i])
                return steppedColorscale


        #Create a heat map function, which has a parameter to account for whether it is the version based on total vs unique engagements
        def createHeatMap(countTotal):
            #Copy all needed variables, to ensure that any edits don't mess up later graphs
            df = originalDf.copy()
            mapping = originalMapping.copy()
            total = originalTotal.copy()
            success = originalSuccess.copy()
            percent = originalPercent.copy()
            engagementList = originalEngagementList.copy()
            
            
            df = df.sort_values(['Unique ID', 'Events Start Date Date'], ascending=[True, True])
            #It is critical after sorting that the indices are dropped (reset), otherwise any iteration through the dataframe based on the index will go out of order 
            df.reset_index(drop=True, inplace=True)

            #For total engagements heatmap
            def heatMapCountingTotalEngagements(df, total, success):
                #Iterate through the dataframe
                for ind in df.index:
                    tempInd = ind + 1
                    #Keep track of the total number of engagements in a dataframe
                    total.loc[df['Engagement Type'][ind]] += 1
                    alreadyCounted = []
                    while (tempInd + 1< len(df) and df['Unique ID'][tempInd] == df['Unique ID'][tempInd + 1]):
                            #For each future engagement by the same student, as long as that new engagement hasn't been counted yet, add it to a dataframe to track that it was engaged with afterwards
                            if not df['Engagement Type'][tempInd] in alreadyCounted:
                                success.loc[df['Engagement Type'][ind], df['Engagement Type'][tempInd]] += 1
                                alreadyCounted.append(df['Engagement Type'][tempInd])
                            tempInd +=1
            #For unique engagements, perform the same operation, but only perform it once for each student
            def heatMapCountingUniqueEngagements(df, total, success):
                countedPerson = []
                for ind in df.index:
                    if (ind + 1< len(df) and (df['Unique ID'][ind] != df['Unique ID'][ind + 1])):
                        if not df['Engagement Type'][ind] in countedPerson:
                            total.loc[df['Engagement Type'][ind]] += 1
                        countedPerson = []
                        continue
                    tempInd = ind + 1 
                    if not df['Engagement Type'][ind] in countedPerson:
                        countedPerson.append(df['Engagement Type'][ind])
                        total.loc[df['Engagement Type'][ind]] += 1
                        alreadyCounted = []
                        while (tempInd < len(df) and tempInd - 1 > -1 and (df['Unique ID'][tempInd] == df['Unique ID'][tempInd - 1])):
                            if not df['Engagement Type'][tempInd] in alreadyCounted:
                                success.loc[df['Engagement Type'][ind], df['Engagement Type'][tempInd]] += 1
                                alreadyCounted.append(df['Engagement Type'][tempInd])
                            tempInd +=1

            if countTotal:
                heatMapCountingTotalEngagements(df, total, success)
            else:
                heatMapCountingUniqueEngagements(df, total, success)


            #Some of this code is no longer used, as it was used in a previous iteration where the heatmap was outputted as an excel file
            a = np.array(success.values)
            b = np.array(total.values)
            

            totalCount = [str(f'{int(item):,}') for item in total[total.columns[0]]]
            percent = pd.DataFrame(np.divide(a, b, out=np.zeros_like(a), where=b!=0), index = total.index.values + " (" + totalCount + ")", columns=engagementList)
            percent = percent.astype(float).round(decimals=4)

            name = "HM - "
            longName = "Engagement Relationships -- "
            if countTotal:
                name += "Total"
                longName += "Total"
            else:
                name += "Unique"
                longName += "Unique"

            if graduationYearToRestrictBy != 'Do not restrict by graduation year':
                name += " - " + graduationYearToRestrictBy
                longName += " -- Class of " + graduationYearToRestrictBy
                

            name += ".xlsx"

            percent.rename_axis('Heat Map', inplace = True)
            percent.columns.name = "Second Events"
            (max_row, max_col) = percent.shape


            

            hoverText = percent.copy().astype(str)
            percentStrings = percent.copy().astype(str)
            sortedEngagementList = (list(engagementList))

            #Iterate through each value in the percent dataframe, was used for the excel file
            for col in range(0, max_col):
                for row in range(0, max_row):
                    rowEvent = percent.index[row]
                    colEvent = sortedEngagementList[col]
                    cell = format(percent[colEvent][rowEvent], ".0%")
                    event1 = sortedEngagementList[row].strip()
                    event2 = colEvent.strip()
                    if countTotal:
                        string = cell + " of the time " + event1 + " led to " + event2 + " (at any point)."
                    else:
                        string = cell + " of people who went to " + event1 + ", later went to " +event2 + " (at any point)."



                    percentStrings.loc[rowEvent, colEvent] = cell
                    if countTotal:
                        hoverText.loc[rowEvent, colEvent] = cell + " of the time " + event1 + " led to " + event2 + " (at any point)."
                    else:
                        hoverText.loc[rowEvent, colEvent] = cell + " of people who went to " + event1 + ", later went to " +event2 + " (at any point)."




            percent.rename_axis('First Events', inplace = True)

            #A normalized dataframe is used so that the colors are normalized for their columns, not based on the total display. 
            # This means that the heatmap coloring is based on these normalized values, but they should never be shown to the user as they are misleading and inaccurate (they are just accurate relative to each other)
            normalized_df=(percent-percent.min())/(percent.max()-percent.min())


            colorscale = ["red","lemonchiffon", "green"]
            if st.session_state['steppedColorbars']:
                colorscale = steppedColorscale(colorscale)

            #Create the heatmap with the values from the normalized dataframe, but using the real data as displae
            fig = go.Figure(data=go.Heatmap(x = percent.columns,
                                            y = percent.index,
                                            z = normalized_df,
                                            colorscale = colorscale,
                                            hoverinfo='none',
                                            texttemplate="%{text}", 
                                            text = percentStrings,
                                            ))

            #Add proper formatting to the chart
            fig.update_xaxes(title_text="Second Event")
            fig.update_yaxes(title_text="First Event")
            if countTotal:
                fig.update_layout(title = longName + "<br><sub>Depicts the percentage of total engagements where the first engagement was followed by the second, at any point</sub>")
            else:
                fig.update_layout(title = longName + "<br><sub>Depicts the percentage of students who went to the second engagement at any point after the first</sub>")
            fig.update_traces(showscale=False)

            fig.update_layout(
                    title={'x':0.5, 'xanchor': 'center'}, 
                    xaxis_title = "Second Event<br><i><sub>" + subtitle + "</sub></i>")
            
            if countTotal:
                chartType = "Engagement Relationships (Total)"
            else:
                chartType = "Engagement Relationships (Unique)"



            #Based on the plotly/streamlit version currently being used, heatmaps don't work with click interactivity. To get past this, there is a second, hidden layer used -- a scatter plot
            # This allows for the click interactivity to work (because the computer processes that the click is happeneing on the scatter plot, and therefor can appropriately print the values as expected)
            xlist = []
            ylist = []
            value = []

            
            for col in percent.columns:
                for row in percent.index:
                    xlist.append(col)
                    ylist.append(row)
                    value.append(100*percent[col][row]) 
             
            #Adds the scatter plot, with the proper hover template
            fig.add_trace(go.Scatter(x=xlist, y=ylist, opacity=0, marker_size = value, hoverinfo = None, mode = "markers", name="Scatter Plot"))
            if countTotal:
                fig.update_traces(hovertemplate="%{marker.size:.0%} of the time %{x} led to %{y} (at any point).<extra></extra>", selector = ({'name':'Scatter Plot'}))
            else:  
                fig.update_traces(hovertemplate="%{marker.size:.0%} of people who went to %{x}, later went to %{y} (at any point).<extra></extra>", selector = ({'name':'Scatter Plot'}))

            addChartToPage(fig)

        #Creates a sankey diagram
        def createSankeyDiagram():
            #Copies all variables so that edits don't interfere with later graphs
            df = originalDf.copy()
            mapping = originalMapping.copy()
            total = originalTotal.copy()
            success = originalSuccess.copy()
            percent = originalPercent.copy()
            engagementList = originalEngagementList.copy()
            

            df = df.sort_values(['Unique ID', 'Events Start Date Date'], ascending=[True, True])
            #It is critical after sorting that the indices are dropped (reset), otherwise any iteration through the dataframe based on the index will go out of order 
            df.reset_index(drop=True, inplace=True)


            #Calculates the maximum possible amount of steps from any student, and then adds four to ensure there is enough space (given that this includes "Never Engaged Before" and "Never Engaged Again")
            maxStep = df['Unique ID'].value_counts().iat[0] + 4


            engagementList = list(engagementList)
            engagementList.insert(0, "Never Engaged Before")
            engagementList.append("Never Engaged Again")


            mapping["Never Engaged Before"] = 0
            mapping["Never Engaged Again"] = len(engagementList) - 1

            #Use a numpy array to perform the calculations rather than pandas because it won't be in 2D
            #This grid uses two dimensions for the engagement that the student is coming from and going to, and then a third dimension to represent the step (1st engagement, 8th engagement, etc.)
            grid = np.zeros((maxStep, len(engagementList), len(engagementList)))

            stepCounter = 0
            for ind in df.index:
                currentEvent = df['Event Ranking from User'][ind]

                #If the user wants the sankey diagram to show neverEngagedBefore and it is the users first engagement, update the grid
                if st.session_state['neverEngagedBefore']:
                    if (ind-1 > 0 and df['Unique ID'][ind] != df['Unique ID'][ind - 1]):
                        grid[0][0][currentEvent] += 1
                
                #Keep updating the grid until either it is a new students (which resets the step counter), or it is the end of the dataframe
                if (ind+1<len(df)):
                    stepCounter += 1
                    if (df['Unique ID'][ind] == df['Unique ID'][ind + 1]):
                        grid[stepCounter][currentEvent][df['Event Ranking from User'][ind + 1]] += 1
                    else:
                        grid[stepCounter][currentEvent][len(engagementList) - 1] += 1
                        stepCounter = 0
                


            #Convert from an array in higher than 2D down to a dataframe in 2D
            TD = xr.Dataset(
                {
                    "Count": (["Step", "First Event", "Second Event"], grid),
                },
                coords={
                    "First Event": list(engagementList),
                    "Second Event": list(engagementList),
                    "Step": range(maxStep),
                },
            )

            new = TD.to_dataframe()
            



            source = [] #The event that the student is coming from and the step number
            target = []#The event that the student is going to and the step number
            value = [] #The number of students on that line
            nodeTotals = {}
            minimumLineWeight = st.session_state['sankeyLineWeight'] - 1 ##This is restricting so only larger lines are displayed
            maximumAllowedStep = st.session_state['sankeyColumns'] ##This is restricting so only the first few steps are displayed
            for ind in new.index:
                for series_name, series in new.items():
                    #If the size of the line is large enough and the step number is less than the maximum step size
                    if (series[ind] > minimumLineWeight and ind[0] < maximumAllowedStep):
                        #If the engagement is either not going to the last engagement or the user allows for the last engagement line
                        if st.session_state['neverEngagedAgain'] or ind[2] != "Never Engaged Again":
                            source.append(ind[1] + " " + str(ind[0]))
                            target.append(ind[2] + " " + str(ind[0] + 1))
                            value.append(int(series[ind]))
                    #Update the nodeTotals set, which is used to calculate the number of students at each engagement (even if the line isn't displayed)
                    if (ind[0] <= maximumAllowedStep):
                        e = ind[1] + " " + str(ind[0])
                        if e in nodeTotals:
                            nodeTotals[e] += int(series[ind])
                        else:
                            nodeTotals[e] = int(series[ind])


            
            #Shorten the above arrays to be unique (which is needed for how the sankey diagram is generated)
            shortenedLists = list(set(source + target))
            dictionaryConverter = dict(zip(shortenedLists, range(len(shortenedLists))))

            sourceConverted = [dictionaryConverter[key] for key in source]
            targetConverted = [dictionaryConverter[key] for key in target]
            
            colorLinkList = [x[:x.rfind(" ")] for x in source] #Used later to assign colors for each node/line


            #Split up the name of the event (rather than the name and step)
            locationList = []
            eventNameList = []
            for event in shortenedLists:
                locationList.append((float(event.split()[-1])))
                eventNameList.append(event[:event.rfind(" ")])

            #If the "Never Engaged Before" is not included, every value needs to be shifted down (because these values are used to determine x position for the sankey diagram)
            while (min(locationList) != 0):
                locationList = [loc - 1 for loc in locationList]

            #Calculate the x location based on the step 
            # The reason 1e-9 is used is because if the value is 0, it does not display correctly in the sankey diagram
            locationList = [x/max(locationList) if x != 0 else 1e-9 for x in locationList]
            locationList = [x if x != 1 else 1-1e-9 for x in locationList]

            import plotly.graph_objects as go
            #Possible set of colors to be used in the sankey diagram
            colorSet = ["firebrick", "orangered", "forestgreen",  "blueviolet", "grey", "darkcyan", "cornflowerblue",  "mediumvioletred", "turquoise", "saddlebrown"]


            #Create the color mapping, and loop through the colors if there are too many different events
            colorMapping = {}
            colorTracker = 0
            for event in set(eventNameList):
                colorMapping[event] = colorSet[colorTracker]
                colorTracker += 1
                if colorTracker == len(colorSet):
                    colorTracker = 0


            #Create the list of colors for the links, making them 30% transparents
            colorsList = [colorMapping[x] for x in eventNameList]
            colorLinkList = ["rgba" + str(colors.to_rgba(colorMapping[x], alpha = 0.3)) for x in colorLinkList]
            

            nodeValues = [nodeTotals[item] for item in shortenedLists]

            linkPercentage = [value[index] / nodeValues[sourceConverted[index]] for index in range(len(sourceConverted))]

            #Create the sankey diagram, with all appropriate values
            fig = go.Figure(go.Sankey(
                arrangement = "snap",
                node = dict(
                pad = 15,       
                thickness = 20,
                line = dict(color = "black", width = 0.5),
                label = shortenedLists, 
                customdata = nodeValues,
                x = locationList,
                y = [0.1]*len(locationList), #when given an x value the sankey must receive a y value as well, but will handle the collisions appropriately
                color = colorsList,
                hovertemplate='%{customdata:,} students went to %{label}<extra></extra>',
                ),
                link = dict(
                source = sourceConverted, # indices correspond to labels, eg A1, A2, A1, B1, ...
                target = targetConverted,
                value = value,
                color = colorLinkList,
                customdata = linkPercentage,
                hovertemplate='%{customdata:.1%} of the students who went to %{source.label}<br>went next to %{target.label} (%{value:,} students)<extra></extra>',
                )))

            #Update the layout of the sankey diagram appropriately
            fig.update_layout(
                margin=dict(l=10, r=10, t=50, b=100),
            )

            fig.update_layout(
                hoverlabel=dict(
                    bgcolor="black",
                    font_color = "white",
                    font_size = 14,
                )
            )

            fig.update_layout(
                title_text="Sequential Pathways of Student Engagements<br><sup>Shows the order of events that students engaged in, and the pathways in between to represent students transition</sup>",
                font_color="black",
                font_size=14,
            )

            fig.update_layout(
                    title={'x':0.5, 'xanchor': 'center'}, 
                    xaxis_title = "Semester<br><i><sub>" + subtitle + "</sub></i>")
            #Add the subtitle, needs to be handled differently to the other charts because how the sankey diagram works
            fig.add_annotation(
                x=0.5, 
                y=-0.1, 
                xref='paper', 
                yref='paper',
                text="<br><i><sub>" + subtitle + "</sub></i>",
                showarrow=False,
            )
            addChartToPage(fig)

            #Used for a partial project but no longer critical
            reshapedDataFrame = new.loc[0, :, :]

            for step in set(new.index.get_level_values('Step')):
                reshapedDataFrame = reshapedDataFrame.join(new.loc[step, :, :], lsuffix='', rsuffix=' ' + str(step))

            reshapedDataFrame = reshapedDataFrame.drop('Count', axis=1)
        
        #Create a line graph. This is NO LONGER EVER USED. This is saved purely for reference and is not guaranteed to work at the current iteration
        def createLineGraph():
            df = originalDf.copy()
            mapping = originalMapping.copy()
            engagementList = originalEngagementList.copy()



            semesterValueMappings = {}

            df = df.drop(df[df['Semester'].str.contains('Summer')].index)
            df = df.drop(df[df['Semester'].str.contains('Winter')].index)
            
            df['Unique ID'] = df.groupby(['Full Name','Email']).ngroup()

            ##THIS IS STILL USEFUL! THIS APPLIES A MANUAL SORTING BASED ON sort_engagement
            ##df['Event Number'] = df.apply(sort_engagement, axis = 1)
            ##THIS IS STILL USEFUL! THIS SORTS IF I HAVEN'T MANUALLY DONE IT
            df['Event Number'] = df.groupby(['Engagement Type']).ngroup()+1

            def graphWithDates(df):
                df = df.drop_duplicates(subset=['Events Start Date Date', 'Unique ID'])
                df = df.pivot(index='Events Start Date Date', columns='Unique ID', values='Ranked Events')
                return df

            def graphWithSemesters(df):
                df['Semester Number'] = df.apply(lambda x: create_semester_value(x.Semester, semesterValueMappings), axis=1)
                global secondDataframe 
                secondDataframe = df.value_counts(['Semester Number', 'Ranked Events']).reset_index().rename(columns={0:'count'})
                df = df.drop_duplicates(subset=['Semester Number', 'Unique ID'])
                #print(len(df.index))
                df = df.pivot(index='Semester Number', columns='Unique ID', values='Ranked Events')
                return df




            df = graphWithSemesters(df)

            #print("HERE'S THE SECOND ONE")
            #print(secondDataframe)

            #print("Pivot Table:")
            #df = df.astype(str)
            #print(df.dtypes)
            #print(df)


            dfGraph = df.interpolate(method = 'linear')
            ax = dfGraph.plot.line(alpha = 100/len(df.columns), ms=1, color='black')
            #print(type(ax))

            items = list(mapping.keys())
            items[:] = [item+" (" + str(events[item]) + ")" for item in items]

            firstDate = df.apply(pd.Series.first_valid_index)
            pd.concat([pd.Series([1]), firstDate])
            counter = 0
            firstEvent = []
            #print(firstDate)
            #print(len(df.columns))
            #print(firstDate[3])
            while counter < len(df.columns)-1:
                #print(counter)
                #print(firstDate[counter])
                firstEvent.append(df.at[firstDate[counter], counter])
                counter += 1
            firstEvent.insert(0, 1)


            #print("HERE IT IS!!")
            #print(firstDate)
            #print(firstEvent)
            #ax.scatter(firstDate, firstEvent, color='limegreen', alpha = 35/len(df.columns), s=25)

            dataframe = pd.DataFrame(list(zip(firstDate, firstEvent)), columns =['Date', 'Event'])
            #dataframe = pd.DataFrame(lst, columns= ["Date", "Event"])
            #print(dataframe)
            #print(dataframe.duplicated(keep=False).value_counts())

            dataframe = dataframe.value_counts(['Date', 'Event']).reset_index().rename(columns={0:'count'})
            #print(dataframe)
            #print(dataframe[['Date', 'Event']].apply(pd.Series.value_counts()))
            #df[['a', 'b']].apply(pd.Series.value_counts)
            lastDate = df.apply(pd.Series.last_valid_index)
            pd.concat([pd.Series([1]), lastDate])
            lastCounter = 0
            lastEvent = []
            #print(lastDate)
            #print(len(df.columns))
            while lastCounter < len(df.columns)-1:
                #print(lastCounter)
                #print(lastDate[lastCounter])
                lastEvent.append(df.at[lastDate[lastCounter], lastCounter])
                lastCounter += 1
            lastEvent.insert(0, 1)


            #ax.scatter(lastDate, lastEvent, color='red', alpha = 25/len(df.columns), s=25)




            #plt.show()

            #df.plot.scatter(x="Events Start Date Date", y="Event Type Name", alpha = 0.1)
            #plt.show()

            #df.to_excel('2023Seniors.xlsx', sheet_name="Cleaned Data", index=False)

            #fig = Figure
            
            #print(dfGraph)
            #fig1 = fig.add_subplot(111)
            #print(firstDatePLOT)
            #fig1.scatter(firstDatePLOT, firstEventPLOT)
            #fig = plt.figure()
            YlGn = mpl.colormaps['Blues']
            Reds = mpl.colormaps['Reds']
            maxCount = dataframe['count'].max()
            secondMaxCount = secondDataframe['count'].max()
            secondTheScatter = plt.scatter(secondDataframe['Semester Number'], secondDataframe['Ranked Events'], c = secondDataframe['count'], cmap = Reds, alpha = 1, s = secondDataframe['count']/secondMaxCount * 200)
            theScatter = plt.scatter(dataframe['Date'], dataframe['Event'], c = dataframe['count'], cmap = YlGn, alpha = 1, s = dataframe['count']/secondMaxCount * 200)
            #plt.plot(dfGraph, alpha = 100/len(df.columns), ms=1, color='black')
            #secondLegend1 = fig1.legend(*secondTheScatter.legend_elements(num=10), title="Color Key", bbox_to_anchor=(1.21, 1), loc='upper left', draggable = True)
            #fig1.add_artist(secondLegend1)
            plt.colorbar(cm.ScalarMappable(norm = mpl.colors.Normalize(vmin=dataframe['count'].min(), vmax=maxCount), cmap=YlGn), ax=ax)
            plt.colorbar(cm.ScalarMappable(norm = mpl.colors.Normalize(vmin=secondDataframe['count'].min(), vmax=secondMaxCount), cmap=Reds), ax=ax)



            ax.set_yticks(list(mapping.values()), items)
            ax.set_xticks(list(semesterValueMappings.keys()), list(semesterValueMappings.values()))
            ax.set_xticklabels(ax.get_xticklabels(), rotation=75, ha='right')
            ax.set(xlabel="Semester", ylabel="Event Type")
            ax.get_legend().remove()
            if graduationYearToRestrictBy != "Do not restrict by graduation year":
                plt.title("The Graduating Class of " + str(graduationYearToRestrictBy) + "'s Engagement Graph") # type: ignore
            else:
                plt.title("Engagement Graph")
            plt.subplots_adjust(left = 0.285, bottom = 0.28, right = 0.99, top = 0.92)


            st.pyplot(plt)
        
        #Creates all scatter plots at once, and within this function handles which should be shown
        def createScatterPlot():

            #Create copies of all varaibels needed
            df = originalDf.copy()
            mapping = originalMapping.copy()
            engagementList = originalEngagementList.copy()

            #Drop any entries without a Unique ID (should only be a very few people who don't have an email listed)
            df.dropna(subset=['Unique ID'], inplace=True)

            #In the dataframe creates columns in the dataframe and functions to work if the data needs to be aggregated along the x axis
            semesterValueMappings = {}
            df['Semester Number'] = df.apply(lambda x: create_semester_value(x.Semester, semesterValueMappings), axis=1)
            aggregatedSemesterValueMappings = {16: "Senior Spring", 15: "Senior Winter", 14: "Senior Fall", 13: "Senior Summer", 12: "Junior Spring", 11: "Junior Winter", 10: "Junior Fall", 9: "Junior Summer", 8: "Sophomore Spring", 7: "Sophomore Winter", 6: "Sophomore Fall", 5: "Sophomore Summer", 4: "Freshman Spring", 3: "Freshman Winter", 2: "Freshman Fall", 1: "Freshman Summer"}
            df['Aggregated Semester Number'] = df.apply(lambda x: create_aggregated_semester_value(x.Semester, x.Graduation_Semester), axis=1)
            df['Double Aggregated Semester Number'] = (np.ceil(df['Aggregated Semester Number'] / 4)).astype(int)
            doubleAggregatedSemesterValueMappings = {4: "Senior Year", 3: "Junior Year", 2:"Sophomore Year", 1:"Freshman Year"}
            

            def aggregated_semester_name(row):
                num = row['Aggregated Semester Number']
                if num in aggregatedSemesterValueMappings:
                    return aggregatedSemesterValueMappings[num]
                else:
                    return "Do Not Include"
                
            def double_aggregated_semester_name(row):
                num = row['Double Aggregated Semester Number']
                if num in doubleAggregatedSemesterValueMappings:
                    return doubleAggregatedSemesterValueMappings[num]
                else:
                    return "Do Not Include"
            
            df['Aggregated Semester Name'] = df.apply(aggregated_semester_name, axis = 1)
            df['Double Aggregated Semester Name'] = df.apply(double_aggregated_semester_name, axis = 1)

            global secondDataframe 

            
            #Chooses the appropriate x-axis based on how it is being aggregated
            if st.session_state['aggregatedScatter'] == "Do not aggregate (default)":
                semesterNumberedColumn = 'Semester Number'
                semesterMapping = semesterValueMappings
            elif st.session_state['aggregatedScatter'] == "Aggregate by class year (Freshman Fall, Freshman Spring, ...)":
                semesterNumberedColumn = 'Aggregated Semester Number'
                semesterMapping = aggregatedSemesterValueMappings
            elif st.session_state['aggregatedScatter'] == "Aggregate by class year and semester (Freshman Year, Sophomore Year, ...)":
                semesterNumberedColumn = 'Double Aggregated Semester Number'
                semesterMapping = doubleAggregatedSemesterValueMappings

            #Creates two dataframes with a column for each engagement and a row (index) for each semester
            averages = pd.DataFrame(index = range(df[semesterNumberedColumn].min(), df[semesterNumberedColumn].max()+1), columns = engagementList, data = [])
            combined = averages.copy()
            
            #Fill dataframes with empty lists to be appended to later
            for col in averages.columns:
                for row in averages.index:
                    averages.loc[row, col] = []
                    combined.loc[row, col] = []


            df = df.sort_values(['Unique ID', 'Events Start Date Date'], ascending=[True, True])
            #It is critical after sorting that the indices are dropped (reset), otherwise any iteration through the dataframe based on the index will go out of order 
            df.reset_index(drop=True, inplace=True)

            #Create 2 similar dataframes but filled with 0's rather than empty lists
            firstEngagements = pd.DataFrame(index = range(df[semesterNumberedColumn].min(), df[semesterNumberedColumn].max()+1), columns = engagementList, data = 0)
            oneAndDone = firstEngagements.copy()


            #Create one more dataframe but filled with empty sets
            numberOfUniqueEngagements = pd.DataFrame(index = range(df[semesterNumberedColumn].min(), df[semesterNumberedColumn].max()+1), columns = engagementList, data = {})

            for col in numberOfUniqueEngagements.columns:
                for row in numberOfUniqueEngagements.index:
                    numberOfUniqueEngagements.loc[row, col] = set()
            


            firstIndexMapping = {}
            lastIndexMapping = {}

            #Iterate through the dataframe to update the created dataframes appropriately
            for ind in df.index:
                ID = df['Unique ID'][ind]
                #Check to see if it is the first engagement
                if ID not in firstIndexMapping:
                    firstIndexMapping[ID] = ind
                #Calculate the last engagement if necessary
                if ID not in lastIndexMapping:
                    tempInd = ind
                    while tempInd + 1 in df.index and ID == df['Unique ID'][tempInd + 1]:
                        tempInd += 1
                    lastIndexMapping[ID] = tempInd
                
                semesterNumber = df[semesterNumberedColumn][ind]
                engagementType = df['Engagement Type'][ind]

                #Add the amount of events attended after this one to the averages dataframe
                averages.loc[semesterNumber, engagementType].append(lastIndexMapping[ID]-ind)

                #Add this ID to the set in uniqueEngagements dataframe (to calculate the number of unique engagements)
                numberOfUniqueEngagements.loc[semesterNumber, engagementType].add(int(ID))
                
                #If this is the first engagement, update the necessary dataframes
                if firstIndexMapping[ID] == ind:
                    firstEngagements.loc[semesterNumber, engagementType] += 1
                    combined.loc[semesterNumber, engagementType].append(lastIndexMapping[ID]-ind)
                #If this is the fist and last engagement for this student, update the necessary dataframe
                if firstIndexMapping[ID] == ind and lastIndexMapping[ID] ==ind:
                    oneAndDone.loc[semesterNumber, engagementType] += 1

            
            #Create a data frame that contains a combination of all of the information to be used for scatter plots (in various different arragements)
            scatterDataFrame = pd.DataFrame(columns=["Engagement Type", "Semester", "Average", "Number of Engagements", "First Engagements", "Percent First Engagement", "Unique Number of Engagements", "Unique Percent First Engagement", "Percentage of Unique Engagements", "One and Done", "Percentage of One and Done"])  
            
            #Iterate through the first created data frame
            for row in averages.index:
                skip = True
                #If all of the engagements in the given semester (row) are too small, do not add this semester to the dataframe so that it isn't added to any of the scatter plots
                for col in averages.columns:
                    if len(averages.loc[row, col]) >= st.session_state['scatterMinimumSize']:
                        skip = False
                        break
                #If there is at least one engagement of valid size
                if skip == False:
                    for col in averages.columns:
                        #Account for the current semester and aggregation setting
                        if st.session_state['aggregatedScatter'] == "Do not aggregate (default)":
                            if row not in semesterValueMappings:
                                create_semester_value_from_number(row, semesterValueMappings)
                        #If the data is being aggregated, and the semester does not fall into any of the appropriate groupings (like it is the year after senior year), skip the data
                        elif st.session_state['aggregatedScatter'] == "Aggregate by class year (Freshman Fall, Freshman Spring, ...)":
                            if row not in aggregatedSemesterValueMappings:
                                continue
                        elif st.session_state['aggregatedScatter'] == "Aggregate by class year and semester (Freshman Year, Sophomore Year, ...)":
                            if row not in doubleAggregatedSemesterValueMappings:
                                continue
                        
                        #Calculate the appropriate data from the different dataframes
                        firstEngageData = firstEngagements.loc[row][col]
                        oneAndDoneData = oneAndDone.loc[row][col]

                        avgUniqueList = numberOfUniqueEngagements.loc[row, col]
                        #Account for dividing by 0 errors for both the unique and total lists (which are used for different graphs)
                        if len(avgUniqueList) >= st.session_state['scatterMinimumSize']:
                            uniqueLength = len(avgUniqueList)
                            uniquePercentage =  firstEngageData/uniqueLength
                        else:
                            uniqueLength = 0
                            uniquePercentage = 0
                        
                        
                        avgList = averages.loc[row, col]
                        if len(avgList) >= st.session_state['scatterMinimumSize']:
                            avg = statistics.fmean(avgList)
                            length = len(avgList)
                            percent = firstEngageData/length
                            percentageOfUniqueVsTotal = uniqueLength/length
                            percentOfOneAndDone = oneAndDoneData/uniqueLength
                        else:
                            avg = 0
                            length = 0
                            percent = 0
                            percentageOfUniqueVsTotal = 0
                            percentOfOneAndDone = 0
                        
                        #Add all the accumulated data to one row in the new dataframe
                        scatterDataFrame.loc[len(scatterDataFrame.index)] = [col, semesterMapping[row], avg, length, firstEngageData, percent, uniqueLength, uniquePercentage, percentageOfUniqueVsTotal, oneAndDoneData, percentOfOneAndDone]

            #This is based on the same principle and is largely the same as the above loop, but is instead tuned for a different set of the data (specifically, when a row should be skipped is based on combined dataframe rather than averages dataframe)
            combinedScatterDataFrame = pd.DataFrame(columns=["Engagement Type", "Semester", "Average", "Number of First Engagements", "First Engagements", "Percent First Engagement", "One and Done", "Percentage of One and Done"])  
            for row in combined.index:
                skip = True
                for col in combined.columns:
                    if len(combined.loc[row, col]) >= st.session_state['scatterMinimumSize']:
                        skip = False
                        break
                if skip == False:
                    for col in combined.columns:
                        if st.session_state['aggregatedScatter'] == "Do not aggregate (default)":
                            if row not in semesterValueMappings:
                                create_semester_value_from_number(row, semesterValueMappings)
                        elif st.session_state['aggregatedScatter'] == "Aggregate by class year (Freshman Fall, Freshman Spring, ...)":
                            if row not in aggregatedSemesterValueMappings:
                                continue
                        elif st.session_state['aggregatedScatter'] == "Aggregate by class year and semester (Freshman Year, Sophomore Year, ...)":
                            if row not in doubleAggregatedSemesterValueMappings:
                                continue

                        avgList = combined.loc[row, col]
                        oneAndDoneData = oneAndDone.loc[row][col]

                        if len(avgList) >= st.session_state['scatterMinimumSize']:
                            avg = statistics.fmean(avgList)
                            length = len(avgList)
                            percentOfOneAndDone = oneAndDoneData/length
                            percentFirstEngagement = firstEngageData/length
                        else:
                            avg = 0
                            length = 0
                            percentOfOneAndDone = 0
                            percentFirstEngagement = 0
                        firstEngageData = firstEngagements.loc[row][col]
                        
                        combinedScatterDataFrame.loc[len(combinedScatterDataFrame.index)] = [col, semesterMapping[row], avg, length, firstEngageData, percentFirstEngagement, oneAndDoneData, percentOfOneAndDone]
            
            
            #The next section accounts for all of the different scatter plots and what should happen if the user wants to view that scatter plot
            #For the most part, the process is similar for each but tuned differently depending on the graph
            #The first version is more heavily commented, and can be used as a reference to understand the process

            
            colorscale = ["red","yellow", "green"]
            if st.session_state['steppedColorbars']:
                colorscale = steppedColorscale(colorscale)
            if "Return Rates Based on All Engagements" in graphTypes:
                #If there should be a maximum percentage for the colorbar, set it
                maximum = np.percentile(scatterDataFrame['Average'], st.session_state['scatterMaxPercentile'])
                #Set the minimuum for the colorbar to be the lowest number other than 0, because for any circles that don't exist it is interpreted as a 0
                minimum = min([x if x!=0 else max(scatterDataFrame['Average']) for x in scatterDataFrame['Average']])
                
                #Create the scatter plot with appropriate data
                #   Title is formatted with standard html tags, which is accepted in the current version of plotly
                #   Labels Average is set to be nothing, to get rid of the title above the colorbar. This is necessary because otherwise the colorbar title is far too large and the graph becomes squished
                #   Hover data is used later when the hovertemplate is declared, and serves to store extra data with each point that can be called on later
                fig = px.scatter(scatterDataFrame, x="Semester", y="Engagement Type", color = 'Average', range_color = (minimum, maximum), size="Number of Engagements", color_continuous_scale= colorscale, 
                                    title = "Return Rates Based on All Engagements<br><sup>Shows how students engaged over time</sup><br><i><sub>Color: the average number of engagements attended after</sub><br><sup> Size: the number of engagements</sup></i>", 
                                    labels={"Average": ""}, hover_data={"Average": False, "Average Number of Events Attended Afterwards": (':.1f', scatterDataFrame['Average'])})

                #Center the title and add information at the bottom of the graph about how the data is restricted
                fig.update_layout(
                    title={'x':0.5, 'xanchor': 'center'}, 
                    xaxis_title = "Semester<br><i><sub>" + subtitle + "</sub></i>")
                
                #Add a thin outline for all circles, which serves to make them more easily visible (especially useful for yellows which are hard to see against white)
                fig.update_traces(marker=dict(
                              line=dict(width=0.25,
                                        color='Black')),
                  selector=dict(mode='markers'))

                #Create a hover template which uses the data stored with each point
                fig.update_traces(hovertemplate="There were %{marker.size:,} %{y} engagements in %{x},<br>with an average number of %{customdata[1]:.1f} subsequent engagements<extra></extra>")
                
                #Call the function to add the chart to the page
                addChartToPage(fig)

            if "Return Rates Based on First Engagements" in graphTypes:
                maximum = np.percentile(combinedScatterDataFrame['Average'], st.session_state['scatterMaxPercentile'])
                minimum = min([x if x!=0 else max(scatterDataFrame['Average']) for x in scatterDataFrame['Average']])
                fig = px.scatter(combinedScatterDataFrame, x="Semester", y="Engagement Type", color = "Average", range_color = (minimum, maximum), size="Number of First Engagements", color_continuous_scale=colorscale, 
                                    title = "Return Rates Based on First Engagements<br><sup>Shows how students engaged after their first engagement point</sup><br><i><sub>Color: the average number of engagements attended after</sub><br><sup> Size: the number of first engagements</sup></i>", labels={"Average": ""}, hover_data={"Average": False, "Average Number of Events Attended Afterwards": (':.1f', combinedScatterDataFrame['Average'])})

                fig.update_layout(
                    title={'x':0.5, 'xanchor': 'center'}, 
                    xaxis_title = "Semester<br><i><sub>" + subtitle + "</sub></i>")
                fig.update_traces(marker=dict(
                              line=dict(width=0.25,color='Black')),
                  selector=dict(mode='markers'))

                fig.update_traces(hovertemplate="There were %{marker.size:,} %{y} first engagements in %{x},<br>with an average number of %{customdata[1]:.1f} subsequent engagements<extra></extra>")
                addChartToPage(fig)

            
            #All colorscales are similar, but whenever there is a differnent encoding for the color, a different colorbar is used
            colorscale2 = ["sandybrown", "gold", "green"]
            if st.session_state['steppedColorbars']:
                colorscale2 = steppedColorscale(colorscale2)

            if "First Engagements Data (Total)" in graphTypes:
                #Depending on whether users want to use total numbers or percents, update the name of the column used and the string to be added to the title
                if st.session_state['numbervspercent'] == False:
                    colorData = 'Percent First Engagement'
                    titleSubstring = "Color: the percent of first engagements"
                else:
                    colorData = "First Engagements"
                    titleSubstring = "Color: the number of first engagements"
                maximum = np.percentile(scatterDataFrame[colorData], st.session_state['scatterMaxPercentile'])
                minimum = min([x if x!=0 else max(scatterDataFrame[colorData]) for x in scatterDataFrame[colorData]])
                fig = px.scatter(scatterDataFrame, x="Semester", y="Engagement Type", color = colorData, range_color=(minimum,maximum), size="Number of Engagements", color_continuous_scale=colorscale2, 
                                title = "First Engagements Data (Total)<br><sup>Data shows total and first engagements across activity and semester</sup><br><i><sub>" + titleSubstring + "</sub><br><sup> Size: the number of total engagements</sup></i>", 
                                labels={"First Engagements": "", colorData : ""}, hover_data={"First Engagements": False, "Number of First Engagements": (':d', scatterDataFrame['First Engagements']), "Percentage of First Engagements": (':.0%', scatterDataFrame['Percent First Engagement'])})

                fig.update_layout(
                    title={'x':0.5, 'xanchor': 'center'}, 
                    xaxis_title = "Semester<br><i><sub>" + subtitle + "</sub></i>")
                fig.update_traces(marker=dict(
                            line=dict(width=0.25,
                                        color='Black')),
                selector=dict(mode='markers'))

                fig.update_traces(hovertemplate='Of the %{marker.size:,} %{y} engagements in %{x},<br>%{customdata[2]:.0%} of them (%{customdata[1]:,d}) were first time engagements<extra></extra>')
                addChartToPage(fig)


            if "First Engagements Data (Unique)" in graphTypes:
                if st.session_state['numbervspercent'] == False:
                    colorData = 'Unique Percent First Engagement'
                    titleSubstring = "Color: the percent of first engagements"
                else:
                    colorData = "First Engagements"
                    titleSubstring = "Color: the number of first engagements"
                maximum = np.percentile(scatterDataFrame[colorData], st.session_state['scatterMaxPercentile'])
                minimum = min([x if x!=0 else max(scatterDataFrame[colorData]) for x in scatterDataFrame[colorData]])
                fig = px.scatter(scatterDataFrame, x="Semester", y="Engagement Type", color = colorData, range_color=(minimum, maximum), size="Unique Number of Engagements", color_continuous_scale=colorscale2, 
                                title = "First Engagements Data (Unique)<br><sup>Data shows unique and first engagements across activity and semester</sup><br><i><sub>" + titleSubstring + "</sub><br><sup> Size: the number of unique engagements</sup></i>", 
                                labels={"First Engagements": "", colorData : ""}, hover_data={"First Engagements": False, "Number of First Engagements": (':d', scatterDataFrame['First Engagements']), "Unique Percentage of First Engagements": (':.0%', scatterDataFrame['Unique Percent First Engagement'])})

                fig.update_layout(
                    title={'x':0.5, 'xanchor': 'center'}, 
                    xaxis_title = "Semester<br><i><sub>" + subtitle + "</sub></i>")
                fig.update_traces(marker=dict(
                            line=dict(width=0.25,
                                        color='Black')),
                selector=dict(mode='markers'))

                fig.update_traces(hovertemplate='%{marker.size:,} students went to %{y} in %{x},<br>%{customdata[2]:.0%} of them (%{customdata[1]:,d}) were students who were engaging for the first time<extra></extra>')
                addChartToPage(fig)

            colorscale3 = ["gold", "darkorange", "crimson"]
            if st.session_state['steppedColorbars']:
                colorscale3 = steppedColorscale(colorscale3)
            if "Rates of Unique Engagements" in graphTypes:
                if st.session_state['numbervspercent'] == False:
                    colorData = 'Percentage of Unique Engagements'
                    titleSubstring = "Color: the percentage of unique engagements"
                else:
                    colorData = "Unique Number of Engagements"
                    titleSubstring = "Color: the number of unique engagements"
                maximum = np.percentile(scatterDataFrame[colorData], st.session_state['scatterMaxPercentile'])
                minimum = min([x if x!=0 else max(scatterDataFrame[colorData]) for x in scatterDataFrame[colorData]])
                fig = px.scatter(scatterDataFrame, x="Semester", y="Engagement Type", color = colorData, range_color=(minimum,maximum), size="Number of Engagements", color_continuous_scale=colorscale3, 
                                title = "Rates of Unique Engagements<br><sup>Data shows unique and total engagements across activity and semester</sup><br><i><sub>" + titleSubstring + "</sub><br><sup> Size: the number of total engagements</sup></i>", 
                                labels={"Number of Engagements": "", colorData : ""}, hover_data={colorData: False, "Number of Unique Engagements": (':,d', scatterDataFrame['Unique Number of Engagements']), "Number of Total Engagements": (':,d', scatterDataFrame['Number of Engagements']), "Percent of Unique Engagements": (':.0%', scatterDataFrame['Percentage of Unique Engagements'])})

                fig.update_layout(
                    title={'x':0.5, 'xanchor': 'center'}, 
                    xaxis_title = "Semester<br><i><sub>" + subtitle + "</sub></i>")
                fig.update_traces(marker=dict(
                              line=dict(width=0.25,
                                        color='Black')),
                  selector=dict(mode='markers'))

                fig.update_traces(hovertemplate='There were %{marker.size:,} %{y} engagements in %{x},<br>%{customdata[3]:.0%} of them (%{customdata[1]:,d} students) were unique engagements<extra></extra>')
                addChartToPage(fig)
            
            colorscale4 = ["green", "gold", "orangered"]
            if st.session_state['steppedColorbars']:
                colorscale4 = steppedColorscale(colorscale4)
            if "Students with only 1 Engagement" in graphTypes:
                if st.session_state['numbervspercent'] == False:
                    colorData = 'Percentage of One and Done'
                    titleSubstring = "Color: the percentage of first engagements which never engaged again"
                else:
                    colorData = "One and Done"
                    titleSubstring = "Color: the number of students who engaged for the first and last time"
                maximum = np.percentile(combinedScatterDataFrame[colorData], st.session_state['scatterMaxPercentile'])
                minimum = min([x if x!=0 else max(combinedScatterDataFrame[colorData]) for x in combinedScatterDataFrame[colorData]])
                fig = px.scatter(combinedScatterDataFrame, x="Semester", y="Engagement Type", color = colorData, range_color=(minimum,maximum), size="Number of First Engagements", color_continuous_scale=colorscale4, 
                                title = "Students with only 1 Engagement<br><sup>Data shows the students who went to an event once and never again engaged with Hiatt</sup><br><i><sub>" + titleSubstring + "</sub><br><sup> Size: the number of first engagements</sup></i>", 
                                labels={"Number of First Engagements": "", colorData : ""}, hover_data={colorData: False, "Students who only engaged once": (':,d', combinedScatterDataFrame['One and Done']), "Percent of all students how many only engaged once": (':.0%', combinedScatterDataFrame['Percentage of One and Done'])})
                fig.update_layout(
                    title={'x':0.5, 'xanchor': 'center'}, 
                    xaxis_title = "Semester<br><i><sub>" + subtitle + "</sub></i>")
                fig.update_traces(marker=dict(
                              line=dict(width=0.25,
                                        color='Black')),
                  selector=dict(mode='markers'))
                fig.update_traces(hovertemplate='There were %{marker.size:,} %{y} first engagements in %{x},<br>%{customdata[2]:.0%} of them (%{customdata[1]:,d}) were students who engaged for the first and last time<extra></extra>')
                addChartToPage(fig)

        
        #Create a line graph that is used, based on the graduating class
        def createGraduateGraph():
            #Create copies of variables used so that modifications don't interfere with other graphs
            graduateEmailsDF = st.session_state['graduateEmails']
            df = originalDf.copy()
            engagementList = originalEngagementList.copy()

            emailSet = set(df['Email'])
            graduateYears = graduateEmailsDF.columns
            
            #Create a dataframe that is updated throughout this process
            percentagesDF = pd.DataFrame(columns = ["Class Year", "Category", "Percentages"])
            
            for year in graduateYears:
                #Create a set of the emails from a specific years graduating class and get rid of any null values
                currentSet = set(graduateEmailsDF[year])
                currentSet.discard(np.nan)
                
                #Restrict the emails included based on any major restrictions, otherwise the values will be incorrectly calculated
                # (This works the same way as it does below when doing this for the whole dataframe)
                majorsToInclude = set(st.session_state['majorsToInclude'])
                majMap = st.session_state['Majors Mapping']
                if len(majorsToInclude) > 0:
                    to_discard = list()
                    for gradEmail in currentSet:
                        if gradEmail not in majMap:
                            to_discard.append(gradEmail)
                        elif not set(majMap[gradEmail]).intersection(majorsToInclude):
                            to_discard.append(gradEmail)
                    for d in to_discard:
                        currentSet.discard(d)

                #Calculate the overlap between all of the emails and the graduates emails (number of graduates who engaged) and divide by the number of graduates
                percent = len(emailSet & currentSet) / len(currentSet)
                percentagesDF.loc[len(percentagesDF)] = [year, "Any Engagement", percent]

                #Perform the same operation for each type of engaegement and add them to the dataframe
                for category in engagementList:
                    df_subset = df[df['Engagement Type'] == category]
                    tempBaseSet = set(df_subset['Email'])

                    percent = len(tempBaseSet & currentSet) / len(currentSet)
                    percentagesDF.loc[len(percentagesDF)] = [year, category, percent]
                
            #Create a line graph with all of the data
            fig = px.line(percentagesDF, x="Class Year", y="Percentages", color = "Category", title='Percentage of Each Class Year that Engaged with Hiatt', markers=True, hover_data={"Type of Engagement": percentagesDF['Category']})
            #Use percentages in the y axis and set it to go from 0 - 100%
            fig.update_layout(yaxis_tickformat = '.0%', yaxis_range = [0, 1])
            fig.update_layout(
                    title={'x':0.5, 'xanchor': 'center'}, 
                    xaxis_title = "Class Year<br><i><sub>" + subtitle + "</sub></i>")
            fig.update_traces(hovertemplate="For the %{x}, %{y:.0%} of students engaged with %{customdata[0]}<extra></extra>")
            addChartToPage(fig)

        
        #Create the engagement over time graph (also a line graph)
        def createGradesEngagementsGraph():
            #Create copies of the needed variables
            df = originalDf.copy()
            #Remove students who don't have a Unique ID
            df.dropna(subset=['Unique ID'], inplace=True)
            percentagesDF = pd.DataFrame(columns = ["Semester", "Category", "Percentages", "Total Number of Graduates", "Semester Name", "Graduating Year", "Engagement"])


            #Account for aggregating x-axis in the same way as done for the scatter plots 
            semesterValueMappings = {}
            df['Semester Number'] = df.apply(lambda x: create_semester_value(x.Semester, semesterValueMappings), axis=1)
            aggregatedSemesterValueMappings = {16: "Senior Spring", 15: "Senior Winter", 14: "Senior Fall", 13: "Senior Summer", 12: "Junior Spring", 11: "Junior Winter", 10: "Junior Fall", 9: "Junior Summer", 8: "Sophomore Spring", 7: "Sophomore Winter", 6: "Sophomore Fall", 5: "Sophomore Summer", 4: "Freshman Spring", 3: "Freshman Winter", 2: "Freshman Fall", 1: "Freshman Summer"}
            df['Aggregated Semester Number'] = df.apply(lambda x: create_aggregated_semester_value(x.Semester, x.Graduation_Semester), axis=1)
            df['Double Aggregated Semester Number'] = (np.ceil(df['Aggregated Semester Number'] / 4)).astype(int)
            doubleAggregatedSemesterValueMappings = {4: "Senior Year", 3: "Junior Year", 2:"Sophomore Year", 1:"Freshman Year"}
            

            def aggregated_semester_name(row):
                num = row['Aggregated Semester Number']
                if num in aggregatedSemesterValueMappings:
                    return aggregatedSemesterValueMappings[num]
                else:
                    return "Do Not Include"
                
            def double_aggregated_semester_name(row):
                num = row['Double Aggregated Semester Number']
                if num in doubleAggregatedSemesterValueMappings:
                    return doubleAggregatedSemesterValueMappings[num]
                else:
                    return "Do Not Include"
            
            df['Aggregated Semester Name'] = df.apply(aggregated_semester_name, axis = 1)
            df['Double Aggregated Semester Name'] = df.apply(double_aggregated_semester_name, axis = 1)


            df = df.sort_values(['Unique ID', 'Events Start Date Date'], ascending=[True, True])
            #It is critical after sorting that the indices are dropped (reset), otherwise any iteration through the dataframe based on the index will go out of order 
            df.reset_index(drop=True, inplace=True)

            if st.session_state['aggregatedScatter'] == "Do not aggregate (default)":
                semesterNumberedColumn = 'Semester Number'
                correctMapping = semesterValueMappings
            elif st.session_state['aggregatedScatter'] == "Aggregate by class year (Freshman Fall, Freshman Spring, ...)":
                semesterNumberedColumn = 'Aggregated Semester Number'
                correctMapping = aggregatedSemesterValueMappings
            elif st.session_state['aggregatedScatter'] == "Aggregate by class year and semester (Freshman Year, Sophomore Year, ...)":
                semesterNumberedColumn = 'Double Aggregated Semester Number'
                correctMapping = doubleAggregatedSemesterValueMappings



            def agg_to_set(series):
                return set(series)
            
            graduateEmailsDF = st.session_state['graduateEmails']
            graduateYears = graduateEmailsDF.columns
            
            #Figure out which engagement types to use and iterate through them
            engagementsToUse = st.session_state['lineGraphEngagementOptions']
            for category in engagementsToUse:
                #Select the appropriate data based on the Engagement Type
                if category != "Any Engagement":
                    first_df_subset = df[df['Engagement Type'] == category]
                else:
                    first_df_subset = df
                
                #Iterate through the graduating years
                for year in graduateYears:
                    #Select all of the data from the main dataframe with students from that graduating year
                    df_subset = first_df_subset[first_df_subset['Email'].isin(graduateEmailsDF[year])] 
                    #Create a pivot table based on each student, the semester, and have the values be the engagement type(s)
                    pivot_table = df_subset.pivot_table(index='Unique ID', columns=semesterNumberedColumn, values='Engagement Type', aggfunc=agg_to_set)
                    #Update the pivot table so that all values fill to the right of them. 
                    # This is because if a student engaged with an Appointment in the spring, the following fall, we want to still register them as having engaged with an Appointment before
                    pivot_table = pivot_table.ffill(axis=1)
                    #Drop any columns that aren't a valid value for the x-axis (happens when aggregating the x-axis)
                    pivot_table = pivot_table.drop(columns=[col for col in pivot_table.columns if col not in correctMapping.keys()])
                    #Drop any row which is now completely empty
                    pivot_table.dropna(axis = 0, how = "all", inplace = True)

                    
                    currentSet = set(graduateEmailsDF[year])
                    currentSet.discard(np.nan)

                    #Restrict the graduates to only be of the appropriate majors
                    majorsToInclude = set(st.session_state['majorsToInclude'])
                    majMap = st.session_state['Majors Mapping']
                    if len(majorsToInclude) > 0:
                        to_discard = list()
                        for gradEmail in currentSet:
                            if gradEmail not in majMap:
                                to_discard.append(gradEmail)
                            elif not set(majMap[gradEmail]).intersection(majorsToInclude):
                                to_discard.append(gradEmail)
                        for d in to_discard:
                            currentSet.discard(d)

                    numOfGrads = len(currentSet)

                    #Add all of the data to the dataframe
                    #   The main calculation here is summing the number of rows which are filled for each column (how many students have engaged before) and divided by the total number of graduates, to see how the values change over time
                    for col in pivot_table.columns:
                        percentagesDF.loc[len(percentagesDF)] = [col, year + " " + category, pivot_table[col].count()/numOfGrads, numOfGrads, correctMapping[col], year, category]

            #Sort these values, because plotly generates based on the ordering in the dataframe
            percentagesDF.sort_values(by=["Category", "Semester"], ascending = [True, True], inplace=True)
            
            #Create the line graph and update the necessary formatting
            fig = px.line(percentagesDF, x="Semester", y="Percentages", color = "Category", title='When Students Engaged with Hiatt', markers=True, hover_data={"Type of Engagement": percentagesDF['Category'], "Real Semester": percentagesDF['Semester Name'], "Year": percentagesDF['Graduating Year'], "Engagement Name": percentagesDF['Engagement']})
            fig.update_layout(yaxis_tickformat = '.0%')
            fig.update_layout(
                    title={'x':0.5, 'xanchor': 'center'}, 
                    xaxis_title = "Semester<br><i><sub>" + subtitle + "</sub></i>")
            fig.update_traces(hovertemplate="%{y:.0%} of the graduating class of %{customdata[2]} engaged with %{customdata[3]} by %{customdata[1]}<extra></extra>")
            #Update the x axis so that it has the correct names (they are generated using the number versions, because it ensures that plotly puts them in the correct order)
            fig.update_xaxes(ticktext=list(correctMapping.values()), tickvals=list(correctMapping.keys())) 
            addChartToPage(fig)

            return
        
            



        
        






        ### Extra space added here just to make very clear the distinction 
        ### between the code to generate the graphs and the code that runs everytime the button is pressed


















        

        
        df = st.session_state['df'].copy()
        
        #Create a unique ID for each student based on the email (in the past was used with name as well, but that was found to be less effective)
        df['Unique ID'] = df.groupby(['Email']).ngroup()
        
        #Create a new Semester column based on the data cleaning function
        df['Semester'] = df.apply(clean_semesters, axis=1)

        #Function that restricts the data based on the graduating year
        def updatedRestrictByCohort(df, graduationYear):
            df.drop(df[
                (df['Graduation_Semester'] != 'Spring Semester ' + str(graduationYear)) &
                (df['Graduation_Semester'] != 'Summer Semester ' + str(graduationYear)) &
                (df['Graduation_Semester'] != 'GPS Spring Semester ' + str(graduationYear)) &
                (df['Graduation_Semester'] != 'GPS Fall Semester ' + str(graduationYear-1)) &
                (df['Graduation_Semester'] != 'Fall Semester ' + str(graduationYear-1))].index, inplace=True)
            return df
        #Old method used to restrict based on the graduating year
        def restrictByCohort(df, graduationYear):
            df.drop(df[
                ((df['Class Level'] != 'Senior') &
                (df['Class Level'] != 'Junior')  &
                (df['Class Level'] != 'Sophomore') &
                (df['Class Level'] != 'Freshman'))
                ].index, inplace=True)
            df.drop(df[((df['Semester'] == (str(graduationYear-1) + 'Fall')))].index, inplace=True)
            df.drop(df[((df['Class Level'] == 'Senior') & 
                    ((df['Semester'] != ('Summer ' + str(graduationYear-1))) & 
                    (df['Semester'] != ('Fall ' + str(graduationYear-1))) &
                    (df['Semester'] != ('Winter ' + str(graduationYear-1))) & 
                    (df['Semester'] != ('Spring ' + str(graduationYear)))))].index, inplace=True)
            df.drop(df[((df['Class Level'] == 'Junior') & 
                    ((df['Semester'] != ('Summer ' + str(graduationYear-2))) & 
                    (df['Semester'] != ('Fall ' + str(graduationYear-2))) &
                    (df['Semester'] != ('Winter ' + str(graduationYear-2))) & 
                    (df['Semester'] != ('Spring ' + str(graduationYear-1)))))].index, inplace=True)
            df.drop(df[((df['Class Level'] == 'Sophomore') & 
                    ((df['Semester'] != ('Summer ' + str(graduationYear-3))) & 
                    (df['Semester'] != ('Fall ' + str(graduationYear-3))) &
                    (df['Semester'] != ('Winter ' + str(graduationYear-3))) & 
                    (df['Semester'] != ('Spring ' + str(graduationYear-2)))))].index, inplace=True)
            df.drop(df[((df['Class Level'] == 'Freshman') & 
                ((df['Semester'] != ('Summer ' + str(graduationYear-4))) & 
                (df['Semester'] != ('Fall ' + str(graduationYear-4))) &
                (df['Semester'] != ('Winter ' + str(graduationYear-4))) & 
                (df['Semester'] != ('Spring ' + str(graduationYear-3)))))].index, inplace=True)
            return(df)


        #Restrict based on the graduating year if instructed by the user
        if(graduationYearToRestrictBy != 'Do not restrict by graduation year'):
            df = updatedRestrictByCohort(df, int(graduationYearToRestrictBy))
            #The subtitle variable is used to keep track of how the data is being restricted, and is printed at the bottom of all graphs in order to ensure that it is clear 
            # (this is especially important when the data is being added to the workbook, because then the user may misremember which graph has which restriction, while the other fine tuning options are visually identifiable)
            subtitle = "Graduating class of " + graduationYearToRestrictBy
        else:
            subtitle = "Data not restricted by graduating class"
        

        #Add a column to account for the size of each event. This is used for the heatmap and used to be used as priority, but now the user inputs the event rankings
        def event_sizes(row):
            return eventSize[row['Engagement Type']]

        eventSize = df.groupby('Engagement Type').count().to_dict(orient='dict')['Semester']
        df['Event Size'] = df.apply(event_sizes, axis=1)


        #Create some lists to be used for different graphs based on creating dictionaries/lists/sets of the different types of engagements
        mapping = {}
        events = df.groupby('Engagement Type').count().to_dict(orient='dict')['Unique ID']
        sorted_events = sorted(events.items(), key=lambda x:x[1], reverse=True)
        sorted_events_dictionary = dict(sorted_events)
        
        x=0
        while x < len(sorted_events):
            mapping[sorted_events[x][0]] = x+1
            x +=1

        def ranked_events(row):
            return mapping[row['Engagement Type']]
        df['Ranked Events'] = df.apply(ranked_events, axis=1)
        

        originalEngagementList = st.session_state['RankedEngagementList']

        #Create a basic dataframe that is often modified for different graphs
        total = pd.DataFrame(index = originalEngagementList, columns=originalEngagementList)

        for col in total.columns:
            total[col].values[:] = 0


        #Restrict the data to only include the desired majors
        majorsToInclude = set(st.session_state['majorsToInclude'])
        if len(majorsToInclude) > 0:
            to_delete = list()
            #If the student doesn't have any of the majors that are on the list of majors to include, add them to a list to delete
            for id, row in df.iterrows():
                if not set(row.Majors).intersection(majorsToInclude):
                    to_delete.append(id)
            df.drop(to_delete, inplace=True)
            
            #The subtitle variable is used to keep track of how the data is being restricted, and is printed at the bottom of all graphs in order to ensure that it is clear 
            # (this is especially important when the data is being added to the workbook, because then the user may misremember which graph has which restriction, while the other fine tuning options are visually identifiable)
            subtitle += ", only including students with majors in the following categories: " + ', '.join(majorsToInclude)
        else:
             # The subtitle is modified depending on whether the data has been restricted by graduating class as well or not
            if subtitle == "Data not restricted by graduating class":
                subtitle += " or students major"
            else:
                subtitle += ", data not restricted by students major"

        
        #If the user instructs to restrict based on known graduates, all rows are removed unless their email is found within the list of emails known to have graduated
        if st.session_state['restrictByKnownGraduates']:
            #The subtitle variable is used to keep track of how the data is being restricted, and is printed at the bottom of all graphs in order to ensure that it is clear 
            # (this is especially important when the data is being added to the workbook, because then the user may misremember which graph has which restriction, while the other fine tuning options are visually identifiable)
            if subtitle != "Data not restricted by graduating class or students major":
                subtitle += "<br>Data also restricted to only include students known to have graduated"
            else:
                subtitle = "Data restricted to only include students known to have graduated, but not by students major or graduating class"
            
            graduateEmailsDF = st.session_state['graduateEmails']
            graduateEmailsList = graduateEmailsDF.values.flatten()
            df = df[df['Email'].isin(graduateEmailsList)]



        #Rename the main variables (this was done to ensure that they are not modified accidentally)
        originalDf = df
        originalMapping = mapping
        originalTotal = total
        originalSuccess = total
        originalPercent = total
        

        #Based on what graphs the user has instructed to generate, run the appropriate functions
        if "Engagement Relationships (Unique)" in graphTypes:
            createHeatMap(False)
        if "Engagement Relationships (Total)" in graphTypes:
            createHeatMap(True)
        if "Sequential Pathways of Student Engagements" in graphTypes:
            createSankeyDiagram()
        #All code for this line graph is still present, but they have been removed from the options
        #  (To be clear, there are two new line graphs. This was an old version of a line graph that has not been used since the end of Summer of 2024)
        #if "Line Graph" in graphTypes:
        #    createLineGraph()

        #If any of the scatterplots are requested
        if bool({"First Engagements Data (Total)", "First Engagements Data (Unique)", "Return Rates Based on All Engagements", "Return Rates Based on First Engagements", "Rates of Unique Engagements", "Students with only 1 Engagement"} & set(graphTypes)):
            createScatterPlot()
        if "Total Engagement Percentages" in graphTypes:
            createGraduateGraph()
        if "When Students Engaged with Hiatt" in graphTypes:
            createGradesEngagementsGraph()




    #If the generate button has not been pressed but there have been graphs generated, display all the graphs
    # While seemingly minor, this ensures that the graphs persist even when the user interacts with the website
    elif st.session_state['graphsGenerated']:
        for fig in st.session_state['currentGraphs']:
            addChartToPage(fig)
