# -*- python -*-
# ex: set syntax=python:
env_vars = {
    "LIB": ["${LIB}", "${OSGEO4W_ROOT}\\lib", "${OSGEO4W_ROOT}\\apps\\Python27\\libs", "${MICROSOFT_SDK}\\lib", "${GDAL_2_0}\\lib"],
    "INCLUDE": ["${INCLUDE}", "${OSGEO4W_ROOT}\\include", "${GDAL_2_0}\\include" ],
    "PATH": ["${PATH}", "${OSGEO4W_ROOT}\\bin", "${OSGEO4W_ROOT}\\apps\\Python27\\Scripts", "${GDAL_2_0}\\bin"],
    "PYTHONHOME": ["${OSGEO4W_ROOT}\\apps\\Python27"],
    "QT_PLUGIN_PATH": ["${OSGEO4W_ROOT}\\apps\\Qt4\\plugins"],
    "QT_RASTER_CLIP_LIMIT": ["4096"]
}