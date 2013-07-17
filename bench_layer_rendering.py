"""
Test rendering shapefile / posgist data
"""

import sys
import os
from time import time
from math import sqrt
from subprocess import Popen, PIPE

# Allow python to find libraries for testing on the buildbot
sys.path.insert(0, "/usr/local/lib/python%s/site-packages" % sys.version[:3])


MAPNIK_TEST_DBNAME = 'mapnik-postgis-perf-test-db'
POSTGIS_TEMPLATE_DBNAME = 'template_postgis'
SHAPEFILE = os.path.join(os.getcwd(), 'data/world_merc.shp')

import mapnik


def psql_can_connect():
    """Test ability to connect to a postgis template db with no options.

    Basically, to run these tests your user must have full read
    access over unix sockets without supplying a password. This
    keeps these tests simple and focused on postgis not on postgres
    auth issues.
    """
    try:
        call('psql %s -c "select postgis_version()"' % POSTGIS_TEMPLATE_DBNAME)
        return True
    except RuntimeError:
        print 'Notice: skipping postgis tests (connection)'
        return False


def shp2pgsql_on_path():
    """Test for presence of shp2pgsql on the user path.

    We require this program to load test data into a temporarily database.
    """
    try:
        call('shp2pgsql')
        return True
    except RuntimeError:
        print 'Notice: skipping postgis tests (shp2pgsql)'
        return False


def createdb_and_dropdb_on_path():
    """Test for presence of dropdb/createdb on user path.

    We require these programs to setup and teardown the testing db.
    """
    try:
        call('createdb --help')
        call('dropdb --help')
        return True
    except RuntimeError:
        print 'Notice: skipping postgis tests (createdb/dropdb)'
        return False


def call(cmd, silent=False):
    stdin, stderr = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE).communicate()
    if not stderr:
        return stdin.strip()
    elif not silent and not 'NOTICE' in stderr:
        raise RuntimeError(stderr.strip())


def postgis_setup():
    call('dropdb %s' % MAPNIK_TEST_DBNAME, silent=True)
    call('createdb -T %s %s' % (POSTGIS_TEMPLATE_DBNAME, MAPNIK_TEST_DBNAME), silent=False)
    call('shp2pgsql -s 3857 -g geom -W LATIN1 %s world_merc | psql -q %s' % (SHAPEFILE, MAPNIK_TEST_DBNAME), silent=True)


def bench_render_map(mapfile, w, h, n):

    m = mapnik.Map(w, h)
    mapnik.load_map(m, mapfile)
    im = mapnik.Image(w, h)
    m.zoom_all()

    acc = 0.0
    acc2 = 0.0

    for i in range(n):
        tm = time()
        mapnik.render(m, im)
        dt = time() - tm
        acc += dt
        acc2 += dt*dt

    mean = acc/n
    rms = acc2/n
    stddev = sqrt(rms - mean**2)

    return acc, mean, stddev


testcases = (
    ("data/pg_merc_layer.xml", 256, 256, 1000),
    ("data/pg_merc_layer.xml", 384, 384, 1000),
    ("data/pg_merc_layer.xml", 512, 512, 1000),
    ("data/pg_merc_layer.xml", 768, 768, 1000),
    ("data/shp_merc_layer.xml", 256, 256, 1000),
    ("data/shp_merc_layer.xml", 384, 384, 1000),
    ("data/shp_merc_layer.xml", 512, 512, 1000),
    ("data/shp_merc_layer.xml", 768, 768, 1000),
)


print("- mapnik path: %s" % mapnik.__file__)
if hasattr(mapnik, '_mapnik'):
    print("- _mapnik.so path: %s" % mapnik._mapnik.__file__)
print("- Input plugins path: %s" % mapnik.inputpluginspath)
print("- Font path: %s" % mapnik.fontscollectionpath)
if 'postgis' in mapnik.DatasourceCache.plugin_names() \
        and createdb_and_dropdb_on_path() \
        and psql_can_connect() \
        and shp2pgsql_on_path():
    # initialize test database
    postgis_setup()
    postgis_initialized = True
else:
    postgis_initialized = False
    print('postgis missing')
print('')
print("- Running benchmarks:")
print('')

for t in testcases:
    if not postgis_initialized and "pg" in t[0]:
        break
    sys.stdout.write("{} : ".format(t))
    acc, mean, stddev = bench_render_map(*t)
    sys.stdout.write("total: {:.3f} mean: {:.3f} stddev: {:.3f})\n".format(acc, mean, stddev))
