#!/usr/bin/env python

# Launch sequence:
# source /srv/.venvs/moodload/bin/activate
# uwsgi --master --processes=4 --socket=:8001 --wsgi-file=moodload.py

# It's important to monkeypatch socket before all modules are imported
from gevent import monkey; monkey.patch_socket()

import argparse
# import itertools
import logging
# import mimetypes
import os
# import re
# import shutil
# import subprocess
import sys
# import urllib
# import urllib2
# import urlparse
# import uuid

# from bs4 import BeautifulSoup
import gevent
from gevent.pywsgi import WSGIServer

import colors
# from colors import Colors

log = None

# verbose = True
# noInfo = False
# noWarnings = True
# noDir = False
# noParDir = True

# respond = None
# cookies = None
# modResource = None
# dirLevel = 0
# dirSpace = '    '

def main(env, sr):
    log.info(env['REMOTE_ADDR'])
    gevent.sleep(5)
    if env.has_key('wsgi.websocket'):
        log.info('Is a websocket')
    else:
        log.info('Not a websocket')
        sr('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
        return ['Not a websocket']

    # global respond, cookies, modResource
    # respond = sr
    # query = urlparse.parse_qs(env['QUERY_STRING'])
    # url = None
    # auto = False

    # if query.has_key('moodload-url'):
    #     url = query['moodload-url'][0]
    #     del query['moodload-url']
    # else:
    #     return error('No moodload-url')

    # info('Url is ' + url)

    # if query.has_key('moodload-auto'):
    #     if query['moodload-auto'][0] in ['0', '1']:
    #         auto = query['moodload-auto'][0] == '1'
    #     del query['moodload-auto']
    # else:
    #     warning('No moodload-auto')

    # info('Auto is ' + str(auto))
    # cookies = '; '.join([x + '=' + y[0] for x, y in query.items()])
    # info('Cookies are ' + cookies)
    # urlParsed = urlparse.urlparse(url)
    # urlRoot = urlParsed.scheme + '://' + urlParsed.netloc
    # courseID = urlparse.parse_qs(urlParsed.query)

    # if not courseID.has_key('id'):
    #     return error('No id in ' + url)

    # courseID = courseID['id'][0]
    # courseDOM = load(url)

    # if not courseDOM:
    #     return error('Failed to load the course page')

    # courseName = re.search(':\s(.+)$', courseDOM.title.get_text());

    # if courseName:
    #     courseName = fix(courseName.group(1))
    # else:
    #     warning('The title does not look like \'%blah%: %course%\' at' + url)
    #     courseName = 'Course ' + courseID

    # sections = {}
    # sectionsDOM = courseDOM.select('tr.section.main')

    # if sectionsDOM:
    #     for sectionDOM in sectionsDOM:
    #         keyDOM = sectionDOM.select('td.left.side')
    #         titleDOM = (
    #             sectionDOM.select('h1') +
    #             sectionDOM.select('h2') +
    #             sectionDOM.select('h3') +
    #             sectionDOM.select('h4') +
    #             sectionDOM.select('h5') +
    #             sectionDOM.select('h6')
    #         )

    #         if keyDOM and titleDOM:
    #             keyText = fix(keyDOM[0].get_text())
    #             titleText = fix(titleDOM[0].get_text())

    #             if len(keyText) and keyText != ' ' and len(titleText):
    #                 sections[keyText] = titleText;
    # else:
    #     warning('No \'tr.section.main\' at ' + url)

    # modResource = urlRoot + '/mod/resource/'
    # resUrl = modResource + 'index.php?id=' + courseID
    # resourcesPageDOM = load(resUrl)

    # if not resourcesPageDOM:
    #     return error('Failed to load the resources page')

    # resourceEntriesDOM = resourcesPageDOM.select(
    #     'table.generaltable.boxaligncenter tr'
    # )

    # if not resourceEntriesDOM:
    #     return error('No \'table.generaltable.boxaligncenter\' at ' + resUrl)

    # mainPath = os.path.dirname(os.path.realpath(__file__))

    # # In case the previous request didn't end successfully
    # # NOTE: doesn't really help
    # if mainPath != os.getcwd():
    #     os.chdir(mainPath)

    # logDir()
    # tmpRootPath = os.path.join(mainPath, 'tmp')
    
    # if not os.path.exists(tmpRootPath):
    #     os.mkdir(tmpRootPath)

    # tmpDir = unique(str(uuid.uuid4())[:8])
    # tmpPath = os.path.join(tmpRootPath, tmpDir)
    # os.mkdir(tmpPath)
    # os.chdir(tmpPath)
    # logDir()

    # currentKey = '0'
    # currentSection = courseName
    # currentSubDir = None
    # hasSomething = False

    # for resourceEntryDOM in resourceEntriesDOM:
    #     keyDOM = resourceEntryDOM.select('td.cell.c0')

    #     if keyDOM:
    #         keyText = fix(keyDOM[0].get_text())

    #         if len(keyText) and keyText != ' ':
    #             currentKey = keyText
    #             currentSection = sections.get(currentKey, 'Section')

    #             if currentSubDir:
    #                 parDir()

    #                 if hasSomething:
    #                     hasSomething = False
    #                 else:
    #                     os.rmdir(currentSubDir)

    #                 currentSubDir = None

    #     resourceLinkDOM = resourceEntryDOM.select('td.cell.c1 > a')

    #     if not resourceLinkDOM:
    #         warning('No \'td.cell.c1 > a\'')
    #         continue

    #     if not currentSubDir:
    #         currentSubDir = subDir(currentSection, currentKey)

    #     resourceName = fix(resourceLinkDOM[0].get_text())
    #     resourceLink = (
    #         modResource + resourceLinkDOM[0].get('href') + '&inpopup=true'
    #     )
    #     resourceDOM = load(resourceLink)

    #     if resourceDOM:
    #         folderDir = subDir(resourceName)
    #         hasSomething = True

    #         if parseFolder(resourceDOM):
    #             info('Parsed ' + resourceLink)
    #         else:
    #             subprocess.call([
    #                 'wget', '-E', '-H', '-k', '-p', '-nd', '-c', '-q',
    #                 '--header', 'Cookie: ' + cookies,
    #                 resourceLink
    #             ])

    #             # ZIP is not compatible with years before 1980
    #             for wgetFile in os.listdir('.'):
    #                 os.utime(wgetFile, None)

    #             info('Saved ' + resourceLink)

    #         parDir()
    #     else:
    #         if download(resourceLink, resourceName):
    #             hasSomething = True

    # staticRootPath = os.path.join(mainPath, 'static')
    
    # if not os.path.exists(staticRootPath):
    #     os.mkdir(staticRootPath)

    # zipPath = os.path.join(staticRootPath, tmpDir, courseName)
    # shutil.make_archive(zipPath, 'zip', tmpPath)
    # os.chdir(mainPath)
    # shutil.rmtree(tmpPath)
    # logDir(-1)
    # info('Generated ' + zipPath + '.zip')

    # if auto:
    #     sr('200 OK', [
    #         ('Content-Type', 'application/octet-stream'),
    #         ('Content-Disposition', 'attachment; filename="' + 
    #             courseName.encode('utf-8') + '.zip"')
    #     ])
    #     return open(zipPath + '.zip', 'rb').read()
    # else:
    #     sr('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
    #     return open('moodload.html', 'rb').read().replace(
    #         '_HREF_',
    #         tmpDir + '/' + courseName + '.zip'
    #     ).replace(
    #         '_COURSE_',
    #         courseName
    #     ).encode('utf-8')

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument('-v', '--verbosity', help='the logging level',
            choices=['INFO', 'WARNING', 'ERROR'], default='WARNING'
        )
        parser.add_argument('-p', '--port', help='the port to bind to',
            type=int, default=8001
        )

        try:
            args = parser.parse_args()
        except:
            # Logging is not initialized yet
            print 'Invalid arguments'
            sys.exit(2)

        # The root log config applies to all logs created after this
        log = logging.getLogger('')
        log.setLevel(logging.INFO)
        # Edit colors.py to configure the formatter
        logFormatter = colors.ColoredFormatter()

        logConsoleHandler = logging.StreamHandler()
        logConsoleHandler.setLevel(getattr(logging, args.verbosity))
        logConsoleHandler.setFormatter(logFormatter)
        log.addHandler(logConsoleHandler)

        # The default mode is O_APPEND
        logFileHandler = logging.FileHandler(str(args.port) + '.log')
        logFileHandler.setLevel(logging.INFO)
        logFileHandler.setFormatter(logFormatter)
        log.addHandler(logFileHandler)

        log = logging.getLogger('server')

        if args.port < 1 or args.port > 65535:
            log.error('Port ' + str(args.port) + ' is not valid')
            sys.exit(2)

        try:
            log.info('Binding to ' + str(args.port) + '...')
            WSGIServer(('0.0.0.0', args.port), main, log=None).serve_forever()
        except IOError as e:
            log.error(e.strerror)
            sys.exit(1)
    except KeyboardInterrupt:
        print
    finally:
        print colors.Colors.RED + 'Nooooooooooooooo!' + colors.Colors.END
