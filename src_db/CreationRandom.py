import random
import sqlite3
import os.path
from datetime import date, timedelta
from time import time
from collections import namedtuple


def time_meter(func):
    def wrapper():
        st = time()
        func()
        print(f"Время выполнения - {round(time() - st, 1)} сек.")
    wrapper.__doc__ = func.__doc__
    wrapper.__name__ = func.__name__
    return wrapper


def _months_range(end: date) -> list:
    temp = date(2020, 1, 1)
    result = [temp]
    while True:
        temp = date(temp.year, temp.month + 1, 1) if temp.month + 1 <= 12 else date(temp.year + 1, 1, 1)
        result.append(temp)
        if temp.year == end.year and temp.month == end.month:
            break
    return result


def _request_for_inserting(cursor, table_name: str) -> str:
    pragma = f"PRAGMA table_info({table_name})"
    cols_count = len(cursor.execute(pragma).fetchall())
    placeholder = f"({','.join(['?'] * cols_count)})"
    return f"INSERT INTO {table_name} VALUES {placeholder}"


@time_meter
def creation():
    divisions = [f"Дивизион{i}" for i in range(1, random.randint(3, 5))]
    regions = [f"Регион{i}" for i in range(1, random.randint(10, 20))]
    cities = [f"НасПункт{i}" for i in range(1, random.randint(30, 50))]

    Requisites = namedtuple("Requisites", ["div_name", "reg_name", "city_name", "old_shop", "shop_name"])
    shops = dict()
    for shop_id in range(1, random.randint(100, 200)):
        div, reg, city = random.choice(divisions), random.choice(regions), random.choice(cities)
        old = random.choice([0, 1])
        shops[shop_id] = Requisites(div, reg, city, old, f"Магазин{shop_id}")
    shop_ids = list(shops.keys())
    old_shops_ids = list([k for k, val in shops.items() if val.old_shop == 1])
    not_old_shops_ids = list(set(shop_ids).difference(set(old_shops_ids)))

    up_folder = os.path.split(os.path.dirname(__file__))[0]
    db_app = os.path.join(up_folder, "database\\summary.db")
    con_app = None
    try:
        con_app = sqlite3.connect(db_app)
        cur_app = con_app.cursor()
        schema = open(os.path.join(up_folder, "database\\schema_summary.sql"), encoding="utf8")
        cur_app.executescript(schema.read())

        request = _request_for_inserting(cur_app, table_name="tt")
        for shop_id, ln in shops.items():
            cur_app.execute(request, (*ln, shop_id))
        print("Справочники магазинов и последних дат записаны.")

        last_proc_date = date(2022, random.randint(1, 12), random.randint(1, 28))
        last_roz_date = date(2022, random.randint(1, 12), 1)
        last_max_date = max(last_proc_date, last_roz_date)
        date_range = _months_range(last_max_date)
        date_range_strings = [dt.strftime("%Y-%m") for dt in date_range]
        cur_app.execute("INSERT INTO last_data_dates VALUES (?,?)",
                        (date(2020, 1, 1).strftime("%Y-%m"), last_max_date.strftime("%Y-%m")))
        print("Начальная и конечная даты данных записаны в базу приложения.")

        request_data = _request_for_inserting(cur_app, table_name="data")
        request_carts = _request_for_inserting(cur_app, table_name="carts")
        for dt_str in date_range_strings:
            carts = set()
            chosen_shops = old_shops_ids.copy()
            shops_qnt = random.randint(len(not_old_shops_ids) // 2, len(not_old_shops_ids))
            for i in range(shops_qnt):
                chosen_shops.append(random.choice(not_old_shops_ids))

            for shop_id in chosen_shops:
                sales = random.randint(150000, 3000000)
                sales_carts = sales * random.uniform(0.6, 0.95)
                chk_qnt = sales / random.randint(300, 500)
                chk_qnt_carts = chk_qnt * random.uniform(0.7, 0.95)
                sales_not_bonus = sales * random.uniform(0.8, 0.99)
                cost_price = sales_not_bonus / random.uniform(1.3, 1.7)
                woff = sales_not_bonus * random.uniform(0.01, 0.01)
                beer_ltr = sales * random.uniform(0.4, 0.6) / random.uniform(90, 110)
                beer_kz_ltr = beer_ltr * random.uniform(0.9, 0.99)
                row = (dt_str, shop_id, shops[shop_id].old_shop,
                       sales, sales_carts, chk_qnt, chk_qnt_carts, sales_not_bonus,
                       cost_price, woff, beer_ltr, beer_kz_ltr)
                cur_app.execute(request_data, row)

                carts_qnt = random.randint(100, 300)
                for j in range(carts_qnt):
                    crt = random.randint(1, 999999)
                    carts.add((shop_id, shops[shop_id].old_shop, crt))

            for row in carts:
                cur_app.execute(request_carts, (dt_str, *row))
            carts.clear()
            del carts
            print(f"Данные за {dt_str} записаны.")
        con_app.commit()
        print("База данных приложения создана.")
    finally:
        if con_app is not None:
            con_app.close()


if __name__ == "__main__":
    creation()
