# -*- coding: utf-8 -*-
import base64
import io
import os

import colorlover as cl
import dash_core_components as dcc
import dash_html_components as html
import plotly.colors
import plotly.graph_objs as go
import pandas as pd

from dash.dependencies import Input, Output, State
from flask_caching import Cache
from utils import tighten_up

# load the app itself
from app import app

server = app.server

# building a filesystem cache for our app
CACHE = Cache()
CACHE_DIR = os.path.join(os.sep, 'tmp', 'dash_cache')
if not os.path.isdir(CACHE_DIR):
    os.makedirs(CACHE_DIR)

CACHE_CONFIG = {
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': CACHE_DIR,
}

CACHE.init_app(app.server, config=CACHE_CONFIG)

# a quick utility item
# get some pandas dataframe by loading it from a url
IRIS_URL = (
    'https://raw.githubusercontent.com/uiuc-cse/data-fa14/gh-pages/data/'
    'iris.csv'
)
@CACHE.memoize()
def df_from_url(url):
    print('loading pandas df from url {}'.format(url))
    df = pd.read_csv(url)
    tighten_up(df)
    return df

DF = df_from_url(IRIS_URL)


# some plotting and styling constants
COLOR_SCALES_CONTINUOUS = [
    'Greys',
    'YlGnBu',
    'Greens',
    'YlOrRd',
    'Bluered',
    'RdBu',
    'Reds',
    'Blues',
    'Picnic',
    'Rainbow',
    'Portland',
    'Jet',
    'Hot',
    'Blackbody',
    'Earth',
    'Electric',
    'Viridis',
    'Cividis',
]
CL_QUAL = {
    int(numcolors): {
        name: plotly.colors.make_colorscale(colors)
        for (name, colors) in v['qual'].items()
    }
    for (numcolors, v) in cl.scales.items()
}

# loading the intro and description text, written in external markdown documents
# (because it's easy)
with open('intro.md', 'r') as fp:
    INTRO = fp.read()
with open('description.md', 'r') as fp:
    DESCRIPTION = fp.read()


# build the frame in which we will render the different apps based on url. leave
# the list of other padges at the top like a very shitty toc
app.layout = html.Div(className="container", children=[
    html.Div(className="row", children=[dcc.Markdown(INTRO)]),
    html.Hr(),
    html.Div(className="row", children=[
        html.Div(className="four columns", id='feature-menu', children=[
            html.Div(className='row', id='feature-selector', children=[
                html.H4("Included Features"),
                html.Label(
                    'Select which features you want to include in your '
                    'parallel coordinates plot'
                ),
                dcc.Dropdown(
                    id='feature-selector-dropdown',
                    options=[
                        {'label': col, 'value': col} for col in DF.columns
                    ],
                    value=DF.columns[:-1],
                    multi=True,
                )
            ]),
            html.Div(className='row', id='target-selector', children=[
                html.H4("Target Feature"),
                html.Label('Select your target feature:'),
                dcc.Dropdown(
                    id='target-selector-dropdown',
                    options=[
                        {'label': col, 'value': col} for col in DF.columns
                    ],
                    value=DF.columns[-1]
                )
            ]),
            html.Div(className='row', id='color-selector', children=[
                html.H4("Color Scale"),
                html.Label("Select your color scale:"),
                dcc.Dropdown(
                    id='color-selector-dropdown',
                    # default options and value are determined by target
                )
            ]),
        ]),
        html.Div(className="eight columns", id='uploads', children=[
            html.Div(className='row', children=[html.H4("Load your dataset")]),
            html.Div(
                className='row', id='url-upload-df-trigger', hidden=True,
                n_clicks=0
            ),
            html.Div(className='row', id='url-upload-div', children=[
                html.Label('URL upload:'),
                dcc.Input(
                    id='url-upload-input',
                    placeholder="URL of your data file",
                    type='text',
                    value=IRIS_URL,
                    style={'width': '80%', 'margin': '0px 5px 0px 0px'},
                ),
                html.Button(
                    id='url-submit-button', className='button-primary',
                    children="Submit", style={'width': '15%'},
                ),
            ]),
            html.Div(
                className='row', id='file-upload-df-trigger', hidden=True,
                n_clicks=0
            ),
            html.Div(className='row', id='file-upload-div', children=[
                html.Label('Local file upload:'),
                dcc.Upload(
                    id='file-upload',
                    children=['Drag and drop or ', html.A('select a file')],
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                    },
                )
            ]),
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className='row', id='pc-plot-div', children=[
            dcc.Graph(id='pc-plot')
        ]),
    ]),
    html.Hr(),
    html.Div(className="row", children=[dcc.Markdown(DESCRIPTION)]),
], style={'max-width': 1080})


# someone pressed the url upload submit button -- get the new url, cache it,
# and trigger a redraw of the graph
@app.callback(
    Output('url-upload-df-trigger', 'value'),
    [Input('url-submit-button', 'n_clicks')],
    [State('url-upload-input', 'value')]
)
def url_input(n_clicks, url):
    global DF
    DF = df_from_url(url)
    return n_clicks


# someone uploaded a file -- save the file as a temp file, load it as a
# dataframe and trigger a redraw of the graph
@app.callback(
    Output('file-upload-df-trigger', 'value'),
    [
        Input('file-upload', 'contents'),
        Input('file-upload', 'filename'),
    ],
    [State('file-upload-df-trigger', 'value')]
)
def file_upload(contents, filename, current_value):
    global DF

    if contents is None:
        return current_value

    contenttype, contentstr = contents.split(',')
    decoded = base64.b64decode(contentstr)

    ext = os.path.splitext(filename)[-1]

    print('attempting to load file {}'.format(filename))

    if ext == '.csv':
        with io.StringIO(decoded.decode('utf-8')) as fp:
            DF = pd.read_csv(fp)
    elif ext in ['.xls', '.xlsx']:
        with io.BytesIO(decoded) as fp:
            DF = pd.read_excel(fp)
    elif ext in ['.dat']:
        with io.StringIO(decoded) as fp:
            DF = pd.read_fwf(fp)
    else:
        raise ValueError('unsuported file extension {}'.format(ext))

    tighten_up(DF)

    return (current_value or 0) + 1


# update the available and default values for the included features whenever
# one of the upload df trigger elements changes
@app.callback(
    Output('feature-selector-dropdown', 'options'),
    [
        Input('url-upload-df-trigger', 'value'),
        Input('file-upload-df-trigger', 'value'),
    ]
)
def update_feature_options(urltrigger, filetrigger):
    return [{'label': col, 'value': col} for col in DF.columns]


@app.callback(
    Output('feature-selector-dropdown', 'value'),
    [
        Input('url-upload-df-trigger', 'value'),
        Input('file-upload-df-trigger', 'value'),
    ]
)
def update_feature_values(urltrigger, filetrigger):
    return DF.columns[:-1]


# same story but now for the target
@app.callback(
    Output('target-selector-dropdown', 'options'),
    [
        Input('url-upload-df-trigger', 'value'),
        Input('file-upload-df-trigger', 'value'),
    ]
)
def update_target_options(urltrigger, filetrigger):
    return [{'label': col, 'value': col} for col in DF.columns]


@app.callback(
    Output('target-selector-dropdown', 'value'),
    [
        Input('url-upload-df-trigger', 'value'),
        Input('file-upload-df-trigger', 'value'),
    ]
)
def update_target_value(urltrigger, filetrigger):
    return DF.columns[-1]


# update the color scale whenever the target changes (discrete vs. continuous)
@app.callback(
    Output('color-selector-dropdown', 'options'),
    [
        Input('target-selector-dropdown', 'value'),
        Input('url-upload-df-trigger', 'value'),
        Input('file-upload-df-trigger', 'value'),
    ]
)
def update_color_options(target, urltrigger, filetrigger):
    if is_cat(target):
        t = DF[target].astype('category')
        n = t.nunique()
        return [
            {'label': cn, 'value': cn}
            # if we don't have a qualitative color set large enough for n, we
            # will default to the colorscales in COLOR_SCALE_CONTINUOUS
            for cn in CL_QUAL.get(n, COLOR_SCALES_CONTINUOUS)
        ]
    else:
        return [
            {'label': cs, 'value': cs}
            for cs in COLOR_SCALES_CONTINUOUS
        ]

@app.callback(
    Output('color-selector-dropdown', 'value'),
    [
        Input('target-selector-dropdown', 'value'),
        Input('url-upload-df-trigger', 'value'),
        Input('file-upload-df-trigger', 'value'),
    ]
)
def update_color_options(target, urltrigger, filetrigger):
    if is_cat(target):
        t = DF[target].astype('category')
        n = t.nunique()
        try:
            return list(CL_QUAL[n].keys())[0]
        except KeyError:
            return 'Jet'
    else:
        return 'Jet'


# load categorical as numbers we can acutally include in our parallel
# coordinates plots
def is_cat(col):
    return DF[col].dtype.kind == 'O'


def smart_load(col):
    """convert categories to category values"""
    return DF[col].astype('category').cat.codes if is_cat(col) else DF[col]


def smart_colorscale(colorscale, target):
    if is_cat(target):
        t = DF[target].astype('category')
        n = t.nunique()
        try:
            return CL_QUAL[n][colorscale]
        except KeyError:
            return colorscale
    else:
        return colorscale


def smart_linestyle(target, colorscale):
    return {
        'color': smart_load(target),
        'colorscale': smart_colorscale(colorscale, target),
        'showscale': not is_cat(target)
    }

# update the graph when any of the side panel elements change, or the upload
# of a dataframe trigger element is updated
@app.callback(
    Output('pc-plot', 'figure'),
    [
        Input('feature-selector-dropdown', 'value'),
        Input('target-selector-dropdown', 'value'),
        Input('color-selector-dropdown', 'value'),
        Input('url-upload-df-trigger', 'value'),
        Input('file-upload-df-trigger', 'value'),
    ]
)
def update_figure(features, target, colorscale, urltrigger, filetrigger):
    return {
        'data': [
            go.Parcoords(
                line=smart_linestyle(target, colorscale),
                dimensions=[
                    {
                        #'range': [DF[feature].min(), DF[feature].max()],
                        'label': feature,
                        'values': smart_load(feature),
                    }
                    for feature in features
                ]
            )
        ],
    }


# populate the feature selection checkbox list
#@app.callback(
#    Output(component_id='feature-selector', component_property='children'),
#    [Input(component_id='')]
#)


# this callback will replace the page-content div with whatever the url dictates
# (think of this as a bad routing table)
#@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
#def display_page(pathname):
#    return ROUTES.get(pathname, '404')


if __name__ == "__main__":
    app.run_server(debug=True)
