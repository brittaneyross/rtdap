#libraries
import pandas as pd
import numpy as np
import random
from datetime import datetime, date

#bokeh
from bokeh.io import show, output_notebook, push_notebook
from bokeh.plotting import figure

from bokeh.layouts import layout, column, row, WidgetBox
from bokeh.models import CustomJS, Panel, Spacer, HoverTool, LogColorMapper, ColumnDataSource,FactorRange, RangeSlider,\
                         NumeralTickFormatter
from bokeh.models.widgets import Div, Tabs, Paragraph, Dropdown, Button, PreText, Toggle, Select,\
                                DatePicker,DateRangeSlider

from bokeh.tile_providers import STAMEN_TERRAIN_RETINA,CARTODBPOSITRON_RETINA

#mapping
from shapely.geometry import Polygon, Point, MultiPoint, MultiPolygon
import geopandas as gpd

from bokeh.transform import factor_cmap
from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
from bokeh.core.properties import value

#color
from bokeh.palettes import Spectral6

from bokeh.io import curdoc

#table
vds_table = pd.read_csv(r'C:\Users\bross\Documents\GitHub\rtdap\rtdap_prototype\data\vds_table_2008_2018.csv')

#
vds_table['corridor'] = vds_table['corridor'].fillna('N/A')
vds_table['corridor'] = np.where(vds_table['corridor'] == '0', 'N/A',vds_table['corridor'])

vds_table['hour'] = vds_table['hour'].replace([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],
                                              [1,1,1,1,1,1,2,3,3,4, 5, 5, 5, 5, 6, 6, 7, 7, 8, 8, 1, 1, 1, 1])

vds_table['date'] = (vds_table.year.astype(str)+"-"+vds_table.month.astype(str)+"-"+vds_table.day.astype(str)).apply(str)

vds_table['date'] = pd.to_datetime(vds_table['date'],format='%Y-%m-%d')

vds_table['dow'] = vds_table['dow'].replace([1,2,3,4,5],['Monday','Tuesday','Wednesday','Thursday','Friday'])

vds_table.loc[vds_table['date'] > '2017-04-03']
#Selection Tab Functions

def make_base_map(tile_map=CARTODBPOSITRON_RETINA,map_width=800,map_height=500, xaxis=None, yaxis=None,
                xrange=(-9990000,-9619944), yrange=(5011119,5310000),plot_tools="pan,wheel_zoom,reset,save"):

    p = figure(tools=plot_tools, width=map_width,height=map_height, x_axis_location=xaxis, y_axis_location=yaxis,
                x_range=xrange, y_range=yrange)

    p.grid.grid_line_color = None
    #p.background_fill_color = None
    p.background_fill_alpha = 0.5
    p.border_fill_color = None

    p.add_tile(tile_map)

    return p

def rtdap_avg(df,corr,value):

    """
    returns mean for specificed attribute by highway corridor

    Keyword arguments:
    df -- dataframe to filter by corridor and calculate mean
    corr -- corridor name
    value -- dataframe column name to calculate mean
    """

    df_corr = df.loc[df['corridor'] == corr]
    mean_value = df_corr[value].mean()

    return mean_value

def filter_selection(df, corr, date_s, date_e, weekday, tod):

    """
    returns subset of data based on corridor and time selections

    Keyword arguments:
    df -- dataframe to filter by corridor and time selections
    corr -- corridor name
    date_s -- start date
    date_e -- end date
    weekday -- day of week (Monday - Friday)
    tod -- time of day (8 tod time periods)
    """

    tod_start = tod[0]
    tod_end = tod[1]
    date_start = datetime.strptime(date_s, '%Y-%m-%d')
    date_end = datetime.strptime(date_e, '%Y-%m-%d')

    if weekday == 'All':
        weekday = df['dow'].drop_duplicates().values.tolist()
    else:
        weekday = [weekday]

    select_df = df.loc[(df['corridor'] == corr) &\
                       (df['date']>=date_start) & (df['date']<=date_end) &\
                       (df['dow'].isin(weekday)) &\
                       (df['hour']>=tod_start) & (df['hour']<=tod_end)]

    return select_df

def summarize_metrics(df, corr, group, avg, select, label, missing):

    """
    return a summary of frequency, mean, mean difference, and count of missing values

    Keyword arguments:
    df -- dataframe to summarize
    corr -- corridor name
    group -- dataframe column name used to group and summarize data
    avg -- mean value derived from rtdap_avg(), used calculate mean diff
    select -- dateframe column name to calculate mean
    label -- name for values being calculate (ie Speed, Volumne, Time etc)
    missing -- dataframe column name of missing values
    """

    df['freq'] = 1
    df_groupby = df.groupby(group).agg({'freq':'count',
                                    select:np.mean,
                                    missing:sum}).reset_index()

    df_groupby.loc[:,'Mean Diff'] = (avg - df_groupby[select])/df_groupby[select]
    df_groupby.loc[:, group] = label
    df_groupby.columns = [corr, 'Frequency','Mean', 'Missing Values','Mean Diff']
    df_groupby = df_groupby.set_index(corr)

    return df_groupby[['Frequency','Mean','Mean Diff','Missing Values']]

def vbar_chart(full_df, df):
    """
    returns bokeh horizontal barchart representing mean % diff

    Keyword arguments:
    df -- dataframe to derive content of barchart
    col -- column name for values to diplay in graph
    """
    df_avg = full_df.groupby('FieldDeviceID').agg({'avgSpeed':np.mean})

    df_select= df.groupby('FieldDeviceID').agg({'avgSpeed':np.mean})
    df_select.columns = ['speed']

    diff = df_avg.merge(df_select,how='left',left_index=True, right_index=True).fillna(0)
    diff_no_zero = diff.loc[(diff['avgSpeed'] > 0 )& (diff['speed'] > 0)]
    diff_no_zero['speed_difference'] = diff_no_zero['avgSpeed'] - diff_no_zero['speed']
    diff_no_zero = diff_no_zero.reset_index()

    diff_no_zero['bins'] = pd.cut(diff_no_zero['speed_difference'],bins=list(range(-20,22)),
                                 labels = list(range(-20,22))[:-1])

    source = ColumnDataSource(data = diff_no_zero.groupby('bins').agg({'speed_difference':'count'}).reset_index())

    p = figure(plot_width=1000, plot_height=150, title="Speed Difference Distribution")

    p.vbar(x='bins' , top='speed_difference', width=1, color='navy', alpha=0.5, source = source)

    #p.yaxis.visible = False
    #p.xaxis.formatter = NumeralTickFormatter(format="0.f%")
    p.xgrid.visible = False
    p.ygrid.visible = False
    #p.background_fill_color = None
    p.background_fill_alpha = 0.5
    p.border_fill_color = None

    return p

def hbar_chart(df,col):
    """
    returns bokeh horizontal barchart representing mean % diff

    Keyword arguments:
    df -- dataframe to derive content of barchart
    col -- column name for values to diplay in graph
    """
    df_src = df[[col]]
    df_src['type'] = df_src.index
    df_src['order'] = 0

    df_src['order'] = np.where(df_src.index =='Speed',2,df_src['order'])
    df_src['order'] = np.where(df_src.index =='Occupancy',1,df_src['order'])
    df_src['order'] = np.where(df_src.index =='Volume',0,df_src['order'])
    df_src['color'] = '#C0C0C0'
    df_src['color'] = np.where(df_src['Mean Diff'] < -.05, '#FF0000', df_src['color'])
    df_src['color'] = np.where(df_src['Mean Diff'] > .05, '#008000', df_src['color'])
    source = ColumnDataSource(data = df_src.sort_values(by='order'))

    hover = HoverTool(
            tooltips=[
                ("Corridor Attribute", "@type"),
                ("% Difference", "@{%s}" % (col) + '{%0.2f}'),
            ]
        )
    tools = ['reset','save',hover]
    p = figure(plot_width=400, plot_height=175, toolbar_location="above",
               title = 'Mean Difference', tools = tools)

    p.hbar(y='order', height=0.5, left=0,fill_color ='color',line_color=None,
           right=col, color="navy", source = source)

    p.yaxis.visible = False
    p.xaxis.formatter = NumeralTickFormatter(format="0.f%")
    p.xgrid.visible = False
    p.ygrid.visible = False
    #p.background_fill_color = None
    p.background_fill_alpha = 0.5
    p.border_fill_color = None

    return source, p


def scatter_plot(title_text):
    rng = np.random.RandomState(0)
    x = rng.randn(100)
    y = rng.randn(100)

    source = ColumnDataSource(
            data=dict(
                x=rng.randn(100),
                y=rng.randn(100),
                desc=['A', 'b', 'C', 'd', 'E']*20,
            )
        )

    hover = HoverTool(
            tooltips=[
                ("index", "$index"),
                ("(x,y)", "($x, $y)"),
                ("desc", "@desc"),
            ]
        )

    p = figure(plot_width=300, plot_height=250, tools=[hover, 'box_select'],
               title=title_text)

    p.circle('x', 'y', size=5, source=source)
    #p.background_fill_color = None
    p.background_fill_alpha = 0.5
    p.border_fill_color = None

    return p


#side panel and view
def selection_tab(rtdap_data):

    """
    return selection tab contents

    Keyword arguments:
    rtdap_data - dataframe containing rtdap vds detail data
    """

    #-----------------------------------------------------------------------------------------------------------------
    #submit_selection -- Data Selection Update Function

    def submit_selection():

        """
        python callback to update table and visual content based on
        user selections in the data review panel
        """

        avgs_speed = rtdap_avg(rtdap_data, corridor_select.value,'avgSpeed')
        avgs_occ = rtdap_avg(rtdap_data, corridor_select.value,'avgOccupancy')
        avgs_volume = rtdap_avg(rtdap_data, corridor_select.value,'avgVolume')

        filtered_data = filter_selection(rtdap_data, corridor_select.value,
                                         str(date_picker_start.value),
                                         str(date_picker_end.value),
                                         day_of_week.value,
                                         time_of_day.value)

        speed = summarize_metrics(filtered_data, corridor_select.value, 'corridor',avgs_speed,'avgSpeed',
                                  'Speed','missing_speed')
        occ = summarize_metrics(filtered_data, corridor_select.value, 'corridor',avgs_occ,'avgOccupancy',
                                'Occupancy', 'missing_occ')
        volume = summarize_metrics(filtered_data, corridor_select.value, 'corridor',avgs_volume,'avgVolume',
                                   'Volume', 'missing_vol')

        summary_df = speed.append(occ)
        summary_df = summary_df.append(volume)

        summary_title.text = "<h1>"+corridor_select.value+" Summary</h1>"

        summary_df_tbl = summary_df.copy()
        summary_df_tbl['Mean Diff'] = summary_df_tbl['Mean Diff'] * 100
        summary_df_tbl = summary_df_tbl.reset_index()
        summary_table.text = str(summary_df_tbl.fillna(0).to_html(index=False,
                                                        formatters = [str,'{:20,}'.format,
                                                        '{:20,.1f}'.format,'{:20,.1f}%'.format,
                                                        '{:20,}'.format],classes=[ "w3-table" , "w3-hoverable","w3-small"]))
        if len(summary_df) > 0:
            new_df = summary_df.fillna(0)
            bar_viz_new = hbar_chart(new_df,'Mean Diff')[0]
            bar_viz_src.data.update(bar_viz_new.data)
    #-----------------------------------------------------------------------------------------------------------------
    #Data Review Panel

    panel_title = Div(text="Data Review", css_classes = ["panel-title","text-center"])
    panel_text = Div(text="""Lorem Ipsum is simply dummy text of the printing and typesetting industry.
           Lorem Ipsum has been the industry's standard dummy text ever since the 1500s,
           when an unknown printer took a galley of type and scrambled it to make a type
           specimen book.""", css_classes = ["panel-content"])

    #Panel Buttons
    corridor_select = Select(options=rtdap_data['corridor'].drop_duplicates().values.tolist(), title = 'Corridor:',
                            height=60, value = 'Dan Ryan Express Lane')

    date_picker_start = DatePicker(min_date = date(2015, 1, 1),max_date = date(2018, 12, 31),
                            css_classes = ["panel-content"], title = "Start Date:",
                            height=60, value = date(2015, 12, 31))

    date_picker_end = DatePicker(min_date = date(2015, 1, 1),max_date = date(2018, 12, 31),
                             css_classes = ["panel-content"], title = "End Date:",
                            height=60, value = date(2017, 12, 31))

    time_of_day = RangeSlider(start = 1, end= 8, step=1, value=(1, 2),
                              title="Time of Day:", bar_color="black",
                              css_classes = ["panel-content"])

    tod_description = Div(text="""Time of Day Categories:<br>
                          <ol>
                          <li>8pm-6am</li>
                          <li>6pm-7am</li>
                          <li>7am-8am</li>
                          <li>9am-10am</li>
                          <li>10am-2pm</li>
                          <li>2pm-4pm</li>
                          <li>4pm-6pm</li>
                          <li>6pm-8pm</li>
                          </ol>""",
                          css_classes = ["panel-content", "caption"])

    day_of_week = Select(options=['All'] + rtdap_data['dow'].drop_duplicates().values.tolist(),
                        title = "Day of Week:",css_classes = ["panel-content"], height=60,
                        value = "All")

    select_data = Button(label="Select Subset",css_classes = ["panel-content"], height=60)

    select_data.on_click(submit_selection)
    #-----------------------------------------------------------------------------------------------------------------


    #-----------------------------------------------------------------------------------------------------------------
    #Create initial content
    avgs_speed = rtdap_avg(rtdap_data, corridor_select.value,'avgSpeed')
    avgs_occ = rtdap_avg(rtdap_data, corridor_select.value,'avgOccupancy')
    avgs_volume = rtdap_avg(rtdap_data, corridor_select.value,'avgVolume')

    filtered_data = filter_selection(rtdap_data, corridor_select.value, str(date_picker_start.value),
                                     str(date_picker_end.value),
                                     day_of_week.value, time_of_day.value)

    speed = summarize_metrics(filtered_data, corridor_select.value, 'corridor',avgs_speed,'avgSpeed',
                              'Speed','missing_speed')
    occ = summarize_metrics(filtered_data, corridor_select.value, 'corridor',avgs_occ,'avgOccupancy',
                            'Occupancy', 'missing_occ')
    volume = summarize_metrics(filtered_data, corridor_select.value, 'corridor',avgs_volume,'avgVolume',
                               'Volume', 'missing_vol')

    summary_df = speed.append(occ)
    summary_df = summary_df.append(volume)
    summary_df_tbl = summary_df.copy()
    summary_df_tbl['Mean Diff'] = summary_df_tbl['Mean Diff'] * 100
    summary_df_tbl = summary_df_tbl.reset_index()

    summary_title = Div(text= "<h1>"+corridor_select.value+" Summary</h1>", width = 1000)
    summary_table = Div(text="", width = 550, height = 150)

    summary_table.text = str(summary_df_tbl.fillna(0).to_html(index=False,
                                                    formatters = [str,'{:20,}'.format,
                                                    '{:20,.1f}'.format,'{:20,.1f}%'.format,
                                                    '{:20,}'.format],classes=[ "w3-table" , "w3-hoverable","w3-small"]))

    line = Div(text="<hr>", css_classes = ["w3-container"], width = 1000)
    #-----------------------------------------------------------------------------------------------------------------


    #-----------------------------------------------------------------------------------------------------------------
    #Create initial graphics

    '''#horizontal bar chart
    p = figure(plot_width=300, plot_height=100)
    p.hbar(y=[1, 2, 3], height=0.5, left=0,
           right=[1.2, 2.5, 3.7], color="navy")
    p.yaxis.visible = False
    p.xaxis.formatter = NumeralTickFormatter(format="0.0f%")'''

    bar_viz = hbar_chart(summary_df.fillna(0),'Mean Diff')
    bar_viz_src = bar_viz[0]
    bar_viz_chart = bar_viz[1]


    volume_scatter = scatter_plot('Volumes')
    time_scatter = scatter_plot('Time')

    corr_df = rtdap_data.loc[rtdap_data['corridor'] == corridor_select.value]
    speed_diff_vbar = (vbar_chart(corr_df,filtered_data))
    occ_diff_vbar = (vbar_chart(corr_df,filtered_data))
    volume_diff_vbar = (vbar_chart(corr_df,filtered_data))

    base_map = make_base_map(map_width=500,map_height=1000, xaxis=None, yaxis=None,
                xrange=(-9990000,-9619944), yrange=(5011119,5310000),plot_tools="pan,wheel_zoom,reset,save")

    return row(
           #PANEL
           column(panel_title, panel_text, corridor_select,date_picker_start,
               date_picker_end, day_of_week, time_of_day,tod_description,
               Spacer(height = 20), select_data,height = 1000, css_classes = ["w3-panel","w3-grey", "w3-round-xlarge"]),

           #CONTENT
          column(
              row(Spacer(width=50),column(Spacer(height=10),
              row(column(summary_title,summary_table, width = 575),column(Spacer(height=70),bar_viz_chart), width=1000))),
              row(line),
              row(Spacer(width=50),volume_scatter,time_scatter),
              row(Spacer(width=50),column(speed_diff_vbar,occ_diff_vbar,volume_diff_vbar))),
          column(Spacer(height=90),base_map),
          css_classes = ["w3-container","w3-blue-grey"], width = 2000, height = 1200)

#side panel and view
def analytics_tab():
    panel_title = Div(text="Highway Performance", css_classes = ["panel-title","text-center"])
    panel_text = Div(text="""Lorem Ipsum is simply dummy text of the printing and typesetting industry.
           Lorem Ipsum has been the industry's standard dummy text ever since the 1500s,
           when an unknown printer took a galley of type and scrambled it to make a type
           specimen book.""", css_classes = ["panel-content"])

    #Date Range
    date_range = Div(text="Data References:<br>MMDDYYYY - MMDDYYYY",
                     css_classes = ["panel-content","text-center"])


    #Panel Buttons
    period_select = Select(options=['test 1','test 2', 'test 3'], title = 'Time Period:',
                            height=60)

    date_picker_start = DatePicker(min_date = date(2015, 1, 1),max_date = date(2017, 12, 31),
                            css_classes = ["panel-content", "col-lg-4"], title = "Start Date:",
                            height=60)

    month = Select(options=["January","February","March","April","May","June",
                            "July","August","September","October","November","December"],
                   title = "Month:", css_classes = ["panel-content", "col-lg-4"],
                            height=60)

    day_of_week = Select(options=["Monday","Tuesday","Wednesday","Thursday","Friday"],
                        title = "Day of Week:",
                            height=60)

    time_of_day = RangeSlider(start = 1, end= 24,step=1, value=(1, 7),
                        title="Time of Day:", bar_color="black", height=60)

    l1 = Div(text="test", css_classes = ["text-center"])

    return row(column(panel_title, panel_text, date_range,
                                period_select, month, day_of_week,
                                time_of_day, height = 700, css_classes = ["panel","col-lg-4"]),
                      column(l1,css_classes = ["container-fluid","col-lg-8"]),
                      css_classes = ["container-fluid","col-lg-12"])

#side panel and view
def compare_tab():
    panel_title = Div(text="[Corridor Comparison]", css_classes = ["panel-title","text-center"])
    panel_text = Div(text="""Lorem Ipsum is simply dummy text of the printing and typesetting industry.
           Lorem Ipsum has been the industry's standard dummy text ever since the 1500s,
           when an unknown printer took a galley of type and scrambled it to make a type
           specimen book.""", css_classes = ["panel-content"])

    #Date Range
    date_range = Div(text="Data References:<br>MMDDYYYY - MMDDYYYY",
                     css_classes = ["panel-content","text-center"])


    #Panel Buttons
    year_text = Div(text="<b>Year:", height=10)
    year_v1 = RangeSlider(start = 2015, end= 2017,step=1, value=(2015, 2017), height=25,
                            bar_color="black",title = "View 1")
    year_v2 = RangeSlider(start = 2015, end= 2017,step=1, value=(2015, 2017), height=25,
                            bar_color="black",title = "View 2")

    season_text = Div(text="<b>Season</b><br> (1=Winter, 2=Fall, 3=Spring, 4=Summer):", height=25)
    season_v1 = RangeSlider(start = 1, end= 4,step=1, value=(1, 2), height=25,
                            bar_color="black",title = "View 1")
    season_v2 = RangeSlider(start = 1, end= 4,step=1, value=(1, 2), height=25,
                            bar_color="black",title = "View 2")

    month_text = Div(text="<b>Month:", height=10)
    month_v1 = RangeSlider(start = 1, end= 12,step=1, value=(1, 2), height=25,
                            bar_color="black",title = "View 1")
    month_v2 = RangeSlider(start = 1, end= 12,step=1, value=(1, 2), height=25,
                            bar_color="black",title = "View 2")

    week_text = Div(text="<b>Day of Week:", height=10)
    week_v1 = RangeSlider(start = 1, end= 5,step=1, value=(1, 5), height=25,
                            bar_color="black",title = "View 1")
    week_v2 = RangeSlider(start = 1, end= 5,step=1, value=(1, 5), height=25,
                            bar_color="black",title = "View 2")

    time_of_day_text = Div(text="<b>Time of Day:", height=10)
    time_of_day_v1 = RangeSlider(start = 1, end= 24,step=1, value=(1, 7),
                       bar_color="black", height=25)
    time_of_day_v2 = RangeSlider(start = 1, end= 24,step=1, value=(1, 7),
                        bar_color="black", height=25)

    l1 = Div(text="test", css_classes = ["text-center"])

    return row(column(panel_title, panel_text, date_range,
                              year_text, year_v1, year_v2, Spacer(height=25),
                              season_text, season_v1, season_v2, Spacer(height=25),
                              month_text, month_v1, month_v2, Spacer(height=25),
                              week_text, week_v1, week_v2, Spacer(height=25),
                              time_of_day_text, time_of_day_v1, time_of_day_v2,
                             height = 1000, css_classes = ["panel","col-lg-4"]),
                      column(l1,css_classes = ["container-fluid","col-lg-8"]),
                      css_classes = ["container-fluid","col-lg-12"])

l0=Div(text="Test")
l1=Div(text="Test")
l2=Div(text="Test")
l3=Div(text="Test")

tab_0 = Panel(child=l0, title ='Overview')
tab_1 = Panel(child=selection_tab(vds_table), title ='Data Selection')
tab_2 = Panel(child=analytics_tab(), title ='Analytics')
tab_3 = Panel(child=compare_tab(), title ='Comparison')

tabs = Tabs(tabs = [tab_0, tab_1, tab_2, tab_3], sizing_mode = "scale_width")

curdoc().add_root(tabs)
