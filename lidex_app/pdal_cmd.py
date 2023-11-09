import subprocess
import json
import os
from django.contrib.gis.geos import Polygon

PDAL_EXE = "pdal" #"/usr/bin/pdal" #"/opt/conda/envs/pdal/bin/pdal"
POTREECONVERTER_EXE = "/opt/PotreeConverter/build/PotreeConverter"

def extentToPolygon(ex):
    return Polygon(
        (
            (ex[0],ex[1]),
            (ex[0],ex[3]),
            (ex[2],ex[3]),
            (ex[2],ex[1]),
            (ex[0],ex[1]),
        )
    )

class PDALException(Exception):
    pass

def ex_executePDAL(commands, cmd=None ,path=None, feedback=None):
    if not cmd:
        commands.insert(0, PDAL_EXE)
    else:
        commands.insert(0, cmd)
    print (os.environ.copy())
    try:
        encoding = "utf-8" #locale.getdefaultlocale()[1] or 
        with subprocess.Popen(
            commands,
            #shell=os.name == "nt",
            #env=os.environ.copy(),
            stdout=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding=encoding,
            cwd=path,
        ) as proc:
            if feedback is not None:
                output = []
                err = []
                for line in proc.stderr:
                    feedback(line)
                    err.append(line)
                for line in proc.stdout:
                    output.append(line)
                stdout = "".join(output)
                stderr = "".join(err)
                proc.communicate()  # need to get the returncode
            else:
                stdout, stderr = proc.communicate()
            if proc.returncode:
                print (stderr)
                raise PDALException(stderr)
                return "error: " + stderr
            else:
                return stdout
    except Exception as e:
        print ("pdal exception",str(e))
        raise PDALException(str(e))
        return "error: " + str(e)

def executePDAL(commands, cmd=None ,path=None, feedback=None):
    if not cmd:
        commands.insert(0, PDAL_EXE)
    else:
        commands.insert(0, cmd)
    cmd = " ".join(commands)
    print (cmd)
    return subprocess.getoutput(cmd)
    #return os.system(cmd)
    #return subprocess.run(commands) 

def pdal_info(las):
    return executePDAL(["info", las])

def pdal_tindex_merge(index, output, bounds=None, polygon=None, t_srs=None, ogrdriver=None, lyr_name=None):
    if bounds:
        polygon = extentToPolygon(bounds)
    
    args = ["tindex", "merge", '--polygon', '"%s"' % polygon.wkt]

    if ogrdriver:
        args = args + ['--ogrdriver', '"%s"' % ogrdriver]

    if lyr_name:
        args = args + ['--lyr_name', '"%s"' % lyr_name]

    if t_srs:
        args = args + ['--t_srs', '"%s"' % t_srs]# '"%s"' % t_srs]
    
    args = args + [index, output]

    print (args)
    
    return executePDAL(args)

def potreeConvert(las):
    output_dir = os.path.join(os.path.dirname(las), "model")
    print ("potree output", output_dir)
    return executePDAL([las, "-o", output_dir,"--generate-page", "index"], cmd=POTREECONVERTER_EXE)