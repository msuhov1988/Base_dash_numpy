import numpy as np
from plotly.graph_objects import Scatter, Bar
from collections import namedtuple


def _div(dividend: str, divider: str, subtrahend=None, unit_minus=0):
    def inner(data: dict[str, np.array]):
        sub = data[subtrahend] if subtrahend is not None else 0.0
        div = data[dividend] - sub
        if subtrahend == SAL_NB:
            div[sub == 0.0] = 0.0
        der = data[divider]
        result = np.zeros(div.size, dtype=np.float32)
        for i in range(result.size):
            if der[i] != 0.0:
                result[i] = div[i] / der[i] - unit_minus
        return result
    inner.__name__ = f"{_div.__name__}_{dividend}_{divider}"
    return inner


def _sub(minuend: str, subtrahend: str, subtrahend_additional=None):
    def inner(data: dict[str, np.array]):
        temp = data[subtrahend_additional] if subtrahend_additional else 0.0
        return data[minuend] - data[subtrahend] - temp
    inner.__name__ = f"{_sub.__name__}_{minuend}_{subtrahend}_{subtrahend_additional}"
    return inner


# constants like names of database columns (table data), it is a prime data
SAL, SAL_NB, S_COST, WOF = "sales_bn", "sales_not_bn", "self_cost", "write_off"
SAL_CRT, CHK, CHK_CRT = "sales_carts_bn", "checks_qnt", "checks_carts_qnt"
BEER, BEER_KZ = "beer_litres", "beer_kz_litres"

M = namedtuple("SUM_Requisites", ("label", "for_one", "percent_format", "plot", "fn", "fn_arg", "prime"))
SETUP = {SAL: M('1.1 Выручка', False, False, Scatter, fn=None, fn_arg=(), prime=True),
         SAL_NB: M('1.2 Выручка без бонусов', False, False, Scatter, fn=None, fn_arg=(), prime=True),
         S_COST: M('1.3 Себестоимость', False, False, Scatter, fn=None, fn_arg=(), prime=True),
         WOF: M('1.4 Списания', False, False, Scatter, fn=None, fn_arg=(), prime=True),
         SAL_CRT: M('1.5 Выручка по картам', False, False, Scatter, fn=None, fn_arg=(), prime=True),
         CHK: M('1.6 Кол-во чеков', False, False, Scatter, fn=None, fn_arg=(), prime=True),
         CHK_CRT: M('1.7 Кол-во чеков по картам', False, False, Scatter, fn=None, fn_arg=(), prime=True),
         BEER: M('1.8 Пиво разливное, литры', False, False, Scatter, fn=None, fn_arg=(), prime=True),
         BEER_KZ: M('1.9 Пиво Канцлер, литры', False, False, Scatter, fn=None, fn_arg=(), prime=True),
         'p_crt_sale': M('2.1 % карт в выручке', True, True, Bar, fn=_div, fn_arg=(SAL_CRT, SAL), prime=False),
         'p_bn_sale': M('2.2 % бонусов в выручке', True, True, Bar, fn=_div, fn_arg=(SAL, SAL, SAL_NB), prime=False),
         'v_prof': M('3.1 Вал-ая приб.', False, False, Scatter, fn=_sub, fn_arg=(SAL_NB, S_COST), prime=False),
         'm_prof': M('3.2 Марж-ая приб.', False, False, Scatter, fn=_sub, fn_arg=(SAL_NB, S_COST, WOF), prime=False),
         'markup': M('3.3 Наценка без бон-в', True, True, Bar, fn=_div, fn_arg=(SAL_NB, S_COST, None, 1), prime=False),
         'margin': M('3.4 Марж-ть без бон-в', True, True, Bar, fn=_div, fn_arg=(SAL_NB, S_COST, WOF, 1), prime=False),
         'p_crt_chk': M('4.1 Доля карт в чеках', True, True, Bar, fn=_div, fn_arg=(CHK_CRT, CHK), prime=False),
         'chk_mid': M('4.2 Сред. чек', True, False, Bar, fn=_div, fn_arg=(SAL, CHK), prime=False),
         'chk_crt_mid': M('4.3 Сред. чек по картам', True, False, Bar, fn=_div, fn_arg=(SAL_CRT, CHK_CRT), prime=False),
         'shops_active': M('5.1 Кол-во магазинов', False, False, Scatter, fn=None, fn_arg=(), prime=False),
         'shops_new': M('5.2 Новых магазинов', False, False, Scatter,  fn=None, fn_arg=(), prime=False),
         'shops_lost': M('5.3 Закрытых магазинов', False, False, Scatter, fn=None, fn_arg=(), prime=False),
         'crt_active': M('6.1 Активных карт', False, False, Scatter, fn=None, fn_arg=(), prime=False),
         'crt_new': M('6.2 Новых карт', False, False, Scatter, fn=None, fn_arg=(), prime=False),
         'crt_lost': M('6.3 Карт, далее неактивных', False, False, Scatter, fn=None, fn_arg=(), prime=False),
         'on_crt_sal': M('6.4 Выр-ка на карту', True, False, Bar, fn=_div, fn_arg=(SAL_CRT, 'crt_active'), prime=False),
         'on_crt_chk': M('6.5 Чеков на карту', True, False, Bar, fn=_div, fn_arg=(CHK_CRT, 'crt_active'), prime=False)}
SHOPS_QNT = "shops_active"
PRIMES = {key for key, val in SETUP.items() if val.prime}
SETS = {key for key, val in SETUP.items() if not val.prime and val.fn is None}
CART_SETS = {"crt_active", "crt_new", "crt_lost"}
LAGGING = {SAL_NB, S_COST, WOF}
UNITED_CHECK_LIST = {val.label: key for key, val in SETUP.items()}


if __name__ == "__main__":
    print("Primes:")
    print(PRIMES)
    print("Sets:")
    print(SETS)
    print("Prime attributes in dependencies:")
    print({arg for val in SETUP.values() for arg in val.fn_arg if arg in PRIMES})
    print("Set attributes in dependencies:")
    print({arg for val in SETUP.values() for arg in val.fn_arg if arg in SETS})
