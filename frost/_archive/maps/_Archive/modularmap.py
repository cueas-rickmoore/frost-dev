import sys
from mx import DateTime
import numpy as np

import PIL.Image
sys.modules['Image'] = PIL.Image
import Image
from mpl_toolkits.basemap import Basemap
from mpl_toolkits.basemap import maskoceans
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from mpl_toolkits.axes_grid1 import make_axes_locatable

#################################################

def Basemap_mapper_justaddimage(lats,lons,options):			
	if options["area"].find("gulfmaine") < 0:
		lon_min = np.min(lons)
		lat_min = np.min(lats)
		lat_max = np.max(lats)
		lon_max = np.max(lons)
	else:
		lon_min = -77.0
		lat_min = 41.2
		lat_max = 49.5
		lon_max = -59.0
	map = Basemap(resolution='i', projection='merc',\
		llcrnrlon=lon_min, llcrnrlat=lat_min, urcrnrlon=lon_max,\
		urcrnrlat=lat_max, lat_ts=(lat_max+lat_min)/2.0)
	x_max, y_max = map(lon_max,lat_max)
	x_min, y_min = map(lon_min,lat_min)
	return map, x_max, y_max, x_min, y_min

#################################################

def plot_setup(lats,lons,options):
	defaults = {
		"size_tup": (12.0,8.3),
		"titlefontsize": 15,
		"cbarsettings": [0.25, 0.06, 0.5, 0.03],	# [left, bottom, width, height]
		"cbarlabelsize": 10,
		"pltshow": True,
		"cmap": "jet",
		"outputfile": "newmap.png",
		"titlexoffset": 0.05,
		"titleyoffset": 0.10,
		"shapelocation": '',
		"colorbar": True
	}

	for key in defaults:
		if not options.has_key(key):
			options[key] = defaults[key]
			
# setup plot figure
	fig = plt.figure(figsize=(options["size_tup"]))

	if options.has_key("area"):
		map,x_max,y_max,x_min,y_min = Basemap_mapper_justaddimage(lats,lons,options)
	else:
		# old version just for Northeast
#		print "No area specified; using old Basemap_mapper_Northeast"
#		map,fig,x_max,y_max,x_min,y_min = Basemap_mapper_Northeast(lats,lons,fig,options)
		print "Base_mapper_Northeast is no longer supported; must specify area in options"
		sys.exit()

# add logo
	if options.has_key("logo") and options["logo"]:
		try:
			img = Image.open(options["logo"])
		except:
			print "*** Error opening logo file",options["logo"],"***"
		xdiff = x_max-x_min
		ydiff = y_max-y_min
		plt.imshow(img, extent=(x_max-0.30*xdiff, x_max-0.01*xdiff, y_min+0.01*ydiff, y_min+0.15*ydiff))

# add title
	if options.has_key("title"):
		plt.text(x_min+options["titlexoffset"]*(x_max-x_min), y_max-options["titleyoffset"]*(y_max-y_min),\
			     options["title"], backgroundcolor="white", fontsize=options["titlefontsize"],\
			     multialignment="center", zorder=10)

# add template
	if options.has_key("area"):
		img = Image.open(options["shapelocation"] + options["area"] + "_template.png")
		plt.imshow(img, extent=(x_min+.0015*(x_max-x_min),x_max,y_min,y_max), zorder=3)

# add box around the map
	map.drawmapboundary(linewidth=1.0,color="black",zorder=15)
	
	return map,fig,options

#################################################

def plot_finishup(options):
	plt.savefig(options["outputfile"], bbox_inches='tight', pad_inches=0.02)
	if options["pltshow"]:
		plt.show()

#################################################

def filled_contour(map_val,lats,lons,clevs,options={}):
	from mpl_toolkits.basemap import interp
##	from scipy.interpolate import Rbf ##
	map,fig,options = plot_setup(lats,lons,options)

# interpolate topo data to higher resolution grid (to better match
#  the land/sea mask). Output looks less 'blocky' near coastlines.
##	rbf = Rbf(lons[0], lats[:,0], map_val, epsilon=2)	##
	nlats = 5*lats.shape[0]
	nlons = 5*lats.shape[1]
	new_lons = np.linspace(np.min(lons),np.max(lons),nlons)
	new_lats = np.linspace(np.min(lats),np.max(lats),nlats)
	new_lons, new_lats = np.meshgrid(new_lons,new_lats)
	x_new, y_new = map(new_lons,new_lats)
	map_val_i = interp(map_val,lons[0],lats[:,0],new_lons,new_lats)		##map_val to rbf

# interpolate land/sea mask to topo grid, mask ocean values.
	map_val_i = maskoceans(new_lons, new_lats, map_val_i,resolution = 'i',grid=1.25,inlands=False)
	map_val_i[map_val_i == -999] = np.nan

# draw filled contours
	if not options.has_key("colors"):
		fg1 = map.contourf(x_new,y_new,map_val_i,clevs,extend='both',cmap=cm.get_cmap(options["cmap"]))
	else:
		fg1 = map.contourf(x_new,y_new,map_val_i,clevs,extend='both',colors=options["colors"])

##	Following code is attempts to obtain better color map
##	cmap_def = cm.datad[options["cmap"]]
##	cmap = cm.colors.LinearSegmentedColormap('' ,cmap_def, len(clevs))
##	fg1 = map.contourf(x_new,y_new,map_val_i,clevs,extend='both',cmap=cmap)
##	fg1 = map.contourf(x_new,y_new,map_val_i,clevs,extend='both',colors=('#ff0000', '#ff9900', '#999900', 'w', '#009999', '#0099ff', '#0000ff'))

# add color bar
	if options["colorbar"]:
		ax1 = fig.add_axes(options["cbarsettings"])
		cbar = fig.colorbar(fg1, ax1, orientation='horizontal')
		if options.has_key("cbarlabelsize"):
			cbar.ax.tick_params(labelsize=options["cbarlabelsize"])	##added kle
			
# add key to bottom, if desired
	if options.has_key("keylabels"):
		for i in range(len(options["keylabels"])):
			xpos = 0.16 + ((2.0*i+1.0) * (1.0/(len(options["keylabels"])*2.0))) * 0.7
			fig.text(xpos, options["cbarsettings"][1], options["keylabels"][i], color=options["colors"][i],\
					 fontsize=options["cbarlabelsize"], horizontalalignment="center")	

##	Following code is attempt to draw colorbar without need for cbarsettings or cbarlabelsize
##	cbar = plt.colorbar(fg1, orientation='horizontal', shrink=0.5)
##	l,b,w,h = fig.gca().get_positon().bounds
##	ll,bb,ww,hh = cbar.ax.get_positon().bounds
##	cbar.ax.set_position([ll,b-0.25*h,ww,hh])
	
	plot_finishup(options)

#################################################

def dotmap(map_lat,map_lon,map_val,lats,lons,options={}):
	if not options.has_key("markers"):
		options["markers"] = {0: 'go', 1: 'yo', 2: 'ro'}
	map,fig,options = plot_setup(lats,lons,options)

# plot colored dots on map
	for map_lon,map_lat,map_val in zip(map_lon,map_lat,map_val):
		x, y = map(map_lon,map_lat)
		marker_string = options["markers"][map_val]
		fg1 = map.plot(x, y, marker_string, markersize=options["titlefontsize"]*0.67, mec='None')

# add key to bottom
	if options.has_key("keylabels"):
		for i in range(len(options["keylabels"])):
			xpos = 0.16 + ((2.0*i+1.0) * (1.0/(len(options["keylabels"])*2.0))) * 0.7
			fig.text(xpos, options["cbarsettings"][1], options["keylabels"][i], color=options["markers"][i][0],\
					 fontsize=options["cbarlabelsize"], horizontalalignment="center")	

	plot_finishup(options)
