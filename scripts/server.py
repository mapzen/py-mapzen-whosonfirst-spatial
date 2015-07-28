#!/usr/bin/env python

# see notes in (local) whosonfirst.py about namespaces
# and anger (20150723/thisisaaronland)

import whosonfirst

import mapzen.whosonfirst.utils as utils
import mapzen.whosonfirst.placetypes as placetypes
import logging

import os
import flask
import werkzeug
import werkzeug.security
from werkzeug.contrib.fixers import ProxyFix

dsn = os.environ['WOF_LOOKUP_DSN']
db = whosonfirst.lookup(dsn)

app = flask.Flask('WOF_LOOKUP')
app.wsgi_app = ProxyFix(app.wsgi_app)

logging.basicConfig(level=logging.INFO)

@app.route("/")
def lookup():

    lat = flask.request.args.get('latitude', None)
    lon = flask.request.args.get('longitude', None)
    bbox = flask.request.args.get('bbox', None)

    placetype = flask.request.args.get('placetype', None)

    if placetype:

        placetype = placetype.split(",")

        for p in placetype:

            if not placetypes.is_valid_placetype(p):
                flask.abort(400)

    if lat and lon:
        rsp = by_latlon(lat, lon, placetype)

    elif bbox:
        rsp = by_extent(bbox, placetype)

    else:
        flask.abort(400)

    return enresponsify(rsp)

def by_latlon(lat, lon, placetypes):

    # TO DO - sanity check lat and lon here...

    lat = float(lat)
    lon = float(lon)

    rsp = db.get_by_latlon_recursive(lat, lon, placetypes=placetypes)        
    return rsp

def by_extent(bbox, placetypes):

    # sudo make a "recursive" version of me...
    placetype = placetypes[0]

    bbox = bbox.split(",")
    swlat, swlon, nelat, nelon = map(float, bbox)

    # TO DO - sanity check lat and lon here...

    rsp = db.get_by_extent(swlat, swlon, nelat, nelon, placetype=placetype)
    return rsp

"""
def by_tms(tms, placetype):
    z, x, y = tms

    bbox = whereami(z, x, y)
    return by_exent(bbox, placetype)
"""

def enresponsify(rsp):

    features = []

    for feature in rsp:

        props = feature['properties']
        id = props['wof:id']

        path = utils.id2relpath(id)
        props['wof:path'] = path

        feature['properties'] = props
        features.append(feature)

    rsp = {'type': 'FeatureCollection', 'features': features}
    return flask.jsonify(rsp)

if __name__ == '__main__':

    import sys
    import optparse

    opt_parser = optparse.OptionParser()

    opt_parser.add_option('-p', '--port', dest='port', action='store', default=8888, help='')

    opt_parser.add_option('-v', '--verbose', dest='verbose', action='store_true', default=False, help='Be chatty (default is false)')
    options, args = opt_parser.parse_args()

    if options.verbose:	
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    port = int(options.port)
    app.run(port=port)
