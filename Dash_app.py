#!/usr/bin/env python
# coding: utf-8

import dash
from dash import dcc, html
from dash.dependencies import Input, Output

import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
import numpy as np
from datetime import date

confirmed = pd.read_csv('https://raw.githubusercontent.com/YoussefElkilaney/Dash_app/main/time_series_covid19_confirmed_global.csv')
deaths = pd.read_csv('https://raw.githubusercontent.com/YoussefElkilaney/Dash_app/main/time_series_covid19_deaths_global.csv')

countries = deaths.apply(lambda x:f'{x[1]}{"" if pd.isna(x[0]) else ", "+x[0]}', axis=1)

confirmed.drop(columns=['Province/State'], inplace=True)
deaths.drop(columns=['Province/State'], inplace=True)

confirmed.iloc[:,0] = countries
deaths.iloc[:,0] = countries

countries = list(countries.values)

latlongCountry =  confirmed.iloc[:,:3]

confirmeddf = confirmed.T.iloc[3:,:]
confirmeddf.columns = countries

deathsdf = deaths.T.iloc[3:,:]
deathsdf.columns = countries

confirmeddf.index = pd.to_datetime(confirmeddf.index)
deathsdf.index = pd.to_datetime(deathsdf.index)

coronadf = confirmeddf.join(deathsdf, lsuffix='_confirmed', rsuffix='_deaths')

# MultiIndex Column, Country -> Confirmed/Deaths
coronadf = coronadf.reindex(sorted(coronadf.columns), axis=1)
coronadf_cols = pd.MultiIndex.from_product([confirmeddf.columns, ["confirmed", "deaths"]])

# MultiIndex Column, Confirmed/Deaths -> Country
# coronadf_cols = pd.MultiIndex.from_product([["confirmed"], confirmeddf.columns]).append(pd.MultiIndex.from_product([["deaths"], confirmeddf.columns]))

coronadf.columns = coronadf_cols

coronadfCumulative = coronadf.copy()

for i in range(len(coronadf)-1,0,-1):
    coronadf.iloc[i,:] -= coronadf.iloc[i-1,:]

tmp = coronadf.sum().reset_index()
tmp['tmp'] = tmp['level_0']+'_'+tmp['level_1'].str[0]
tmp = tmp.drop(columns=['level_0','level_1'])

# countryStats = pd.DataFrame([countries, list(tmp[tmp['tmp'].str[-1]=='c'][0]), list(tmp[tmp['tmp'].str[-1]=='d'][0])]).T
# countryStats.columns = ['country', 'confirmed', 'death']

latlongCountry['confirmed'] = list(tmp[tmp['tmp'].str[-1]=='c'][0])
latlongCountry['death'] = list(tmp[tmp['tmp'].str[-1]=='d'][0])

app = dash.Dash(__name__)

server = app.server


ctry = countries[1]

inlineStyle = {'display': 'inline-block'}

Inputs = [
    html.Div([
        html.Div([ dcc.Dropdown(
            id="ctryDrpDwn",
            options=[{"label": x, "value": x} for x in countries],
            value=countries[:2],
            multi=True,
        )], style={**inlineStyle, 'width': '88%', 'margin-right':'10px'}),
        dcc.Checklist(
            id='ChoiceSlctBox',
            options=[{'label':x, 'value':x[0]} for x in ['Confirmed','Deaths']],
            value=['C','D'],
            style={**inlineStyle, 'width':'10%'},
        ),
    ]),

]

Graph1_1 = dcc.Graph(id='Graph1_1'),

Graph1_2 = dcc.Graph(id='Graph1_2'),

Graph2 = [
    html.Div([
        html.Div([ dcc.Dropdown(
            id='PorjectionSlctBox',
            options=[
                {'label': 'Default', 'value': 0},
                {'label': 'natural earth', 'value': 1},
                {'label': 'orthographic', 'value': 2}
            ],
            multi=False,
            value=2
        )], style={**inlineStyle, 'width': '88%', 'margin-right':'10px'}),
        dcc.RadioItems(id='ChoiceRadioBox',
            options=[
                {'label': 'Confirmed', 'value': 'confirmed'},
                {'label': 'Deaths', 'value': 'death'}
            ],
            value='confirmed',
            style={**inlineStyle, 'width':'10%'},
        ),
    ]),
    dcc.Graph(id='Graph2'),
]

Header = [
    html.Div([
        html.H3('Corona Dataset Analysis')
    ])
]

app.layout = html.Div([
    *Header,
    *Inputs,
    html.Div(html.Br()),
    dcc.Tabs(id='graphTabsId', value='0', children=[
        dcc.Tab(label='Line Plot', value='0'),
        dcc.Tab(label='Bar Plot', value='1'),
    ]),
    html.Div(id='graphTabs'),
    html.Div(html.Br()),
    *Graph2
])

@app.callback(
    Output('graphTabs','children'),
    Input('graphTabsId','value')
)
def updateTabsGraph1(tab):
    return [Graph1_1, Graph1_2][int(tab)]
    
@app.callback(
    Output('Graph1_1', 'figure'),
    [Input("ctryDrpDwn", 'value'),
     Input("ChoiceSlctBox", 'value')],
#      Input('DateTimeRange', 'start_date'),
#      Input('DateTimeRange', 'end_date')]
)
def updateGraph1_1(ctry, choices):
    fig = go.Figure()
    
    for c in ctry:
        ctry_df = coronadf.loc[:,c]
        
        selector = 0
        
        if len(c) > 20:
            c = '..' + ', '.join(c.split(',')[1:])[:20]
            
        if 'C' in choices:
            fig.add_trace(go.Scatter(x=ctry_df.index,
                                     y=ctry_df['confirmed'],
                                     name=f'{c}, confirmed',
                                     mode='lines+markers',
                                     marker_symbol='circle')
                         )
#             fig.update_traces(selector=selector, 'style':''); #line={'color':"#f55"}
            selector += 1

        if 'D' in choices:
            fig.add_trace(go.Scatter(x=ctry_df.index,
                                     y=ctry_df['deaths'],
                                     name=f'{c}, deaths',
                                     mode='lines+markers',
                                     marker_symbol='square')
                         )
#             fig.update_traces(selector=selector, line={'color':"#bbb"});

    fig.update_layout({'title':f'Confirmed / Deaths rate In {", ".join(ctry)}'}, hovermode="x")

    return fig

@app.callback(
    Output('Graph1_2', 'figure'),
    [Input("ctryDrpDwn", 'value'),
     Input("ChoiceSlctBox", 'value')],
)
def updateGraph1_2(ctry, choices):
    fig = go.Figure()

    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    months = [f'{months[y-1]}, {x}' for x,y in coronadf.groupby([coronadf.index.year, coronadf.index.month]).sum().index]

    for c in ctry:
        selector = 0

        if len(c) > 20:
            c = '..' + ', '.join(c.split(',')[1:])[:20]

        if 'C' in choices:
            ctry_df = list(coronadf.loc[:,(c,'confirmed')].groupby([coronadf.index.year, coronadf.index.month]).sum())
            fig.add_trace(go.Bar(x=months,
                                     y=ctry_df,
                                     name=f'{c}, confirmed',
                                )
                         )
    #             fig.update_traces(selector=selector, 'style':''); #line={'color':"#f55"}
            selector += 1

        if 'D' in choices:
            ctry_df = list(coronadf.loc[:,(c,'deaths')].groupby([coronadf.index.year, coronadf.index.month]).sum())
            fig.add_trace(go.Bar(x=months,
                                     y=ctry_df,
                                     name=f'{c}, deaths',
                                )
                         )
    #             fig.update_traces(selector=selector, line={'color':"#bbb"});

    fig.update_layout({'title':f'Confirmed / Deaths rate In {", ".join(ctry)}'}, hovermode="x")

    return fig

@app.callback(
    Output('Graph2', 'figure'),
    [Input("ctryDrpDwn", 'value'),
     Input("ChoiceRadioBox", 'value'),
     Input("PorjectionSlctBox", 'value')]
)
def updateGraph2(ctry, choice='confirmed', projection=2):
    fig = go.Figure()
    fig.add_trace(
        go.Scattergeo(
            lat = latlongCountry['Lat'],
            lon = latlongCountry['Long'],
            mode = 'markers',
            hovertext=latlongCountry['Country/Region'],
            name='',
            showlegend=False,
            marker = {'color':'#4477bb', 'size':np.log(1+latlongCountry[choice]), 'opacity':1},
        ),
    )

    fig.update_traces(
        mode='markers',
        hovertext=[f'{ctry}<br>confirm = {confirm:,}<br>death = {death:,}' for ctry,confirm,death in list(latlongCountry[['Country/Region', 'confirmed', 'death']].values)]
    )

    fig.update_geos(
        showland=True, landcolor="LightGreen",
        showocean=True, oceancolor="LightBlue",
        showcountries=True, countrycolor="Black",
        projection_type=[None,"natural earth", "orthographic"][projection],
#         projection_rotation={'lon':30, 'lat':33, 'roll':0},
        showframe=False
    )

    fig.update_layout(
        margin=dict(r=0, t=0, b=0, l=0),
        annotations=[
            go.layout.Annotation(
                text="Corona Dataset Analysis",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0,
                y=0)
        ]
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=False)
