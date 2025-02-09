# LIDar EXtractor

A Django app for easy publishing and serving human friendly extraction of point cloud coverage

## Build docker containers

```
docker compose build
```

## Copy coverage data

Copy the point cloud coverage and dtm/dsm raster data inside .data/coverage folder

A test coverage is available in `test_coverage` folder

```
mv test_coverage/* data/coverage/
```

## Configuration

- copy enviroment variables template

  `cp .env_template .env`

- edit config file

  `nano .env`

- edit webgis default config (ref: [wegue configuration](https://wegue-oss.github.io/wegue/#/wegue-configuration))

  `nano wegue_custom_app/wegue_custom/static/app-conf.json`

## Start Service

  ```
  docker compose up -d
  ```

## Endpoints

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