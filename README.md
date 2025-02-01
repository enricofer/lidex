# LIDar EXtractor

A Django app for easy publishing and serving human friendly extraction of point cloud coverage

## Build docker containers

```
docker build -t lidex_webapp:latest .
docker build -t lidex_qgis:latest ./build_qgis
docker build -t lidex_nginx:latest ./build_nginx
docker build -t lidex_mapproxy:latest ./build_mapproxy
docker build -t lidex_frontend_dev:latest -f ./wegue/Dockerfile_dev ./wegue
```


## Configuration

- add `'lidex'` to INSTALLED_APPS in settings.py webapp

- include 'urls.py' to webapp

- Add to settings.py lidex defaults

```
# point cloud tile index made by pdal tindex create ...
LIDEX_COVERAGE_INDEX_PATH = "/coverage/index.sqlite"
# tile index og22ogr format
LIDEX_COVERAGE_INDEX_FORMAT = "SQLite"
# tile index layer
LIDEX_COVERAGE_INDEX_LAYER = "pdal"
# point cloud and dsm/dtm srid
LIDEX_COVERAGE_INDEX_SRS = "EPSG:7792"
# output directory
LIDEX_OUTPUT_DIR = "/output"
# subpath in url
LIDEX_SUBPATH = "/lidex"
# dsm raster location
LIDEX_DSM_PATH = "/coverage/dsm.tif"
# dtm raster location
LIDEX_DTM_PATH = "/coverage/dtm.tif"
# sampling distance along section line
LIDEX_PROFILE_SAMPLING = 0.2
# pdal command path
LIDEX_PDAL_EXE = '/opt/conda/bin/pdal'
# potree converter command path
LIDEX_POTREECONVERTER_EXE = "/opt/PotreeConverter/build/PotreeConverter"
```

## endpoints

- #### raster sampling

  `[webapp base url]/lidex/raster/?sample=[x],[y]` returns json results]

- #### DXF profile extraction

  `[webapp base url]/lidex/profilo/[supporto]/ POST json data with line geometry` returns json results with dxf output location]

- #### Point cloud extraction in format .laz

  `[webapp base url]/lidex/punti/ POST json data with extent or geom(wkt geometry) ` returns json results with laz result and potree static site output location]

- #### Output file

  `[webapp base url]/lidex/output_file/[dir]/[file]/` returns file response

- #### Viewshed

  `[webapp base url]/lidex/viewshed/?observation=[x],[y]` returns file response with the location of dsm viewshed visibility from observation point