# -*- coding: utf-8 -*-
import dash
import dash_auth

app = dash.Dash()
auth = dash_auth.BasicAuth(app, [['dash', '4cash']])
server = app.server
app.config.suppress_callback_exceptions = True

# dash basic css
app.css.append_css(
    {"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"}
)

# loading screen css
#app.css.append_css(
#    {"external_url": "https://codepen.io/chriddyp/pen/brPBPO.css"}
#)
