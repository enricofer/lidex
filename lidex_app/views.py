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
