from . import Basics as Bs
from .ObjectConstants import UNITED_CHECK_LIST
from datetime import date
import dash_bootstrap_components as dbc
from dash import html
from dash import dcc


def layout_create(drop_div: tuple[str], drop_reg: tuple[str], drop_city: tuple[str], drop_tt: dict[str, int],
                  end_date, beg_date, end_date_lag):
    return html.Div(children=[
                html.Div(className='base_body_reference', children=[
                    html.Div(className='base_row_reference', children=[
                        dbc.Row([
                            dbc.Col(html.Label('Дивизион'), width={'size': 2, 'offset': 1}),
                            dbc.Col(html.Label('Регион'), width=2),
                            dbc.Col(html.Label('Населенный пункт'), width=2),
                            dbc.Col(html.Label('Магазин'), width=3)
                        ]),
                        dbc.Row([
                            dbc.Col(html.Label('ОСНОВНОЙ:', className="label"), width=1),
                            dbc.Col(
                                dcc.Dropdown(
                                    id="base_divisions",
                                    options=[{"label": k, "value": k} for k in drop_div],
                                    value=[],
                                    placeholder="Итого",
                                    multi=True), width={'size': 2}
                            ),
                            dbc.Col(
                                dcc.Dropdown(
                                    id="base_regions",
                                    options=[{"label": k, "value": k} for k in drop_reg],
                                    value=[],
                                    placeholder="Итого",
                                    multi=True), width=2
                            ),
                            dbc.Col(
                                dcc.Dropdown(
                                    id="base_cities",
                                    options=[{"label": k, "value": k} for k in drop_city],
                                    value=[],
                                    placeholder="Итого",
                                    multi=True), width=2
                            ),
                            dbc.Col(
                                dcc.Dropdown(
                                    id="base_shops",
                                    options=[{"label": k, "value": v} for k, v in drop_tt.items()],
                                    value=[],
                                    placeholder="Итого",
                                    multi=True), width=3
                            )
                        ]),
                    ]),
                    html.Div(className='base_row_reference', children=[
                        dbc.Row([
                            dbc.Col(html.Label('Дивизион сравнения'), width={'size': 2, 'offset': 1}),
                            dbc.Col(html.Label('Регион сравнения'), width=2),
                            dbc.Col(html.Label('Населенный пункт сравнения'), width=2),
                            dbc.Col(html.Label('Магазин сравнения'), width=3)
                        ]),
                        dbc.Row([
                            dbc.Col(
                                dcc.Checklist(
                                    id="compare_activate",
                                    options=[{'label': "СРАВНИТЬ:", 'value': "yes"}],
                                    value=[],
                                    labelClassName="label"), width=1
                            ),
                            dbc.Col(
                                dcc.Dropdown(
                                    id="base_divisions_compare",
                                    options=[{"label": k, "value": k} for k in drop_div],
                                    value=[],
                                    multi=True,
                                    placeholder="Итого",
                                    disabled=True), width=2
                            ),
                            dbc.Col(
                                dcc.Dropdown(
                                    id="base_regions_compare",
                                    options=[{"label": k, "value": k} for k in drop_reg],
                                    value=[],
                                    multi=True,
                                    placeholder="Итого",
                                    disabled=True), width=2
                            ),
                            dbc.Col(
                                dcc.Dropdown(
                                    id="base_cities_compare",
                                    options=[{"label": k, "value": k} for k in drop_city],
                                    value=[],
                                    multi=True,
                                    placeholder="Итого",
                                    disabled=True), width=2
                            ),
                            dbc.Col(
                                dcc.Dropdown(
                                    id="base_shops_compare",
                                    options=[{"label": k, "value": v} for k, v in drop_tt.items()],
                                    value=[],
                                    multi=True,
                                    placeholder="Итого",
                                    disabled=True), width=3
                            )
                        ]),
                    ])
                ]),
                html.Div(className="base_graph_row", children=[
                    dbc.Row([
                        dbc.Col(
                            html.Div(className="base_body_sales_checklist", children=[
                                dcc.Checklist(
                                    id="base_sales_checklist",
                                    options=[{'label': key, 'value': val} for key, val in UNITED_CHECK_LIST.items()],
                                    value=[list(UNITED_CHECK_LIST.values())[0]],
                                    labelStyle={'display': 'block'})
                            ]), width=2
                        ),
                        dbc.Col(
                            dcc.Graph(
                                id="base_sales_graph",
                                responsive=True,
                                figure={"layout": {"plot_bgcolor": "#222",
                                                   "paper_bgcolor": "#222",
                                                   "yaxis": {"gridcolor": "#212529"},
                                                   "xaxis": {"gridcolor": "#212529"}}},
                                style={"height": "100%"}
                            ), width=8
                        ),
                        dbc.Col(
                            html.Div(className="types_for_choose", children=[
                                html.Div(className="base_body_one_checklist", children=[
                                    dcc.Checklist(
                                        id="base_one_checklist",
                                        options=[{'label': 'В общем', 'value': Bs.ForOneSign.anyone.value},
                                                 {'label': 'На одну ТТ', 'value': Bs.ForOneSign.for_one.value}],
                                        value=[Bs.ForOneSign.anyone.value],
                                        labelStyle={'display': 'block'}),
                                ]),
                                html.Div(className="base_body_dtt_checklist", children=[
                                    dcc.Checklist(
                                        id="base_dtt_checklist",
                                        options=[{'label': 'Все ТТ', 'value': Bs.OldSign.anyone.value},
                                                 {'label': 'ТТ с 01.01.20', 'value': Bs.OldSign.old_only.value}],
                                        value=[Bs.OldSign.anyone.value],
                                        labelStyle={'display': 'block'}),
                                ]),
                                html.Div(className="base_body_graph_radio", children=[
                                    dcc.RadioItems(
                                        id="base_graph_radio",
                                        options=[{'label': 'График: по годам', 'value': Bs.LineType.years.value},
                                                 {'label': 'График: динамика', 'value': Bs.LineType.chronic.value}],
                                        value=Bs.LineType.chronic.value,
                                        labelStyle={'display': 'block'}),
                                ]),
                                html.Div(className="base_body_button_graph", children=[
                                    html.Button('Выгрузить в файл', id='base_button_graph'),
                                    dcc.Download(id="base_graph_download")
                                ]),
                                html.Div(className="base_body_graph_loading", children=[
                                    dcc.Loading(
                                        id="base_graph_loading",
                                        children=html.Div(id="base_graph_loading_output", children=[]),
                                        type="dot"),
                                    dcc.Loading(
                                        id="base_graph_loading_file",
                                        children=html.Div(id="base_graph_loading_output_file", children=[]),
                                        type="dot")
                                ])
                            ]), width=2)
                    ]),
                ]),
                html.Div(className="base_body_table_reference", children=[
                    html.Div(className="base_row_reference", children=[
                        dbc.Row(
                            dbc.Col([
                                html.Label("ТАБЛИЦА ИТОГОВ")
                            ], width={'size': 8, 'offset': 2})),
                        dbc.Row(
                            dbc.Col(html.Label("ЕДИНИЦА ВРЕМЕНИ - МЕСЯЦ. КОНКРЕТНЫЕ ЧИСЛА НЕ ВЛИЯЮТ НА ВЫВОД."),
                                    width={'size': 8, 'offset': 2})

                        )
                    ]),
                    html.Div(className="base_row_reference", children=[
                        dbc.Row([
                            dbc.Col([
                                html.Div(className="base_table_checklist", children=[
                                    html.Div(className="base_date_range", children=[
                                        html.Label("Основной период:", className="label"),
                                        dcc.DatePickerRange(
                                            id='base_date_range',
                                            min_date_allowed=beg_date,
                                            max_date_allowed=end_date,
                                            start_date=date(end_date.year, 1, 1),
                                            end_date=end_date,
                                            display_format="MM.YYYY",
                                            number_of_months_shown=4
                                        ),
                                    ]),
                                    html.Div(className="base_date_range_compare", children=[
                                        dcc.Checklist(
                                            id="table_compare_activate",
                                            options=[{'label': "Сравнить:", 'value': "yes"}],
                                            value=[]),
                                        dcc.DatePickerRange(
                                            id='base_date_range_compare',
                                            min_date_allowed=beg_date,
                                            max_date_allowed=end_date,
                                            display_format="MM.YYYY",
                                            number_of_months_shown=4,
                                            disabled=True
                                        )
                                    ])
                                ])
                            ], width=3
                            ),
                            dbc.Col(
                                html.Div(className="base_table_checklist", children=[
                                    html.Label("Срез данных таблицы", className="label"),
                                    dcc.Checklist(
                                        id="base_table_slice_checklist",
                                        options=[{'label': v, 'value': k} for k, v in Bs.TableSlices.items()],
                                        value=[],
                                        labelStyle={'display': 'block'})
                                ]), width=2
                            ),
                            dbc.Col([
                                html.Div(className="base_table_checklist", children=[
                                    dcc.Checklist(
                                        id="base_table_one_checklist",
                                        options=[{'label': 'В общем', 'value': Bs.ForOneSign.anyone.value},
                                                 {'label': 'На одну ТТ', 'value': Bs.ForOneSign.for_one.value}],
                                        value=[Bs.ForOneSign.anyone.value],
                                        labelStyle={'display': 'block'}),
                                ]),
                                html.Div(className="base_table_checklist", children=[
                                    dcc.Checklist(
                                        id="base_table_dtt_checklist",
                                        options=[{'label': 'Все ТТ', 'value': Bs.OldSign.anyone.value},
                                                 {'label': 'ТТ с 01.01.20', 'value': Bs.OldSign.old_only.value}],
                                        value=[Bs.OldSign.anyone.value],
                                        labelStyle={'display': 'block'}),
                                ])
                            ], width=2
                            ),
                            dbc.Col([
                                html.Div(className="base_table_checklist", children=[
                                    html.Div(className="base_date_range", children=[
                                        html.Label("Показатели продаж", className="label"),
                                        dcc.Dropdown(
                                            id="base_table_sales_references",
                                            options=[{"label": k, "value": v} for k, v in UNITED_CHECK_LIST.items()],
                                            value=[list(UNITED_CHECK_LIST.values())[0]],
                                            multi=True)
                                    ])
                                ]),
                                html.Div(className="base_table_warning", children=[
                                    html.Div(id="base_table_message", children=[])
                                ])
                                ], width=3
                            )
                        ]),
                        dbc.Row([
                            dbc.Col(
                                html.Div(className="base_table_drops", children=[
                                    html.Div(className='base_date_range', children=[
                                        html.Label('Дивизион'),
                                        dcc.Dropdown(
                                            id="base_table_divisions",
                                            options=[{"label": k, "value": k} for k in drop_div],
                                            value=[],
                                            placeholder="Итого",
                                            multi=True)
                                    ])
                                ]), width=2
                            ),
                            dbc.Col(
                                html.Div(className="base_table_drops", children=[
                                    html.Div(className='base_date_range', children=[
                                        html.Label('Регион'),
                                        dcc.Dropdown(
                                            id="base_table_regions",
                                            options=[{"label": k, "value": k} for k in drop_reg],
                                            value=[],
                                            placeholder="Итого",
                                            multi=True)
                                    ])
                                ]), width=2
                            ),
                            dbc.Col(
                                html.Div(className="base_table_drops", children=[
                                    html.Div(className='base_date_range', children=[
                                        html.Label('Населенный пункт'),
                                        dcc.Dropdown(
                                            id="base_table_cities",
                                            options=[{"label": k, "value": k} for k in drop_city],
                                            value=[],
                                            placeholder="Итого",
                                            multi=True)
                                    ])
                                ]), width=2
                            ),
                            dbc.Col(
                                html.Div(className="base_table_drops", children=[
                                    html.Div(className='base_date_range', children=[
                                        html.Label('Магазин'),
                                        dcc.Dropdown(
                                            id="base_table_shops",
                                            options=[{"label": k, "value": v} for k, v in drop_tt.items()],
                                            value=[],
                                            placeholder="Итого",
                                            multi=True)
                                    ])
                                ]), width=3
                            ),
                            dbc.Col(
                                html.Div([
                                    html.Div(className="base_body_table_loading", children=[
                                        dcc.Loading(
                                            id="base_table_loading",
                                            children=html.Div(id="base_table_loading_output", children=[]),
                                            type="circle"),
                                        dcc.Loading(
                                            id="base_table_file_loading",
                                            children=html.Div(id="base_table_file_loading_output", children=[]),
                                            type="circle")
                                    ])
                                ]), width=1
                            )
                        ])
                    ])
                ]),
                html.Div(children=[
                    dbc.Row(
                        dbc.Col(
                            html.Div([
                                html.Button('Выгрузить в файл', id='base_button_table'),
                                dcc.Download(id="base_table_download")
                            ]), width={'size': 2, 'offset': 9}
                        )
                    ),
                ]),
                html.Div(children=[
                    dbc.Row(
                        dbc.Col(
                            html.Div(id="base_table", children=[])
                        )
                    )
                ])
            ])
