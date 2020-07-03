import os
import io
import flask
import numpy as np
import pandas as pd
import datetime as dt
import time
import random
import dash
import dash_auth
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import sqlalchemy
from rq import Queue
from rq.job import Job
from worker import conn
from settings import *
from users import *
from startup import *


#redis test
def layout_router(pathname):
    current_style = {'background-color': 'black', 'margin-right': '12px', 'font-weight': 'bold', 'color': 'white', 'font-family': 'Microsoft JhengHei', 'font-size': '18px', 'border-radius': '28px'}
    origin_style = {'background-color': 'white', 'margin-right': '12px', 'font-weight': 'bold', 'color': 'black', 'font-family': 'Microsoft JhengHei', 'font-size': '18px', 'border-radius': '28px'}
    if pathname == '/subject_analysis':
        link_subject_analysis_style = current_style
        link_home_style, link_portfolio_style, link_market_risk_style, link_other_links_style = origin_style, origin_style, origin_style, origin_style
        layout = layout_subject_analysis
    elif pathname == '/portfolio':
        link_portfolio_style = current_style
        link_home_style, link_subject_analysis_style, link_market_risk_style, link_other_links_style = origin_style, origin_style, origin_style, origin_style
        layout = layout_portfolio
    elif pathname == '/market_risk':
        link_market_risk_style = current_style
        link_home_style, link_portfolio_style, link_subject_analysis_style, link_other_links_style = origin_style, origin_style, origin_style, origin_style
        layout = layout_market_risk
    elif pathname == '/other_links':
        link_other_links_style = current_style
        link_home_style, link_portfolio_style, link_market_risk_style, link_subject_analysis_style = origin_style, origin_style, origin_style, origin_style
        layout = layout_other_links
    else:
        link_home_style = current_style
        link_subject_analysis_style, link_portfolio_style, link_market_risk_style, link_other_links_style = origin_style, origin_style, origin_style, origin_style
        layout = layout_home
    return [link_home_style, link_subject_analysis_style, link_portfolio_style, link_market_risk_style, link_other_links_style, layout, None]

##-----------------------------





#____________________________________________
#|____LAYOUTS____________________________________
def call_layout_header():
    layout = dbc.Container(
        dbc.Row([
            dbc.Col(
                html.A([
                    html.Img(
                        src = app.get_asset_url('spark_logo.jpg'),
                        style = {'height': '100px', 'margin-right': '8px'}
                    )
                ],
                href = 'https://rising-spark.herokuapp.com'),
                width = {'size': 'auto'}
            ),

            dbc.Col(
                html.Div([
                    html.Br(),
                    html.Br(),
                    dbc.Nav([
                        dbc.NavLink('資訊首頁', id = 'link_home', href = '/home'),
                        dbc.NavLink('標的分析', id = 'link_subject_analysis', href = '/subject_analysis'),
                        dbc.NavLink('投資組合', id = 'link_portfolio', href = '/portfolio'),
                        dbc.NavLink('市場風險', id = 'link_market_risk', href = '/market_risk'),
                        dbc.NavLink('其他策略', id = 'link_other_links', href = '/other_links')
                    ])
                ]),
                width = {'size': 'auto'}
            )
        ], justify = 'between', style = {'margin-top': '1%', 'margin-left': '1%'})
    , fluid = True)
    return layout

def call_layout_home():
    # import data
    future_decision_table, fd_table_stk_open, fd_table_stk_close, fd_table_stk_hold, decision_count, spy_df, range_breaks = startup_home()
    
    # data computation
    stk_count = int(decision_count.sum(axis = 1).mean())
    fd_close_count = len(fd_table_stk_close)
    fd_open_count = len(fd_table_stk_open)
    fd_hold_count = len(fd_table_stk_hold)
    fd_close_display = str(fd_close_count) + ' 檔，佔 ' + str(stk_count) + ' 檔中的 ' + str(round(fd_close_count/stk_count*100,2)) + '%'
    fd_open_display = str(fd_open_count) + ' 檔，佔 ' + str(stk_count) + ' 檔中的 ' + str(round(fd_open_count/stk_count*100,2)) + '%'
    fd_hold_display = str(fd_hold_count) + ' 檔，佔 ' + str(stk_count) + ' 檔中的 ' + str(round(fd_hold_count/stk_count*100,2)) + '%'
    his_count_x_date = list(decision_count.date)
    his_count_x_axis = list(np.arange(1,len(decision_count)+1))
    his_close_count = list(decision_count.close_count)
    his_open_count = list(decision_count.open_count)
    his_hold_count = list(decision_count.hold_count)
    spy_breaks = list(range_breaks.full_dates[range_breaks.spy_breaks == 0])
    fd_close_popover_body = list(map(lambda x: x+ ', ', list(fd_table_stk_close.stk.sort_values())))
    fd_open_popover_body = list(map(lambda x: x+ ', ', list(fd_table_stk_open.stk.sort_values())))
    fd_hold_popover_body = list(map(lambda x: x+ ', ', list(fd_table_stk_hold.stk.sort_values())))
    tickers_stk = list(future_decision_table[future_decision_table['type'] == 'STK']['stk'])
    home_stk_check_dropdown_df = pd.DataFrame({'label':tickers_stk, 'value':tickers_stk})
    home_stk_check_dropdown_df = home_stk_check_dropdown_df.sort_values('label')
    home_stk_check_dropdown_dict = home_stk_check_dropdown_df.to_dict('records')

    # layout content
    layout = dbc.Container([
        # Title Row
        dbc.Row(
            dbc.Col(
                html.Div(
                    children = '★ 首頁｜Spark A.I. 預測速覽【S&P 500 成份股】',
                    style = {'font-family': 'Microsoft JhengHei', 'font-weight': 'bold', 'font-size': '23px'}
                )
            ), 
            style = {'margin-left': '1%', 'margin-right': '1%'}
        ),
        # Future Prediction Info + SPY T.A. Analysis
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([
                        html.Div(
                            children = '開盤賣出',
                            style = {
                                'font-family': 'Microsoft JhengHei',
                                'font-weight': 'bold',
                                'font-size': '26px'
                            }
                        ),
                        html.Div([
                            dbc.Button(
                                children = 'Check',
                                id = 'fd_close_popover_button',
                                color = 'dark',
                                style = {
                                    'font-family': 'Microsoft JhengHei',
                                    'font-weight': 'bold',
                                    'font-size': '10px'
                                }
                            ),
                            dbc.Popover(
                                [
                                    dbc.PopoverHeader('Spark 開盤賣出清單'),
                                    dbc.PopoverBody(fd_close_popover_body)
                                ],
                                id = 'fd_close_popover',
                                is_open = False,
                                target = 'fd_close_popover_button',
                                placement = 'bottom'
                            )
                        ])
                    ], style = {
                        'width': '42mm',
                        'min-width': '27mm',
                        'height': '26mm',
                        'background-color': '#f23b2e',
                        'border-top-left-radius': '7px',
                        'border-bottom-left-radius': '7px',
                        'border': '2px black solid',
                        'display': 'flex', 'flex-direction': 'column', 'justify-content': 'center', 'align-items': 'center'
                    }),
                    html.Div(
                        html.Div([
                            html.Div(
                                children = fd_close_display,
                                style = {
                                    'font-family': 'Microsoft JhengHei',
                                    'font-weight': 'bold',
                                    'font-size': '16px',
                                    'color': 'black',
                                    'width': '80mm',
                                    'height': '10mm',
                                    'background-color': '#e3e8e5',
                                    'border-top-right-radius': '7px',
                                    'border-top': '2px black solid',
                                    'border-right': '2px black solid',
                                    'display': 'flex', 'justify-content': 'center', 'align-items': 'center'
                                }
                            ),
                            html.Div(
                                dcc.Graph(
                                    figure = {
                                        'data': [
                                            go.Bar(
                                                x = his_count_x_axis,
                                                y = his_close_count,
                                                marker = {'color': his_close_count, 'colorscale': 'RdYlGn'}
                                            )
                                        ],
                                        'layout': go.Layout(
                                            dragmode =  'pan',
                                            showlegend = False,
                                            xaxis_rangeslider_visible = False,
                                            font = {'family': 'Microsoft JhengHei'},
                                            margin = {'t': 3, 'b': 3, 'l': 5, 'r': 5},
                                            xaxis = {
                                                'domain': [0.07, 0.93],
                                                'tickvals': his_count_x_axis,
                                                'ticktext': his_count_x_date,
                                                'fixedrange': True,
                                                'mirror': True
                                            },
                                            yaxis = {'fixedrange': True, 'side': 'right'},
                                            hovermode = 'closest'
                                        )
                                    },
                                    config = {'modeBarButtonsToRemove': ['zoom2d', 'toImage', 'select2d', 'lasso2d', 'autoScale2d', 'toggleSpikelines', 'hoverCompareCartesian', 'hoverClosestCartesian']},
                                    style = {'width': '70mm', 'height': '14mm'}
                                ),
                                style = {
                                    'font-family': 'Microsoft JhengHei',
                                    'color': 'black',
                                    'width': '80mm',
                                    'height': '16mm',
                                    'background-color': 'white',
                                    'border-bottom-right-radius': '7px',
                                    'border-top': '2px black solid',
                                    'border-right': '2px black solid',
                                    'border-bottom': '2px black solid',
                                    'display': 'flex', 'justify-content': 'center', 'align-items': 'center'
                                }
                            )
                        ])
                    )
                ], style = {'display': 'flex', 'justify-content': 'flex-start', 'height': '26mm', 'margin-top': '4%'}),

                html.Div([
                    html.Div([
                        html.Div(
                            children = '開盤買進',
                            style = {
                                'font-family': 'Microsoft JhengHei',
                                'font-weight': 'bold',
                                'font-size': '26px'
                            }
                        ),
                        html.Div([
                            dbc.Button(
                                children = 'Check',
                                id = 'fd_open_popover_button',
                                color = 'dark',
                                style = {
                                    'font-family': 'Microsoft JhengHei',
                                    'font-weight': 'bold',
                                    'font-size': '10px'
                                }
                            ),
                            dbc.Popover(
                                [
                                    dbc.PopoverHeader('Spark 開盤買進清單'),
                                    dbc.PopoverBody(fd_open_popover_body)
                                ],
                                id = 'fd_open_popover',
                                is_open = False,
                                target = 'fd_open_popover_button',
                                placement = 'bottom'
                            )
                        ])
                    ], style = {
                        'width': '42mm',
                        'min-width': '27mm',
                        'height': '26mm',
                        'background-color': '#3dc461',
                        'border-top-left-radius': '7px',
                        'border-bottom-left-radius': '7px',
                        'border': '2px black solid',
                        'display': 'flex', 'flex-direction': 'column', 'justify-content': 'center', 'align-items': 'center'
                    }),
                    html.Div(
                        html.Div([
                            html.Div(
                                children = fd_open_display,
                                style = {
                                    'font-family': 'Microsoft JhengHei',
                                    'font-weight': 'bold',
                                    'font-size': '16px',
                                    'color': 'black',
                                    'width': '80mm',
                                    'height': '10mm',
                                    'background-color': '#e3e8e5',
                                    'border-top-right-radius': '7px',
                                    'border-top': '2px black solid',
                                    'border-right': '2px black solid',
                                    'display': 'flex', 'justify-content': 'center', 'align-items': 'center'
                                }
                            ),
                            html.Div(
                                dcc.Graph(
                                    figure = {
                                        'data': [
                                            go.Bar(
                                                x = his_count_x_axis,
                                                y = his_open_count,
                                                marker = {'color': his_open_count, 'colorscale': 'RdYlGn'}
                                            )
                                        ],
                                        'layout': go.Layout(
                                            dragmode =  'pan',
                                            showlegend = False,
                                            xaxis_rangeslider_visible = False,
                                            font = {'family': 'Microsoft JhengHei'},
                                            margin = {'t': 3, 'b': 3, 'l': 5, 'r': 5},
                                            xaxis = {
                                                'domain': [0.07, 0.93],
                                                'tickvals': his_count_x_axis,
                                                'ticktext': his_count_x_date,
                                                'fixedrange': True,
                                                'mirror': True
                                            },
                                            yaxis = {'fixedrange': True, 'side': 'right'},
                                            hovermode = 'closest'
                                        )
                                    },
                                    config = {'modeBarButtonsToRemove': ['zoom2d', 'toImage', 'select2d', 'lasso2d', 'autoScale2d', 'toggleSpikelines', 'hoverCompareCartesian', 'hoverClosestCartesian']},
                                    style = {'width': '70mm', 'height': '14mm'}
                                ),
                                style = {
                                    'font-family': 'Microsoft JhengHei',
                                    'color': 'black',
                                    'width': '80mm',
                                    'height': '16mm',
                                    'background-color': 'white',
                                    'border-bottom-right-radius': '7px',
                                    'border-top': '2px black solid',
                                    'border-right': '2px black solid',
                                    'border-bottom': '2px black solid',
                                    'display': 'flex', 'justify-content': 'center', 'align-items': 'center'
                                }
                            )
                        ])
                    )
                ], style = {'display': 'flex', 'justify-content': 'flex-start', 'height': '26mm', 'margin-top': '5%'}),

                html.Div([
                    html.Div([
                        html.Div(
                            children = '繼續持有',
                            style = {
                                'font-family': 'Microsoft JhengHei',
                                'font-weight': 'bold',
                                'font-size': '26px'
                            }
                        ),
                        html.Div([
                            dbc.Button(
                                children = 'Check',
                                id = 'fd_hold_popover_button',
                                color = 'dark',
                                style = {
                                    'font-family': 'Microsoft JhengHei',
                                    'font-weight': 'bold',
                                    'font-size': '10px'
                                }
                            ),
                            dbc.Popover(
                                [
                                    dbc.PopoverHeader('Spark 繼續持有清單'),
                                    dbc.PopoverBody(fd_hold_popover_body)
                                ],
                                id = 'fd_hold_popover',
                                is_open = False,
                                target = 'fd_hold_popover_button',
                                placement = 'right'
                            )
                        ])
                    ], style = {
                        'width': '42mm',
                        'min-width': '27mm',
                        'height': '26mm',
                        'background-color': '#f2bb22',
                        'border-top-left-radius': '7px',
                        'border-bottom-left-radius': '7px',
                        'border': '2px black solid',
                        'display': 'flex', 'flex-direction': 'column', 'justify-content': 'center', 'align-items': 'center'
                    }),
                    html.Div(
                        html.Div([
                            html.Div(
                                children = fd_hold_display,
                                style = {
                                    'font-family': 'Microsoft JhengHei',
                                    'font-weight': 'bold',
                                    'font-size': '16px',
                                    'color': 'black',
                                    'width': '80mm',
                                    'height': '10mm',
                                    'background-color': '#e3e8e5',
                                    'border-top-right-radius': '7px',
                                    'border-top': '2px black solid',
                                    'border-right': '2px black solid',
                                    'display': 'flex', 'justify-content': 'center', 'align-items': 'center'
                                }
                            ),
                            html.Div(
                                dcc.Graph(
                                    figure = {
                                        'data': [
                                            go.Bar(
                                                x = his_count_x_axis,
                                                y = his_hold_count,
                                                marker = {'color': his_hold_count, 'colorscale': 'RdYlGn'}
                                            )
                                        ],
                                        'layout': go.Layout(
                                            dragmode =  'pan',
                                            showlegend = False,
                                            xaxis_rangeslider_visible = False,
                                            font = {'family': 'Microsoft JhengHei'},
                                            margin = {'t': 3, 'b': 3, 'l': 5, 'r': 5},
                                            xaxis = {
                                                'domain': [0.07, 0.93],
                                                'tickvals': his_count_x_axis,
                                                'ticktext': his_count_x_date,
                                                'fixedrange': True,
                                                'mirror': True
                                            },
                                            yaxis = {'fixedrange': True, 'side': 'right'},
                                            hovermode = 'closest'
                                        )
                                    },
                                    config = {'modeBarButtonsToRemove': ['zoom2d', 'toImage', 'select2d', 'lasso2d', 'autoScale2d', 'toggleSpikelines', 'hoverCompareCartesian', 'hoverClosestCartesian']},
                                    style = {'width': '70mm', 'height': '14mm'}
                                ),
                                style = {
                                    'font-family': 'Microsoft JhengHei',
                                    'color': 'black',
                                    'width': '80mm',
                                    'height': '16mm',
                                    'background-color': 'white',
                                    'border-bottom-right-radius': '7px',
                                    'border-top': '2px black solid',
                                    'border-right': '2px black solid',
                                    'border-bottom': '2px black solid',
                                    'display': 'flex', 'justify-content': 'center', 'align-items': 'center'
                                }
                            )
                        ])
                    )
                ], style = {'display': 'flex', 'justify-content': 'flex-start', 'height': '26mm', 'margin-top': '5%'})
            ], width = 3.5),

            dbc.Col([
                html.Div(
                    children = '※ SPY 技術分析 ※',
                    style = {'font-family': 'Microsoft JhengHei', 'font-weight': 'bold', 'font-size': '19px', 'display': 'flex', 'justify-content': 'center', 'align-items': 'center'}
                ),
                html.Div(
                    dcc.Graph(
                        figure = {
                            'data': [
                                # K 線
                                go.Candlestick(
                                    x = spy_df.date,
                                    open = list(spy_df.open),
                                    high = list(spy_df.high), 
                                    low = list(spy_df.low),
                                    close = list(spy_df.close),
                                    increasing_line_color = 'black',
                                    increasing_fillcolor = '#32EA32',
                                    decreasing_line_color = 'black',
                                    decreasing_fillcolor = '#FE3232',
                                    line_width = 0.5,
                                    yaxis = 'y',
                                    name = 'K線'
                                ),
                                # 月 ma
                                go.Scatter(
                                    x = spy_df.date,
                                    y = list(spy_df.ma_20),
                                    line_width = 1,
                                    yaxis = 'y',
                                    name = '月線 MA'
                                ),
                                # 季 ma
                                go.Scatter(
                                    x = spy_df.date,
                                    y = list(spy_df.ma_60),
                                    line_width = 1,
                                    yaxis = 'y',
                                    name = '季線 MA'
                                ),
                                # 半年 ma
                                go.Scatter(
                                    x = spy_df.date,
                                    y = list(spy_df.ma_120),
                                    line_width = 1,
                                    yaxis = 'y',
                                    name = '半年線 MA'
                                ),
                                # 年 ma
                                go.Scatter(
                                    x = spy_df.date,
                                    y = list(spy_df.ma_240),
                                    line_width = 1,
                                    yaxis = 'y',
                                    name = '年線 MA'
                                ),
                                # BBANDS 上緣
                                go.Scatter(
                                    x = spy_df.date,
                                    y = list(spy_df.bbands_upper),
                                    line_width = 2,
                                    yaxis = 'y',
                                    name = 'BBANDS 正二標準差'
                                ),
                                # BBANDS 下緣
                                go.Scatter(
                                    x = spy_df.date,
                                    y = list(spy_df.bbands_lower),
                                    line_width = 2,
                                    yaxis = 'y',
                                    name = 'BBANDS 負二標準差'
                                ),
                                # 成交量
                                go.Bar(
                                    x = spy_df.date,
                                    y = list(spy_df.volume),
                                    yaxis = 'y2',
                                    marker = {'color': spy_df.v_bar_color},
                                    name = '成交量'
                                ),
                                # MACD
                                go.Bar(
                                    x = spy_df.date,
                                    y = list(spy_df['hist']),
                                    yaxis = 'y3',
                                    marker = {'color': spy_df.hist_bar_color},
                                    name = 'MACD 柱線'
                                ),
                                go.Scatter(
                                    x = spy_df.date,
                                    y = list(spy_df['macd']),
                                    line_width = 1,
                                    yaxis = 'y3',
                                    name = 'MACD DIF'
                                ),
                                go.Scatter(
                                    x = spy_df.date,
                                    y = list(spy_df['signal']),
                                    line_width = 1,
                                    yaxis = 'y3',
                                    name = 'MACD'
                                )
                            ],

                            'layout': go.Layout(
                                dragmode =  'pan',
                                xaxis_rangeslider_visible = False,
                                xaxis_rangebreaks = [dict(values = spy_breaks)],
                                showlegend = True,
                                font = {'family': 'Microsoft JhengHei'},
                                margin = {'t': 3, 'b': 3, 'l': 2, 'r': 2},
                                xaxis = {'domain': [0.03, 0.97]},
                                yaxis = {'domain': [0.4, 0.98], 'side': 'right'},
                                yaxis2 = {'domain': [0.25, 0.4], 'side': 'right'},
                                yaxis3 = {'domain': [0.02, 0.25], 'side': 'right'},
                                legend = {'x': 1.02, 'y': 0.95}
                            )
                        },
                        config = {'modeBarButtonsToRemove': ['toImage', 'select2d', 'lasso2d', 'autoScale2d', 'toggleSpikelines'], 'scrollZoom': True},
                        style = {'height': '100mm'}
                    )
                )
            ])
        ], style = {'margin-left': '3%', 'margin-right': '3%'}),
        # Stock Search Row
        dbc.Row(
            dbc.Col(
                html.Div([
                    html.Div(
                        children = '※ 個股代號查詢：',
                        style = {'font-family': 'Microsoft JhengHei', 'font-weight': 'bold', 'font-size': '19px'}
                    ),
                    html.Div(
                        dcc.Dropdown(
                            id = 'home_stk_check_dropdown',
                            options = home_stk_check_dropdown_dict,
                            value = home_stk_check_dropdown_dict[random.choice(range(0,len(tickers_stk)))]['value'],
                            multi = False,
                            style = {'font-size': '13px', 'text-align': 'center'}
                        ), style = {'width': '13%'}
                    ),
                    html.Div(
                        dcc.Loading(id = 'home_stk_check_loading', color = '#0E446E', fullscreen = False),
                        style = {'margin-left': '5%'}
                    )
                ], style = {'display': 'flex', 'justify-content': 'start', 'align-items': 'center'})
            ),
            style = {'margin-left': '2%', 'margin-right': '2%'}
        ),
        # Stock Graph Plot + Stock Info Boxes
        dbc.Row([
            dbc.Col([
                html.Div(
                    html.Div([
                        html.Div(children = 'Spark A.I. 近半年持有期間', style = {'font-family': 'Microsoft JhengHei', 'font-weight': 'bold', 'font-size': '14px', 'margin-top': '2%', 'text-align': 'center'}),
                        html.Div(id = 'home_stock_check_chart'),
                    ]),
                    style = {'border': '1px #5b616e solid', 'border-radius': '23px', 'margin-top': '2%'}
                )
            ], width = 5),
            dbc.Col([
                # Company Name Row
                dbc.Row(
                    dbc.Col(
                        html.Div([
                            html.Div(
                                id = 'home_stk_check_basic_info_company_name',
                                style = {
                                    'font-family': 'Microsoft JhengHei', 'font-size': '26px', 'font-weight': 'bold', 'color': 'black'
                                }
                            ),
                            html.Div([
                                html.Div(
                                    dbc.Button(
                                        children = '公司簡介',
                                        id = 'home_stk_company_description_collapse_button',
                                        color = 'dark',
                                        style = {
                                            'font-family': 'Microsoft JhengHei', 'font-size': '14px'
                                        }
                                    ),
                                    style = {'width': '100px'}
                                ),
                                html.Div(
                                    dbc.Button(
                                        children = '最新消息',
                                        id = 'home_stk_company_news_collapse_button',
                                        color = 'dark',
                                        style = {
                                            'font-family': 'Microsoft JhengHei', 'font-size': '14px',
                                            'margin-left': '2%'
                                        }
                                    ),
                                    style = {'width': '100px'}
                                ),
                                html.Div(
                                    dbc.Button(
                                        children = 'Bloomberg 新聞',
                                        id = 'home_stk_company_bloomberg_news_collapse_button',
                                        color = 'dark',
                                        style = {
                                            'font-family': 'Microsoft JhengHei', 'font-size': '14px',
                                            'margin-left': '2%'
                                        }
                                    ),
                                    style = {'width': '145px'}
                                )
                            ], style = {'display': 'flex'})
                        ], style = {'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center'})
                    )
                ),
                # Hidden Collapse Row
                dbc.Row(
                    dbc.Col(
                        dbc.Collapse(
                            dbc.Card(
                                dbc.CardBody(
                                    id = 'home_stk_company_description_collapse_content',
                                    style = {'font-family': 'Microsoft JhengHei'}
                                ),
                                style = {
                                    'margin-top': '1%', 'margin-left': '2%', 'margin-right': '2%', 'margin-bottom': '1%', 'background-color': '#ced4e0'
                                }
                            ),
                            id = 'home_stk_company_description_collapse'
                        )
                    )
                ),
                dbc.Row(
                    dbc.Col(
                        dbc.Collapse(
                            dbc.Card(
                                dbc.CardBody(
                                    id = 'home_stk_company_news_collapse_content',
                                    style = {'font-family': 'Microsoft JhengHei'}
                                ),
                                style = {
                                    'margin-top': '1%', 'margin-left': '2%', 'margin-right': '2%', 'margin-bottom': '1%', 'background-color': '#f5f5f5'
                                }
                            ),
                            id = 'home_stk_company_news_collapse'
                        )
                    )
                ),
                dbc.Row(
                    dbc.Col(
                        dbc.Collapse(
                            dbc.Card(
                                dbc.CardBody(
                                    id = 'home_stk_company_bloomberg_news_collapse_content',
                                    style = {'font-family': 'Microsoft JhengHei'}
                                ),
                                style = {
                                    'margin-top': '1%', 'margin-left': '2%', 'margin-right': '2%', 'margin-bottom': '1%', 'background-color': '#f5f5f5'
                                }
                            ),
                            id = 'home_stk_company_bloomberg_news_collapse'
                        )
                    )
                ),
                dbc.Row(id = 'bloomberg_news_count', style = {'display': 'none'}),
                dbc.Row(id = 'bloomberg_news_0', style = {'display': 'none'}),
                dbc.Row(id = 'bloomberg_news_1', style = {'display': 'none'}),
                dbc.Row(id = 'bloomberg_news_2', style = {'display': 'none'}),
                dbc.Row(id = 'bloomberg_news_3', style = {'display': 'none'}),
                dbc.Row(id = 'bloomberg_news_4', style = {'display': 'none'}),
                # Spark A.I. Info Boxes Row
                html.Div([
                    # row 1
                    dbc.Row([
                        # info box 1-1: 
                        dbc.Col(
                            [
                                html.Div(
                                    id = 'home_spark_infos_price_range_plot',
                                    style = {
                                        'font-family': 'Microsoft JhengHei', 'font-size': '20px', 'font-weight': 'bold',
                                        'text-align': 'center', 'margin-top': '3%', 'margin-bottom': '1%', 'color': 'black'
                                    }
                                ),
                                html.Div(
                                    id = 'home_spark_infos_price_range_data',
                                    style = {
                                        'font-family': 'Microsoft JhengHei', 'font-size': '9px', 'font-weight': 'bold',
                                        'text-align': 'center', 'margin-bottom': '3%', 'color': 'black'
                                    }
                                ),
                                html.Div(
                                    children = '最新收盤價｜52 週股價區間',
                                    style = {
                                        'font-family': 'Microsoft JhengHei', 'font-size': '11px', 'font-weight': 'bold',
                                        'align-self': 'flex-end', 'margin-bottom': '2%', 'margin-right': '2px', 'color': 'black'
                                    }
                                )   
                            ],
                            style = {
                                'display': 'flex', 'flex-direction': 'column', 'justify-content': 'space-between', 'height': '30mm',
                                'border-radius': '7px', 'box-shadow': '2px 2px 2px grey', 'background-color': '#f5f5f5', 'margin-right': '2%'
                            }
                        ),
                        # info box 1-2: 
                        dbc.Col(
                            [
                                html.Div(
                                    id = 'home_spark_infos_volume_range_plot',
                                    style = {
                                        'font-family': 'Microsoft JhengHei', 'font-size': '20px', 'font-weight': 'bold',
                                        'text-align': 'center', 'margin-top': '3%', 'margin-bottom': '1%', 'color': 'black'
                                    }
                                ),
                                html.Div(
                                    id = 'home_spark_infos_volume_range_data',
                                    style = {
                                        'font-family': 'Microsoft JhengHei', 'font-size': '9px', 'font-weight': 'bold',
                                        'text-align': 'center', 'margin-bottom': '3%', 'color': 'black'
                                    }
                                ),
                                html.Div(
                                    children = '最新成交量｜近一季平均成交量',
                                    style = {
                                        'font-family': 'Microsoft JhengHei', 'font-size': '11px', 'font-weight': 'bold',
                                        'align-self': 'flex-end', 'margin-bottom': '2%', 'margin-right': '2px', 'color': 'black'
                                    }
                                )   
                            ],
                            style = {
                                'display': 'flex', 'flex-direction': 'column', 'justify-content': 'space-between', 'height': '30mm',
                                'border-radius': '7px', 'box-shadow': '2px 2px 2px grey', 'background-color': '#f5f5f5', 'margin-right': '2%'
                            }
                        ),
                        # info box 1-3: 
                        dbc.Col(
                            [
                                html.Div(
                                    id = 'home_spark_infos_eps_trend',
                                    style = {
                                        'font-family': 'Microsoft JhengHei', 'font-size': '20px', 'font-weight': 'bold',
                                        'text-align': 'center', 'margin': 'auto', 'color': 'black'
                                    }
                                ),
                                html.Div(
                                    children = '近 12 季 EPS',
                                    style = {
                                        'font-family': 'Microsoft JhengHei', 'font-size': '11px', 'font-weight': 'bold',
                                        'align-self': 'flex-end', 'margin-bottom': '2%', 'margin-right': '2px', 'color': 'black'
                                    }
                                )   
                            ],
                            style = {
                                'display': 'flex', 'flex-direction': 'column', 'justify-content': 'space-between', 'height': '30mm',
                                'border-radius': '7px', 'box-shadow': '2px 2px 2px grey', 'background-color': '#f5f5f5', 'margin-right': '2%'
                            }
                        ),
                        # info box 1-4: 
                        dbc.Col(
                            [
                                html.Div(
                                    id = 'home_spark_infos_earnings_date',
                                    style = {
                                        'font-family': 'Microsoft JhengHei', 'font-size': '20px', 'font-weight': 'bold',
                                        'text-align': 'center', 'margin': 'auto', 'color': 'black'
                                    }
                                ),
                                html.Div(
                                    children = '次營收發布日',
                                    style = {
                                        'font-family': 'Microsoft JhengHei', 'font-size': '11px', 'font-weight': 'bold',
                                        'align-self': 'flex-end', 'margin-bottom': '2%', 'margin-right': '2px', 'color': 'black'
                                    }
                                )   
                            ],
                            style = {
                                'display': 'flex', 'flex-direction': 'column', 'justify-content': 'space-between', 'height': '30mm',
                                'border-radius': '7px', 'box-shadow': '2px 2px 2px grey', 'background-color': '#f5f5f5'
                            }
                        )
                    ], style = {'margin-top': '1%', 'margin-left': '2%', 'margin-right': '2%', 'margin-bottom': '1%'}),
                ]),
                html.Div([
                    # row 2
                    dbc.Row([
                        # info box 2-1: 
                        dbc.Col(
                            [
                                html.Div(
                                    html.Div([
                                        html.Div(
                                            id = 'home_spark_infos_latest_prediction',
                                            style = {
                                                'font-family': 'Microsoft JhengHei', 'font-size': '20px', 'font-weight': 'bold',
                                                'text-align': 'center', 'color': 'black'
                                            }
                                        ),
                                        html.Div(
                                            id = 'latest_prediction_signal_ball_color',
                                            style = {'margin-left': '1%'}
                                        )
                                    ], style = {'display': 'flex', 'justify-content': 'center', 'align-items': 'center'}),
                                    style = {'margin-top': 'auto', 'margin-bottom': 'auto'}
                                ),
                                html.Div(
                                    children = 'Spark A.I. 最新預測',
                                    style = {
                                        'font-family': 'Microsoft JhengHei', 'font-size': '11px', 'font-weight': 'bold',
                                        'align-self': 'flex-end', 'margin-bottom': '2%', 'margin-right': '2px', 'color': 'black'
                                    }
                                )
                            ],
                            style = {
                                'display': 'flex', 'flex-direction': 'column', 'justify-content': 'space-between', 'height': '22mm',
                                'border-radius': '7px', 'box-shadow': '2px 2px 2px grey', 'background-color': '#f5f5f5', 'margin-right': '2%'
                            }
                        ),
                        # info box 2-2: 
                        dbc.Col(
                            [
                                html.Div(
                                    id = 'home_spark_infos_pred_start_date',
                                    style = {
                                        'font-family': 'Microsoft JhengHei', 'font-size': '20px', 'font-weight': 'bold',
                                        'text-align': 'center', 'margin': 'auto', 'color': 'black'
                                    }
                                ),
                                html.Div(
                                    children = '起始日',
                                    style = {
                                        'font-family': 'Microsoft JhengHei', 'font-size': '11px', 'font-weight': 'bold',
                                        'align-self': 'flex-end', 'margin-bottom': '2%', 'margin-right': '2px', 'color': 'black'
                                    }
                                )   
                            ],
                            style = {
                                'display': 'flex', 'flex-direction': 'column', 'justify-content': 'space-between', 'height': '22mm',
                                'border-radius': '7px', 'box-shadow': '2px 2px 2px grey', 'background-color': '#f5f5f5', 'margin-right': '2%'
                            }
                        ),
                        # info box 2-3: 
                        dbc.Col(
                            [
                                html.Div(
                                    id = 'home_spark_infos_pred_period',
                                    style = {
                                        'font-family': 'Microsoft JhengHei', 'font-size': '20px', 'font-weight': 'bold',
                                        'text-align': 'center', 'margin': 'auto', 'color': 'black'
                                    }
                                ),
                                html.Div(
                                    children = '持續期間',
                                    style = {
                                        'font-family': 'Microsoft JhengHei', 'font-size': '11px', 'font-weight': 'bold',
                                        'align-self': 'flex-end', 'margin-bottom': '2%', 'margin-right': '2px', 'color': 'black'
                                    }
                                )   
                            ],
                            style = {
                                'display': 'flex', 'flex-direction': 'column', 'justify-content': 'space-between', 'height': '22mm',
                                'border-radius': '7px', 'box-shadow': '2px 2px 2px grey', 'background-color': '#f5f5f5', 'margin-right': '2%'
                            }
                        ),
                        # info box 2-4: 
                        dbc.Col(
                            [
                                html.Div(
                                    id = 'home_spark_infos_period_acc_ret',
                                    style = {
                                        'font-family': 'Microsoft JhengHei', 'font-size': '20px', 'font-weight': 'bold',
                                        'text-align': 'center', 'margin': 'auto', 'color': 'black'
                                    }
                                ),
                                html.Div(
                                    children = '期間累計報酬率',
                                    style = {
                                        'font-family': 'Microsoft JhengHei', 'font-size': '11px', 'font-weight': 'bold',
                                        'align-self': 'flex-end', 'margin-bottom': '2%', 'margin-right': '2px', 'color': 'black'
                                    }
                                )   
                            ],
                            style = {
                                'display': 'flex', 'flex-direction': 'column', 'justify-content': 'space-between', 'height': '22mm',
                                'border-radius': '7px', 'box-shadow': '2px 2px 2px grey', 'background-color': '#f5f5f5'
                            }
                        )
                    ], style = {'margin-left': '2%', 'margin-right': '2%', 'margin-bottom': '1%'}),
                    # row 3
                    dbc.Row([
                        # info box 3-1: 
                        dbc.Col(
                            [   
                                html.Div(
                                    id = 'home_spark_infos_n_years_eq_plot',
                                    style = {'margin-top': '2%', 'margin-bottom': '1%'}
                                ),
                                html.Div(
                                    id = 'home_spark_infos_n_years_eq_performace',
                                    style = {
                                        'font-family': 'Microsoft JhengHei', 'font-size': '18px', 'font-weight': 'bold',
                                        'text-align': 'center', 'margin': 'auto', 'color': 'black'
                                    }
                                ),
                                html.Div(
                                    html.Div([
                                        html.Div(
                                            children = '過去',
                                            style = {'font-family': 'Microsoft JhengHei', 'font-size': '13px', 'font-weight': 'bold', 'margin-right': '3px'}
                                        ),
                                        html.Div(
                                            dcc.Dropdown(
                                                id = 'home_spark_infos_eq_plot_choose_n',
                                                options = [{'label': '1', 'value': '1'}, {'label': '3', 'value': '3'}, {'label': '5', 'value': '5'}, {'label': '全期', 'value': '全期'}],
                                                value = '3',
                                                multi = False,
                                                style = {'font-family': 'Microsoft JhengHei', 'font-size': '10px'}
                                            )
                                        ),
                                        html.Div(
                                            children = '年 Spark A.I. 累計績效',
                                            style = {'font-family': 'Microsoft JhengHei', 'font-size': '13px', 'font-weight': 'bold', 'margin-left': '3px'}
                                        )
                                    ], style = {'display': 'flex', 'align-items': 'center'}),
                                    style = {'align-self': 'flex-end', 'margin-bottom': '2%', 'margin-right': '2px', 'color': 'black'}
                                ) 
                            ],
                            style = {
                                'display': 'flex', 'flex-direction': 'column', 'justify-content': 'space-between', 'height': '75mm',
                                'border-radius': '7px', 'box-shadow': '2px 2px 2px grey', 'background-color': '#f5f5f5', 'margin-right': '2%'
                            }
                        ),
                        # info box 3-2: 
                        dbc.Col(
                            [   
                                html.Div(
                                    id = 'home_spark_infos_year_performance_table'
                                ),
                                html.Div(
                                    html.Div(
                                        children = '各年度績效數據【近五年】',
                                        style = {
                                            'font-family': 'Microsoft JhengHei', 'font-size': '13px', 'font-weight': 'bold',
                                            'align-self': 'flex-end', 'margin-bottom': '2%', 'margin-right': '2px', 'color': 'black'
                                        }
                                    ),
                                    style = {'align-self': 'flex-end', 'margin-bottom': '2%', 'margin-right': '2px', 'color': 'black'}
                                )
                            ],
                            style = {
                                'display': 'flex', 'flex-direction': 'column', 'justify-content': 'space-between', 'height': '75mm',
                                'border-radius': '7px', 'box-shadow': '2px 2px 2px grey', 'background-color': '#f5f5f5'
                            }
                        )
                    ], style = {'display': 'flex', 'justify-content': 'flex-start', 'align-items': 'center', 'margin-left': '2%', 'margin-right': '2%', 'margin-bottom': '1%'})
                ]),
            ], width = 7)
        ], style = {'margin-left': '3%', 'margin-right': '3%'})
    ], fluid = True)
    return layout
    
def call_layout_subject_analysis():
    layout = dbc.Container([
        html.Div('功能更新中')
    ])
    return layout
    
def call_layout_portfolio():
    layout = dbc.Container([
        html.Div('功能更新中')
    ])
    return layout

def call_layout_market_risk():
    layout = dbc.Container([
        html.Div('功能更新中')
    ])
    return layout

def call_layout_other_links():
    layout = dbc.Container([
        html.A(
            children = '負二標準差策略',
            href = 'https://value2std.herokuapp.com/today_signal'
        )
    ])
    return layout

#____________________________________________
#|____APP____________________________________
app = dash.Dash(
    __name__,
    external_stylesheets = [dbc.themes.BOOTSTRAP],
    meta_tags = [{'name': 'viewport', 'content': 'width = device-width, initial-scale = 1'}]
)

# create RQ queue
q = Queue(connection=conn)
job = None
# all layouts
layout_home = call_layout_home()
layout_subject_analysis = call_layout_subject_analysis()
layout_portfolio = call_layout_portfolio()
layout_market_risk = call_layout_market_risk()
layout_other_links = call_layout_other_links()
# call data from postgres database
def call_db(table, PGUSER=PGUSER, PGPASSWORD=PGPASSWORD, PGDATABASE=PGDATABASE, PGHOST=PGHOST, PGPORT=PGPORT, method='all', tail_count=100):
    engine = sqlalchemy.create_engine('postgresql://'+PGUSER+':'+PGPASSWORD+'@'+PGHOST+':'+PGPORT+'/'+PGDATABASE)
    con = engine.connect()
    if method == 'all':
        df = pd.read_sql_table(table, con = engine, schema = 'spark')
    else:
        df = pd.read_sql_table(table, con = engine, schema = 'spark').tail(tail_count)
    con.close()
    return df

app.title = 'Rising - Spark A.I.'
auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)
app.config.suppress_callback_exceptions = True
app.layout = html.Div([
    dcc.Interval(id = 'update_timer', interval=1000),
    html.Div(children=None, id = 'task_state'),
    dcc.Location(id = 'url', refresh = False),
    call_layout_header(),
    html.Div(style = {'background-color': 'black', 'margin-top': '1%', 'height': '7px', 'border-radius': '6px'}),
    html.Br(),
    dcc.Loading(id = 'page_switch_loading', color = '#0E446E', fullscreen = False),
    html.Div(id = 'page_layout'),
    html.Br(),
    html.Div(style = {'background-color': 'black', 'margin-top': '1%', 'height': '4px', 'border-radius': '6px'}),
    html.Br()
])
server = app.server

#____________________________________________
#|____CALLBACKS____________________________________
# href page layouts
@app.callback(
    Output('task_state', 'children'),
    [Input('url', 'pathname')]
)
def display_page_layout(pathname):
    # current_style = {'background-color': 'black', 'margin-right': '12px', 'font-weight': 'bold', 'color': 'white', 'font-family': 'Microsoft JhengHei', 'font-size': '18px', 'border-radius': '28px'}
    # origin_style = {'background-color': 'white', 'margin-right': '12px', 'font-weight': 'bold', 'color': 'black', 'font-family': 'Microsoft JhengHei', 'font-size': '18px', 'border-radius': '28px'}
    # if pathname == '/subject_analysis':
    #     link_subject_analysis_style = current_style
    #     link_home_style, link_portfolio_style, link_market_risk_style, link_other_links_style = origin_style, origin_style, origin_style, origin_style
    #     layout = layout_subject_analysis
    # elif pathname == '/portfolio':
    #     link_portfolio_style = current_style
    #     link_home_style, link_subject_analysis_style, link_market_risk_style, link_other_links_style = origin_style, origin_style, origin_style, origin_style
    #     layout = layout_portfolio
    # elif pathname == '/market_risk':
    #     link_market_risk_style = current_style
    #     link_home_style, link_portfolio_style, link_subject_analysis_style, link_other_links_style = origin_style, origin_style, origin_style, origin_style
    #     layout = layout_market_risk
    # elif pathname == '/other_links':
    #     link_other_links_style = current_style
    #     link_home_style, link_portfolio_style, link_market_risk_style, link_subject_analysis_style = origin_style, origin_style, origin_style, origin_style
    #     layout = layout_other_links
    # else:
    #     link_home_style = current_style
    #     link_subject_analysis_style, link_portfolio_style, link_market_risk_style, link_other_links_style = origin_style, origin_style, origin_style, origin_style
    #     layout = layout_home
    # return link_home_style, link_subject_analysis_style, link_portfolio_style, link_market_risk_style, link_other_links_style, layout, None

    job_id = q.enqueue(layout_router, pathname).id

    return job_id

@app.callback(
    [Output('link_home', 'style'),
    Output('link_subject_analysis', 'style'),
    Output('link_portfolio', 'style'),
    Output('link_market_risk', 'style'),
    Output('link_other_links', 'style'),
    Output('page_layout', 'children'),
    Output('page_switch_loading', 'children')],
    [Input('update_timer', 'n_intervals')],
    [State('task_state', 'children')])
def layout_subscriber(update_timer, task_state):
    if task_state is not None:
        job = Job.fetch(task_state)
        if job.get_status() == 'finished':
            print("ok", job.result)
            return job.result
        else:
            return [None, None, None, None, None, None, None]
    else:
        return [None, None, None, None, None, None, None]
# homepage future predictions popover button → future predictions popover
@app.callback(
    Output('fd_close_popover', 'is_open'),
    [Input('fd_close_popover_button', 'n_clicks')],
    [State('fd_close_popover', 'is_open')]
)
def fd_close_toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output('fd_open_popover', 'is_open'),
    [Input('fd_open_popover_button', 'n_clicks')],
    [State('fd_open_popover', 'is_open')]
)
def fd_close_toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output('fd_hold_popover', 'is_open'),
    [Input('fd_hold_popover_button', 'n_clicks')],
    [State('fd_hold_popover', 'is_open')]
)
def fd_close_toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open

# homepage stock check dropdown → stock check chart and info boxes
@app.callback(
    [Output('home_stock_check_chart', 'children'),
    Output('home_stk_check_basic_info_company_name', 'children'),
    Output('home_stk_company_description_collapse_content', 'children'),
    Output('home_stk_company_news_collapse_content', 'children'),
    Output('home_stk_company_bloomberg_news_collapse_content', 'children'),
    Output('bloomberg_news_count', 'children'),
    Output('bloomberg_news_0', 'children'),
    Output('bloomberg_news_1', 'children'),
    Output('bloomberg_news_2', 'children'),
    Output('bloomberg_news_3', 'children'),
    Output('bloomberg_news_4', 'children'),
    Output('home_spark_infos_price_range_plot', 'children'),
    Output('home_spark_infos_price_range_data', 'children'),
    Output('home_spark_infos_volume_range_plot', 'children'),
    Output('home_spark_infos_volume_range_data', 'children'),
    Output('home_spark_infos_eps_trend', 'children'),
    Output('home_spark_infos_earnings_date', 'children'),
    Output('home_spark_infos_latest_prediction', 'children'),
    Output('latest_prediction_signal_ball_color', 'children'),
    Output('home_spark_infos_pred_start_date', 'children'),
    Output('home_spark_infos_pred_period', 'children'),
    Output('home_spark_infos_period_acc_ret', 'children'),
    Output('home_spark_infos_n_years_eq_plot', 'children'),
    Output('home_spark_infos_n_years_eq_performace', 'children'),
    Output('home_spark_infos_year_performance_table', 'children'),
    Output('home_stk_check_loading', 'children')],
    [Input('home_stk_check_dropdown', 'value'),
    Input('home_spark_infos_eq_plot_choose_n', 'value')]
)
def home_stock_check(ticker_value, eq_n):
    def locate_date_breaks(df):
        live_dates = list(map(lambda x: dt.datetime.strptime(x, '%Y-%m-%d'), list(df['date'])))
        full_dates = pd.date_range(start = live_dates[0], end = live_dates[-1])
        breaks = list(map(lambda x: dt.datetime.strftime(x, '%Y-%m-%d'), [i for i in full_dates if i not in live_dates]))
        return breaks
    def round_str_percent(data, method = 'per'):
        if method == 'int':
            try:
                returned_data = str(int(data))
            except:
                returned_data = 'N/A'
        elif method == 'round':
            try:
                returned_data = str(round(data, 2))
            except:
                returned_data = 'N/A'
        else:
            try:
                returned_data = str(round(data*100,2))+'%'
            except:
                returned_data = 'N/A'
        return returned_data
    # call data from database
    home_all_tickers_info = call_db('rising_spark_home_all_tickers_info')
    df = call_db('rising_spark_home_stock_check_'+ticker_value.lower().replace('.','_'))
    yr_performance_df = call_db('rising_spark_year_performance_analysis')
    # latest english news
    try:
        news_en = call_db('rising_spark_news_en_'+ticker_value.lower().replace('.','_'))
        news_en = news_en.drop_duplicates()
        news_en = news_en.sort_values('publication_date', ascending = False).reset_index().drop('index', axis = 1)
        news_en = news_en.iloc[:30,:]
        news_en['publication_date'] = list(map(lambda x: x.split('+00:')[0], list(news_en['publication_date'])))
        news_show_df = news_en[['publication_date', 'title']]
        news_show_df.columns = ['發布日期時間', '新聞標題']
        if len(news_en) == 0:
            news_en = '無相關新聞'
    except:
        news_en = '無相關新聞'
    # latest bloomberg news
    try:
        news_cn = call_db('rising_spark_news_cn_'+ticker_value.lower().replace('.','_'))
        news_cn = news_cn.drop_duplicates()
        news_cn = news_cn.sort_values('publication_date', ascending = False).reset_index().drop('index', axis = 1)
        news_cn = news_cn.iloc[:5,:]
        news_cn['publication_date'] = list(map(lambda x: x.split('+00:')[0], list(news_cn['publication_date'])))
        bloomberg_news_df = news_cn[['publication_date', 'title_cn', 'summary_cn']]
        bbg_news_count = len(news_cn)
        if len(news_cn) == 0:
            news_cn = '無 Bloomberg 報導'
    except:
        bbg_news_count = 0
        news_cn = '無 Bloomberg 報導'
    # info boxes data computation
    temp_info = home_all_tickers_info[home_all_tickers_info.ticker == ticker_value].copy()
    company_ticker_badge = '【'+ticker_value+'】'
    company_name = list(temp_info['company_name'])[0] + company_ticker_badge
    company_description = list(temp_info['long_description_cn'])[0]
    spark_latest_pred = list(temp_info.latest_act)[0]
    spark_pred_start = list(temp_info.act_start_date)[0]
    spark_pred_period = list(temp_info.act_period)[0]
    spark_pred_period_ret = list(temp_info.act_period_acc_ret)[0]
    if spark_latest_pred == '開盤賣出':
        signal_ball_color = '#f23b2e'
    elif spark_latest_pred == '開盤買進':
        signal_ball_color = '#3dc461'
    elif spark_latest_pred == '繼續持有':
        signal_ball_color = '#f2bb22'
    else:
        signal_ball_color = '#57595e'
    # price_range_df data computation
    price_range_df = df.iloc[-260:,:].copy()
    price_range_df.index = price_range_df.date
    price_range_df['latest_close'] = price_range_df.close[-1]
    price_range_print = str(price_range_df.close[-1]) + ' ｜（' + str(price_range_df.low.min()) + ' - ' + str(price_range_df.high.max()) + '）' 
    # volume_range_df data computation
    volume_range_df = df.iloc[-63:,:].copy()
    volume_range_df.index = volume_range_df.date
    volume_range_df['avg_volume'] = volume_range_df.volume.mean()
    volume_range_print = str(round(volume_range_df.volume[-1]/1000000,2)) + 'M ｜ ' + str(round(volume_range_df.avg_volume[-1]/1000000,2)) + 'M'
    # eq_plot_df data computation
    eq_plot_df = df.copy()
    eq_plot_df.index = eq_plot_df.date
    if eq_n != '全期':
        eq_plot_df = eq_plot_df.iloc[-int(eq_n)*252:,:]
    eq_plot_list = list(eq_plot_df.spark_eq /eq_plot_df.spark_eq[0] * eq_plot_df.close[0])
    spark_eq_ret = str(round((eq_plot_df.spark_eq[-1] / eq_plot_df.spark_eq[0] - 1)*100,2))+'%'
    bench_eq_ret = str(round((eq_plot_df.bench_eq[-1] / eq_plot_df.bench_eq[0] - 1)*100,2))+'%'
    eq_performace_print = 'Spark A.I.： ' + spark_eq_ret + ' ｜ 標的： ' + bench_eq_ret
    plot_df = df.iloc[-126:,:].copy()
    # yr_performance_df data computation
    yr_performance_df.index = yr_performance_df.stk
    required_data = yr_performance_df.loc[ticker_value]
    appeared_years = list(range(dt.datetime.now().year-4,dt.datetime.now().year+1))
    show_df = pd.DataFrame(index = ['股價走勢', 'Spark 績效', '股價最大回落', 'Spark 最大回落', 'Spark 交易次數', 'Spark 交易勝率', 'Spark 獲利因子'], columns = ['指標']+appeared_years)
    for yr in show_df.columns:
        if yr == '指標':
            continue
        show_df[yr] = [round_str_percent(required_data[str(yr)+'_EAR_bench']), round_str_percent(required_data[str(yr)+'_EAR_strategy']), round_str_percent(required_data[str(yr)+'_MDD_bench']), round_str_percent(required_data[str(yr)+'_MDD_strategy']), round_str_percent(required_data[str(yr)+'_tradeCount'], method = 'int'), round_str_percent(required_data[str(yr)+'_winRate']), round_str_percent(required_data[str(yr)+'_profitFactor'], method = 'round')]
    show_df['指標'] = show_df.index
    show_df.columns = ['指標']+list(map(lambda x: str(x), appeared_years))
    # info box - news header
    if type(news_en) == str:
        news_table = html.Div(news_en)
    else:
        news_table = html.Div(
            dash_table.DataTable(
                columns = [{'name': i, 'id': i} for i in news_show_df.columns],
                data = news_show_df.to_dict('records'),
                style_table = {
                    'height': '300px',
                    'overflowY': 'auto',
                    'overflowX': 'hidden',
                },
                style_header = {
                    'backgroundColor': '#54647d',
                    'color': 'white',
                    'fontSize': '12px',
                    'fontWeight': 'bold',
                    'fontFamily': 'Microsoft JhengHei',
                    'textAlign': 'center',
                },
                style_data = {
                    'fontSize': '10px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                },
                style_cell_conditional = [
                    {
                        'if': {
                            'column_id': '發布日期時間'
                        },
                        'fontFamily': 'Microsoft JhengHei',
                        'textAlign': 'center',
                        'minWidth': '145px', 'width': '145px', 'maxWidth': '145px',
                    },
                    {
                        'if': {
                            'column_id': '新聞標題'
                        },
                        'fontFamily': 'Microsoft JhengHei',
                        'textAlign': 'left',
                        'maxWidth': '380px',
                    }
                ],
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#edf2fc'
                    }
                ],
            ),
            style = {'margin-top': '1%', 'margin-left': '1%', 'margin-right': '1%', 'margin-bottom': '1%'}
        )
    # info box - bloomberg news
    def make_bloomberg_news_button(placement):
        bloomberg_buttons = dbc.Button(
            children = '最近 '+str(placement+1)+' 篇報導',
            id = 'bloomberg_news_button_'+str(placement),
            size = 'sm',
            style = {'font-family': 'Microsoft JhengHei', 'font-size': '10px', 'margin-right': '1%'}
        )
        return bloomberg_buttons
    def make_fake_bloomberg_news_button(placement):
        bloomberg_buttons = dbc.Button(
            children = '最近 '+str(placement+1)+' 篇報導',
            id = 'bloomberg_news_button_'+str(placement),
            size = 'sm',
            style = {'display': 'none'}
        )
        return bloomberg_buttons
    def make_bloomberg_news_content(placement):
        bloomberg_news = html.Div([
            html.Div([
                html.Div(
                    children = '報導標題：',
                    style = {'font-family': 'Microsoft JhengHei', 'font-size': '12px', 'font-weight': 'bold'}
                ),
                html.Div(
                    children = bloomberg_news_df.title_cn[placement],
                    style = {'font-family': 'Microsoft JhengHei', 'font-size': '15px', 'font-weight': 'bold'}
                )
            ], style = {'display': 'flex', 'align-items': 'center', 'margin-bottom': '3px'}),

            html.Div([
                html.Div(
                    children = '發布日期時間：',
                    style = {'font-family': 'Microsoft JhengHei', 'font-size': '12px', 'font-weight': 'bold'}
                ),
                html.Div(
                    children = bloomberg_news_df.publication_date[placement],
                    style = {'font-family': 'Microsoft JhengHei', 'font-size': '14px'}
                )
            ], style = {'display': 'flex', 'align-items': 'center', 'margin-bottom': '3px'}),
            
            html.Div(
                children = '報導內容：',
                style = {'font-family': 'Microsoft JhengHei', 'font-size': '12px', 'font-weight': 'bold', 'margin-bottom': '1px'}
            ),
            html.Div(
                children = bloomberg_news_df.summary_cn[placement],
                style = {'font-family': 'Microsoft JhengHei', 'font-size': '14px', 'margin-bottom': '2px'}
            ),
        ], style = {'margin-top': '1%', 'margin-left': '1%', 'margin-right': '1%'})
        return bloomberg_news
    if type(news_cn) == str:
        bloomberg_news = html.Div(news_cn)
    else:
        bloomberg_news = html.Div([
            html.Div(
                children = [make_bloomberg_news_button(i) for i in range(bbg_news_count)],
                style = {'display': 'flex', 'align-items': 'center'}
            ),
            html.Div(
                children = [make_fake_bloomberg_news_button(i) for i in range(bbg_news_count,5)],
                style = {'display': 'flex', 'align-items': 'center'}
            ),
            html.Div(id = 'bloomberg_news_display_area', style = {'margin-top': '1%'})
        ])
    bbg_news_content_0, bbg_news_content_1, bbg_news_content_2, bbg_news_content_3, bbg_news_content_4 = html.Div(), html.Div(), html.Div(), html.Div(), html.Div()
    if bbg_news_count > 4:
        bbg_news_content_4 = make_bloomberg_news_content(4)
    if bbg_news_count > 3:
        bbg_news_content_3 = make_bloomberg_news_content(3)
    if bbg_news_count > 2:
        bbg_news_content_2 = make_bloomberg_news_content(2)
    if bbg_news_count > 1:
        bbg_news_content_1 = make_bloomberg_news_content(1)
    if bbg_news_count > 0:
        bbg_news_content_0 = make_bloomberg_news_content(0)
    # stock T.A. chart layout
    stock_check_chart_layout = html.Div(
        dcc.Graph(
            figure = {
                'data': [
                    # K 線
                    go.Candlestick(
                        x = plot_df.date,
                        open = list(plot_df.open),
                        high = list(plot_df.high), 
                        low = list(plot_df.low),
                        close = list(plot_df.close),
                        increasing_line_color = 'black',
                        increasing_fillcolor = '#32EA32',
                        decreasing_line_color = 'black',
                        decreasing_fillcolor = '#FE3232',
                        line_width = 0.5,
                        yaxis = 'y',
                        name = 'K線'
                    ),
                    # 季 ma
                    go.Scatter(
                        x = plot_df.date,
                        y = list(plot_df.ma_60),
                        line_width = 1,
                        yaxis = 'y',
                        name = '季線 MA'
                    ),
                    # 年 ma
                    go.Scatter(
                        x = plot_df.date,
                        y = list(plot_df.ma_120),
                        line_width = 1,
                        yaxis = 'y',
                        name = '年線 MA'
                    ),
                    # 成交量
                    go.Bar(
                        x = plot_df.date,
                        y = list(plot_df.volume),
                        yaxis = 'y2',
                        marker = {'color': plot_df.v_bar_color},
                        name = '成交量'
                    ),
                    # SPARK 買進並持有期間
                    go.Bar(
                        x = plot_df.date,
                        y = list(plot_df.decision_bar),
                        yaxis = 'y3',
                        marker = {'color': 'rgba(255, 193, 7, 0.35)'},
                        name = 'SPARK 買進並持有期間'
                    )
                ],

                'layout': go.Layout(
                    dragmode =  'pan',
                    xaxis_rangeslider_visible = False,
                    xaxis_rangebreaks = [dict(values = locate_date_breaks(plot_df))],
                    legend_orientation = 'h',
                    showlegend = True,
                    font = {'family': 'Microsoft JhengHei'},
                    margin = {'t': 2, 'b': 2, 'l': 2, 'r': 2},
                    xaxis = {'domain': [0.04, 0.96]},
                    yaxis = {'domain': [0.25, 0.97], 'side': 'right', 'overlaying': 'y3'},
                    yaxis2 = {'domain': [0.05, 0.25], 'side': 'right'},
                    yaxis3 = {'domain': [0.25, 0.97], 'side': 'left'},
                    legend = {'x': 0, 'y': 0.01}
                )
            },
            config = {'modeBarButtonsToRemove': ['toImage', 'select2d', 'lasso2d', 'autoScale2d', 'toggleSpikelines']},
            style = {'height': '120mm'}
        ),
        style = {'margin-left': '2%', 'margin-right': '2%', 'margin-bottom': '2%'}
    )
    # info box - price range
    info_box_price_range_layout = html.Div(
        dcc.Graph(
            figure = {
                'data': [
                    go.Scatter(
                        x = price_range_df.index,
                        y = price_range_df.close,
                        line_width = 2,
                        line_color = 'black',
                        name = '52 週股價'
                    ),
                    go.Scatter(
                        x = price_range_df.index,
                        y = price_range_df.latest_close,
                        line_width = 3,
                        line_color = 'royalblue',
                        name = '最後收盤價'
                    ),
                ],
                'layout': go.Layout(
                    dragmode =  'pan',
                    showlegend = False,
                    xaxis_rangeslider_visible = False,
                    font = {'family': 'Microsoft JhengHei'},
                    margin = {'t': 2, 'b': 2, 'l': 1, 'r': 2},
                    xaxis = {
                        'domain': [0.03, 0.87],
                        'fixedrange': True,
                        'mirror': True
                    },
                    yaxis = {
                        'domain': [0.04, 0.95],
                        'fixedrange': True,
                        'side': 'right'
                    },
                    hovermode = 'closest'
                )
            },
            config = {'modeBarButtonsToRemove': ['zoom2d', 'toImage', 'select2d', 'lasso2d', 'autoScale2d', 'toggleSpikelines', 'hoverCompareCartesian', 'hoverClosestCartesian']},
            style = {'height': '15mm', 'border': '1px #8e9aad solid'}
        )
    )
    # info box - volume range
    info_box_volume_range_layout = html.Div(
        dcc.Graph(
            figure = {
                'data': [
                    go.Bar(
                        x = volume_range_df.index,
                        y = volume_range_df.volume,
                        marker = {'color': volume_range_df.volume, 'colorscale': 'RdYlGn'},
                        name = '近一季成交量'
                    ),
                    go.Scatter(
                        x = volume_range_df.index,
                        y = volume_range_df.avg_volume,
                        line_color = 'black',
                        line_width = 3,

                        name = '近一季成交量平均值'
                    ),
                ],
                'layout': go.Layout(
                    dragmode =  'pan',
                    showlegend = False,
                    xaxis_rangeslider_visible = False,
                    xaxis_rangebreaks = [dict(values = locate_date_breaks(volume_range_df))],
                    font = {'family': 'Microsoft JhengHei'},
                    margin = {'t': 2, 'b': 2, 'l': 1, 'r': 2},
                    xaxis = {
                        'domain': [0.03, 0.85],
                        'fixedrange': True,
                        'mirror': True
                    },
                    yaxis = {
                        'domain': [0.04, 0.95],
                        'fixedrange': True,
                        'side': 'right'
                    },
                    hovermode = 'closest'
                )
            },
            config = {'modeBarButtonsToRemove': ['zoom2d', 'toImage', 'select2d', 'lasso2d', 'autoScale2d', 'toggleSpikelines', 'hoverCompareCartesian', 'hoverClosestCartesian']},
            style = {'height': '15mm', 'border': '1px #8e9aad solid'}
        )
    )
    # info box - latest prediction signal ball
    info_box_signal_ball_layout = html.Div(
        style = {'background-color': signal_ball_color, 'border': '1px black solid', 'border-radius': '50%', 'width': '20px', 'height': '20px'}
    )
    # info box - n years eq plot
    info_box_eq_plot_layout = html.Div(
        dcc.Graph(
            figure = {
                'data': [
                    go.Scatter(
                        x = eq_plot_df.index,
                        y = eq_plot_list,
                        line_width = 3,
                        name = 'Spark A.I. 權益曲線'
                    ),
                    go.Scatter(
                        x = eq_plot_df.index,
                        y = list(eq_plot_df.close),
                        line_width = 2,
                        name = '標的股價走勢'
                    ),
                ],
                'layout': go.Layout(
                    dragmode =  'pan',
                    showlegend = False,
                    xaxis_rangeslider_visible = False,
                    font = {'family': 'Microsoft JhengHei'},
                    margin = {'t': 2, 'b': 2, 'l': 1, 'r': 2},
                    xaxis = {
                        'domain': [0.03, 0.93],
                        'fixedrange': True,
                        'mirror': True
                    },
                    yaxis = {
                        'domain': [0.08, 0.95],
                        'fixedrange': True,
                        'side': 'right'
                    },
                    hovermode = 'closest'
                )
            },
            config = {'modeBarButtonsToRemove': ['zoom2d', 'toImage', 'select2d', 'lasso2d', 'autoScale2d', 'toggleSpikelines', 'hoverCompareCartesian', 'hoverClosestCartesian']},
            style = {'height': '45mm', 'border': '1px #8e9aad solid'}
        )
    )
    # info box - year performance table
    info_box_year_performance_table = html.Div(
        dash_table.DataTable(
            columns = [{'name': i, 'id': i} for i in show_df.columns],
            data = show_df.to_dict('records'),
            style_header = {
                'backgroundColor': '#54647d',
                'color': 'white',
                'fontSize': '12px',
                'fontWeight': 'bold',
                'fontFamily': 'Microsoft JhengHei',
                'whiteSpace': 'normal',
                'textAlign': 'center'
            },
            style_cell = {
                'fontSize': '10px'
            },
            style_cell_conditional = [
                {
                    'if': {
                        'column_id': '指標'
                    },
                    'backgroundColor': '#bdc8d9',
                    'fontFamily': 'Microsoft JhengHei',
                    'textAlign': 'center',
                    'fontSize': '12px',
                    'fontWeight': 'bold'
                }
            ],
        ),
        style = {'margin-top': '2%', 'margin-left': '3%', 'margin-right': '3%', 'margin-bottom': '1%'}
    )
    return stock_check_chart_layout, company_name, company_description, news_table, bloomberg_news, bbg_news_count, bbg_news_content_0, bbg_news_content_1, bbg_news_content_2, bbg_news_content_3, bbg_news_content_4, info_box_price_range_layout, price_range_print, info_box_volume_range_layout, volume_range_print, '(功能更新中)', '(功能更新中)', spark_latest_pred, info_box_signal_ball_layout, spark_pred_start, spark_pred_period, spark_pred_period_ret, info_box_eq_plot_layout, eq_performace_print, info_box_year_performance_table, None
    
# Company description Collapse
@app.callback(
    Output('home_stk_company_description_collapse', 'is_open'),
    [Input('home_stk_company_description_collapse_button', 'n_clicks')],
    [State('home_stk_company_description_collapse', 'is_open')],
)
def home_company_description_toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
# News Collapse
@app.callback(
    Output('home_stk_company_news_collapse', 'is_open'),
    [Input('home_stk_company_news_collapse_button', 'n_clicks')],
    [State('home_stk_company_news_collapse', 'is_open')],
)
def home_company_news_toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
# Bloomberg News
@app.callback(
    Output('home_stk_company_bloomberg_news_collapse', 'is_open'),
    [Input('home_stk_company_bloomberg_news_collapse_button', 'n_clicks')],
    [State('home_stk_company_bloomberg_news_collapse', 'is_open')],
)
def home_company_bloomberg_news_toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
@app.callback(
    Output('bloomberg_news_display_area', 'children'),
    [Input('bloomberg_news_button_0', 'n_clicks'),
    Input('bloomberg_news_button_1', 'n_clicks'),
    Input('bloomberg_news_button_2', 'n_clicks'),
    Input('bloomberg_news_button_3', 'n_clicks'),
    Input('bloomberg_news_button_4', 'n_clicks')],
    [State('bloomberg_news_0', 'children'),
    State('bloomberg_news_1', 'children'),
    State('bloomberg_news_2', 'children'),
    State('bloomberg_news_3', 'children'),
    State('bloomberg_news_4', 'children')],
)
def display_bloomberg_news(n_0, n_1, n_2, n_3, n_4, news_content_0, news_content_1, news_content_2, news_content_3, news_content_4):
    news_content = '點閱 Bloomberg 新聞'
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'bloomberg_news_button_0' in changed_id:
        news_content = news_content_0
    elif 'bloomberg_news_button_1' in changed_id:
        news_content = news_content_1
    elif 'bloomberg_news_button_2' in changed_id:
        news_content = news_content_2
    elif 'bloomberg_news_button_3' in changed_id:
        news_content = news_content_3
    elif 'bloomberg_news_button_4' in changed_id:
        news_content = news_content_4
    return news_content


#____________________________________________
#|____SERVER____________________________________

if __name__ == "__main__":
    app.run_server(debug = True)
