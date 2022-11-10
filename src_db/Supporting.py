from collections import defaultdict
from datetime import date


BASE_NOM = ('НОМЕНКЛАТУРА СО ШТРИХКОДОМ', 'СТАРАЯ НОМЕНКЛАТУРА')
DRAFT_BEER = 'Пиво разливное (гр)'
DRAFT_KZ = ("Пиво разливное Канцлер", "Пиво разливное б/а", "Пиво разливное Крафт Кран")


class _DataKit:
    def __init__(self):
        self.sales = 0.0
        self.sales_carts = 0.0
        self.checks_qnt = 0
        self.checks_carts_qnt = 0
        self.sales_not_bonus = 0.0
        self.cost_price = 0.0
        self.woff = 0.0
        self.beer_ltr = 0.0
        self.beer_kz_ltr = 0.0

    def tuple_to_write(self):
        return (self.sales, self.sales_carts, self.checks_qnt, self.checks_carts_qnt,
                self.sales_not_bonus, self.cost_price, self.woff, self.beer_ltr, self.beer_kz_ltr)


def _request_for_inserting(cursor, table_name: str) -> str:
    pragma = f"PRAGMA table_info({table_name})"
    cols_count = len(cursor.execute(pragma).fetchall())
    placeholder = f"({','.join(['?'] * cols_count)})"
    return f"INSERT INTO {table_name} VALUES {placeholder}"


def collect_and_writing(con_write, con_proc, con_roz, date_arg: str, shops: dict):
    year, month = [int(date_part) for date_part in date_arg.split("-")]
    result = defaultdict(lambda: _DataKit())
    carts = set()
    for ln in con_proc.execute("""SELECT c.mag_id, c.cart, SUM(c.summ)
                                  FROM checks as c INNER JOIN sku as s
                                  ON c.sku_code = s.code
                                  WHERE c.month = ? and c.year = ? and s.upcateg in (?, ?)                
                                  GROUP BY c.mag_id, c.date, c.cart, c.chk_id
                                  HAVING SUM(c.summ) is not NULL""", (month, year, *BASE_NOM)):
        shop_id, summa = ln[0], ln[2]
        try:
            crt = int(ln[1])
        except ValueError:
            crt = 0
        result[shop_id].sales += summa
        result[shop_id].checks_qnt += 1 if summa >= 0.0 else -1
        if crt:
            result[shop_id].sales_carts += summa
            result[shop_id].checks_carts_qnt += 1 if summa >= 0.0 else -1
            carts.add((shop_id, shops[shop_id].old_shop, crt))

    for ln in con_proc.execute("""SELECT c.mag_id, s.subgrp, SUM(c.qnt)
                                  FROM checks as c INNER JOIN sku as s
                                  ON s.code = c.sku_code
                                  WHERE c.month = ? and c.year = ? and s.grp = ?                  
                                  GROUP BY c.mag_id, s.subgrp
                                  HAVING SUM(c.qnt) is not NULL""", (month, year, DRAFT_BEER)):
        shop_id, summa = ln[0], ln[2]
        result[shop_id].beer_ltr += summa
        if ln[1] in DRAFT_KZ:
            result[shop_id].beer_kz_ltr += summa

    for ln in con_roz.execute("""SELECT s.mag_id, SUM(s.summ), SUM(s.sebest)
                                 FROM sales as s INNER JOIN sku as k
                                 ON s.sku_code = k.code
                                 WHERE s.year = ? and s.month = ? and k.upcateg in (?, ?)  
                                 GROUP BY s.mag_id""", (year, month, *BASE_NOM)):
        result[ln[0]].sales_not_bonus += 0.0 if ln[1] is None else ln[1]
        result[ln[0]].cost_price += 0.0 if ln[2] is None else ln[2]

    for ln in con_roz.execute("""SELECT s.mag_id, SUM(s.summ)
                                 FROM woff as s INNER JOIN sku as k
                                 ON s.sku_code = k.code
                                 WHERE s.year = ? and s.month = ? and k.upcateg in (?, ?)
                                 GROUP BY s.mag_id""", (year, month, *BASE_NOM)):
        result[ln[0]].woff += 0.0 if ln[1] is None else ln[1]

    request = _request_for_inserting(con_write, table_name="data")
    for shop_id, data in result.items():
        row = (date_arg, shop_id, shops[shop_id].old_shop, *data.tuple_to_write())
        con_write.execute(request, row)
    request = _request_for_inserting(con_write, table_name="carts")
    for row in carts:
        con_write.execute(request, (date_arg, *row))


if __name__ == "__main__":
    import sqlite3
    db = r"C:\Users\suhov\!_DB_project\checks_integers.db"
    con = sqlite3.connect(db)
    cur = con.cursor()
    print(_request_for_inserting(cur, table_name="checks"))
    print(_request_for_inserting(cur, table_name="tt"))
    con.close()
