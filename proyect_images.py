#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Draft of the pipeline to run ASP over several images.
ASP/bin should be in $PATH

Author: Esteban Alonso González - e.alonsogzl@gmail.com
"""

import pandas as pd
import subprocess
from pyproj import Proj, transform
import gdal
import glob
import os
import tempfile
import numpy as np
from PIL import Image


# Argumentos
files_path = './Data/files'
out_path = './Data/output'
dem_path = './Data/DEM_m.tif'
GCP_path = './Data/GCPs.csv'
focal = 617.6471
opt_cen1 = 320
opt_cen2 = 240
pixpich = 1
tr = 5
nprocess = 8

# Set projwindow, if provided as None the imput DEM is used
xmax = 266904.1671
xmin = 265320.6359
ymax = 4755356.6430
ymin = 4757847.5628


########################################################
# It should not be necesary to touch under this commet
########################################################


# get the list of images
photos = glob.glob(files_path + '/*.csv')

# Use first image to get the camera conditions
# create tmp name
tmp_dir = tempfile._get_default_tempdir()
tmp_name = next(tempfile._get_candidate_names()) + '.tif'
name_tmp = os.path.join(tmp_dir, tmp_name)

ima_nump = np.array(pd.read_csv(photos[0], delimiter=';', decimal=',',
                                header=None))
ima_nump = np.delete(ima_nump, 640, 1)
im = Image.fromarray(ima_nump)
im.save(name_tmp)


# Create options
ref = '--reference-dem ' + dem_path
flengt = '--focal-length ' + str(focal)
opt_cen = '--optical-center ' + str(opt_cen1) + ' ' + str(opt_cen2)
pp = '--pixel-pitch ' + str(pixpich)
output = '-o img.tsai'
tr = '--tr ' + str(tr)


# get coordinates of pixels in lon-lat
GCP = pd.read_csv(GCP_path)

inProj, outProj = Proj(init='epsg:32631'), Proj(init='epsg:4326')
GCP['newLon'], GCP['newLat'] = transform(inProj, outProj, GCP['X'].tolist(),
                                         GCP['Y'].tolist())


# create lon lat and pixel values options
lonlanvalues = GCP[['newLon', 'newLat']].to_string(header=False, index=False,
                                                   index_names=False)
lonlanvalues = lonlanvalues.replace('\n', ', ')

pixvalues = GCP[['line', 'column']].to_string(header=False, index=False,
                                              index_names=False)
pixvalues = pixvalues.replace('\n', ', ')


# run ASPcam_gen
order = 'cam_gen --refine-camera' + ' ' +\
    '--lon-lat-values ' + "'" + lonlanvalues + "'" + ' ' +\
    '--pixel-values ' + "'" + pixvalues + "'" + ' ' +\
    ref + ' ' + flengt + ' ' + opt_cen + ' ' + pp + ' ' +\
    name_tmp + ' ' + output + ' ' + '--gcp-file img.gcp --gcp-std 1e-3'

subprocess.call(order, shell=True)


# Optimize img.tsai
order = 'bundle_adjust ' + name_tmp + ' img.tsai img.gcp -o img.tsai' +\
    ' ' + '--inline-adjustments --robust-threshold 10000'
subprocess.call(order, shell=True)


# get extent of the raster if prjwin not provided
if (xmin is None or
    xmax is None or
    ymin is None or
        ymax is None):

    src = gdal.Open(dem_path)
    xmin, xres, xskew, ymax, yskew, yres = src.GetGeoTransform()
    xmax = xmin + (src.RasterXSize * xres)
    ymin = ymax + (src.RasterYSize * yres)


# create prowin option
projwin = '--t_projwin' + ' ' + str(int(xmin)) + ' ' + str(int(ymin)) +\
    ' ' + str(int(xmax)) + ' ' + str(int(ymax))

# Remove tmp image
os.unlink(name_tmp)

# create image from csv
for n in range(len(photos)):
    # out name
    name_out = os.path.join(out_path, 'proj_' +
                            os.path.basename(photos[n]).rsplit('.')[0] +
                            '.tif')

    # This 'if' is to allow to restart the process since the last file created
    if os.path.isfile(name_out):
        continue

    # create tmp name
    tmp_dir = tempfile._get_default_tempdir()
    tmp_name = next(tempfile._get_candidate_names()) + '.tif'
    name_tmp = os.path.join(tmp_dir, tmp_name)

    ima_nump = np.array(pd.read_csv(photos[n], delimiter=';', decimal=',',
                                    header=None))
    # HACK: remove last column as it is saved as empty column by the camera
    # software
    ima_nump = np.delete(ima_nump, 640, 1)
    im = Image.fromarray(ima_nump)
    im.save(name_tmp)

    order = 'mapproject --num-processes ' + str(nprocess) + ' ' + tr + ' ' +\
        projwin + ' ' + dem_path + ' ' + name_tmp + ' img.tsai-img.tsai ' +\
            name_out
    subprocess.call(order, shell=True)

# Remove tmp image
os.unlink(name_tmp)

