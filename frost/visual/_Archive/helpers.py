import os, sys, time, urllib, urllib2, pprint, copy, warnings, pickle
import numpy as np
from mx import DateTime
from matplotlib.mlab import griddata as griddata_nn
from scipy.interpolate import griddata as griddata_linear
#from print_exception import print_exception
import frost.maps.modularmap as basemapper

user = os.getlogin()

try :
   import json 
except ImportError:
   import simplejson as json

warnings.simplefilter("ignore")
pp = pprint.PrettyPrinter()

#get dates from command line
def getDates():
	dates_dt = []
	for i in range(1, len(sys.argv)):
		cols = sys.argv[i].split(",")
		if len(cols) == 3:
			dates_dt.append(DateTime.DateTime(int(cols[0]),int(cols[1]),int(cols[2])))
	if len(dates_dt) == 2:
	#	Two arguments are start and end date
		sdate = dates_dt[0]
		edate = dates_dt[1]
	elif len(dates_dt) == 1:
	#	One argument is end date - do week ending that date
		edate = dates_dt[0]
		sdate = edate + DateTime.RelativeDate(days=-6)
	elif len(dates_dt) == 0:
	#	No arguments default to week ending yesterday
		edate = DateTime.now() + DateTime.RelativeDate(days=-1)
		sdate = edate + DateTime.RelativeDate(days=-6)
	else:
		sys.exit()
	return sdate, edate
	
#retrieve data defined by input_dict from web services
def getData(input_dict,server="GridData"):
	try:
		pp.pprint(input_dict)
		params = urllib.urlencode({'params':json.dumps(input_dict)})
		print DateTime.now(),'Calling',server
		req = urllib2.Request('http://data.rcc-acis.org/'+server, params, {'Accept':'application/json'})
		response = urllib2.urlopen(req)
		data_vals = json.loads(response.read())
	except:
		print 'Problem with web service call',input_dict,'; Retrying...'
		time.sleep(35)
		try:
			req = urllib2.Request('http://data.rcc-acis.org/'+server, params, {'Accept':'application/json'})
			response = urllib2.urlopen(req)
			data_vals = json.loads(response.read())
		except:
			print 'Problem getting data'
			#print_exception()
			sys.exit()
	print DateTime.now(),server,'call successful'
	return data_vals

#combine map-specific options with (overriding) defaults
def setupOptions(option_file_name):
	# Following are defaults. Can be superseded by values in input control file.
	#  Other possible options from control files include: "title", "title2", "outputfile", 
	#   "elems", "cmap", "contourbounds", "keylabels", "interpmethod", "colors", "another"
	defaults = {
		"size_tup": (6.8, 6.55),					# new standard size is (6.8, 6.55), thumbnail is (2.3, 2.3), original standard is (4.7, 4.55), large is (12,8.3)
		"titlefontsize": 12,						# standard is 12, original is 10, large is 15, (none for thumbnail)
		"cbarlabelsize": 8,							# small is 8, large is 10
		"cbarsettings": [0.25, 0.11, 0.5, 0.02],	# small is [0.25, 0.11, 0.5, 0.02], large is [0.25, 0.06, 0.5, 0.03] -- [left, bottom, width, height]
		"titlexoffset": 0.05,						# 0.05 for all but those specified below
		"titleyoffset": 0.10,						# 0.10 for all but those specified below
		"pltshow": False,							# boolean
		"datesfromfile": False,						# boonean
		"maptype": 'contourf',						# contourf, interpf or dotmap
		'area': 'northeast',						# northeast, westny, eastny, ny, etc.
		'inputfile': None,							# tab-delimited input file for dotmap or interpf
		"numlevels": 8,								# number of contour levels
		"grid": 3,									# GridData grid id
		"colorbar": True,							# whether or not to plot a colorbar
		"levelmult": None,							# contour bounds are multiples of this value (None = pick based on data)
		"shapelocation": '/Users/'+user+'/BaseMapper/templates/',			# location of template or shapefiles (old basemap)
		"metalocation": '/Users/'+user+'/BaseMapper/metadata/',				# location of saved metadata files
		"logo": '/Users/'+user+'/BaseMapper/PoweredbyACIS-rev2010-08.png',	# also available ...PoweredbyACIS_NRCC.jpg (False for no logo)
	}
	area_bbox = {
		'northeast':          [-82.70, 37.20, -66.90, 47.60],
		'ny':                 [-79.90, 40.45, -71.80, 45.05],
		'westny':             [-80.00, 41.95, -74.75, 45.00],
		'eastny':             [-77.00, 40.45, -71.80, 43.45],
		'midatlantic':        [-79.75, 37.25, -73.00, 41.75],
		'newengland':         [-73.80, 40.95, -66.85, 47.60],
		'easternregion':      [-85.10, 31.90, -66.80, 47.60],
		'gulfmaine_masked':   [-77.00, 41.20, -59.00, 49.50],
		'gulfmaine_unmasked': [-77.00, 41.20, -59.00, 49.50],
		'greatlakes_unmasked':[-94.30, 40.00, -74.00, 51.50],
		'vt':                 [-74.00, 42.50, -71.20, 45.25],
		'me':                 [-72.00, 42.75, -66.85, 47.60],
		'wv':                 [-83.00, 37.00, -77.50, 40.80],
		'wv_state':           [-83.00, 37.00, -77.50, 40.80],
		'pa':                 [-80.75, 39.50, -74.25, 42.25],
		'nh':                 [-72.75, 42.50, -70.25, 45.50],
		'ma':                 [-73.75, 41.25, -69.75, 43.00],
		'ct':                 [-73.75, 40.75, -71.25, 42.25], 
		'ri':                 [-72.50, 41.00, -70.50, 42.25],
		'md':                 [-80.00, 37.50, -74.75, 40.00],
		'nj':                 [-76.00, 38.75, -73.50, 41.75],
	}
	try:
		del map_input
	except NameError:
		pass
	exec("from " + option_file_name + "_inputs import map_input")
	#combine
	options = copy.deepcopy(defaults)
	for key in map_input.keys():
		options[key] = map_input[key]
	#get area bbox
	options["bbox"] = area_bbox[options["area"]]
	#special case title location
	if options["area"] in ["easternregion", "midatlantic"]:
		options["titlexoffset"] = 0.25
	if options["area"] in ["ny"]:
		options["titlexoffset"] = 0.01
	elif options["area"] in ["wv","wv_state"]:
		options["titlexoffset"] = 0.48
		options["titleyoffset"] = 0.09
	elif options["area"] in ["newengland"]:
		options["titlexoffset"] = 0.15
	elif options["area"] in ["eastny"]:
		options["titlexoffset"] = 0.23
	elif options["area"] == "gulfmaine":
		options["titlexoffset"] = 0.65
		options["titleyoffset"] = 0.90	#not tested
	elif options["area"] == "greatlakes":
		options["titlexoffset"] = 0.55
		options["titleyoffset"] = 0.15	#not tested
	return options

# obtain grid lat/lon metadata. Should be stored in file, but if not, obtain from gridData call
def getMeta(options):
	try:
		data_vals = {}
		metafile = open("%s%s.pkl"%(options["metalocation"],options["area"]), 'rb')
		data_vals["meta"] = pickle.load(metafile)
		metafile.close()
	except IOError:
		print "Unable to open a metadata file; accessing lat/lon from gridData"
		yest = DateTime.now() + DateTime.RelativeDate(days=-1)
		input_dict = {
			"sdate": '%d-%02d-%02d' % (yest.year, yest.month, yest.day),
			"edate": '%d-%02d-%02d' % (yest.year, yest.month, yest.day),
			"grid":  3,
			"elems": 'pcpn',
			"bbox":  options["bbox"],
			"meta":  'll'
		}
		data_vals = getData(input_dict)
	return data_vals

#determine contour levels (from options, if available)
def getBounds(data_grid, options):
	if options.has_key("contourbounds"):
		contour_bounds = options["contourbounds"]
	else:
		contour_bounds = plot_bound(np.hstack(data_grid.astype(int)), options["numlevels"], options["levelmult"])
	return contour_bounds

#create a string containing single date or data range based on first line of input file
def makeDatesFromFile(options):
	inf = open(options["inputfile"], "r")
	line1 = inf.readline()
	inf.close()
	idates = line1.strip().split("\t")
	if len(idates) == 1:
		cols = idates[0].split(",")
		dp = DateTime.DateTime(int(cols[0]),int(cols[1]),int(cols[2]))
		dateline  = "%s %s, %s" % (dp.strftime("%B"),dp.day,dp.year)
	elif len(idates) == 2:
		cols = idates[0].split(",")
		sdp = DateTime.DateTime(int(cols[0]),int(cols[1]),int(cols[2]))
		cols = idates[1].split(",")
		edp = DateTime.DateTime(int(cols[0]),int(cols[1]),int(cols[2]))
		dateline = makeDateline(sdp,edp,options)
	else:
		print "Unexpected date line in input file",line1
		sys.exit()
	return dateline

#create a string containing the range of dates covered by the map
def makeDateline(sdate,edate,options):
	sMonName = sdate.strftime("%B")
	eMonName = edate.strftime("%B")
	if not options.has_key("elems") or not options["elems"][0].has_key("interval") or options["elems"][0]["interval"] != "mly":
		#dates with daily precision
		if edate.year != sdate.year:
			dateline = "%s %s, %s-%s %s, %s" % (sMonName,sdate.day,sdate.year,eMonName,edate.day,edate.year)
		elif edate.month != sdate.month:
			dateline = "%s %s-%s %s, %s" % (sMonName,sdate.day,eMonName,edate.day,edate.year)
		elif edate.day != sdate.day:
			dateline = "%s %s-%s, %s" % (sMonName,sdate.day,edate.day,edate.year)
		else:
			dateline = "%s %s, %s" % (eMonName,edate.day,edate.year)
	else:
		#dates with monthly precision
		if edate.year != sdate.year:
			dateline = "%s %s - %s %s" % (sMonName,sdate.year,eMonName,edate.year)
		elif edate.month != sdate.month:
			dateline = "%s - %s %s" % (sMonName,eMonName,edate.year)
		else:
			dateline = "%s %s" % (eMonName,edate.year)
	return dateline

#build map title
def makeTitle(options,sdate=None,edate=None):
	title = options["title"]
	# add title2 as second line of title, otherwise make dates the second line
	if options.has_key("title2"):
		title += '\n%s' % (options["title2"])
		if options.has_key("datesfromfile") and options["datesfromfile"]:
			title += "%s" % (makeDatesFromFile(options))
	else:
		if options.has_key("datesfromfile") and options["datesfromfile"]:
			title += "\n%s" % (makeDatesFromFile(options))
		else:
			title += '\n%s' % (makeDateline(sdate, edate, options))
	return title

#retrieve values from a tab-delimited mapping file (columns are id, lat, lon, value)
def getValsFromFile(infile):
	if infile:
		ifile = np.genfromtxt(infile, dtype=None, skip_header=1, delimiter="\t")
		lats= ifile['f1']
		lons = ifile['f2']
		vals = ifile['f3']
		return lats,lons,vals
	else:
		print "No plot produced; need to specify an input file"
		sys.exit()

#determine reasonable contour intervals
def plot_bound(array_1d,num_bins,mult=None):
	array_1d = array_1d[array_1d != -999]
	array_1d = array_1d[array_1d > -9000000000000000000]

#	added 4/28/2014 -kle
	if not mult:
		gmax = np.amax(array_1d)
		gmin = np.amin(array_1d)
		gint = (gmax-gmin)/num_bins
		mult = 1
		for i in [500,100,50,10,5]:
			if gint > i:
				mult = i
				break
	array_1d = (array_1d / mult)

	array_min = np.amin(array_1d)
	bin_mid = np.histogram (array_1d,bins=num_bins)
	bin_minimum =bin_mid[1][0]
	bin_maximum = bin_mid[1][-1]
	bin_converge = 0

	while bin_converge == 0:
		bin_tot_low = 0
		bin_tot_hi = 0
		bin_start = bin_mid[1][1]
		bin_end = bin_mid[1][num_bins]		
		for val in range(len(bin_mid[0])):
			bin_tot_low=bin_tot_low+bin_mid[0][val]
			if bin_tot_low/float(len(array_1d))<0.01:
				bin_start =bin_mid[1][val+1]
			else:
				break

		for val in range(len(bin_mid[0])-1,-1,-1):
			bin_tot_hi=bin_tot_hi+bin_mid[0][val]
			if bin_tot_hi/float(len(array_1d))<0.01:
				bin_end = bin_mid[1][val]    ###changed to val from val -1 atd 2/14
			else:
				break
				
		if bin_start > bin_end:
			bin_start = bin_end
		bin_final = np.histogram (array_1d,bins=num_bins,range=(bin_start,bin_end))
		bin_range = abs(bin_mid[0][1]-bin_mid[0][0])
		if bin_final[0][0]/float(len(array_1d))>=0.01 or (abs(bin_final[1][0] - bin_final[1][-1]) < 1):
			bin_converge = 1
		else:
			bin_mid = bin_final

	# round bin contours, omitting the first and last bins as these will be extended to all values less and greater
	bin_contours=[]
	for vals in range(1,len(bin_final[1])-1):
		bin_contours.append(round(bin_final[1][vals],0))
	
	# create bins of equal integer width
	crange = bin_contours[-1]-bin_contours[0]
	resid = crange%num_bins
	factor = 1
	if resid<num_bins/2. and resid <>0:
		### shorten end bins
		b_change = round(resid/2.)
		low_change = b_change
		hi_change=-1*b_change 
		if b_change>resid/2.:
			hi_change = -1*(b_change -1)
	if resid <> 0:
		### length end bins
		b_change = round((num_bins-resid)/2.)
		low_change = -1*b_change
		hi_change = b_change
		if b_change>(num_bins-resid)/2.:
			hi_change = b_change -1	
	else:
		b_change=0
		low_change=0
		hi_change=0
		
	binw = (crange+abs(low_change)+abs(hi_change))/num_bins
	bin_contours_new = [bin_contours[0]+low_change]
	for bin in range(len(bin_contours)):
		if bin_contours_new[bin]+binw <= bin_contours[-1]+hi_change:
			bin_contours_new.append(bin_contours_new[bin]+binw)
		else:
			break	

	# remove duplicates and contours less than the min value of the array
	for i in range(len(bin_contours_new)-1,0,-1):
		if bin_contours_new[i] == bin_contours_new[i-1] or bin_contours_new[i] < array_min:
			del bin_contours_new[i]
	if bin_contours_new[0] < array_min:
		del bin_contours_new[0]

	# need to have at least two levels for contouring
	if len(bin_contours_new) == 1:
		bin_contours_new.append(np.max(array_1d) + 1)

	# convert back to non-scaled values
	for i in range(len(bin_contours_new)):
		bin_contours_new[i] = bin_contours_new[i] * mult
	return bin_contours_new

#plot requested map
def create_map(data_vals, options, data_grid=None):
	lats=np.array(data_vals['meta']['lat'])
	lons=np.array(data_vals['meta']['lon'])

	if options["maptype"] == "contourf":
		try:
			if not data_grid: 
				if data_vals.has_key('smry'):
					data_grid = np.array(data_vals['smry'][0])
				elif data_vals.has_key('data'):
					data_grid = np.array(data_vals['data'][0][1])
				else:
					print "Cannot find data array to map"
					sys.exit()
		except ValueError:
			pass
		contour_bounds = getBounds(data_grid, options)
		basemapper.filled_contour(data_grid.astype(float), lats, lons, contour_bounds, options)
	elif options["maptype"] == "dotmap":
		flats,flons,fvals = getValsFromFile(options["inputfile"])
		basemapper.dotmap(flats, flons, fvals, lats, lons, options)
	elif options["maptype"] == "interpf":
		flats,flons,fvals = getValsFromFile(options["inputfile"])
		if options.has_key("interpmethod") and options["interpmethod"] == "linear":
			farr = np.array([flons,flats]).T
			darr = np.array([lons,lats]).T
			data_grid = griddata_linear(farr, fvals, darr, method='linear')
			data_grid = data_grid.T
		else:
			data_grid = griddata_nn(flons, flats ,fvals, lons, lats, interp='nn')
		contour_bounds = getBounds(data_grid, options)
		basemapper.filled_contour(data_grid.astype(float), lats, lons, contour_bounds, options)
	elif options["maptype"] == "gridf":
		data_grid = np.load(options["inputfile"])
		contour_bounds = getBounds(data_grid, options)
		basemapper.filled_contour(data_grid.astype(float), lats, lons, contour_bounds, options)
	else:
		print "No plot produced; unknown map type",options["maptpe"]
		sys.exit()
