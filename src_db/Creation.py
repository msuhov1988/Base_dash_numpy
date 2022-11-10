import sqlite3
import os.path
from datetime import date, timedelta
from collections import namedtuple
import time
from . import Supporting as Sup


DB_PROC = r"C:\Users\suhov\!_DB_project\checks_integers.db"
DB_ROZ = r"C:\Users\suhov\!_DB_project\dash.db"
_up_folder = os.path.split(os.path.dirname(__file__))[0]
DB_APP = os.path.join(_up_folder, "database\\summary.db")
SCHEMA_FILE = os.path.join(_up_folder, "database\\schema_summary.sql")


def _time_meter(func):
    def wrapper():
        st = time.time()
        func()
        print(f"Время выполнения - {round(time.time() - st, 1)} сек.")
    wrapper.__name__ = func.__name__
    return wrapper


def _months_range(begin: date, end: date) -> list:
    temp = begin
    result = [temp]
    while True:
        temp = date(temp.year, temp.month + 1, 1) if temp.month + 1 <= 12 else date(temp.year + 1, 1, 1)
        result.append(temp)
        if temp.year == end.year and temp.month == end.month:
            break
    return result


class Connect:
    def __init__(self, database_path):
        self.database = database_path
        self.connection = None

    def __enter__(self):
        self.connection = sqlite3.connect(self.database)
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection is not None:
            self.connection.close()


@_time_meter
def creation():
    prime_proc_modified = time.ctime(os.path.getmtime(DB_PROC))
    prime_roz_modified = time.ctime(os.path.getmtime(DB_ROZ))
    with Connect(DB_PROC) as con_proc, Connect(DB_ROZ) as con_roz, Connect(DB_APP) as con_app:
        exist_table = con_app.execute("""SELECT name
                                         FROM sqlite_master
                                         WHERE type='table' AND name = 'last_changes_dates_primary'""").fetchone()
        if exist_table:
            last_dates = con_app.execute("SELECT proc_changes, roz_changes FROM last_changes_dates_primary").fetchone()
            if last_dates:
                app_proc_modified, app_roz_modified = last_dates
                if app_proc_modified == prime_proc_modified and app_roz_modified == prime_roz_modified:
                    print("Данные первичных баз не изменились.")
                    print("Перезапись базы приложения не требуется.")
                    return

        print("Создание базы данных...")
        schema = open(SCHEMA_FILE, encoding="utf8")
        con_app.executescript(schema.read())
        con_app.execute("INSERT INTO last_changes_dates_primary VALUES (?,?)",
                        (prime_proc_modified, prime_roz_modified))
        print("Даты изменений первичных баз записаны в базу приложения.")

        year, month = con_roz.execute("""SELECT year, MIN(month) FROM sales
                                         WHERE year = (SELECT MIN(year) FROM sales)""").fetchone()
        first_date = date(year, month, 1)

        last_proc_int = con_proc.execute("SELECT MAX(date) FROM checks").fetchone()[0]
        last_proc_date = first_date + timedelta(last_proc_int)
        year, month = con_roz.execute("""SELECT year, MAX(month) FROM sales
                                         WHERE year = (SELECT MAX(year) FROM sales)""").fetchone()
        last_roz_date = date(year, month, 1)
        last_max_date = max(last_roz_date, last_proc_date)
        con_app.execute("INSERT INTO last_data_dates VALUES (?,?)",
                        (first_date.strftime("%Y-%m"), last_max_date.strftime("%Y-%m")))
        print("Начальная и конечная даты данных записаны в базу приложения.")

        temp_con, table = (con_roz, 'sales') if last_proc_date < last_roz_date else (con_proc, 'checks')
        request = """SELECT mag_id FROM {0} WHERE month = ? and year = ?
                     INTERSECT
                     SELECT mag_id FROM {0} WHERE month = ? and year = ?""".format(table)
        old_shops = {ln[0] for ln in temp_con.execute(request, (first_date.month, first_date.year,
                                                                last_max_date.month, last_max_date.year))}
        print("Перечень магазинов, работающих с {0} получен.".format(first_date.strftime("%d.%m.%Y")))

        Requisites = namedtuple("Requisites", ["div_name", "reg_name", "city_name", "old_shop", "shop_name"])
        shops = dict()
        for ln in con_proc.execute("""SELECT id, division, region, city, name FROM tt"""):
            old = 1 if ln[0] in old_shops else 0
            shops[ln[0]] = Requisites(ln[1], ln[2], ln[3], old, ln[4])

        cols_count = len(con_app.execute("PRAGMA table_info(tt)").fetchall())
        placeholder = f"({','.join(['?'] * cols_count)})"
        request = f"INSERT INTO tt VALUES {placeholder}"
        for shop_id, ln in shops.items():
            con_app.execute(request, (*ln, shop_id))
        print("Справочник магазинов записан в базу приложения.")

        date_range = _months_range(begin=first_date, end=last_max_date)
        date_range_strings = [dt.strftime("%Y-%m") for dt in date_range]
        for dt in date_range_strings:
            Sup.collect_and_writing(con_write=con_app, con_proc=con_proc, con_roz=con_roz, date_arg=dt, shops=shops)
            print(f"Данные за {dt} записаны в базу приложения.")

        con_app.commit()

    print("База данных приложения создана.")


if __name__ == "__main__":
    creation()
