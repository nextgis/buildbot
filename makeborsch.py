# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *
import os

c = {}

repositories = [
    {'repo':'lib_z', 'args':[], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'py_sip', 'args':[], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_sqlite', 'args':['-DBUILD_TESTING=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_gif', 'args':[], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_geos', 'args':['-DBUILD_TESTING=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_qhull', 'args':[], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_expat', 'args':[], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'numpy', 'args':[], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'py_markupsafe', 'args':[], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'py_subprocess32', 'args':[], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'py_kiwisolver', 'args':[], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_jsonc', 'args':['-DBUILD_TESTING=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_spatialindex', 'args':['-DBUILD_TESTS=ON', '-DWITH_GTest_EXTERNAL=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_gsl', 'args':['-DBUILD_TESTING=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_yaml', 'args':['-DBUILD_TESTING=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'py_yaml', 'args':['-DWITH_YAML_EXTERNAL=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'py_psycopg', 'args':['-DWITH_OpenSSL_EXTERNAL=ON', '-DWITH_PostgreSQL_EXTERNAL=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'py_spatialite', 'args':['-DWITH_SQLite3_EXTERNAL=ON', '-DWITH_Spatialite_EXTERNAL=ON', '-DWITH_PROJ_EXTERNAL=ON', '-DWITH_GEOS_EXTERNAL=ON', '-DWITH_ICONV=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]}, # TODO: FreeXL,
    {'repo':'py_matplotlib', 'args':['-DWITH_PNG_EXTERNAL=ON', '-DWITH_Freetype_EXTERNAL=ON', '-DWITH_AGG_EXTERNAL=ON', '-DWITH_QHULL_EXTERNAL=ON', '-DWITH_NUMPY_EXTERNAL=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_jbig', 'args':['-DBUILD_TESTING=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_szip', 'args':['-DBUILD_TESTING=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_opencad', 'args':['-DBUILD_TESTING=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_openjpeg', 'args':['-DBUILD_TESTING=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_jpeg', 'args':['-DBUILD_TESTING=ON', '-DBUILD_JPEG_12=ON', '-DBUILD_JPEG_8=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_tiff', 'args':['-DBUILD_TESTING=ON', '-DWITH_ZLIB=ON', '-DWITH_JPEG_EXTERNAL=ON', '-DWITH_JBIG_EXTERNAL=ON', '-DWITH_LibLZMA_EXTERNAL=ON', '-DWITH_JPEG12_EXTERNAL=ON', '-DWITH_JPEG=ON', '-DWITH_JBIG=ON', '-DWITH_LibLZMA=ON', '-DWITH_JPEG12=ON','-DWITH_WEBP=ON', '-DWITH_WEBP_EXTERNAL=ON',], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_proj', 'args':['-DWITH_SQLite3=ON', '-DWITH_SQLite3_EXTERNAL=ON', '-DWITH_TIFF=ON', '-DWITH_TIFF_EXTERNAL=ON', '-DWITH_CURL=ON', '-DWITH_CURL_EXTERNAL=ON', '-DBUILD_TESTING=OFF', '-DGENERATE_PROJ_DB=OFF', '-DWITH_GTest_EXTERNAL=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_iconv', 'args':['-DBUILD_TESTING=ON'], 'requirements':[], 'os':['win32','win64'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_lzma', 'args':['-DWITH_ICONV=ON', '-DBUILD_TESTING=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_png', 'args':['-DWITH_ZLIB=ON', '-DPNG_TESTS=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_freetype', 'args':['-DWITH_ZLIB=ON', '-DWITH_PNG_EXTERNAL=ON', '-DWITH_PNG=ON', '-DWITH_BZip2=ON', '-DWITH_BZip2_EXTERNAL=ON', '-DWITH_HarfBuzz_EXTERNAL=ON','-DWITH_HarfBuzz=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]}, 
    {'repo':'lib_agg', 'args':['-DWITH_Freetype=ON', '-DWITH_Freetype_EXTERNAL=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_openssl', 'args':['-DOPENSSL_NO_DYNAMIC_ENGINE=ON', '-DWITH_ZLIB=ON', '-DBUILD_APPS=ON', '-DBUILD_TESTING=ON', '-DSTATIC_RUNTIME=ON'], 'requirements':[], 'os':['mac','win64','win32'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_curl', 'args':['-DENABLE_INET_PTON=OFF', '-DWITH_ZLIB=ON', '-DCMAKE_USE_OPENSSL=ON', '-DWITH_OpenSSL=ON', '-DWITH_OpenSSL_EXTERNAL=ON', '-DBUILD_TESTING=ON', '-DCMAKE_USE_LIBSSH2=OFF'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_xml2', 'args':['-DWITH_ZLIB=ON', '-DWITH_LibLZMA=ON', '-DWITH_LibLZMA_EXTERNAL=ON', '-DWITH_ICONV=ON', '-DBUILD_TESTING=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_pq', 'args':['-DWITH_OpenSSL=ON', '-DWITH_OpenSSL_EXTERNAL=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_spatialite', 'args':['-DWITH_ZLIB=ON', '-DWITH_LibXml2_EXTERNAL=ON', '-DWITH_LibXml2=ON', '-DWITH_ICONV=ON', '-DWITH_SQLite3_EXTERNAL=ON', '-DWITH_GEOS_EXTERNAL=ON', '-DWITH_PROJ_EXTERNAL=ON', '-DWITH_SQLite3=ON', '-DWITH_GEOS=ON', '-DWITH_PROJ=ON', '-DOMIT_FREEXL=ON', '-DENABLE_LWGEOM=FALSE','-DBUILD_TESTING=OFF', '-DBUILD_QT4=ON', '-DWITH_Qt4_EXTERNAL=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]}, # TODO: FreeXL, LWGEOM
    {'repo':'lib_geotiff', 'args':['-DWITH_ZLIB=ON', '-DWITH_TIFF=ON', '-DWITH_TIFF_EXTERNAL=ON', '-DWITH_PROJ=ON', '-DWITH_PROJ_EXTERNAL=ON', '-DWITH_JPEG=ON', '-DWITH_JPEG_EXTERNAL=ON', '-DWITH_JBIG=ON', '-DWITH_JBIG_EXTERNAL=ON', '-DWITH_LibLZMA=ON', '-DWITH_LibLZMA_EXTERNAL=ON', '-DWITH_SQLite3=ON', '-DWITH_SQLite3_EXTERNAL=ON', '-DWITH_UTILITIES=ON', '-DBUILD_TESTING=OFF'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_hdf4', 'args':['-DWITH_ZLIB=ON', '-DWITH_JPEG=ON', '-DWITH_JPEG_EXTERNAL=ON', '-DWITH_SZIP=ON', '-DWITH_SZIP_EXTERNAL=ON', '-DBUILD_TESTING=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':['-R','MFHDF_TEST-clearall|HDF_TEST-testhdf_thf']},
    {'repo':'lib_gdal', 'args':['-DWITH_ZLIB=ON', '-DWITH_EXPAT=ON', '-DWITH_EXPAT_EXTERNAL=ON', '-DWITH_JSONC=ON', '-DWITH_JSONC_EXTERNAL=ON', '-DWITH_ICONV=ON', '-DWITH_CURL=ON', '-DWITH_CURL_EXTERNAL=ON', '-DWITH_LibXml2=ON', '-DWITH_LibXml2_EXTERNAL=ON', '-DWITH_GEOS=ON', '-DWITH_GEOS_EXTERNAL=ON', '-DWITH_JPEG=ON', '-DWITH_JPEG_EXTERNAL=ON', '-DWITH_JPEG12=OFF', '-DWITH_JPEG12_EXTERNAL=OFF', '-DWITH_TIFF=ON', '-DWITH_TIFF_EXTERNAL=ON', '-DWITH_GeoTIFF=ON', '-DWITH_GeoTIFF_EXTERNAL=ON','-DWITH_JBIG=ON', '-DWITH_JBIG_EXTERNAL=ON', '-DWITH_GIF=ON', '-DWITH_GIF_EXTERNAL=ON', '-DWITH_OpenCAD=ON', '-DWITH_OpenCAD_EXTERNAL=ON', '-DWITH_PNG=ON', '-DWITH_PNG_EXTERNAL=ON', '-DWITH_PROJ=ON', '-DWITH_PROJ_EXTERNAL=ON', '-DWITH_OpenJPEG=ON', '-DWITH_OpenJPEG_EXTERNAL=ON', '-DENABLE_OPENJPEG=ON', '-DWITH_OpenSSL=ON', '-DWITH_OpenSSL_EXTERNAL=ON', '-DWITH_LibLZMA=ON', '-DWITH_LibLZMA_EXTERNAL=ON','-DWITH_PYTHON=ON', '-DWITH_PYTHON3=OFF', '-DENABLE_OZI=ON', '-DENABLE_NITF_RPFTOC_ECRGTOC=ON', '-DGDAL_ENABLE_GNM=ON', '-DWITH_OCI=ON','-DWITH_OCI_EXTERNAL=ON', '-DENABLE_OCI=ON', '-DENABLE_GEORASTER=ON','-DWITH_SQLite3=ON', '-DWITH_SQLite3_EXTERNAL=ON', '-DWITH_PostgreSQL=ON', '-DWITH_PostgreSQL_EXTERNAL=ON','-WITH_Boost=ON', '-DWITH_Boost_EXTERNAL=ON', '-DWITH_KML=ON', '-DWITH_KML_EXTERNAL=ON', '-DGDAL_BUILD_APPS=ON', '-DWITH_HDF4=ON','-DWITH_HDF4_EXTERNAL=ON','-DENABLE_HDF4=ON', '-DWITH_QHULL=ON', '-DWITH_QHULL_EXTERNAL=ON', '-DWITH_Spatialite=ON','-DWITH_Spatialite_EXTERNAL=ON','-DWITH_SZIP=ON','-DWITH_SZIP_EXTERNAL=ON','-DWITH_UriParser=ON', '-DWITH_UriParser_EXTERNAL=ON','-DWITH_NUMPY=ON', '-DWITH_NUMPY_EXTERNAL=ON','-DENABLE_WEBP=ON','-DWITH_WEBP=ON','-DWITH_WEBP_EXTERNAL=ON','-DBUILD_TESTING=ON', '-DSKIP_PYTHON_TESTS=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'python', 'args':['-DBUILD_LIBPYTHON_SHARED=ON', '-DWITH_OpenSSL_EXTERNAL=ON', '-DUSE_SYSTEM_ZLIB=ON', '-DWITH_ZLIB=ON', '-DWITH_EXPAT_EXTERNAL=ON', '-DWITH_SQlite3_EXTERNAL=ON', '-DUSE_SYSTEM_BZip2=ON', '-DWITH_BZip2_EXTERNAL=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_qt4', 'args':['-DWITH_ZLIB=ON', '-DWITH_OpenSSL_EXTERNAL=ON', '-DWITH_Freetype_EXTERNAL=ON', '-DWITH_JPEG_EXTERNAL=ON', '-DWITH_PNG_EXTERNAL=ON', '-DWITH_TIFF_EXTERNAL=ON', '-DWITH_SQLite3_EXTERNAL=ON', '-DWITH_PostgreSQL_EXTERNAL=ON', '-DWITH_ICONV=ON', '-DQT_CONFIGURE_ARGS=-webkit'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_qt5', 'args':['-DWITH_ZLIB=ON', '-DWITH_OpenSSL_EXTERNAL=ON', '-DWITH_Freetype_EXTERNAL=ON', '-DWITH_JPEG_EXTERNAL=ON', '-DWITH_PNG_EXTERNAL=ON', '-DWITH_TIFF_EXTERNAL=ON', '-DWITH_SQLite3_EXTERNAL=ON', '-DWITH_PostgreSQL_EXTERNAL=ON', '-DWITH_WEBPDEMUX_EXTERNAL=ON', '-DWITH_WEBPMUX_EXTERNAL=ON','-DWITH_WEBP_EXTERNAL=ON','-DWITH_HarfBuzz_EXTERNAL=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_qca', 'args':['-DWITH_Qt5_EXTERNAL=ON', '-DWITH_OpenSSL=ON', '-DWITH_OpenSSL_EXTERNAL=ON', '-DBUILD_PLUGINS=auto', '-DUSE_RELATIVE_PATHS=OFF', '-DCMAKE_INSTALL_PREFIX=/usr/', '-DBUILD_TESTS=OFF'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_qwt', 'args':['-DWITH_Qt4_EXTERNAL=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'py_qt4', 'args':['-DWITH_SIP_EXTERNAL=ON', '-DWITH_Qt4_EXTERNAL=ON', '-DWITH_ZLIB=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_qscintilla', 'args':['-DWITH_SIP_EXTERNAL=ON', '-DWITH_Qt4_EXTERNAL=ON', '-DWITH_BINDINGS=ON', '-DWITH_PyQt4_EXTERNAL=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'nextgisqgis', 'args':['-DWITH_EXPAT_EXTERNAL=ON', '-DWITH_GDAL_EXTERNAL=ON', '-DWITH_GEOS_EXTERNAL=ON', '-DWITH_GSL_EXTERNAL=ON', '-DWITH_LibXml2_EXTERNAL=ON', '-DWITH_PostgreSQL_EXTERNAL=ON', '-DWITH_PROJ_EXTERNAL=ON', '-DWITH_Qca_EXTERNAL=ON', '-DWITH_Qscintilla_EXTERNAL=ON', '-DWITH_Qwt_EXTERNAL=ON', '-DWITH_SpatialIndex_EXTERNAL=ON', '-DWITH_Spatialite_EXTERNAL=ON', '-DWITH_SQLite3_EXTERNAL=ON', '-DWITH_SIP_EXTERNAL=ON', '-DWITH_Qt4_EXTERNAL=ON', '-DWITH_BINDINGS=ON', '-DWITH_PyQt4_EXTERNAL=ON', '-DWITH_Qsci_EXTERNAL=ON', '-DWITH_ZLIB=ON', '-DWITH_NGSTD_EXTERNAL=ON', '-DWITH_OpenCV_EXTERNAL=ON', '-DWITH_OCI_EXTERNAL=ON'], 'requirements':['PyQt4', 'six'], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis', 'test_regex':[]},
    {'repo':'lib_ngstd', 'args':['-DBUILD_QT5=ON', '-DWITH_GDAL_EXTERNAL=ON', '-DWITH_SENTRYNATIVE_EXTERNAL=ON', '-DWITH_OpenSSL_EXTERNAL=ON', '-DWITH_ZLIB_EXTERNAL=ON', '-DWITH_Qt5_EXTERNAL=ON', '-DBUILD_QT4=ON', '-DWITH_SIP_EXTERNAL=ON', '-DWITH_Qt4_EXTERNAL=ON', '-DWITH_PyQt4_EXTERNAL=ON', '-DWITH_BINDINGS=ON', '-DBUILDBOT_PASSWORD=' + os.environ.get("BUILDBOT_PASSWORD", "0000"),'-DBUILDBOT_USER=' + os.environ.get("BUILDBOT_USER", "buildbot"),], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis', 'test_regex':[]},
    {'repo':'formbuilder', 'args':['-DBUILD_NEXTGIS_PACKAGE=ON', '-DWITH_GDAL_EXTERNAL=ON','-DWITH_ZLIB=ON', '-DWITH_Qt5_EXTERNAL=ON', '-DWITH_NGSTD_EXTERNAL=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis', 'test_regex':[]},
    {'repo':'lib_opencv', 'args':['-DWITH_GDAL_EXTERNAL=ON','-DWITH_ZLIB=ON','-DWITH_PNG_EXTERNAL=ON','-DWITH_JPEG_EXTERNAL=ON','-DWITH_TIFF_EXTERNAL=ON','-DWITH_WEBP_EXTERNAL=ON', '-DWITH_OpenJPEG_EXTERNAL=ON', '-DBUILD_opencv_ts=OFF','-DBUILD_opencv_apps=ON','-DBUILD_TESTS=OFF','-DBUILD_PERF_TESTS=OFF'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':['-R','opencv_test_(fl|co)']},
    {'repo':'manuscript', 'args':['-DWITH_Qt5_EXTERNAL=ON', '-DWITH_ZLIB=ON', '-DWITH_NGSTD_EXTERNAL=ON',], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis', 'test_regex':[]},
    {'repo':'lib_oci', 'args':['-DWITH_Qt4_EXTERNAL=ON', '-DBUILD_QT4=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'py_shapely', 'args':['-DWITH_GEOS_EXTERNAL=ON', '-DWITH_NUMPY_EXTERNAL=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_uriparser', 'args':[], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_kml', 'args':['-DWITH_ZLIB=ON', '-DWITH_Boost=ON', '-DWITH_Boost_EXTERNAL=ON', '-DWITH_UriParser=ON', '-DWITH_UriParser_EXTERNAL=ON', '-DWITH_EXPAT=ON', '-DWITH_EXPAT_EXTERNAL=ON', '-DBUILD_TESTING=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':['-E','engine_style_resolver|dom_round_trip|engine_feature_view|engine_kmz_file|engine_style_inliner|engine_update']},
    {'repo':'py_proj', 'args':['-DWITH_PROJ_EXTERNAL=ON'], 'requirements':['cython'], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_openblas', 'args':['-DBUILD_TESTING=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'py_sci', 'args':[], 'requirements':['numpy'], 'os':['win32','win64'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_littlecms', 'args':['-DBUILD_TESTS=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_webp', 'args':['-DWITH_PNG_EXTERNAL=ON','-DWITH_JPEG_EXTERNAL=ON','-DWITH_TIFF_EXTERNAL=ON','-DWITH_GIF_EXTERNAL=ON','-DBUILD_TESTING=ON','-DWEBP_BUILD_VWEBP=OFF', '-DWEBP_BUILD_CWEBP=OFF', '-DWEBP_BUILD_DWEBP=OFF'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_bzip2', 'args':['-DBUILD_TESTING=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_harfbuzz', 'args':['-DHB_HAVE_FREETYPE=ON','-DWITH_Freetype_EXTERNAL=ON','-DWITH_Freetype=ON', '-DHB_HAVE_CORETEXT=OFF', '-DHB_BUILD_SUBSET=OFF', '-DHB_BUILD_TESTS=OFF'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'py_pillow', 'args':['-DWITH_JPEG_EXTERNAL=ON','-DWITH_OpenJPEG_EXTERNAL=ON','-DWITH_TIFF_EXTERNAL=ON','-DWITH_Freetype_EXTERNAL=ON','-DWITH_LCMS_EXTERNAL=ON','-DWITH_WEBP_EXTERNAL=ON','-DWITH_WEBPMUX_EXTERNAL=ON','-DWITH_WEBPDEMUX_EXTERNAL=ON', '-DWITH_ZLIB=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'nextgis_datastore', 'args':['-DWITH_OpenSSL=ON', '-DWITH_OpenSSL_EXTERNAL=ON', '-DWITH_GEOS=ON', '-DWITH_GEOS_EXTERNAL=ON', '-DWITH_GDAL=ON', '-DWITH_GDAL_EXTERNAL=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis', 'test_regex':[]},
    {'repo':'lib_sentrynative', 'args':['-DWITH_CRASHPAD_EXTERNAL=ON', '-DWITH_CURL_EXTERNAL=ON', '-DWITH_MINICHROMIUM_EXTERNAL=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_qtkeychain', 'args':['-DWITH_Qt5_EXTERNAL=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_zip', 'args':['-DWITH_ZLIB_EXTERNAL=ON', '-DENABLE_GNUTLS=OFF', '-DENABLE_BZIP2=OFF', '-DENABLE_LZMA=OFF'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_xslt', 'args':['-DWITH_LIBXML2=ON', '-DWITH_LIBXML2_EXTERNAL=ON', '-DWITH_ICONV=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'py_lxml', 'args':['-DWITH_LIBXML2=ON', '-DWITH_LIBXML2_EXTERNAL=ON', '-DWITH_LIBXSLT_EXTERNAL=ON', '-DWITH_ZLIB=ON', '-DWITH_ICONV=ON'], 'requirements':[''], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'lib_exiv', 'args':['-DWITH_ZLIB_EXTERNAL=ON', '-DWITH_EXPAT_EXTERNAL=ON', '-DWITH_ICONV=ON','-DWITH_ICONV_EXTERNAL=ON'], 'requirements':[''], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis-borsch', 'test_regex':[]},
    {'repo':'nextgisutilities', 'args':['-DWITH_GDAL_EXTERNAL=ON', '-DWITH_GEOS_EXTERNAL=ON', '-DWITH_PROJ_EXTERNAL=ON'], 'requirements':[], 'os':['win32','win64','mac'], 'repo_root':'git://github.com', 'org':'nextgis', 'test_regex':[]},
]

skip_send2github = [
    "nextgisqgis", "formbuilder", "manuscript",
]

vm_cpu_count = 8

mac_os_min_version = '10.12'
mac_os_sdks_path = '/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs'

release_script_src = 'https://raw.githubusercontent.com/nextgis-borsch/borsch/master/opt/repka_release.py' # 'https://raw.githubusercontent.com/nextgis-borsch/borsch/master/opt/github_release.py'
script_name = 'repka_release.py' # 'github_release.py'
username = 'buildbot' # username = 'bishopgis'
userkey = os.environ.get("BUILDBOT_PASSWORD") # userkey = os.environ.get("BUILDBOT_APITOKEN_GITHUB")
ngftp_base = 'ftp://192.168.245.1:8121'
ngftp = ngftp_base + '/software/installer/src/'
ngftp_user = os.environ.get("BUILDBOT_FTP_USER")
upload_script_src = 'https://raw.githubusercontent.com/nextgis/buildbot/master/worker/ftp_uploader.py'
upload_script_name = 'ftp_upload.py'
install_script_src = 'https://raw.githubusercontent.com/nextgis/buildbot/master/worker/install_from_ftp.py'
install_script_name = 'install_from_ftp.py'
ci_project_name = 'create_installer'

c['change_source'] = []
c['schedulers'] = []
c['builders'] = []

platforms = [
    {'name' : 'win32', 'worker' : 'build-win'},
    {'name' : 'win64', 'worker' : 'build-win'},
    {'name' : 'mac', 'worker' : 'build-mac'},
    {'name' : 'win32-static', 'worker' : 'build-win'},
    {'name' : 'win64-static', 'worker' : 'build-win'},
    {'name' : 'mac-static', 'worker' : 'build-mac'},
]

build_lock = util.MasterLock("borsch_worker_builds")
# build_lock = util.WorkerLock("borsch_worker_builds",
#                              maxCount=1,
#                              maxCountForWorker={'build-win': 1, 'build-mac': 1}
#                              )

logfile = 'stdio'
generator = 'Visual Studio 15 2017'

def get_env(os):
    env = {}
    if 'win32' == os:
        env['PYTHONPATH'] = 'C:\\Python27_32'
        env['PATH'] = [
            "C:\\Perl64\\site\\bin",
            "C:\\Perl64\\bin",
            "C:\\Python27_32",
            "C:\\Python27_32\\Scripts",
            "C:\\Windows\\system32",
            "C:\\Windows",
            "C:\\Windows\\System32\\Wbem",
            "C:\\Windows\\System32\\WindowsPowerShell\\v1.0",
            "C:\\Program Files\\Git\\cmd",
            "C:\\Program Files (x86)\\Xoreax\\IncrediBuild",
            "C:\\Program Files\\CMake\\bin",
            "C:\\Python27_32\\lib\\site-packages\\pywin32_system32",
            "C:\\Program Files (x86)\\IntelSWTools\\compilers_and_libraries\\windows\\bin\\intel64", # _ia32
        ]
        env['ARCH_PATH'] = 'ia32'
        env['C_TARGET_ARCH'] = 'ia32'
        env['INTEL_TARGET_ARCH_IA32'] = 'ia32'
        env['NDK_ARCH'] = 'x86'
        env['TARGET_ARCH'] = 'ia32'
        env['TARGET_VS'] = '2017'
        env['TARGET_VS_ARCH'] = 'x86'
        env['LANG'] = 'en_US'
        env['BUILDBOT_USERPWD'] = '{}:{}'.format(username, userkey)
    elif 'win64' == os:
        env['PYTHONPATH'] = 'C:\\Python27'
        env['PATH'] = [
            "C:\\Perl64\\site\\bin",
            "C:\\Perl64\\bin",
            "C:\\Python27",
            "C:\\Python27\\Scripts",
            "C:\\Windows\\system32",
            "C:\\Windows",
            "C:\\Windows\\System32\\Wbem",
            "C:\\Windows\\System32\\WindowsPowerShell\\v1.0",
            "C:\\Program Files\\Git\\cmd",
            "C:\\Program Files (x86)\\Xoreax\\IncrediBuild",
            "C:\\Program Files\\CMake\\bin",
            "C:\\Python27\\lib\\site-packages\\pywin32_system32",
            "C:\\Program Files (x86)\\IntelSWTools\\compilers_and_libraries\\windows\\bin\\intel64",
        ]
        env['BUILDBOT_USERPWD'] = '{}:{}'.format(username, userkey)
    elif 'mac' == os:
        env = {
            'PATH': [
                        "/usr/local/bin",
                        "${PATH}"
                    ],
            'MACOSX_DEPLOYMENT_TARGET': mac_os_min_version,
            'BUILDBOT_USERPWD': '{}:{}'.format(username, userkey),
        }
    return env

def install_dependencies(factory, requirements, os):
    env = get_env(os)

    for requirement in requirements:
        if requirement == 'perl' and 'win' in os: # This is example. Perl already installed in VM.
            # Upload distro to worker
            factory.addStep(steps.FileDownload(
                            mastersrc="/opt/buildbot/distrib/perl.msi",
                            workerdest="perl.msi"))
            # Execute install
            factory.addStep(steps.ShellCommand(command=['msiexec', '/package', 'perl.msi', '/quiet', '/norestart'],
                                                name="install " + requirement,
                                                description=[requirement, "install"],
                                                descriptionDone=[requirement, "installed"],
                                                haltOnFailure=True))
        elif requirement == 'numpy':
            factory.addStep(
                steps.ShellCommand(command=['pip', 'install', '--user', 'numpy'],
                                    name="install " + requirement,
                                    description=[requirement, "install"],
                                    descriptionDone=[requirement, "installed"],
                                    haltOnFailure=True,
                                    env=env)
            )
        elif requirement == 'six':
            factory.addStep(
                steps.ShellCommand(command=['pip', 'install', '--user', 'six'],
                                    name="install " + requirement,
                                    description=[requirement, "install"],
                                    descriptionDone=[requirement, "installed"],
                                    haltOnFailure=True,
                                    env=env)
            )
        elif requirement == 'cython':
            factory.addStep(
                steps.ShellCommand(command=['pip', 'install', '--user', 'cython'],
                                    name="install " + requirement,
                                    description=[requirement, "install"],
                                    descriptionDone=[requirement, "installed"],
                                    haltOnFailure=True,
                                    env=env)
            )
        elif requirement == 'PyQt4' and os == 'mac':
            factory.addStep(steps.ShellSequence(commands=[
                    util.ShellArg(command=["curl", install_script_src, '-o', install_script_name, '-s', '-L'], logfile=logfile),
                    util.ShellArg(command=["python", install_script_name, '--ftp_user', ngftp_user,
                        '--ftp', ngftp_base, '--build_path', 'install',
                        '--platform', 'mac', '--create_pth', '--packages', 'lib_freetype', 'lib_gif', 'lib_jpeg', 'lib_png', 'lib_sqlite', 'lib_tiff', 'lib_z', 'py_sip', 'lib_qt4', 'py_qt4'], logfile=logfile),
                ],
                name="Install PyQt4",
                haltOnFailure=True,
                env=env))

# Create builders
for repository in repositories:

    project_name = repository['repo']
    org = repository['org']
    repourl = '{}/{}/{}.git'.format(repository['repo_root'], org, project_name)
    branch = 'master'
    if 'branch' in repository:
        branch = repository['branch']
    git_project_name = '{}/{}'.format(org, project_name)
    git_poller = changes.GitPoller(project = git_project_name,
                           repourl = repourl,
                           workdir = project_name + '-workdir',
                           branches = [branch],
                           pollinterval = 3600,)
    c['change_source'].append(git_poller)

    builderNames = []
    for platform in platforms:
        if platform['name'] not in repository['os']:
            continue
        builderNames.append(project_name + "_" + platform['name'])

    scheduler = schedulers.SingleBranchScheduler(
                                name=project_name,
                                change_filter=util.ChangeFilter(project = git_project_name, branch=branch),
                                treeStableTimer=1*60,
                                builderNames=builderNames,)
    c['schedulers'].append(scheduler)

    forceScheduler = schedulers.ForceScheduler(
                                name=project_name + "_force",
                                label="Force build",
                                buttonName="Force build",
                                builderNames=builderNames,)
    c['schedulers'].append(forceScheduler)

    run_args = repository['args']
    run_args.extend(['-DSUPPRESS_VERBOSE_OUTPUT=ON', '-DCMAKE_BUILD_TYPE=Release', '-DSKIP_DEFAULTS=ON'])
    cmake_build = ['cmake', '--build', '.', '--config', 'Release', '--']

    for platform in platforms:
        if platform['name'] not in repository['os']:
            continue

        code_dir_last = 'src'
        code_dir = os.path.join('build', code_dir_last)
        build_subdir = 'bld'
        build_dir = os.path.join(code_dir, build_subdir)

        run_args_ex = list(run_args)
        cmake_build_ex = list(cmake_build)
        env = {}

        if 'win' in platform['name']:
            if platform['name'].endswith('-static'):
                run_args_ex.append('-DBUILD_STATIC_LIBS=ON')
            else:
                run_args_ex.append('-DBUILD_SHARED_LIBS=ON')

            if '-DWITH_ICONV=ON' in repository['args']:
                run_args_ex.append('-DWITH_ICONV_EXTERNAL=ON')
            if '-DWITH_ZLIB=ON' in repository['args']:
                run_args_ex.append('-DWITH_ZLIB_EXTERNAL=ON')

            cmake_build_ex.append('/m:' + str(vm_cpu_count))
            env = {}
            if 'win32' in platform['name']:
                env = get_env('win32')
                env['PATH'].append("C:\\buildbot\worker\\" + project_name + "_" + platform['name'] + "\\build\\" + code_dir_last + "\\" + build_subdir + "\\release")
                run_args_ex.extend(['-G', generator])
            else:
                env = get_env('win64')
                env['PATH'].append("C:\\buildbot\worker\\" + project_name + "_" + platform['name'] + "\\build\\" + code_dir_last + "\\" + build_subdir + "\\release")
                run_args_ex.extend(['-G', generator + ' Win64'])
        elif 'mac' in platform['name']:
            if platform['name'].endswith('-static'):
                run_args_ex.append('-DBUILD_STATIC_LIBS=OM')
            else:
                run_args_ex.append('-DOSX_FRAMEWORK=ON')
            run_args_ex.extend(
                [
                    '-DCMAKE_OSX_SYSROOT=' + mac_os_sdks_path + '/MacOSX.sdk', 
                    '-DCMAKE_OSX_DEPLOYMENT_TARGET=' + mac_os_min_version
                ]
            )
            cmake_build_ex.append('-j' + str(vm_cpu_count))
            env = get_env('mac')

        factory = util.BuildFactory()

        install_dependencies(factory, repository['requirements'], platform['name'])

        factory.addStep(steps.Git(repourl=repourl, mode='full', shallow=True,
                                method='clobber', submodules=False, workdir=code_dir))

        factory.addStep(steps.ShellSequence(commands=[
                util.ShellArg(command=["curl", release_script_src, '-o', script_name, '-s', '-L'], logfile=logfile),
                util.ShellArg(command=["curl", upload_script_src, '-o', upload_script_name, '-s', '-L'], logfile=logfile),
            ],
            name="Download scripts",
            haltOnFailure=True,
            workdir=code_dir,
            env=env))

        factory.addStep(steps.MakeDirectory(dir=build_dir, name="Make build directory"))

        # configure view cmake
        factory.addStep(steps.ShellCommand(command=["cmake", run_args_ex, '..'],
                                           name="configure",
                                           haltOnFailure=True,
                                           timeout=125 * 60,
                                           maxTime=5 * 60 * 60,
                                           workdir=build_dir,
                                           env=env))

        # make
        factory.addStep(steps.ShellCommand(command=cmake_build_ex,
                                           name="make",
                                           haltOnFailure=True,
                                           timeout=125 * 60,
                                           maxTime=15 * 60 * 60,
                                           workdir=build_dir,
                                           env=env))

        # make tests
        test_cmd = ['ctest', '-C', 'Release', '--output-on-failure']
        if repository['test_regex']:
            test_cmd.extend(repository['test_regex'])
        factory.addStep(steps.ShellCommand(command=test_cmd,
                                           name="test",
                                           haltOnFailure=True,
                                           timeout=125 * 60,
                                           maxTime=5 * 60 * 60,
                                           workdir=build_dir,
                                           env=env))

        # make package
        factory.addStep(steps.ShellCommand(command=['cpack', '-C', 'Release', '-V', '.'],
                                           name="pack",
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))

        # send package to github
        if project_name not in skip_send2github:
            # factory.addStep(steps.ShellCommand(command=['python', script_name, '--login',
            #                                         username, '--key', userkey, '--build_path', build_subdir
            #                                         ],
            #                                name="send package to github",
            #                                haltOnFailure=True,
            #                                workdir=code_dir))
            factory.addStep(steps.ShellCommand(command=['python', script_name, '--login',
                                                    username, '--password', userkey, '--build_path', build_subdir
                                                    ],
                                           name="send package to rm.nextgis.com",
                                           haltOnFailure=True,
                                           workdir=code_dir))

        # upload to ftp
        factory.addStep(steps.ShellCommand(command=['python', upload_script_name,
                                                    '--ftp_user', ngftp_user, '--ftp',
                                                    ngftp + project_name + '_' + platform['name'],
                                                    '--build_path', build_subdir],
                                           name="send package to ftp",
                                           haltOnFailure=True,
                                           workdir=code_dir))

        # create installer trigger
        if platform['name'].endswith('-static') == False:
            factory.addStep(steps.Trigger(schedulerNames=[ci_project_name + '_' + platform['name']],
                                        waitForFinish=False,
                                        set_properties={
                                            'suffix' : '-dev',
                                            'notes' : 'Update ' + project_name,
                                            'url' : 'https://rm.nextgis.com/api/repo',
                                        }))

        builder = util.BuilderConfig(name = project_name + "_" + platform['name'],
                                    workernames = [platform['worker']],
                                    factory = factory,
                                    locks = [build_lock.access('exclusive')], # counting
                                    description="Make {} on {}".format(project_name, platform['name']),)

        c['builders'].append(builder)
