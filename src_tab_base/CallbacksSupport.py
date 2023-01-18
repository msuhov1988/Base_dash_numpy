from . import Basics as Bs
from . import ObjectConstants as Obc
import numpy as np
from openpyxl import Workbook
from plotly.graph_objects import Figure, Layout
from dash import dash_table
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme
import os.path
from os import getpid
from typing import Optional
from collections import defaultdict
from time import time


KITS = ("ОСН-Й", "СРАВН")
ENDS_OF_SALES = ("НАЧАЛО ПРОДАЖ", "КОНЕЦ ПРОДАЖ")
PERIOD_TRUNC_WARNING = ("ВНИМАНИЕ! Период(ы) урезан(ы) из-за показателей: выручка без бонусов, себестоимость, списания."
                        " Или показателей, зависящих от перечисленных.")
PERIOD_INCORRECT_SET = ("ВНИМАНИЕ! Период(ы) установлен(ы) не корректно."
                        " Или для него(них) отсутствуют данные в базе по показателям:"
                        " выручка без бонусов, себестоимость, списания или(и) их производным.")


def graph_update(obj, divs: list, regs: list, cities: list, shops: list, opt_shops: list[dict[str, int]],
                 divs_cmp: list, regs_cmp: list, cities_cmp: list, shops_cmp: list, opt_shops_cmp: list[dict[str, int]],
                 cmp_activate: list, attributes: list, for_one: list, old: list, line_type: Bs.LineType):
    traces = list()
    indexes = obj.get_indexes_for_graph(div=divs, reg=regs, city=cities, tt=shops, opt_tt=opt_shops, old=old)
    for ok, ixs in indexes.items():
        if ixs is not None:
            kit_of_trc = obj.calculate_by_month(kit_name=KITS[0], old_name=ok, attrs=attributes, ax0_ind=ixs,
                                                for_one=for_one, line_type=line_type)
            traces.extend(kit_of_trc)
    if cmp_activate:
        indexes_cmp = obj.get_indexes_for_graph(div=divs_cmp, reg=regs_cmp, city=cities_cmp, tt=shops_cmp,
                                                opt_tt=opt_shops_cmp, old=old)
        for ok, ixs in indexes_cmp.items():
            if ixs is not None:
                kit_of_trc = obj.calculate_by_month(kit_name=KITS[1], old_name=ok, attrs=attributes, ax0_ind=ixs,
                                                    for_one=for_one, line_type=line_type)
                traces.extend(kit_of_trc)

    layout_dict = dict()
    if traces:
        means = {t.name: np.mean(t.y, where=t.y != 0.0) if np.any(t.y) else 0.0 for t in traces}
        traces.sort(key=lambda t: means[t.name])
        ind = 1
        base_mean, traces[0].yaxis = means[traces[0].name], "y" + str(ind)
        for i in range(1, len(traces)):
            current_mean = means[traces[i].name]
            if (base_mean <= 1.0 and current_mean <= 1.0) or (current_mean <= base_mean * 5):
                traces[i].yaxis = "y" + str(ind)
            else:
                ind += 1
                traces[i].yaxis, base_mean = "y" + str(ind), current_mean
        traces.sort(key=lambda t: t.name)
        for trace in traces:
            temp = trace.y.copy()
            temp[temp == 0.0] = np.nan
            trace.y = temp
        for j in range(1, ind + 1):
            if j == 1:
                layout_dict["yaxis"] = dict()
            elif j % 2 == 1:
                layout_dict["yaxis" + str(j)] = dict(overlaying='y', side='left', anchor='free', position=0.05,
                                                     gridcolor="#212529")
            else:
                layout_dict["yaxis" + str(j)] = dict(overlaying='y', side='right', anchor='free', position=0.95,
                                                     gridcolor="#212529")
    figure = Figure(data=traces, layout=Layout(**layout_dict))
    figure.update_layout(plot_bgcolor="#222", paper_bgcolor="#222",
                         yaxis={"gridcolor": "#212529"}, xaxis={"gridcolor": "#212529"},
                         legend={"font": {"color": "#fff"}})
    return figure


def graph_load(obj, divs: list, regs: list, cities: list, tt: list, opt_tt: list[dict[str, int]],
               divs_cmp: list, regs_cmp: list, cities_cmp: list, tt_cmp: list, opt_tt_cmp: list[dict[str, int]],
               cmp_activate: list, attributes: list, for_one: list, old: list, line_type: Bs.LineType):
    wb = Workbook()
    ws = wb.active
    title = ["Дивизион", "Регион", "Нас. пункт", "Магазин", "Срез", "ДТТ", "ВСЕ / 1ТТ", "Тип данных"]
    if line_type == Bs.LineType.chronic.value:
        title.extend([str(dt) for dt in obj.month_range])
    else:
        title.append("Год")
        title.extend([f"Месяц {i}" for i in range(1, 13)])
    ws.append(title)

    dv = " ".join(divs) if divs else 'ИТОГО'
    rg = " ".join(regs) if regs else 'ИТОГО'
    ct = " ".join(cities) if cities else 'ИТОГО'
    sh = " ".join([rw.shop_name for i, rw in enumerate(obj.signs_of_shops) if i in tt]) if tt else 'ИТОГО'
    indexes = obj.get_indexes_for_graph(div=divs, reg=regs, city=cities, tt=tt, opt_tt=opt_tt, old=old)
    for ok, ixs in indexes.items():
        if ixs is not None:
            kit_of_trc = obj.calculate_by_month(kit_name=KITS[0], old_name=ok, attrs=attributes, ax0_ind=ixs,
                                                for_one=for_one, line_type=line_type)
            for trc in kit_of_trc:
                line = [dv, rg, ct, sh]
                line.extend(trc.name.split(obj.TRACE_NAME_SEPARATOR))
                line.extend(trc.y)
                ws.append(line)
    if cmp_activate:
        dv_cp = " ".join(divs_cmp) if divs_cmp else 'ИТОГО'
        rg_cp = " ".join(regs_cmp) if regs_cmp else 'ИТОГО'
        ct_cp = " ".join(cities_cmp) if cities_cmp else 'ИТОГО'
        sh_cp = " ".join([rw.shop_name for i, rw in enumerate(obj.signs_of_shops) if i in tt_cmp]) if tt_cmp\
            else 'ИТОГО'
        indexes_cmp = obj.get_indexes_for_graph(div=divs_cmp, reg=regs_cmp, city=cities_cmp, tt=tt_cmp,
                                                opt_tt=opt_tt_cmp, old=old)
        for ok, ixs in indexes_cmp.items():
            if ixs is not None:
                kit_of_trc = obj.calculate_by_month(kit_name=KITS[1], old_name=ok, attrs=attributes, ax0_ind=ixs,
                                                    for_one=for_one, line_type=line_type)
                for trc in kit_of_trc:
                    line = [dv_cp, rg_cp, ct_cp, sh_cp]
                    line.extend(trc.name.split(obj.TRACE_NAME_SEPARATOR))
                    line.extend(trc.y)
                    ws.append(line)

    base_folder = os.path.split(os.path.dirname(__file__))[0]
    file_name = f"_file_exports\\graph_data_{getpid()}.xlsx"
    out_file = os.path.join(base_folder, file_name)
    wb.save(out_file)
    wb.close()
    return out_file


def _table_columns(periods: list[tuple[np.datetime64]], table_slice: list,
                   for_one: list, old: list, attributes: list) -> list[dict]:
    columns = [dict(name=Bs.TableSlices[slc], id=slc) for slc in table_slice]
    if Bs.OldSign.old_only.value in old:
        columns.append(dict(name=Bs.OldSign.old_only.value, id=Bs.OldSign.old_only.value))
    if Bs.ForOneSign.for_one.value in for_one:
        columns.append(dict(name=Bs.ForOneSign.for_one.value, id=Bs.ForOneSign.for_one.value))
    columns.extend([dict(name=e, id=e) for e in ENDS_OF_SALES])
    percentage = FormatTemplate.percentage(2)
    for attr in attributes:
        label, percent = Obc.SETUP[attr].label, Obc.SETUP[attr].percent_format
        for bg, en in periods:
            per = "-".join((bg.item().strftime("%m.%y"), en.item().strftime("%m.%y")))
            col_id = f"{label} {per}"
            if percent:
                columns.append(dict(name=col_id, id=col_id, type='numeric', format=percentage))
            else:
                columns.append(dict(name=col_id, id=col_id, type='numeric',
                                    format=Format(precision=2, scheme=Scheme.fixed).group(True).group_delimiter(" ")))
        if len(periods) > 1:
            col_id = f"{label} РОСТ %"
            columns.append(dict(name=col_id, id=col_id, type='numeric', format=percentage))
    return columns


def table_update(obj, div: list, reg: list, city: list, tt: list, opt_tt: list[dict[str, int]],
                 attributes: list, for_one: list, old: list, table_slice: list,
                 begin: str, end: str, begin_compare: Optional[str], end_compare: Optional[str], file=False):
    lagging = set(attributes).intersection(Obc.LAGGING)
    lagging.update({arg for attr in attributes for arg in Obc.SETUP[attr].fn_arg if arg in Obc.LAGGING})
    trunc_of_period = False
    begin, end = np.datetime64(begin, "M"), np.datetime64(end, "M")
    if lagging and end > obj.lagging_end:
        end = obj.lagging_end
        trunc_of_period = True
    periods = [(begin, end)] if begin <= end else []
    if all((begin_compare, end_compare)):
        begin_compare, end_compare = np.datetime64(begin_compare, "M"), np.datetime64(end_compare, "M")
        if lagging and end_compare > obj.lagging_end:
            end_compare = obj.lagging_end
            trunc_of_period = True
        if begin_compare <= end_compare:
            periods.insert(0, (begin_compare, end_compare))
    if not periods:
        return [], PERIOD_INCORRECT_SET
    periods_quantity = len(periods)
    columns = _table_columns(periods=periods, table_slice=table_slice, for_one=for_one, old=old, attributes=attributes)

    indexes = obj.get_indexes_for_table(div=div, reg=reg, city=city, tt=tt, opt_tt=opt_tt,
                                        old=old, table_slice=table_slice)
    rows = list()
    temp, grow = dict(), defaultdict(lambda: [0.0, 0.0])
    for key in indexes.keys():
        for ok, ixs in indexes[key].items():
            if ixs is None:
                continue
            base_row = {slc: key[i] for i, slc in enumerate(table_slice)}
            base_row[ok] = ok
            for num, (bg, en) in enumerate(periods):
                axis1_beg, axis1_end = int(bg - obj.begin), int(en - obj.begin) + 1
                per = "-".join((bg.item().strftime("%m.%y"), en.item().strftime("%m.%y")))
                data = obj.calculate_by_period(attrs=attributes, ax0_ind=ixs, ax1_beg=axis1_beg, ax1_end=axis1_end,
                                               for_one=for_one)
                for ky, val in data.items():
                    one_tt = ky[0]
                    try:
                        row = temp[one_tt]
                    except KeyError:
                        temp[one_tt] = base_row.copy()
                        row = temp[one_tt]
                        row[one_tt] = one_tt
                        row[ENDS_OF_SALES[0]] = ky[2]
                        row[ENDS_OF_SALES[1]] = ky[3]
                    label, prc = Obc.SETUP[ky[1]].label, Obc.SETUP[ky[1]].percent_format
                    r_val = round(val, 4) if prc else (round(val, 1) if val < 100.0 else round(val, 0))
                    row[f"{label} {per}"] = r_val
                    if periods_quantity > 1:
                        gky = f"{one_tt}_{label}"
                        grow[gky][num] = val
                        if num == periods_quantity - 1:
                            if prc:
                                row[f"{label} РОСТ %"] = grow[gky][-1] - grow[gky][0]
                            else:
                                if grow[gky][0] != 0.0:
                                    row[f"{label} РОСТ %"] = grow[gky][-1] / grow[gky][0] - 1
            rows.extend(temp.values())
            temp.clear()
            grow.clear()
    message = ""
    if trunc_of_period:
        message = PERIOD_TRUNC_WARNING
    if file:
        wb = Workbook()
        ws = wb.active
        ws.append([message])
        ws.append([""])
        ws.append([col["name"] for col in columns])
        temp = [col["id"] for col in columns]
        for row in rows:
            line = []
            for tmp in temp:
                try:
                    line.append(str(row[tmp]) if tmp in ENDS_OF_SALES else row[tmp])
                except KeyError:
                    line.append("")
            ws.append(line)
        base_folder = os.path.split(os.path.dirname(__file__))[0]
        file_name = f"_file_exports\\table_data_{getpid()}.xlsx"
        out_file = os.path.join(base_folder, file_name)
        wb.save(out_file)
        wb.close()
        return out_file

    cell_condition = ([{'if': {'column_id': "real_end"},
                        'border-right': '5px double black'}])
    cell_condition.extend([{'if': {'column_id': c['id']},
                            'border-right': '5px double black'} for c in columns if "РОСТ" in c['id']])
    data_condition = [{
                       "if": {'filter_query': "{{{0}}} >= 0.1".format(c['id']),
                              'column_id': c['id']},
                       'color': '#77b300'
                       } for c in columns if "РОСТ" in c['id']]
    data_condition.extend([{
                            "if": {'filter_query': "{{{0}}} >= 0.0 and {{{0}}} < 0.1".format(c['id']),
                                   'column_id': c['id']},
                            'color': '#f80'
                            } for c in columns if "РОСТ" in c['id']])
    data_condition.extend([{
                            "if": {'filter_query': "{{{0}}} < 0.0".format(c['id']),
                                   'column_id': c['id']},
                            'color': '#c00'
                            } for c in columns if "РОСТ" in c['id']])

    table = dash_table.DataTable(
        style_header={'whiteSpace': 'normal', 'height': 'auto',
                      'backgroundColor': '#222', 'color': 'white',
                      'border-bottom': '5px double black', 'fontWeight': 'bold'},
        style_cell={'backgroundColor': '#222', "color": "#adafae", 'fontWeight': 'bold', 'border': '2px double black'},
        cell_selectable=False,
        columns=columns,
        data=rows,
        page_size=24,
        style_table={'overflowX': 'auto'},
        sort_action="native",
        sort_mode="multi",
        style_header_conditional=cell_condition,
        style_cell_conditional=cell_condition,
        style_data_conditional=data_condition)
    return table, message
