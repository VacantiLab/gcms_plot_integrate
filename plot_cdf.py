# This script plots the contents of a CDF file without needing to access a pre-processed picle file.

# The call to this is:
#     bokeh serve --show plot_cdf.py --port 99
#     the call must be made in the terminal (not in python)

# The call must be made from the directory containing this file
# The directory containing AnalyzeSpectra must be added to the PYTHONPATH system variable
#     use: export PYTHONPATH="${PYTHONPATH}:/Users/nate/git_hub_projects" to add it

from pdb import set_trace
import AnalyzeSpectra
import importlib
import numpy as np
import copy
import re
from AnalyzeSpectra import get_directory

from bokeh.io import curdoc
from bokeh.layouts import column, row, layout, widgetbox
from bokeh.models import ColumnDataSource, Slider, TextInput
from bokeh.plotting import figure, output_file
from bokeh.events import DoubleTap

from pdb import set_trace #python debugger
#import plotly #for plotting, not used here?
from os import listdir #needed to get a list of files
import pandas #a module which allows for making data frames
import copy
import organize_ms_data
importlib.reload(organize_ms_data)
import process_ms_data
importlib.reload(process_ms_data)
import create_output_directory
importlib.reload(create_output_directory)
import integrate_peaks
importlib.reload(integrate_peaks)
import BinData
importlib.reload(BinData)
import fragment_library
importlib.reload(fragment_library)
import print_integrated_peaks
importlib.reload(print_integrated_peaks)
import find_ri_conversion
importlib.reload(find_ri_conversion)
import get_ri_keys_dict
importlib.reload(get_ri_keys_dict)
import calc_coelut
importlib.reload(calc_coelut)
import convert_rt_ri
importlib.reload(convert_rt_ri)
import get_directory
importlib.reload(get_directory)
import locate_overlap
importlib.reload(locate_overlap)
import GetFileBatch
importlib.reload(GetFileBatch)

mz_plot = ['tic','blank','blank','blank']
mz_colors = ['red','blue','green','purple']

#Retrieve Data File Name
print('\nSelect data file ...\n')
#retrieve file directory
retrieve_directory_method = 'gui_file' #specifies you want to select the file with the gui
#    options are: 'manual', 'gui', 'manual_file', 'gui_file'
file_path = get_directory.get_directory(retrieve_directory_method)
#    returns the path to the file including the filename and extension
file_directory = re.sub('/[^/]*$','',file_path)+'/'
#    removes the filename and extension, leaving the terminating /
#        '/[^/]*$': '/' -> match '/'; ''[^/]*'' -> any character except / any number of times; '$'' -> end of string

#get the file name
regex_pattern = re.compile('/[^/]*$')
filename_regex = regex_pattern.search(file_path)
filename = filename_regex[0]
filename = re.sub('/','',filename)
sample_name = filename.split('.')[0]


#Retrieve Alkane File Name
print('\nSelect alkane file ...\n')
#retrieve file directory
retrieve_directory_method = 'gui_file' #specifies you want to select the file with the gui
#    options are: 'manual', 'gui', 'manual_file', 'gui_file'
alkane_path = get_directory.get_directory(retrieve_directory_method)
#    returns the path to the file including the filename and extension
alkane_directory = re.sub('/[^/]*$','',alkane_path)+'/'
#    removes the filename and extension, leaving the terminating /
#        '/[^/]*$': '/' -> match '/'; ''[^/]*'' -> any character except / any number of times; '$'' -> end of string

#get the alkane file name
regex_pattern = re.compile('/[^/]*$')
alkanename_regex = regex_pattern.search(alkane_path)
alkanename = alkanename_regex[0]
alkanename = re.sub('/','',alkanename)
alkane_name = alkanename.split('.')[0]

sample_names_list = [alkane_name,sample_name]


#Create the folder for outputting results
output_plot_directory,output_directory = create_output_directory.create_output_directory()

#Access the data - alkanes file first
for sample_name in sample_names_list:
    # Access the data
    print(sample_name + ':' + ' accessing and organizing m/z, scan acquisition time, and ion count data...')
    ic_df,sat,n_scns,mz_vals,tic = organize_ms_data.organize_ms_data(file_directory + sample_name + '.CDF')
        #ic_df: ion count data frame
        #sat: scan acquisition times
        #n_scns: number of scans
        #mz_vals: the m/z values scanned

    #bin the data as specified: move to organize_ms_data
    ic_df = BinData.BinData(ic_df,1.0005)
        #the second input is the width of the bin

    #reassign the mz values due to the binning
    mz_vals = np.sort(np.array(list(ic_df.index.values)))

    #Process ms data
    print(sample_name + ':' + ' subtracting baselines and smoothing...')
    (ic_smooth_dict,peak_start_t_dict,peak_end_t_dict,
    peak_start_i_dict,peak_end_i_dict,x_data_numpy,peak_i_dict,
    peak_max_dict,p,peak_sat_dict,ic_dict) = process_ms_data.process_ms_data(sat,ic_df,output_plot_directory,n_scns,mz_vals)
         #ic_smooth_dict: a dictionary containing the smoothed and baseline corrected ion count data for each m/z value
         #peak_start_t_dict: a dictionary with all of the peak beginning times for each m/z ion count plot
         #peak_end_t_dict: a dictionary with all of the peak ending times for each m/z ion count plot
         #peak_start_i_dict: a dictionary with all of the peak beginning indices for each m/z ion count plot
         #peak_end_i_dict: a dictionary with all of the peak ending indices for each m/z ion count plot
         #x_data_numpy: scan acquisition time values
         #p: the plot (bokeh) object

    #add the total ion count to the dictionary
    #    note it is not smoothed because it does not really make sense to smooth total ion count data
    ic_smooth_dict['tic'] = tic
    ic_dict['tic'] = tic

    if sample_name == alkane_name:
        #calculate peak overlap dictionary
        print(sample_name + ':' + ' finding coeluting peaks ...')
        peak_overlap_dictionary = locate_overlap.locate_overlap(ic_smooth_dict,peak_start_i_dict,peak_end_i_dict,mz_vals,peak_max_dict)
        #calculate the coelution dictionary with the scan acquisition times as keys
        #    coelution_dict_sat has keys of sat's and arrays of mz's whoe peaks elute at those sat's
        #    coelution_dict_val is the same except the arrays are the corresponding intensity values of the eluting peaks at the sat of the key
        coelut_dict_sat,coelut_dict_val_sat = calc_coelut.calc_coelut(peak_sat_dict,mz_vals,sat,ic_smooth_dict,peak_overlap_dictionary)
        ri_sat,ri_rec = find_ri_conversion.find_ri_conversion(ic_smooth_dict,mz_vals,sat,coelut_dict_sat,coelut_dict_val_sat,sample_name)

    #convert the retention times of the current sample to retention indices
    #    doing this for each sample allows for samples with differing quantities of scan acquisition times
    #    to be analyzed with the same alkane sample for retention index calculation
    ri_array = convert_rt_ri.convert_rt_ri(ri_sat,ri_rec,sat)

    #find ri of each peak
    peak_ri_dict = dict()
    peak_start_ri_dict = dict()
    peak_end_ri_dict = dict()
    for mz_val in mz_vals:
        peak_loc_ind = peak_i_dict[mz_val]
        peak_start_ind = peak_start_i_dict[mz_val]
        peak_end_ind = peak_end_i_dict[mz_val]
        peak_ri_dict[mz_val] = ri_array[peak_loc_ind]
        peak_start_ri_dict[mz_val] = ri_array[peak_start_ind]
        peak_end_ri_dict[mz_val] = ri_array[peak_end_ind]

    #invert the ic_smooth_dict so that retention indices are the keys and a vector of intensities for each mz are the items
    ic_smooth_dict_timekeys = get_ri_keys_dict.get_ri_keys_dict(ic_smooth_dict,ri_array,mz_vals)

    ic_smooth_dict['ri'] = ri_array
    ic_dict['ri'] = ri_array

    print('\n')
#########################################

sample_name = filename.split('.')[0]
input_data_file = file_directory + 'processed_data.p'
output_plot_file = file_directory + 'plot1.html'

plot=figure(title='ion counts vs. time', x_axis_label='retention index',y_axis_label='ion counts',plot_width=950,plot_height=300)


source = {}
mz_text = {}
legend = {}

source_dict_plot1 = {}
source_dict_plot2 = {}
source_dict_plot3 = {}
source_dict_plot4 = {}

x_data_source = 'ri'
#x_data_source = 'sats'
#    can be 'ri' for retention indices or 'sats' for scan acquisition times

x_data = ic_smooth_dict[x_data_source] #this does not change with mz so it is set outside the loop
blank_data = np.zeros(len(x_data))
for i in range(0,len(blank_data)):
    blank_data[i] = np.nan

#change the key names to strings
source_dict = ic_smooth_dict #bc: baseline-corrected
source_dict_keys = list(source_dict.keys())
for key in source_dict_keys:
    new_key = str(key) #change the float key to a string
    new_key = re.sub('\..*$','',new_key) #remove the decimal and everything following
    source_dict[new_key] = source_dict.pop(key) #new key on left of equal sign, old key on right
source_dict['blank'] = blank_data

#set the x data and the initially displayed values
source_dict_plot1['x'] = x_data
source_dict_plot1['y'] = source_dict[mz_plot[0]]

source_dict_plot2['x'] = x_data
source_dict_plot2['y'] = source_dict[mz_plot[1]]

source_dict_plot3['x'] = x_data
source_dict_plot3['y'] = source_dict[mz_plot[2]]

source_dict_plot4['x'] = x_data
source_dict_plot4['y'] = source_dict[mz_plot[3]]


source1 = ColumnDataSource(data=source_dict_plot1) #for bokeh widgets it is stored in a ColmnDataSource object
source2 = ColumnDataSource(data=source_dict_plot2) #for bokeh widgets it is stored in a ColmnDataSource object
source3 = ColumnDataSource(data=source_dict_plot3) #for bokeh widgets it is stored in a ColmnDataSource object
source4 = ColumnDataSource(data=source_dict_plot4) #for bokeh widgets it is stored in a ColmnDataSource object

labels = ['label1','label2','label3','label4']

def update_mz_trace1(attrname, old, new):
    mz = mz_text[0].value
    y = source_dict[mz]
    source1.data = dict(x=x_data, y=y)

def update_mz_trace2(attrname, old, new):
    mz = mz_text[1].value
    y = source_dict[mz]
    source2.data = dict(x=x_data, y=y)

def update_mz_trace3(attrname, old, new):
    mz = mz_text[2].value
    y = source_dict[mz]
    source3.data = dict(x=x_data, y=y)

def update_mz_trace4(attrname, old, new):
    mz = mz_text[3].value
    y = source_dict[mz]
    source4.data = dict(x=x_data, y=y)

source_list = [source1,source2,source3,source4]
update_function_list = [update_mz_trace1,update_mz_trace2,update_mz_trace3,update_mz_trace4]

for j in [0,1,2,3]:
    plot.line('x','y',source=source_list[j],color=mz_colors[j]) #update the plot object for the current mz
    mz_text[j] = TextInput(title=mz_colors[j], value=str(mz_plot[j])) #the textbox widget, the value must be a string
    mz_text[j].on_change('value',update_function_list[j])
    #mz_text[j] = Select(title=mz_colors[j], value=str(mz_plot[j]), options=list(source_dict.keys()))

# intensity vs. mz at specified time################

#Make the ion-count vs. mz plot for each scan acquisition time
source_dict_timekeys = ic_smooth_dict_timekeys
source_dict_timekeys_keys = list(source_dict_timekeys.keys())

#set the x values to all mz values and the initial y value to the first recorded intensities for each mz
source_dict_timekeys_plot = {}
source_dict_timekeys_plot['x'] = mz_vals
test_time_value = list(source_dict_timekeys.keys())[0]
source_dict_timekeys_plot['y'] = source_dict_timekeys[test_time_value]

#convert the keys into strings
source_dict_timekeys_keys = list(source_dict_timekeys.keys())
# for key in source_dict_timekeys_keys:
#     new_key = str(key) #change the float key to a string
#     #new_key = re.sub('\..*$','',new_key) #remove the decimal and everything following
#     source_dict_timekeys[new_key] = source_dict_timekeys.pop(key) #new key on left of equal sign, old key on right

source_timekeys = ColumnDataSource(data=source_dict_timekeys_plot)
plot2 = figure(title='ion counts vs. mz', x_axis_label='m/z',y_axis_label='ion counts',plot_width=950,plot_height=300)
plot2.vbar(x='x', bottom=0, width=0.5, top='y',color='firebrick',source=source_timekeys)

#double-click callback
def callback(event):
    rt_click = event.x
    subtracting_click_time = np.array(source_dict_timekeys_keys) - rt_click
    rt_index = np.argmin(abs(subtracting_click_time))
    rt = source_dict_timekeys_keys[rt_index]
    # x_index = 'x'+'%.3f'%(rt)
    # y_index = 'y'+'%.3f'%(rt)
    x = mz_vals
    y = source_dict_timekeys[rt]
    source_timekeys.data = dict(x=x, y=y)
plot.on_event(DoubleTap, callback)




# Set up layouts and add to document
text_box1 = widgetbox(mz_text[0], width=175, height=20)
text_box2 = widgetbox(mz_text[1], width=175, height=20)
text_box3 = widgetbox(mz_text[2], width=175, height=20)
text_box4 = widgetbox(mz_text[3], width=175, height=20)

l = layout([
  [text_box1,text_box2,text_box3,text_box4],
  [plot],
  [plot2],
], sizing_mode='fixed')

curdoc().add_root(l)
