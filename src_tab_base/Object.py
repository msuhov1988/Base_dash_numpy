from .Basics import ForOneSign, LineType, OldSign
from . import ObjectConstants as Obc
from . import ObjectCache as Caching
import numpy as np
import sqlite3
from collections import namedtuple, defaultdict
from threading import Thread
from copy import deepcopy
from typing import Optional


def _carts_active_in_thread(result: list, ax1_ind: tuple[int], data_matrix: np.array, sign_matrix: np.array):
    for ind in ax1_ind:
        val = np.unique(sign_matrix[data_matrix[..., ind] > 0, 1]).size
        result[ind] = val


def _carts_new_in_thread(result: list, ax1_ind: tuple[int], data_matrix: np.array, sign_matrix: np.array):
    for ind in ax1_ind:
        past = data_matrix[..., :ind].sum(axis=1)
        new = sign_matrix[data_matrix[..., ind] > past, 1]
        old = sign_matrix[past > 0, 1]
        diff = np.setdiff1d(new, old).size
        result[ind] = diff


def _carts_lost_in_thread(result: list, ax1_ind: tuple[int], data_matrix: np.array, sign_matrix: np.array):
    for ind in ax1_ind:
        pres = data_matrix[..., ind + 1:].sum(axis=1)
        lost = sign_matrix[data_matrix[..., ind] > pres, 1]
        continued = sign_matrix[pres > 0, 1]
        diff = np.setdiff1d(lost, continued).size
        result[ind] = diff


class Matrix:
    # ShopReq attributes like ..._name as Basics.TableSlices
    ShopReq = namedtuple("Shop_Requisites_Names", ("div_name", "reg_name", "city_name", "shop_name", "old_shop"))
    TRACE_NAME_SEPARATOR = " | "

    def __init__(self, max_shop_id: int, cart_rows: int, begin: str, end: str, threads_qnt=0):
        self.begin = np.datetime64(begin, "M")
        self.end = np.datetime64(end, "M")
        self.lagging_end = self.end  # modified on load from db
        self.month_range = np.arange(self.begin, self.end + np.timedelta64(1, "M"))
        self.year_range = np.arange(self.begin, self.end + np.timedelta64(1, "Y"), dtype='datetime64[Y]')
        self.old_shops = set()
        self.signs_of_shops = [Matrix.ShopReq(None, None, None, None, 0)] * (max_shop_id + 1)  # modified on load
        for attribute in Obc.PRIMES:
            setattr(self, attribute, np.zeros(shape=(max_shop_id + 1, self.month_range.size), dtype=np.float32))
        self.active_shops = np.zeros(shape=(max_shop_id + 1, self.month_range.size), dtype=np.int8)
        self.shop_cart = np.zeros(shape=(cart_rows, 2), dtype=np.int32)
        self.active_carts = np.zeros(shape=(cart_rows, self.month_range.size), dtype=np.int8)
        interval = list(range(self.month_range.size))
        if threads_qnt <= 0:
            self.intervals = tuple([(i,) for i in interval[1:]])
        else:
            lag = len(interval) // threads_qnt
            if lag == 0:
                self.intervals = tuple([(i,) for i in interval[1:]])
            else:
                aliquot_bound = lag * threads_qnt
                mod_interval = interval[aliquot_bound: len(interval)]
                result = list()
                for num, i in enumerate(range(0, aliquot_bound, lag)):
                    temp = interval[i: i + lag]
                    if num < len(mod_interval):
                        temp.append(mod_interval[num])
                    result.append(temp)
                self.intervals = result
        self.intervals_for_new, self.intervals_for_lost = deepcopy(self.intervals), deepcopy(self.intervals)
        self.intervals_for_new[0].remove(0)
        for num, line in enumerate(self.intervals_for_lost):
            if self.month_range.size - 1 in line:
                self.intervals_for_lost[num].remove(self.month_range.size - 1)
                break

    # name like corresponding key of Obc.SETUP
    def shops_active(self, ax0_ind: list[int], ax1_beg: int = None, ax1_end: int = None) -> np.array:
        if ax1_beg is not None and ax1_end is not None:
            row = self.active_shops[ax0_ind, ax1_beg: ax1_end].sum(1)
            return np.array([np.count_nonzero(row)], dtype=np.float32)
        else:
            return self.active_shops[ax0_ind].sum(axis=0, dtype=np.float32)

    # name like corresponding key of Obc.SETUP
    def shops_new(self, ax0_ind: list[int], ax1_beg: int = None, ax1_end: int = None) -> np.array:
        matrix = self.active_shops[ax0_ind]
        if ax1_beg is not None and ax1_end is not None:
            if ax1_beg == 0:
                return np.zeros(1, dtype=np.float32)
            old, new = matrix[..., :ax1_beg].sum(1), matrix[..., ax1_beg: ax1_end].sum(1)
            val = new[(old == 0) & (new > 0)].size
            return np.array([val], dtype=np.float32)
        else:
            result = np.zeros(self.month_range.size, dtype=np.float32)
            past = np.zeros(matrix.shape[0], dtype=np.int32)
            for ind in range(1, self.month_range.size):
                past += matrix[..., ind - 1]
                result[ind] = np.count_nonzero(matrix[..., ind] > past)
            return result

    # name like corresponding key of Obc.SETUP
    def shops_lost(self, ax0_ind: list[int], ax1_beg: int = None, ax1_end: int = None) -> np.array:
        matrix = self.active_shops[ax0_ind]
        if ax1_beg is not None and ax1_end is not None:
            if ax1_end == self.month_range.size - 1:
                return np.zeros(1, dtype=np.float32)
            continued, lost = matrix[..., ax1_end:].sum(1), matrix[..., ax1_beg: ax1_end].sum(1)
            val = lost[(continued == 0) & (lost > 0)].size
            return np.array([val], dtype=np.float32)
        else:
            result = np.zeros(self.month_range.size, dtype=np.float32)
            future = np.zeros(matrix.shape[0], dtype=np.int32)
            for ind in range(self.month_range.size - 2, -1, -1):
                future += matrix[..., ind + 1]
                result[ind] = np.count_nonzero(matrix[..., ind] > future)
            return result

    # name like corresponding key of Obc.SETUP
    def crt_active(self, sign_matrix: np.array, data_matrix: np.array, attr: str, result: dict[str, np.array],
                   ax1_beg: int = None, ax1_end: int = None) -> np.array:
        if ax1_beg is not None and ax1_end is not None:
            row = data_matrix[..., ax1_beg: ax1_end].sum(1)
            val = np.unique(sign_matrix[row > 0, 1]).size
            res = np.array([val], dtype=np.float32)
            result[attr] = res
        else:
            total = [0.0] * self.month_range.size
            threads = list()
            for interval in self.intervals:
                threads.append(Thread(target=_carts_active_in_thread, args=(total, interval, data_matrix, sign_matrix)))
            for thr in threads:
                thr.start()
            for thr in threads:
                thr.join()
            res = np.array(total, dtype=np.float32)
            result[attr] = res
        
    # name like corresponding key of SETUP
    def crt_new(self, sign_matrix: np.array, data_matrix: np.array, attr: str, result: dict[str, np.array],
                ax1_beg: int = None, ax1_end: int = None) -> np.array:
        if ax1_beg is not None and ax1_end is not None:
            if ax1_beg == 0:
                res = np.array([0], dtype=np.float32)
                result[attr] = res
                return
            old, new = data_matrix[..., :ax1_beg].sum(1), data_matrix[..., ax1_beg: ax1_end].sum(1)
            val = sign_matrix[(old == 0) & (new > 0), 1]
            past_active = sign_matrix[old > 0, 1]
            diff = np.setdiff1d(val, past_active).size
            res = np.array([diff], dtype=np.float32)
            result[attr] = res
        else:
            total = [0.0] * self.month_range.size
            threads = list()
            for interval in self.intervals_for_new:
                threads.append(Thread(target=_carts_new_in_thread, args=(total, interval, data_matrix, sign_matrix)))
            for thr in threads:
                thr.start()
            for thr in threads:
                thr.join()
            res = np.array(total, dtype=np.float32)
            result[attr] = res

    # name like corresponding key of SETUP
    def crt_lost(self, sign_matrix: np.array, data_matrix: np.array, attr: str, result: dict[str, np.array],
                 ax1_beg: int = None, ax1_end: int = None) -> np.array:
        if ax1_beg is not None and ax1_end is not None:
            if ax1_end == self.month_range.size:
                res = np.array([0], dtype=np.float32)
                result[attr] = res
                return
            continued, lost = data_matrix[..., ax1_end:].sum(1), data_matrix[..., ax1_beg: ax1_end].sum(1)            
            val = sign_matrix[(continued == 0) & (lost > 0), 1]
            future_active = sign_matrix[continued > 0, 1]
            diff = np.setdiff1d(val, future_active).size
            res = np.array([diff], dtype=np.float32)
            result[attr] = res
        else:
            total = [0.0] * self.month_range.size
            threads = list()
            for interval in self.intervals_for_lost:
                threads.append(Thread(target=_carts_lost_in_thread, args=(total, interval, data_matrix, sign_matrix)))
            for thr in threads:
                thr.start()
            for thr in threads:
                thr.join()
            res = np.array(total, dtype=np.float32)
            result[attr] = res

    def prime_calculate(self, attrs: list[str], ax0_ind: list[int],
                        ax1_beg: int = None, ax1_end: int = None) -> dict[str, np.array]:
        prime_attrs = set(attrs).intersection(Obc.PRIMES)
        prime_attrs.update({arg for attr in attrs for arg in Obc.SETUP[attr].fn_arg if arg in Obc.PRIMES})
        ax0_slice = Ellipsis if not ax0_ind else ax0_ind
        prime_data = dict()
        if ax1_beg is not None and ax1_end is not None:
            for attr in prime_attrs:
                matrix = getattr(self, attr)
                val = matrix[ax0_slice, ax1_beg: ax1_end].sum()
                prime_data[attr] = np.array([val], dtype=np.float32)
        else:
            for attr in prime_attrs:
                matrix = getattr(self, attr)
                prime_data[attr] = matrix[ax0_slice].sum(axis=0)
        return prime_data
    
    def set_calculate(self, for_one: list[str], attrs: list[str], ax0_ind: list[int],
                      ax1_beg: int = None, ax1_end: int = None) -> dict[str, np.array]:
        set_attrs = set(attrs).intersection(Obc.SETS)
        set_attrs.update({arg for attr in attrs for arg in Obc.SETUP[attr].fn_arg if arg in Obc.SETS})
        if ForOneSign.for_one.value in for_one:
            set_attrs.add(Obc.SHOPS_QNT)
        ax0_slice = Ellipsis if not ax0_ind else ax0_ind
        cart_attrs = set_attrs.intersection(Obc.CART_SETS)
        shop_attrs = set_attrs.difference(cart_attrs)
        sets_data = {attr: getattr(self, attr)(ax0_slice, ax1_beg, ax1_end) for attr in shop_attrs}
        if cart_attrs:
            caching_data = Caching.cache_reading(attrs=cart_attrs, indexes=ax0_ind, ax1_beg=ax1_beg, ax1_end=ax1_end)
            sets_data.update(caching_data)
            not_cat = cart_attrs.difference(set(caching_data.keys()))
            if not_cat:
                if ax0_slice != Ellipsis:
                    indexes = np.isin(self.shop_cart[..., 0], ax0_slice)
                    sign_matrix = self.shop_cart[indexes]
                    data_matrix = self.active_carts[indexes]
                else:
                    sign_matrix = self.shop_cart
                    data_matrix = self.active_carts
                threads = list()
                not_cdt = dict()
                for attr in not_cat:
                    threads.append(Thread(target=getattr(self, attr), args=(sign_matrix, data_matrix, attr, not_cdt,
                                                                            ax1_beg, ax1_end)))
                for thr in threads:
                    thr.start()
                for thr in threads:
                    thr.join()
                sets_data.update(not_cdt)
                Caching.cache_writing(data=not_cdt, indexes=ax0_ind, ax1_beg=ax1_beg, ax1_end=ax1_end)
        return sets_data
    
    def calculate_by_month(self, kit_name: str, old_name: str,
                           attrs: list[str], ax0_ind: list[int],
                           for_one: list[str], line_type: list[str]) -> list:
        data = self.prime_calculate(attrs=attrs, ax0_ind=ax0_ind)
        data.update(self.set_calculate(for_one=for_one, attrs=attrs, ax0_ind=ax0_ind))
        result = dict()
        for a in attrs:
            val = data[a] if Obc.SETUP[a].fn is None else Obc.SETUP[a].fn(*Obc.SETUP[a].fn_arg)(data)
            if ForOneSign.anyone.value in for_one:
                result[(ForOneSign.anyone.value, Obc.SETUP[a].label, a)] = val
            if ForOneSign.for_one.value in for_one:
                shops_qnt = data[Obc.SHOPS_QNT]
                if Obc.SETUP[a].for_one:
                    f_val = val
                else:
                    f_val = np.zeros(self.month_range.size, dtype=np.float32)
                    for i in range(self.month_range.size):
                        if shops_qnt[i] != 0.0:
                            f_val[i] = val[i] / shops_qnt[i]
                result[(ForOneSign.for_one.value, Obc.SETUP[a].label, a)] = f_val
        traces = list()
        if line_type == LineType.chronic.value:
            m_range = self.month_range
            for key, val in result.items():
                name = Matrix.TRACE_NAME_SEPARATOR.join((kit_name, old_name, key[0], key[1]))
                traces.append(Obc.SETUP[key[2]].plot(y=val, x=m_range, name=name))
        else:
            m_range = np.arange(1, 13, dtype=np.int8)
            for key, val in result.items():
                for num, i in enumerate(range(0, val.size, 12)):
                    year = str(self.year_range[num])
                    name = Matrix.TRACE_NAME_SEPARATOR.join((kit_name, old_name, key[0], key[1], year))
                    traces.append(Obc.SETUP[key[2]].plot(y=val[i: i + 12], x=m_range, name=name))
        return traces

    def ends_of_sales_period(self, ax0_ind: list[int]):
        sales_row = getattr(self, Obc.SAL)[ax0_ind].sum(axis=0)
        non_zero_indexes = sales_row.nonzero()[0]
        if non_zero_indexes.size == 0:
            return "", ""
        first = self.begin + np.timedelta64(non_zero_indexes[0], "M")
        last = self.begin + np.timedelta64(non_zero_indexes[-1], "M")
        if last == self.end:
            last = ""
        return first, last

    def calculate_by_period(self, attrs: list[str], ax0_ind: list[int], ax1_beg: int, ax1_end: int,
                            for_one: list[str]) -> dict[str, float]:
        data = self.prime_calculate(attrs=attrs, ax0_ind=ax0_ind, ax1_beg=ax1_beg, ax1_end=ax1_end)
        data.update(self.set_calculate(for_one=for_one, attrs=attrs, ax0_ind=ax0_ind, ax1_beg=ax1_beg, ax1_end=ax1_end))
        first_dt, last_dt = self.ends_of_sales_period(ax0_ind=ax0_ind)
        result = dict()
        for a in attrs:
            val = data[a] if Obc.SETUP[a].fn is None else Obc.SETUP[a].fn(*Obc.SETUP[a].fn_arg)(data)
            if ForOneSign.anyone.value in for_one:
                result[(ForOneSign.anyone.value, a, first_dt, last_dt)] = val[0]
            if ForOneSign.for_one.value in for_one:
                shops_qnt = data[Obc.SHOPS_QNT]
                if Obc.SETUP[a].for_one:
                    f_val = val[0]
                else:
                    f_val = val[0] / shops_qnt[0] if shops_qnt[0] != 0.0 else 0.0
                result[(ForOneSign.for_one.value, a, first_dt, last_dt)] = f_val
        return result

    def get_indexes_for_graph(self, div: list[str], reg: list[str], city: list[str],
                              tt: list[int], opt_tt: list[dict[str, int]],
                              old: list) -> dict[str, Optional[list]]:
        ind = set() if not any((div, reg, city, tt)) else (set(tt) if tt else {i for i in (r["value"] for r in opt_tt)})
        indexes = dict()
        if OldSign.anyone.value in old:
            indexes[OldSign.anyone.value] = list(ind)
        if OldSign.old_only.value in old:
            old_ind = ind.intersection(self.old_shops) if ind else self.old_shops
            indexes[OldSign.old_only.value] = list(old_ind) if old_ind else None
        return indexes

    def get_indexes_for_table(self, div: list[str], reg: list[str], city: list[str],
                              tt: list[int], opt_tt: list[dict[str, int]],
                              old: list[str], table_slice: list[str]) -> dict[str, Optional[list]]:
        ind = set() if not any((div, reg, city, tt)) else (set(tt) if tt else {i for i in (r["value"] for r in opt_tt)})
        temp = defaultdict(lambda: defaultdict(set))
        for i, sign_line in enumerate(self.signs_of_shops[1:], start=1):
            key = tuple((getattr(sign_line, slc) for slc in table_slice))
            if OldSign.anyone.value in old:
                temp[key][OldSign.anyone.value].add(i)
            if OldSign.old_only.value in old and sign_line.old_shop:
                temp[key][OldSign.old_only.value].add(i)

        result = defaultdict(lambda: defaultdict(list))
        for slc in temp.keys():
            for ok in temp[slc].keys():
                slice_ind = temp[slc][ok].intersection(ind) if ind else temp[slc][ok]
                result[slc][ok] = None if not slice_ind else list(slice_ind)
        return result


def loading_from_db(conn: sqlite3.connect, begin: str, end: str, threads_qnt: int = 0):
    max_shop_id = conn.execute("SELECT MAX(shop_id) FROM tt").fetchone()[0]
    row_count = 0
    for _ in conn.execute("SELECT shop_id, cart FROM carts GROUP BY shop_id, cart"):
        row_count += 1
    matrix = Matrix(max_shop_id=max_shop_id, cart_rows=row_count, begin=begin, end=end, threads_qnt=threads_qnt)
    request = f"SELECT date_month, shop_id, {', '.join(Obc.PRIMES)}  FROM data"
    for ln in conn.execute(request):
        axis0_ind = ln[1]
        axis1_ind = int(np.datetime64(ln[0], "M") - matrix.begin)
        numerics = {at: ln[at] for at in Obc.PRIMES}
        for key, val in numerics.items():
            getattr(matrix, key)[axis0_ind, axis1_ind] = val
        if numerics[Obc.SAL] > 0.0:
            matrix.active_shops[axis0_ind, axis1_ind] = 1
    lag_array = getattr(matrix, Obc.SAL_NB).sum(axis=0).nonzero()[0]
    if lag_array.size > 0:
        matrix.lagging_end = matrix.begin + np.timedelta64(lag_array[-1], "M")
    for ln in conn.execute("SELECT div_name, reg_name, city_name, shop_name, shop_id, old_shop FROM tt"):
        axis0_ind = ln[4]
        matrix.signs_of_shops[axis0_ind] = Matrix.ShopReq(*ln[:4], ln[5])
        if ln[5] == 1:
            matrix.old_shops.add(ln[4])
    last, ax0_ind = None, -1
    request = """SELECT shop_id, cart, date_month FROM carts ORDER BY shop_id, cart, date_month"""
    for num, ln in enumerate(conn.execute(request)):
        ax1_ind = int(np.datetime64(ln[2], "M") - matrix.begin)
        if ln[:2] != last:
            ax0_ind += 1
            matrix.shop_cart[ax0_ind][0] = ln[0]
            matrix.shop_cart[ax0_ind][1] = ln[1]
        matrix.active_carts[ax0_ind, ax1_ind] = 1
        last = ln[:2]
    return matrix
