from dash import Dash, dcc, html, Input, Output, Patch
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Initialize the Dash app
dash_app = Dash(__name__, server=False)

# Sample data for the plot
data_y = np.random.rand(100)
data_x = np.arange(0, len(data_y), 1)

fig = go.Figure()
fig.add_trace(go.Scatter(x=data_x, y=data_y, mode='lines'))

# Define the layout of the Dash app
dash_app.layout = html.Div([
    dcc.Graph(id='graph', figure=fig),
    html.Div(id='cursor-info')
])

# Function to create vertical lines
def create_shapes(*positions):
    shapes = [
        {
            'type': 'line',
            'x0': pos,
            'x1': pos,
            'xref': 'x',
            'y0': 0,
            'y1': 1,
            'yref': 'paper',
            'line': {'color': 'red', 'width': 2}
        }
        for pos in positions
    ]
    return shapes

# Callback to update the graph on click
@dash_app.callback(
    [Output('graph', 'figure'), Output('cursor-info', 'children')],
    [Input('graph', 'clickData')]
)
def update_graph(clickData):
    if clickData is None:
        return dash.no_update, ""
    
    x = clickData['points'][0]['x']
    fig.add_shape(type="line",
                  x0=x, x1=x, y0=0, y1=1,
                  line=dict(color="Red",width=2))
    cursor_info = f'Cursor position: {x}'
    return fig, cursor_info
