
import math
import numpy as N


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def gridSearch(locus_lon, locus_lat, search_radius, lons_grid, lats_grid):

    # start with all nodes within rectangular area bounded by search radius
    bbox = (locus_lon-search_radius, locus_lon+search_radius,
            locus_lat-search_radius, locus_lat+search_radius)
    indexes = N.where( (lons_grid >= bbox[0]) & (lats_grid >= bbox[2]) &
                       (lons_grid <= bbox[1]) & (lats_grid <= bbox[3]) )

    node_lons = lons_grid[indexes]
    lon_diffs = locus_lon - node_lons
    node_lats = lats_grid[indexes]
    lat_diffs = locus_lat - node_lats
    sum_of_squares = (lon_diffs*lon_diffs) + (lat_diffs*lat_diffs)
    distances = N.sqrt(sum_of_squares)

    return indexes, distances


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def arraySearch(locus_lon, locus_lat, search_radius, lons_array, lats_array):

    # start with all nodes within rectangular area bounded by search radius
    bbox = (locus_lon-search_radius, locus_lon+search_radius,
            locus_lat-search_radius, locus_lat+search_radius)
    indexes = N.where( (lons_array >= bbox[0]) & (lats_array >= bbox[2]) &
                       (lons_array <= bbox[1]) & (lats_array <= bbox[3]) )
    indexes.sort()

    array_indexes = [ ]
    distances = [ ]

    # narrow list down to those nodes taht are actually in the search circle
    for indx in indexes[0]:

        lon_diff = locus_lon - lons_array[indx]
        lat_diff = locus_lat - lats_array[indx]

        # do not include locus point
        if abs(lon_diff) < 1e-6 and abs(lat_diff) < 1e-6 : continue

        distance = math.sqrt((lon_diff*lon_diff)+(lat_diff*lat_diff))
        # elimate anything outside search circle
        if distance > search_radius: continue
        
        array_indexes.append(indx)
        distances.append(distance)

    return N.array(array_indexes), N.array(distances)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def radialSearch(locus_lon, locus_lat, search_radius, lons_grid, lats_grid,
                 coordinate_order='xy'):

    if coordinate_order == 'yx':
        x_indx = 1
        y_indx = 0
    else:
        x_indx = 0
        y_indx = 1

    indexes, distance = gridSearch(locus_lon, locus_lat, search_radius,
                                   lons_grid, lats_grid)

    x_indexes = [ ]
    y_indexes = [ ] 
    distances = [ ]

    # narrow list down to those nodes taht are actually in the search circle
    for indx in range(len(indexes[0])):
        dist = distance[indx]
        # do not include points outside the circle
        if dist > search_radius: continue
        # do not include locus point
        if abs(dist) < 1e-6 : continue

        x_indexes.append(indexes[x_indx][indx])
        y_indexes.append(indexes[y_indx][indx])
        distances.append(dist)

    indexes = [[],[]]
    indexes[x_indx] = N.array(x_indexes)
    indexes[y_indx] = N.array(y_indexes)
    return indexes, N.array(distances)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def relativeSearch(locus_x, locus_y, relative_indexes, lons_grid, lats_grid,
                   coordinate_order='xy'):

    if coordinate_order == 'yx':
        x_indx = 1
        y_indx = 0
        nodeValue = lambda grid,x,y : grid[y,x]
    else:
        x_indx = 0
        y_indx = 1
        nodeValue = lambda grid,x,y : grid[x,y]

    locus_lon = nodeValue(lons_grid,locus_x,locus_y)
    locus_lat = nodeValue(lats_grid,locus_x,locus_y)

    max_y = lons_grid.shape[y_indx]-1
    max_x = lons_grid.shape[x_indx]-1

    x_indexes = [ ]
    y_indexes = [ ]
    distances = [ ]

    for indx in range(len(relative_indexes[0])):
        # only use nodes that are actually in the grid
        node_x = locus_x + relative_indexes[x_indx][indx]
        if node_x < 0: continue
        elif node_x > max_x: continue
        
        node_y = locus_y + relative_indexes[y_indx][indx]
        if node_y < 0: continue
        elif node_y > max_y: continue

        x_indexes.append(node_x)
        y_indexes.append(node_y)

        # calculate the distance between nodes in decimal degrees
        lon_diff = locus_lon - nodeValue(lons_grid,node_x,node_y)
        lat_diff = locus_lat - nodeValue(lats_grid,node_x,node_y)
        distance = math.sqrt((lon_diff*lon_diff)+(lat_diff*lat_diff))
        distances.append(distance)

    indexes = [[],[]]
    indexes[x_indx] = N.array(x_indexes)
    indexes[y_indx] = N.array(y_indexes)
    return indexes, N.array(distances)

