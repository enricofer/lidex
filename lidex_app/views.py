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

      return JsonResponse({
         "profile": l,
         "dxf": dxffile,
         "output": output,
      })


def globmap(request):
    return render(request, 'map.html', {})

@csrf_exempt
def punti(request):
  clean_output_buffer(3000000000)
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
        "output_dir": output_dir,
        "output_laz": output_laz,
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
