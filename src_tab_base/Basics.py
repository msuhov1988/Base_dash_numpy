from enum import Enum
from collections import namedtuple

# dicts and enums that used in the layout
TableSlices = {'div_name': "Дивизион",
               'reg_name': "Регион",
               'city_name': "Нас пункт",
               'shop_name': "Магазин"}


class OldSign(Enum):
    old_only = "ДТТ"
    anyone = "ВСЕ"


class ForOneSign(Enum):
    for_one = "1ТТ"
    anyone = "ВСЕ"


class LineType(Enum):
    chronic = "chronic"
    years = "years"


def references(db_conn):
    ref_line = namedtuple("ref_line", "division region city shop_name shop_id")
    refers = set()
    divs, regs, cities = set(), set(), set()
    shops = dict()
    trn = str.maketrans({".": "", ",": "", ":": "", ";": ""})
    for ln in db_conn.execute("""SELECT shop_id, div_name, reg_name, city_name, shop_name
                                 FROM tt"""):
        div, reg, city, tt = ln[1].translate(trn), ln[2].translate(trn), ln[3].translate(trn), ln[4].translate(trn)
        refers.add(ref_line(div, reg, city, tt, ln[0]))
        divs.add(div)
        regs.add(reg)
        cities.add(city)
        shops[tt] = ln[0]
    divs = tuple((sorted(list(divs), reverse=True)))
    regs = tuple(sorted(list(regs)))
    cities = tuple(sorted(list(cities)))
    shops = {k: shops[k] for k in sorted(shops)}
    return refers, divs, regs, cities, shops
