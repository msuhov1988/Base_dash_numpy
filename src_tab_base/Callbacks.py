from . import CallbacksSupport as Cbs
from dash import dcc
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate


def base_register_callbacks(app, glob_object, glob_refers, glob_drop_shops):
    @app.callback(
        Output("base_sales_graph", "figure"),
        Output("base_button_graph", "n_clicks"),
        Output("base_graph_loading_output", "children"),
        Input("base_divisions", "value"),
        Input("base_regions", "value"),
        Input("base_cities", "value"),
        Input("base_shops", "value"),
        Input("base_shops", "options"),
        Input("base_divisions_compare", "value"),
        Input("base_regions_compare", "value"),
        Input("base_cities_compare", "value"),
        Input("base_shops_compare", "value"),
        Input("base_shops_compare", "options"),
        Input("compare_activate", "value"),
        Input("base_sales_checklist", "value"),
        Input("base_one_checklist", "value"),
        Input("base_dtt_checklist", "value"),
        Input("base_graph_radio", "value"))
    def base_graph_update(divs, regs, cities, shops, shops_options,
                          divs_compare, regs_compare, cities_compare, shops_compare, shops_compare_options,
                          cmp_activate, attributes, ones, olds, line_type):
        figure = Cbs.graph_update(obj=glob_object,
                                  divs=divs, regs=regs, cities=cities, shops=shops, opt_shops=shops_options,
                                  divs_cmp=divs_compare, regs_cmp=regs_compare, cities_cmp=cities_compare,
                                  shops_cmp=shops_compare, opt_shops_cmp=shops_compare_options,
                                  cmp_activate=cmp_activate, attributes=attributes,
                                  for_one=ones, old=olds, line_type=line_type)
        return figure, None, []

    @app.callback(
        Output('base_graph_download', "data"),
        Output("base_graph_loading_output_file", "children"),
        Input("base_divisions", "value"),
        Input("base_regions", "value"),
        Input("base_cities", "value"),
        Input("base_shops", "value"),
        Input("base_shops", "options"),
        Input("base_divisions_compare", "value"),
        Input("base_regions_compare", "value"),
        Input("base_cities_compare", "value"),
        Input("base_shops_compare", "value"),
        Input("base_shops_compare", "options"),
        Input("compare_activate", "value"),
        Input("base_sales_checklist", "value"),
        Input("base_one_checklist", "value"),
        Input("base_dtt_checklist", "value"),
        Input("base_graph_radio", "value"),
        Input("base_button_graph", "n_clicks"))
    def base_graph_download(divs, regs, cities, shops, shops_options,
                            divs_compare, regs_compare, cities_compare, shops_compare, shops_compare_options,
                            cmp_activate, attributes, ones, olds, line_type, n_clicks):
        if n_clicks is not None:
            file = Cbs.graph_load(obj=glob_object,
                                  divs=divs, regs=regs, cities=cities, tt=shops, opt_tt=shops_options,
                                  divs_cmp=divs_compare, regs_cmp=regs_compare, cities_cmp=cities_compare,
                                  tt_cmp=shops_compare, opt_tt_cmp=shops_compare_options,
                                  cmp_activate=cmp_activate, attributes=attributes,
                                  for_one=ones, old=olds, line_type=line_type)
            return dcc.send_file(file), []
        else:
            raise PreventUpdate

    @app.callback(
        Output('base_table', "children"),
        Output('base_button_table', 'n_clicks'),
        Output('base_table_loading_output', 'children'),
        Output('base_table_message', 'children'),
        Input("base_date_range", "start_date"),
        Input("base_date_range", "end_date"),
        Input("base_date_range_compare", "start_date"),
        Input("base_date_range_compare", "end_date"),
        Input("base_table_divisions", "value"),
        Input("base_table_regions", "value"),
        Input("base_table_cities", "value"),
        Input("base_table_shops", "value"),
        Input("base_table_shops", "options"),
        Input("base_table_slice_checklist", "value"),
        Input("base_table_one_checklist", "value"),
        Input("base_table_dtt_checklist", "value"),
        Input("base_table_sales_references", "value"))
    def base_table_update(begin, end, begin_compare, end_compare, divs, regs, cities, shops, shops_options,
                          table_slices, ones, olds, attributes):
        table, message = Cbs.table_update(obj=glob_object, div=divs, reg=regs, city=cities, tt=shops,
                                          opt_tt=shops_options, attributes=attributes, for_one=ones, old=olds,
                                          table_slice=table_slices, begin=begin, end=end,
                                          begin_compare=begin_compare, end_compare=end_compare, file=False)
        return table, None, [], message

    @app.callback(
        Output('base_table_download', "data"),
        Output('base_table_file_loading_output', 'children'),
        Input("base_date_range", "start_date"),
        Input("base_date_range", "end_date"),
        Input("base_date_range_compare", "start_date"),
        Input("base_date_range_compare", "end_date"),
        Input("base_table_divisions", "value"),
        Input("base_table_regions", "value"),
        Input("base_table_cities", "value"),
        Input("base_table_shops", "value"),
        Input("base_table_shops", "options"),
        Input("base_table_slice_checklist", "value"),
        Input("base_table_one_checklist", "value"),
        Input("base_table_dtt_checklist", "value"),
        Input("base_table_sales_references", "value"),
        Input('base_button_table', 'n_clicks'))
    def base_table_download(begin, end, begin_compare, end_compare, divs, regs, cities, shops, shops_options,
                            table_slices, ones, olds, attributes, n_clicks):
        if n_clicks is not None:
            file = Cbs.table_update(obj=glob_object, div=divs, reg=regs, city=cities, tt=shops, opt_tt=shops_options,
                                    attributes=attributes, for_one=ones, old=olds, table_slice=table_slices,
                                    begin=begin, end=end,
                                    begin_compare=begin_compare, end_compare=end_compare, file=True)
        else:
            raise PreventUpdate
        return dcc.send_file(file), []

    @app.callback(
        Output("base_regions", "options"),
        Output("base_regions", "value"),
        Input("base_divisions", "value"))
    def base_div_input(ad):
        temp = list({i.region for i in glob_refers if (i.division in ad if ad else True)})
        temp.sort()
        return [{"label": i, "value": i} for i in temp], []

    @app.callback(
        Output("base_cities", "options"),
        Output("base_cities", "value"),
        Input("base_divisions", "value"),
        Input("base_regions", "value"))
    def base_div_region_input(ad, ar):
        temp = list({i.city for i in glob_refers if (i.division in ad if ad else True) and
                     (i.region in ar if ar else True)})
        temp.sort()
        return [{"label": i, "value": i} for i in temp], []

    @app.callback(
        Output("base_shops", "options"),
        Output("base_shops", "value"),
        Input("base_divisions", "value"),
        Input("base_regions", "value"),
        Input("base_cities", "value"))
    def base_div_region_city_input(ad, ar, ac):
        temp = list({i.shop_name for i in glob_refers if (i.division in ad if ad else True) and
                     (i.region in ar if ar else True) and (i.city in ac if ac else True)})
        temp.sort()
        return [{"label": name, "value": glob_drop_shops[name]} for name in temp], []

    @app.callback(
        Output("base_divisions_compare", "disabled"),
        Output("base_regions_compare", "disabled"),
        Output("base_cities_compare", "disabled"),
        Output("base_shops_compare", "disabled"),
        Input("compare_activate", "value"))
    def compare_activate(val):
        if val:
            return False, False, False, False
        else:
            return True, True, True, True

    @app.callback(
        Output("base_regions_compare", "options"),
        Output("base_regions_compare", "value"),
        Input("base_divisions_compare", "value"))
    def base_compare_div_input(ad):
        temp = list({i.region for i in glob_refers if (i.division in ad if ad else True)})
        temp.sort()
        return [{"label": i, "value": i} for i in temp], []

    @app.callback(
        Output("base_cities_compare", "options"),
        Output("base_cities_compare", "value"),
        Input("base_divisions_compare", "value"),
        Input("base_regions_compare", "value"))
    def base_compare_div_region_input(ad, ar):
        temp = list({i.city for i in glob_refers if (i.division in ad if ad else True) and
                     (i.region in ar if ar else True)})
        temp.sort()
        return [{"label": i, "value": i} for i in temp], []

    @app.callback(
        Output("base_shops_compare", "options"),
        Output("base_shops_compare", "value"),
        Input("base_divisions_compare", "value"),
        Input("base_regions_compare", "value"),
        Input("base_cities_compare", "value"))
    def base_compare_div_region_city_input(ad, ar, ac):
        temp = list({i.shop_name for i in glob_refers if (i.division in ad if ad else True) and
                     (i.region in ar if ar else True) and (i.city in ac if ac else True)})
        temp.sort()
        return [{"label": name, "value": glob_drop_shops[name]} for name in temp], []

    @app.callback(
        Output("base_date_range_compare", "disabled"),
        Output("base_date_range_compare", "start_date"),
        Output("base_date_range_compare", "end_date"),
        Input("table_compare_activate", "value"))
    def table_compare_activate(val):
        if val:
            return False, None, None
        else:
            return True, None, None

    @app.callback(
        Output("base_table_regions", "options"),
        Output("base_table_regions", "value"),
        Input("base_table_divisions", "value"))
    def base_table_div_input(ad):
        temp = list({i.region for i in glob_refers if (i.division in ad if ad else True)})
        temp.sort()
        return [{"label": i, "value": i} for i in temp], []

    @app.callback(
        Output("base_table_cities", "options"),
        Output("base_table_cities", "value"),
        Input("base_table_divisions", "value"),
        Input("base_table_regions", "value"))
    def base_table_div_region_input(ad, ar):
        temp = list({i.city for i in glob_refers if (i.division in ad if ad else True) and
                     (i.region in ar if ar else True)})
        temp.sort()
        return [{"label": i, "value": i} for i in temp], []

    @app.callback(
        Output("base_table_shops", "options"),
        Output("base_table_shops", "value"),
        Input("base_table_divisions", "value"),
        Input("base_table_regions", "value"),
        Input("base_table_cities", "value"))
    def base_table_div_region_city_input(ad, ar, ac):
        temp = list({i.shop_name for i in glob_refers if (i.division in ad if ad else True) and
                     (i.region in ar if ar else True) and (i.city in ac if ac else True)})
        temp.sort()
        return [{"label": name, "value": glob_drop_shops[name]} for name in temp], []
