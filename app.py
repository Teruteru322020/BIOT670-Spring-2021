'''
    BIOT670 Capstone Project - Quad Viewer
    plotting functions
    nkim
    
    To set virtualenv to configure app.py (Dash application) to any setting 
    To add Files to the Development Folder by adding following files
        app1.py	a Dash application
        .gitignore	used by git, identifies files that won’t be pushed to production
        Procfile	used for deployment
        requirements.txt	describes your Python dependencies, can be created automatically     
'''

import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

USERNAME_PASSWORD_PAIRS = [
    ['JamesBond', '007'],['LouisArmstrong', 'satchmo']
]

app = dash.Dash()
auth = dash_auth.BasicAuth(app,USERNAME_PASSWORD_PAIRS)
server = app.server

app.layout = html.Div([
    dcc.RangeSlider(
        id='range-slider',
        min=-5,
        max=6,
        marks={i:str(i) for i in range(-5, 7)},
        value=[-3, 4]
    ),
    html.H1(id='product')  # this is the output
], style={'width':'50%'})

@app.callback(
    Output('product', 'children'),
    [Input('range-slider', 'value')])
def update_value(value_list):
    return value_list[0]*value_list[1]

if __name__ == '__main__':
    app.run_server()

    
    

'''
    BIOT670 Capstone Project - Quad Viewer
    plotting functions
'''
import json
import os
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import base64
import io
import pandas as pd
from dash.dependencies import Input, Output, State
from uiutils import update_dropdowns, serve_layout
from plotutils import generate_plot
import numpy as np



external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.config.suppress_callback_exceptions = True

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}
# Declare a global dataframe to hold the uploaded information
df = pd.DataFrame()
files = {}

app.layout = serve_layout

# Create pie chart for every row in data frame
colour_column = 'All_Pathways'


# Parse uploaded data function
def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    global df
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'tsv' in filename:
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')),
                sep='\t'
            )
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    df = df.replace(np.nan, 'None', regex=True)
    files[filename] = df.to_dict()


# Callback for handling uploaded data
# After data uploaded it is parsed into global df item and then populates the columns for dropdowns 
@app.callback(Output('file-selector', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]

        return (
            dcc.Dropdown(
                id='file-dropdown',
                options=[{'label': file, 'value': file} for file in list_of_names],
                clearable=False,
                searchable=True,
                placeholder='Please Select Your File'
            ))


@app.callback(Output('file-name', 'children'),
              Output('dropdown-items', 'children'),
              Input('file-dropdown', 'value'))
def drop_down_updates(file_name):
    global df
    if file_name is not None:
        df = pd.DataFrame.from_dict(files[file_name])
    return update_dropdowns(file_name, df)


# After selecting columns to plot, create those traces
@app.callback(
    Output('basic-interactions', 'figure'),
    [Input('xpos-dropdown', 'value'),
     Input('ypos-dropdown', 'value'),
     Input('xneg-dropdown', 'value'),
     Input('yneg-dropdown', 'value'),
     Input('scale-radio', 'value'),
     Input('name-dropdown', 'value'),
     Input('colour-dropdown', 'value'),
     State('basic-interactions', 'figure')])
def create_figure(xpos, ypos, xneg, yneg, scale, name, colour_by, state):
    global df
    return generate_plot(df, xpos, ypos, xneg, yneg, scale, name, colour_by)



# Format and display hover data in a table below the graph
@app.callback(
    Output('hover-data', 'children'),
    [Input('basic-interactions', 'hoverData'),
     Input('xpos-dropdown', 'value'),
     Input('ypos-dropdown', 'value'),
     Input('xneg-dropdown', 'value'),
     Input('yneg-dropdown', 'value'),
     Input('name-dropdown', 'value'),
     Input('colour-dropdown', 'value'),
     State('xpos-dropdown', 'value')])
def display_hover_data(hoverData, xpos, ypos, xneg, yneg, row_name, pathways, state):
    if hoverData is not None:
        global df
        try:
            name = hoverData['points'][0]['customdata'][1]
        except IndexError:
            name = hoverData['points'][0]['customdata'][0]
        if pathways is not None:
            path = df.loc[df[row_name] == name, pathways].values[0]
            path = '\n\t\t'.join(x.strip() for x in path.split(','))
        else:
            path = "NA"
        output_dict = {}
        if xpos is not None:
            output_dict[xpos] = df.loc[df[row_name] == name, xpos].values[0]
        if ypos is not None:
            output_dict[ypos] = df.loc[df[row_name] == name, ypos].values[0]
        if xneg is not None:
            output_dict[xneg] = df.loc[df[row_name] == name, xneg].values[0]
        if yneg is not None:
            output_dict[yneg] = df.loc[df[row_name] == name, yneg].values[0]
        blah = f'Protein:\t{name}\nColoured by:\t{path}\n' + ''.join(
            f'{k}:\t{output_dict[k]}\n' for k in output_dict.keys())
        return blah


if __name__ == '__main__':
    app.run_server(debug=False)
