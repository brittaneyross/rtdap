#libraries
import pandas as pd
import numpy as np
import random
import datetime

#bokeh
from bokeh.io import show, output_notebook, push_notebook
from bokeh.plotting import figure

from bokeh.layouts import layout, column, row, WidgetBox
from bokeh.models import Panel, Spacer, HoverTool, LogColorMapper, ColumnDataSource,FactorRange, RangeSlider
from bokeh.models.widgets import Div, Tabs, Paragraph, Dropdown, Button, PreText, Toggle, Select,\
                                DatePicker

from bokeh.transform import factor_cmap
from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
from bokeh.core.properties import value

#color
from bokeh.palettes import Spectral6

from bokeh.io import curdoc

#table
random_data = pd.DataFrame({'col1':[1,2,3],'col2':[2,5,9],'col3':[8,9,5]}, index =["Speed","Time","Volume"])
def selection_summary(data_table):

    summary_title = Div(text="<h1>[Corridor Name] Summary</h1>",
                        css_classes = ["container-fluid"], width = 1000)

    summary_table = PreText(text="")

    summary_table.text = data_table

    return row(column(summary_title,summary_table))

#side panel and view
def selection_tab():
    panel_title = Div(text="Data Review", css_classes = ["panel-title","text-center"])
    panel_text = Div(text="""Lorem Ipsum is simply dummy text of the printing and typesetting industry.
           Lorem Ipsum has been the industry's standard dummy text ever since the 1500s,
           when an unknown printer took a galley of type and scrambled it to make a type
           specimen book.""", css_classes = ["panel-content"])

    #Panel Buttons
    corridor_select = Select(options=['test 1','test 2', 'test 3'], title = 'Corridor:',
                            height=60)

    date_picker_start = DatePicker(min_date = datetime.date(2015, 1, 1),max_date = datetime.date(2017, 12, 31),
                            title = "Start Date:", height=60)
    date_picker_end = DatePicker(min_date = datetime.date(2015, 1, 1),max_date = datetime.date(2017, 12, 31),
                             title = "End Date:", height=60)

    time_of_day = RangeSlider(start = 1, end= 24,step=1,
                         value=(1, 7), title="Time of Day:", bar_color="black", height=60)

    day_of_week = Select(options=["Monday","Tuesday","Wednesday","Thursday","Friday"],
                        title = "Day of Week:",
                            height=60)

    select_data = Button(label="Select Subset",
                            height=60)


    #Data View
    l1 = selection_summary(str(random_data))
    line = Div(text="<hr>", css_classes = ["col-lg-12"], width = 1000)

    return row(column(panel_title, panel_text, corridor_select,
                             date_picker_start, date_picker_end, day_of_week,
                             time_of_day, Spacer(height = 20), select_data,
                             height = 700, css_classes = ["panel","col-lg-4"]),
               column(row(Spacer(width=50),
               column(Spacer(height=10), l1)), line),
               css_classes = ["container-fluid","col-lg-12"])

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

    date_picker_start = DatePicker(min_date = datetime.date(2015, 1, 1),max_date = datetime.date(2017, 12, 31),
                            title = "Start Date:", height=60)

    month = Select(options=["January","February","March","April","May","June",
                            "July","August","September","October","November","December"],
                   title = "Month:", height=60)

    day_of_week = Select(options=["Monday","Tuesday","Wednesday","Thursday","Friday"],
                        title = "Day of Week:", height=60)

    time_of_day = RangeSlider(start = 1, end= 24,step=1, value=(1, 7),
                        title="Time of Day:", bar_color="black", height=60)

    l1 = Div(text="test", css_classes = ["text-center"])

    return row(column(panel_title, panel_text, date_range,
                                period_select, month, day_of_week,
                                time_of_day, height = 700, css_classes = ["panel","col-lg-4"]),
                      column(l1,css_classes = ["container-fluid","col-lg-8"]),
                      css_classes = ["container-fluid","col-lg-12"])

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
tab_1 = Panel(child=selection_tab(), title ='Data Selection')
tab_2 = Panel(child=analytics_tab(), title ='Analytics')
tab_3 = Panel(child=compare_tab(), title ='Comparison')

tabs = Tabs(tabs = [tab_0, tab_1, tab_2, tab_3], sizing_mode = "scale_width")

curdoc().add_root(tabs)
