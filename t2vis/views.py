# main view for t2vis/ which is our main visualization page working from a single django template, 'index.html' which we
# fill with the script and div provided by bokeh

from django.shortcuts import render
from django.http import HttpResponse
from bokeh.plotting import figure
from bokeh.embed import components
from netCDF4 import Dataset
from netCDF4 import Variable
from django.conf import settings
import os

kDatafilePath = str(os.path.join(settings.BASE_DIR, "static/assets/frontendtest.nc"))

kReqLocIdxName = "location"
kCdfT2Name = "T2"
kCdfLatName = "latitude"
kCdfLongName = "longitude"
kCdfLocIdName = "locationid"
kCdfTimeIdName = "time"

def test(request):
    return HttpResponse("Hello, world.")

def index(request):
# open the file on the server via netcdf4
    try:
        rootgrp = Dataset(kDatafilePath, "r", format="NETCDF4")
    except Exception as e:
        return render(request, "t2vis/index.html", {"fatalError": str(e) + ", file '"+kDatafilePath+"'"})
# check that it has all the bits we're expecting and that they pass basic sanity checks: time and location dimensions match up etc
    try:
        t2 = rootgrp.variables[kCdfT2Name]
    except Exception as e:
        return render(request, "t2vis/index.html", {"fatalError": str(e) + ", file '"+kDatafilePath+"' missing variable "+kCdfT2Name})
    try:
        latitude = rootgrp.variables[kCdfLatName]
    except Exception as e:
        return render(request, "t2vis/index.html", {"fatalError": str(e) + ", file '"+kDatafilePath+"' missing variable "+kCdfLatName})
    try:
        longitude = rootgrp.variables[kCdfLongName]
    except Exception as e:
        return render(request, "t2vis/index.html", {"fatalError": str(e) + ", file '"+kDatafilePath+"' missing variable "+kCdfLongName})
    try:
        time = rootgrp.variables[kCdfTimeIdName]
    except Exception as e:
        return render(request, "t2vis/index.html", {"fatalError": str(e) + ", file '"+kDatafilePath+"' missing variable "+kCdfTimeIdName})

    loclen = longitude.shape[0]
    timelen = time.shape[0]
    if latitude.ndim != 1 or longitude.ndim != 1 or t2.ndim != 2 or \
            latitude.shape[0] != loclen or t2.shape[0] != loclen or t2.shape[1] != timelen:
        return render(request, "t2vis/index.html", {"fatalError": "Data file '"+kDatafilePath+"' location/t2 information malformed "})

# build up lists of names of places (if possible) and string corresponding to these locations
    i = 0
    locLLStr = []
    locNames = []
    while i < loclen:
        if (latitude[i] < 0):
            latStr = str(-latitude[i])+'S'
        else:
            latStr = str(latitude[i])+'N'
        if (longitude[i] < 0):
            lonStr = str(-longitude[i])+'W'
        else:
            lonStr = str(longitude[i])+'E'
            
        locLabel = latStr +", "+ lonStr
        locName = rootgrp.getncattr('location'+str(i))
        if (not locName):
            locName = locLabel
        locLLStr.append(locLabel)
        locNames.append(locName)
        i += 1
    
    location = -1
    warnError = ""

# check that we are actually being requested a location, or whether we should just put up a form asking for the location
    if (request.POST and request.POST.get(kReqLocIdxName)):
        location, warnError = getInt(request.POST.get(kReqLocIdxName), kReqLocIdxName, 0, loclen)
    elif (request.GET and request.GET.get(kReqLocIdxName)):
        location, warnError = getInt(request.GET.get(kReqLocIdxName), kReqLocIdxName, 0, loclen)

# if we're being asked for a location, build up a plot. we plot the time in seconds as given in the time variable from cdf4 file,
# first converting to epoch time, so as to work with the 'datetime' axis type of bokeh 
    if (location >= 0 and not warnError):
        plot = figure(width=1000, height=600, x_axis_type="datetime")
        i=1
# time in data is in seconds ... for datetime, we need it in millis. we're plotting in segments
# as the netcdf4 variables don't have a corresponding python list value
        while i < timelen:
            plot.line([1000*time[i-1], 1000*time[i]], [t2[location,i-1], t2[location, i]], line_width=2) 
            i += 1
# set up niceties for the plot        
        plot.title = "Temperature v. Time at "+locNames[location]+" ("+locLLStr[location]+")";
        plot.xaxis.axis_label = 'Time'
        plot.yaxis.axis_label = 'T2'
        
        script, div = components(plot)
        return render(request, "t2vis/index.html",
                      {'script': script,
                       'div': div,
                       "warnError": warnError,
                       "selectedLocationIdx": location,
                       "locLLStr": locLLStr,
                       "locNames": locNames})
# if we fall through here, we've got no location requested we'll just pop up the form
    return render(request, "t2vis/index.html",
                  {"warnError": warnError,
                   "selectedLocationIdx": location,
                   "locLLStr": locLLStr,
                   "locNames": locNames})

# helper function for checking request parameters
def getInt(lidxStr, name, lb, ub):
    v = lb-1
    try:
        v = int(lidxStr)
    except:
        return v, name+" not a number"
    if (v < lb or v >= ub):
        return v, name+" value out of range"
    return v, "";
    
