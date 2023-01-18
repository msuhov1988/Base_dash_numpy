import src_db.Creation as Db
from src_tab_base import Basics as Bs
from src_tab_base import Layout, Callbacks, Object
from dash import Dash
from dash import dcc
import dash_bootstrap_components as dbc
from fastapi import FastAPI
import uvicorn
from starlette.middleware.wsgi import WSGIMiddleware
import os.path
import sqlite3
from datetime import datetime
from multiprocessing import cpu_count


if __name__ == "__main__":
    Db.creation()

db_path = os.path.join(os.path.dirname(__file__), "database\\summary.db")
conn = None
try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    begin_str, end_str = conn.execute("SELECT first_date, last_date FROM last_data_dates").fetchone()
    BEGIN_DATE, END_DATE = datetime.strptime(begin_str, "%Y-%m").date(), datetime.strptime(end_str, "%Y-%m").date()
    REFERS, DROP_DIV, DROP_REG, DROP_CITY, DROP_SHOP = Bs.references(conn)
    OBJECT = Object.loading_from_db(conn=conn, begin=begin_str, end=end_str, threads_qnt=cpu_count() // 2)
    END_DATE_LAG = datetime.strptime(str(OBJECT.lagging_end), "%Y-%m").date()
    print("Объект данных загружен в память")
finally:
    if conn is not None:
        conn.close()

app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
app.layout =\
    dcc.Tabs([
        dcc.Tab(label="Базовая", children=[Layout.layout_create(DROP_DIV, DROP_REG, DROP_CITY, DROP_SHOP,
                                                                END_DATE, BEGIN_DATE, END_DATE_LAG)])
    ])
Callbacks.base_register_callbacks(app, OBJECT, REFERS, DROP_SHOP)
server = FastAPI()
server.mount("", WSGIMiddleware(app.server))


if __name__ == "__main__":
    from src_tab_base import ObjectCache
    from threading import Thread

    Thread(target=ObjectCache.cache_start, daemon=True).start()
    uvicorn.run("App:server", host="0.0.0.0", port=8050, workers=3)
    # app.run_server(host="127.0.0.1", port=16666, debug=True)
