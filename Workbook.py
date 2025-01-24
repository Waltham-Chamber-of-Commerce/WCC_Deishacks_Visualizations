import streamlit as st
import re  # Import regex for string pattern matching, necessary for click interactivity

# Add a reset button to clear all graphs from the workbook
if st.button("Reset workbook"):
    st.session_state['workbookGraphs'] = []

# Custom CSS to modify the appearance of text area inputs, although the minimum height is no longer used as it doesn't work properly on online streamlit pages
st.markdown(
"""
<style>
div[data-baseweb="base-input"] > textarea {
    min-height: 1px;
    padding: 0;
}
</style>
""", unsafe_allow_html=True
)

# Add main title with custom styling
st.markdown("<p style='text-align: center; font-size: 3em; font-weight: bold; color: #003478; margin-bottom: 0.5em; line-height: 1.2;'>Workbook -- Compare and Notate Graphs<p>", unsafe_allow_html=True)

# Add subtitle with custom styling
st.markdown('<p style="text-align: center; font-size: 1.5em; font-weight: bold; color: #003478; margin-bottom: 1.5em; line-height: 1.1; font-style: italic;">Add graphs from the home page and view them here</p>', unsafe_allow_html=True)

# Custom CSS for horizontal divider, using the Brandeis blue
st.html(
    '''
    <style>
    hr {
        border: none;
        height: 2px;
        color: #003478;  /* old IE */
        background-color: #003478;  /* Modern Browsers */
        margin-bottom: 0px;
        margin-top: 0px;
    }
    </style>
    '''
)
st.divider()  # Add a divider with the above CSS styling

# Loop through each graph stored in the session state to display each one
for fig in st.session_state['workbookGraphs']:
    st.write("")  # Add empty space
    # Display the plotly chart with point selection enabled (click interactivity)
    chart = st.plotly_chart(fig, on_select="rerun", selection_mode="points")
    
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
    
    # Add a text area for notes below each graph
    st.text_area(label = "Add any notes here", 
                placeholder = "Add any additional notes about the graphs here", 
                height = 70, 
                key = fig, 
                label_visibility="collapsed")
