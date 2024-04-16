from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect,JsonResponse,HttpResponse, FileResponse, HttpResponseServerError
from django.urls import reverse
from django.template.loader import render_to_string, get_template
from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.conf import settings

import json
import uuid
import subprocess
import os
from pathlib import Path
import shutil
from datetime import datetime
import struct
import math

from osgeo import gdal,osr
from affine import Affine
from osgeo_utils import gdal_calc

import numpy as np

import ezdxf

dxfcols = {
   "dtm": 1,
   "dsm": 3
}

from pdal_cmd import pdal_tindex_merge, potreeConvert, pdal_info

def get_size(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    print ("OUTPUT_SIZE", total_size)
    return total_size

def clean_output_buffer(size):
   paths = sorted(Path(settings.PDAL_OUTPUT_DIR).iterdir(), key=os.path.getmtime)
   print("SORTED OUTPUT DIRS:", paths)
   totsize = get_size(settings.PDAL_OUTPUT_DIR)
   while paths and totsize > size :
      totsize = totsize - get_size(paths[0])
      print ("deleting", paths[0], totsize)
      shutil.rmtree(paths[0])
      del paths[0]

PRIVATE_IPS_PREFIX = ('10.', '172.', '192.', )

def get_client_ip(request):
    """get the client ip from the request
    """
    remote_address = request.META.get('REMOTE_ADDR')
    ip = remote_address
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        proxies = x_forwarded_for.split(',')
        while (len(proxies) > 0 and
                proxies[0].startswith(PRIVATE_IPS_PREFIX)):
            proxies.pop(0)
        if len(proxies) > 0:
            ip = proxies[0]
    return ip

def extract_point_from_raster(data_source, p, band_number=1):
    """Return floating-point value that corresponds to given point."""

    # Convert point co-ordinates so that they are in same projection as raster
    #point_sr = point.GetSpatialReference()
    #raster_sr = osr.SpatialReference()
    #raster_sr.ImportFromWkt(data_source.GetProjection())
    #transform = osr.CoordinateTransformation(point_sr, raster_sr)
    #point.Transform(transform)

    # Convert geographic co-ordinates to pixel co-ordinates
    #x, y = point.GetX(), point.GetY()
    x, y  = p
    forward_transform = Affine.from_gdal(*data_source.GetGeoTransform())
    reverse_transform = ~forward_transform
    px, py = reverse_transform * (x, y)
    px, py = int(px + 0.5), int(py + 0.5)

    # Extract pixel value
    band = data_source.GetRasterBand(band_number)
    structval = band.ReadRaster(px, py, 1, 1, buf_type=gdal.GDT_Float32)
    result = struct.unpack('f', structval)[0]
    if result == band.GetNoDataValue():
        result = float('nan')
    return result


def clip_raster(data_source,output_dir,wkt_polygon,srid,name="clipped"):
  clip_raster = os.path.join(output_dir,"%s.tif" % name)
  polygon_json = os.path.join(output_dir,"%s.geojson" % name)
  bound = GEOSGeometry(wkt_polygon)
  feature_json = """
{
"type": "FeatureCollection",
"name": "clipped",
"crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG:%s" } },
"features": [
{ "type": "Feature", "properties": { "FID": 0 }, "geometry":  %s  }
]
}
""" % (srid, bound.geojson)
  with open(polygon_json,"w") as outjson:
     outjson.write( feature_json )
  clip_ds = gdal.Warp(
    clip_raster, 
    data_source, 
    cutlineDSName=polygon_json,
    cropToCutline=True,
    dstNodata = 0
  )
  return clip_raster



@csrf_exempt
def raster_clip(request):
  wkt = "MultiPolygon (((725756.99194004340097308 5033097.3502550395205617, 725758.98586401692591608 5033101.92823928128927946, 725760.93224944337271154 5033106.28984660189598799, 725764.55172856152057648 5033114.38015291187912226, 725764.68686586804687977 5033114.67864623293280602, 725765.46170322201214731 5033116.39011867251247168, 725767.5616444549523294 5033121.10003831516951323, 725769.40159250260330737 5033125.33996577281504869, 725771.25154011743143201 5033129.63989212457090616, 725773.57147413236089051 5033135.00961163453757763, 725776.49330876884050667 5033152.57359787728637457, 725778.06127960572484881 5033161.99912041146308184, 725780.19118764076847583 5033174.81907565984874964, 725780.44093347317539155 5033176.42014800477772951, 725781.31035933317616582 5033176.46436056867241859, 725797.39726133039221168 5033175.16005070507526398, 725816.34649835014715791 5033173.6237223306670785, 725839.02348420722410083 5033171.78516298532485962, 725839.0435239520156756 5033171.78353824466466904, 725839.00929532910231501 5033171.30715669319033623, 725838.78519657766446471 5033169.77434113249182701, 725838.60010954912286252 5033169.02923425193876028, 725838.09123523777816445 5033166.26529488246887922, 725837.85642019752413034 5033164.98990227561444044, 725832.50502913608215749 5033135.92394216172397137, 725832.6223568522837013 5033135.9668340552598238, 725820.50540597876533866 5033067.29173220880329609, 725819.40248168481048197 5033067.82572093419730663, 725780.94716244575101882 5033086.22425184678286314, 725757.21896891528740525 5033097.15096196159720421, 725756.95826569583732635 5033097.28050541877746582, 725756.99194004340097308 5033097.3502550395205617)))"
  output_dir = os.path.join(settings.PDAL_OUTPUT_DIR,uuid.uuid4().hex)
  os.makedirs(output_dir)
  res_dsm = clip_raster("/coverage/dsm.tif", output_dir, wkt, "32632", "clipped_dsm")
  res_dtm = clip_raster("/coverage/dtm.tif", output_dir, wkt, "32632", "clipped_dtm")
  res_h1 = os.path.join(output_dir, "clipped_tmp.tif" )
  res_h2 = os.path.join(output_dir, "clipped_h.tif" )
  res_ds1 = gdal_calc.Calc("((A-B)>0.5)*(A-B)", A=res_dsm, B=res_dtm, outfile=res_h1)

  #ds = gdal.Open(res_h1)
  h_array = np.array(res_ds1.GetRasterBand(1).ReadAsArray())

  h_array = np.where(h_array > 0, h_array, np.nan)
  h_array = np.where(h_array > 100000, np.nan, h_array)

  nrows,ncols = np.shape(h_array)
  ds = gdal.GetDriverByName('GTiff').Create(res_h2,ncols, nrows, 1 ,gdal.GDT_Float32)

  print (np.nanmedian(h_array), np.nanmean(h_array), np.nanstd(h_array), np.nanvar(h_array),)

  ds.GetRasterBand(1).WriteArray(h_array)
  ds.FlushCache()

  return JsonResponse({
     "result": res_h2,
     "nanmean": float(np.nanmean(h_array)),
     "nanmedian": float(np.nanmedian(h_array)),
     "nanstd": float(np.nanstd(h_array)),
     "nanvar": float(np.nanvar(h_array)),
  })

@csrf_exempt
def raster_sample(request,supporto):
  if request.method == 'POST':
    json_data = json.loads(request.body)
    p = json_data.get('sample')
    if p:
       ds = gdal.Open("/coverage/%s.tif" % supporto)
       res = extract_point_from_raster(ds,p)
       return JsonResponse({"result": res})
    
@csrf_exempt
def raster_profilo(request,supporto):

  def dist(p0,p1):
     return math.sqrt((p1[0]-p0[0])**2 + (p1[1]-p0[1])**2 )

  if request.method == 'POST':
    json_data = json.loads(request.body)
    l = json_data.get('line')
    if l:
      p0 = l[0]
      p1 = l[1]
      a = math.atan2(p1[1]-p0[1], p1[0]-p0[0])
      stepx = 0.5 * math.cos(a)
      stepy = 0.5 * math.sin(a)
      print (a,stepx,stepy)
      dxfdoc = ezdxf.new()
      msp = dxfdoc.modelspace()

      output = {
         "dtm": {},
         "dsm": {}
      }

      for supporto in output.keys():
        ds = gdal.Open("/coverage/%s.tif" % supporto)
        sample = p0
        m = 0
        output[supporto]["wkt"] = "LINESTRING ZM ( "
        output[supporto]["xyz"] = []
        dxfdoc.layers.add(name=supporto, color=dxfcols[supporto])
        dxfpoints = []

        while ( dist(sample, p1) > 0.5 ):
          res = extract_point_from_raster(ds,sample)
          output[supporto]["xyz"].append([sample[0], sample[1], res])
          output[supporto]["wkt"] += "%f %f %f %f, " % (sample[0], sample[1], res, m)
          dxfpoints.append([m,res])
          sample = [sample[0]+stepx, sample[1]+stepy]
          m += 0.5

        res = extract_point_from_raster(ds,p1)
        output[supporto]["xyz"].append([p1[0], p1[1], res])
        d = dist(p0, p1)
        output[supporto]["wkt"] += "%f %f %f %f )" % (sample[0], sample[1], res, d)
        dxfpoints.append([d,res])
        msp.add_lwpolyline(dxfpoints, dxfattribs={"layer": supporto})

      output_dir = os.path.join(settings.PDAL_OUTPUT_DIR,uuid.uuid4().hex)
      dxffile = os.path.join(output_dir,"profile.dxf")
      os.makedirs(output_dir)
      dxfdoc.saveas(dxffile)

      print ("output", output)

      return JsonResponse({
         "profile": l,
         "dxf": "/lidex"+dxffile,
         "output": output,
      })


def globmap(request):
    return render(request, 'map.html', {})

@csrf_exempt
def punti(request):
  clean_output_buffer(5000000000)
  if request.method == 'POST':
    print(request.body)
    json_data = json.loads(request.body) # request.raw_post_data w/ Django < 1.4
    extent = json_data.get('extent')
    wktgeom = json_data.get('geom')
    if wktgeom:
       geom = GEOSGeometry(wktgeom)
       print("closed poligon?",geom[0][0],geom[0][-1])

    output_dir = os.path.join(settings.PDAL_OUTPUT_DIR,uuid.uuid4().hex)
    os.makedirs(output_dir)
    output_laz = os.path.join(output_dir,"estratto.laz")
    #try:
    res = pdal_tindex_merge(
      settings.PDAL_COVERAGE_INDEX_PATH, 
      output_laz, 
      bounds=extent, 
      polygon= wktgeom,
      t_srs= settings.PDAL_COVERAGE_INDEX_SRS,
      ogrdriver= settings.PDAL_COVERAGE_INDEX_FORMAT,
      lyr_name= settings.PDAL_COVERAGE_INDEX_LAYER
    )

    if os.path.exists(output_laz):

      res2 = potreeConvert(output_laz)
      print ("potree converter", output_laz)

      metadata = {
        "result": res,
        "error": None,
        "extent": extent,
        "polygon": wktgeom,
        "info": json.loads(pdal_info(output_laz)),
        "remote": get_client_ip(request),
        "time": datetime.now().isoformat(),
        "output_dir": "/lidex"+output_dir,
        "output_laz": "/lidex"+output_laz,
      }

      with open(os.path.join(output_dir,"metadata.json"), "w") as outf:
        outf.write(json.dumps(metadata))

      return JsonResponse(metadata)
    else:
      return JsonResponse({
        "result": None,
        "error": "La nuvola di punti non può essere generata",
      })
  else:
    return JsonResponse({
      "result": None,
      "error": "NO extent data",
    })
