# -*- coding: utf-8 -*-
"""
Created on Sat Mar 20 13:39:50 2021

@author: David Blumenstiel




"""
#Very helpful
#https://realpython.com/python-dash/
#https://dash.plotly.com/layout

#Load the libraries
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

#Define the app
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


#Starts the layout
#Makes the text
app.layout = html.Div(children=[  #Took alot of this from the tutorial
    html.H1(children='The Health of Trees in NYC'),

    
    html.H4("Below is a measure of the health of trees in NYC by species. "),
    
    
    html.P(["Select the borough you're interested in, and the type of analyis.",html.Br(),
            "'Total Health Analysis' will show the proportion of trees in a borough by health status.",html.Br(),
            "'Stewardship Comparison' will show a relative health rating for each number of stewards per species."]),
    
    html.Div([
        #This adds a button function which allows for the user to input the borough
        html.Div(   #Took this bit mostly from the tutorial
            dcc.RadioItems(
                id='boro_select',
                options=[{'label': i, 'value': i} for i in ['Queens', 'Bronx','Brooklyn','Manhattan','Staten Island']],
                value='Queens',
                labelStyle={'display': 'inline-block'})
            ),
        
        #This adds a button function whch allows the user to select between charts; either stweardship comparison, or total health status
        html.Div(   #Took this bit mostly from the tutorial
            dcc.RadioItems(
                id='comparison_select',
                options=[{'label': i, 'value': i} for i in ['Total Health Status', 'Stewardship Comparison']],
                value='Total Health Status',
                labelStyle={'display': 'inline-block'})
            )
        
    ]),
    
    #Adds the graph, which is defined in the update function (along with it's style)
    dcc.Graph(
        id='Figure'
            
    )
])

             
           
@app.callback(
    #Need seperate outputs for the figure and its style property
    Output(component_id='Figure', component_property='figure'),
    Output(component_id='Figure', component_property='style'),
    #Inputs from the radio buttons for selecting borough/analyis
    Input(component_id='boro_select', component_property='value'),
    Input(component_id='comparison_select', component_property='value')
)            

def update(boro_select, comparison_select):
        
    #Boro select
    boro = boro_select
    
    if comparison_select == "Total Health Status":
    
        ################ Figure 1 #####################
        #In order below:
        #The base url
        #Selects the data we're interested in, and tells it to take counts by ID
        #Limits things to the boro and to trees which are alive
        #Groups by species, stweardship, and health
        #Increases the row limit (we need 1041 rows after aggregation, which is more than the default permits)
        soql_url = ('https://data.cityofnewyork.us/resource/uvpi-gqnh.json?' +\
                '$select=spc_common,health,count(tree_id)' +\
                '&$where=boroname=\''+boro+'\'&status=Alive' +\
                '&$group=spc_common,health' +\
                '&$limit=2000').replace(' ', '%20')
        soql_trees = pd.read_json(soql_url)
        
        #Adds a column for proportionallity within each species, prep's the data
        sums = soql_trees.groupby(by = "spc_common").count_tree_id.sum() 
        df = soql_trees.join(other = sums, on = "spc_common", rsuffix = "_by_spc")
        df = df.assign(proportion = df.count_tree_id/df.count_tree_id_by_spc)
        df.dropna(axis = 0, inplace = True)
        df.health = pd.Categorical(df.health, ["Poor","Fair","Good"])
        df.sort_values(by = ["spc_common","health"], ascending = [False ,False], inplace = True)
        
        #Makes the figure/style
        fig = px.bar(df, y = "spc_common", x = "proportion", color = "health", title = "Health by Species",  )
        fig['layout']['xaxis']['side'] = 'top'
        style={"height" : 2500, "width" : 1500}
        ##############################################
    
    elif comparison_select == 'Stewardship Comparison':
    
        ################ Figure 2 #####################
        #Initial query
        soql_url = ('https://data.cityofnewyork.us/resource/uvpi-gqnh.json?' +\
                '$select=spc_common,steward,health,count(tree_id)' +\
                '&$where=boroname=\''+boro+'\'&status=Alive' +\
                '&$group=spc_common,steward,health' +\
                '&$limit=2000').replace(' ', '%20')
        soql_trees = pd.read_json(soql_url)
     
        #Short story: makes a health score for each species and stewardship from 0 to 100
        #Trees of poor health weight towards 0, trees of fair health weight towards 50, trees of good health weight towards 100.
        #Its all relative to the stewardship category
        
        #Data prep  
        df = soql_trees  
        df.dropna(axis = 0, inplace = True)
        df.health = pd.Categorical(df.health, ["Poor","Fair","Good"])
        df.sort_values(by = ["spc_common","health"], ascending = [True ,False], inplace = True)
        df["health_category_score"] = df.health.astype('category').cat.codes / 2 #https://stackoverflow.com/questions/38088652/pandas-convert-categories-to-numbers
        df["health_score_sums"] = df.health_category_score * df.count_tree_id
       
        #This sorts and renames things so they look nice
        steward_health_scores = pd.DataFrame(df.groupby(["spc_common","steward"]).health_score_sums.sum() / df.groupby(["spc_common","steward"]).count_tree_id.sum()).reset_index() #Getting the actual counts
        steward_health_scores.columns = ["Species", "Stewards", "Health Score"] #Set column names
        steward_health_scores.Stewards = pd.Categorical(steward_health_scores.Stewards, categories = ["None","1or2","3or4","4orMore"], ordered = True) #Reordering
        steward_health_scores.sort_values(by = ["Species","Stewards"], ascending = [False, True], inplace = True)
        steward_health_scores["Health Score"] = steward_health_scores["Health Score"]*100 #Probably coulda done this earlier
        
        #Makes the figure/style
        fig = px.bar(steward_health_scores,y = "Species", x = "Health Score", color = "Stewards", title = "Health by Species", barmode = 'group')
        fig['layout']['xaxis']['side'] = 'top'
        style={"height" : 5500, "width" : 1500}
        ##############################################
    
    return fig, style

#run it             
if __name__ == '__main__':
    app.run_server(debug=False)
























