# PicIMG
Script to orthorectify oblique images (in csv) using the NASA Ames Stereo Pipeline (ASP)

## Dependences
ASP binaries should be in the Path
```
export PATH=${PATH}:/path/to/StereoPipeline/bin
```
Also pyproj and gdal must be installed in python

## Use
The way forward is to generate the terrain control points (GCP) file and then complete the routes and options within the script. The GCP file can be generated using different tools, but must be in the same format (and colnames) as in the [example](https://github.com/ealonsogzl/PicIMG/Data/GCPs.csv).
We found the [Pic2Map](https://github.com/tproduit/pic2map) toolbox very convenient for this task.
