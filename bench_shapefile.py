"""
Test rendering a shapefile
"""

import sys
from time import time
from math import sqrt
# Allow python to find libraries for testing on the buildbot
sys.path.insert(0, "/usr/local/lib/python%s/site-packages" % sys.version[:3])


import mapnik

def bench_render_map( mapfile, w, h, n ):
    m = mapnik.Map(w,h)
    mapnik.load_map(m,mapfile)
    im = mapnik.Image(w,h)
    m.zoom_all()

    acc = 0.0
    acc2 = 0.0

    for i in range(n):
        tm = time()
        mapnik.render(m,im)
        dt = time() - tm
        acc += dt
        acc2 += dt*dt

    mean = acc/n
    rms  = acc2/n
    stddev = sqrt( rms - mean**2 )

    return  acc, mean, stddev

testcases = (
   ("data/merc_layer.xml", 256, 256, 1000 ),
   ("data/merc_layer.xml", 384, 384, 1000 ),
   ("data/merc_layer.xml", 512, 512, 1000 ),
   ("data/merc_layer.xml", 768, 768, 1000 ),
) 

print("- mapnik path: %s" % mapnik.__file__)
if hasattr(mapnik,'_mapnik'):
   print("- _mapnik.so path: %s" % mapnik._mapnik.__file__)
print("- Input plugins path: %s" % mapnik.inputpluginspath)
print("- Font path: %s" % mapnik.fontscollectionpath)
print('')
print("- Running benchmarks:")
print('')

for t in testcases:
    sys.stdout.write("{} : ".format(t))
    acc, mean, stddev = bench_render_map( *t )
    sys.stdout.write("total: {:.3f} mean: {:.3f} stddev: {:.3f})\n".format(acc, mean, stddev))

