#!/usr/bin/env python

"""Simplest possible import to get some data to work with.  This code
will not be used in production."""

import sys
import os
import datetime
import glob
import csv
import re

import PIL
from django.contrib.auth.models import User
from django.conf import settings

from share2.shareCore.models import Feature, Image
from share2.shareCore.utils import mkdirP, uploadClient
from share2.shareCore.TimeUtils import parseUploadTime

DEFAULT_IMPORT_DIR = os.path.join(settings.CHECKOUT_DIR, 'importData', 'guiberson')

def importImageDirect(imageName, attributes):
    im = PIL.Image.open('%s/photos/%s' % (dir, name), 'r')
    widthPixels, heightPixels = im.size
    del im

    lat = attributes['latitude']
    lon = attributes['longitude']

    img, created = (Image.objects.get_or_create
                    (name=imageName,
                     owner=User.objects.get(username=attributes['userName']),
                     timestamp=parseUploadTime(attributes['cameraTime']),
                     defaults=dict(minLat=lat,
                                   minLon=lon,
                                   maxLat=lat,
                                   maxLon=lon,
                                   roll=attributes['roll'],
                                   pitch=attributes['pitch'],
                                   yaw=attributes['yaw']
                                   notes=attributes['notes'],
                                   tags=attributes['tags'],
                                   widthPixels=widthPixels,
                                   heightPixels=heightPixels,
                                   )))

    if created:
        print 'processing', unicode(img)
        img.process(importFile=os.path.join(dir, 'photos', name))
        img.save()
    else:
        print 'skipping already imported', unicode(img)

def importDir(opts, dir):
    owner = User.objects.get(username=opts.user)
    dir = os.path.realpath(dir)
    csvName = glob.glob('%s/*.csv' % dir)[0]
    reader = csv.reader(file(csvName, 'r'))
    firstLine = True
    i = 0
    for row in reader:
        if firstLine:
            firstLine = False
            continue
        if opts.number != 0 and i >= opts.number:
            break
        allText = ' '.join(row)
        if opts.match and not re.search(opts.match, allText):
            continue
        latStr, lonStr, compassStr, timeStr, name, notes, tagsStr, creatorName = row
        tags = [t.strip() for t in tagsStr.split(',')]
        tags = [t for t in tags if t != 'default']
        tags.append(creatorName)
        tagsDb = ', '.join(tags)
        lat, lon, compass = float(latStr), float(lonStr), float(compassStr)
        if lat == -999:
            continue
        importFile = os.path.join(dir, 'photos', name)
        
        # map to field names in upload form
        attributes = dict(name=name,
                          userName=userName,
                          timestamp=timeStr,
                          latitude=lat,
                          longitude=lon,
                          yaw=compass,
                          notes=notes,
                          tags=tagsDb)
        if opts.url:
            print 'uploading', imageName
            uploadClient.uploadImage(opts.url, importFile, attributes)
        else:
            importImageDirect(importFile, attributes)

        i += 1

def doit(opts, importDirs):
    if opts.clean:
        print 'cleaning'
        features = Feature.objects.all()
        for f in features:
            f.deleteFiles()
            f.delete()
    for dir in importDirs:
        importDir(opts, dir)

def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog <dir1> [dir2 ...]')
    parser.add_option('-c', '--clean',
                      action='store_true', default=False,
                      help='Clean database before import')
    parser.add_option('-u', '--user',
                      default='root',
                      help='Owner of imported photos')
    parser.add_option('-m', '--match',
                      default=None,
                      help='Import only photos matching specified pattern')
    parser.add_option('-n', '--number',
                      default=0,
                      help='Number of photos to import')
    parser.add_option('-u', '--url',
                      default=None,
                      help='If specified, upload images to this url instead of directly connecting to db')
    opts, args = parser.parse_args()
    if not args:
        print >>sys.stderr, 'warning: no import dirs specified, not importing anything'
    importDirs = args
    doit(opts, importDirs)

if __name__ == '__main__':
    main()