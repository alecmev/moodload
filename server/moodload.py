# Launch sequence:
# source /srv/.venvs/moodload/bin/activate
# uwsgi --master --processes=4 --socket=:8001 --wsgi-file=moodload.py

import itertools
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import urllib
import urllib2
import urlparse
import uuid

from bs4 import BeautifulSoup

sys.dont_write_bytecode = True

from colors import colors

verbose = True
noInfo = False
noWarnings = True
noDir = False
noParDir = True

respond = None
cookies = None
modResource = None
dirLevel = 0
dirSpace = '    '

# The entry point
def application(env, sr):
    global respond, cookies, modResource
    respond = sr
    query = urlparse.parse_qs(env['QUERY_STRING'])
    url = None
    auto = False

    if query.has_key('moodload-url'):
        url = query['moodload-url'][0]
        del query['moodload-url']
    else:
        return error('No moodload-url')

    info('Url is ' + url)

    if query.has_key('moodload-auto'):
        if query['moodload-auto'][0] in ['0', '1']:
            auto = query['moodload-auto'][0] == '1'
        del query['moodload-auto']
    else:
        warning('No moodload-auto')

    info('Auto is ' + str(auto))
    cookies = '; '.join([x + '=' + y[0] for x, y in query.items()])
    info('Cookies are ' + cookies)
    urlParsed = urlparse.urlparse(url)
    urlRoot = urlParsed.scheme + '://' + urlParsed.netloc
    courseID = urlparse.parse_qs(urlParsed.query)

    if not courseID.has_key('id'):
        return error('No id in ' + url)

    courseID = courseID['id'][0]
    courseDOM = load(url)

    if not courseDOM:
        return error('Failed to load the course page')

    courseName = re.search(':\s(.+)$', courseDOM.title.get_text());

    if courseName:
        courseName = fix(courseName.group(1))
    else:
        warning('The title does not look like \'%blah%: %course%\' at' + url)
        courseName = 'Course ' + courseID

    sections = {}
    sectionsDOM = courseDOM.select('tr.section.main')

    if sectionsDOM:
        for sectionDOM in sectionsDOM:
            keyDOM = sectionDOM.select('td.left.side')
            titleDOM = (
                sectionDOM.select('h1') +
                sectionDOM.select('h2') +
                sectionDOM.select('h3') +
                sectionDOM.select('h4') +
                sectionDOM.select('h5') +
                sectionDOM.select('h6')
            )

            if keyDOM and titleDOM:
                keyText = fix(keyDOM[0].get_text())
                titleText = fix(titleDOM[0].get_text())

                if len(keyText) and keyText != ' ' and len(titleText):
                    sections[keyText] = titleText;
    else:
        warning('No \'tr.section.main\' at ' + url)

    modResource = urlRoot + '/mod/resource/'
    resourcesPageDOM = load(modResource + 'index.php?id=' + courseID)

    if not resourcesPageDOM:
        return error('Failed to load the resources page')

    resourceEntriesDOM = resourcesPageDOM.select(
        'table.generaltable.boxaligncenter tr'
    )

    if not resourceEntriesDOM:
        return error('No \'table.generaltable.boxaligncenter\' at ' + url)

    mainPath = os.path.dirname(os.path.realpath(__file__))

    # In case the previous request didn't end successfully
    if mainPath != os.getcwd():
        os.chdir(mainPath)

    logDir()
    tmpRootPath = os.path.join(mainPath, 'tmp')
    
    if not os.path.exists(tmpRootPath):
        os.mkdir(tmpRootPath)

    tmpDir = unique(str(uuid.uuid4())[:8])
    tmpPath = os.path.join(tmpRootPath, tmpDir)
    os.mkdir(tmpPath)
    os.chdir(tmpPath)
    logDir()

    currentKey = '0'
    currentSection = courseName
    currentSubDir = None
    hasSomething = False

    for resourceEntryDOM in resourceEntriesDOM:
        keyDOM = resourceEntryDOM.select('td.cell.c0')

        if keyDOM:
            keyText = fix(keyDOM[0].get_text())

            if len(keyText) and keyText != ' ':
                currentKey = keyText
                currentSection = sections.get(currentKey, 'Section')

                if currentSubDir:
                    parDir()

                    if hasSomething:
                        hasSomething = False
                    else:
                        os.rmdir(currentSubDir)

                    currentSubDir = None

        resourceLinkDOM = resourceEntryDOM.select('td.cell.c1 > a')

        if not resourceLinkDOM:
            warning('No \'td.cell.c1 > a\'')
            continue

        if not currentSubDir:
            currentSubDir = subDir(currentSection, currentKey)

        resourceName = fix(resourceLinkDOM[0].get_text())
        resourceLink = (
            modResource + resourceLinkDOM[0].get('href') + '&inpopup=true'
        )
        resourceDOM = load(resourceLink)

        if resourceDOM:
            folderDir = subDir(resourceName)
            hasSomething = True

            if parseFolder(resourceDOM):
                info('Parsed ' + resourceLink)
            else:
                subprocess.call([
                    'wget', '-E', '-H', '-k', '-p', '-nd', '-c', '-q',
                    '--header', 'Cookie: ' + cookies,
                    resourceLink
                ])
                info('Saved ' + resourceLink)

            parDir()
        else:
            if download(resourceLink, resourceName):
                hasSomething = True

    staticRootPath = os.path.join(mainPath, 'static')
    
    if not os.path.exists(staticRootPath):
        os.mkdir(staticRootPath)

    zipPath = os.path.join(staticRootPath, tmpDir, courseName)
    shutil.make_archive(zipPath, 'zip', tmpPath)
    os.chdir(mainPath)
    shutil.rmtree(tmpPath)
    logDir(-1)
    info('Generated ' + zipPath + '.zip')

    if auto:
        sr('200 OK', [
            ('Content-Type', 'application/octet-stream'),
            ('Content-Disposition', 'attachment; filename="' + 
                courseName.encode('utf-8') + '.zip"')
        ])
        return open(zipPath + '.zip', 'rb').read()
    else:
        sr('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
        return open('moodload.html', 'rb').read().replace(
            '_HREF_',
            tmpDir + '/' + courseName + '.zip'
        ).replace(
            '_COURSE_',
            courseName
        ).encode('utf-8')

# Parse a folder, parse all subfolders and download all files
# Returns True if any files downloaded (including subfolders), False otherwise
def parseFolder(resourcePageDOM):
    folderEntriesDOM = resourcePageDOM.select('tr.folder td.name a')
    linkEntriesDOM = resourcePageDOM.select('tr.file td.name a')
    hasSomething = False

    if folderEntriesDOM:
        for folderEntryDOM in folderEntriesDOM:
            folderHref = folderEntryDOM.get('href')
            folderDOM = load(
                modResource + folderHref + 
                ('&' if '?' in folderHref else '?') + 'inpopup=true'
            )

            if folderDOM:
                folderDir = subDir(fix(folderEntryDOM.get_text()))

                if parseFolder(folderDOM):
                    hasSomething = True
                    parDir()
                else:
                    parDir()
                    os.rmdir(folderDir)

    if linkEntriesDOM:
        for linkEntryDOM in linkEntriesDOM:
            linkHref = linkEntryDOM.get('href')

            if download(
                linkHref + ('&' if '?' in linkHref else '?') + 'inpopup=true'
            ):
                hasSomething = True

    return hasSomething

# Replaces the unicode representation of a space with an actual space and
# trims at both sides
# Returns the resulting string
def fix(str):
    return str.replace(u'\xa0', u' ').strip()

# Prints a message
def info(comment):
    if verbose and not noInfo:
        print (
            colors.BLUE + (dirSpace * dirLevel) + 'INFO ' + 
            colors.END + comment
        )

# Prints a warning
def warning(comment):
    if verbose and not noWarnings:
        print (
            colors.YELLOW + (dirSpace * dirLevel) + 'WARNING ' + 
            colors.END + comment
        )

# Prints an error and sets the code to 422
# Returns a message for output
def error(comment):
    print colors.RED + (dirSpace * dirLevel) + 'ERROR ' + colors.END + comment
    respond('422 Unprocessable Entity', [('Content-Type','text/plain')])
    return '422 Unprocessable Entity [' + str(comment) + ']'

# Prints current location and updates the indentation
# delta = 1 is subdir, delta = -1 is pardir, delta = 0 is everything else
def logDir(delta=0):
    global dirLevel

    # http://stackoverflow.com/a/3501408/242684
    if isinstance(delta, (int, long)) and delta >= -1 and delta <= 1:
        dirLevel += delta

    if verbose and not noDir and not (delta == -1 and noParDir):
        print colors.GREEN + (dirSpace * dirLevel) + os.getcwd() + colors.END

# Picks a unique extension-aware [file/dir]name in the working dir
# Returns the resulting name (race condition unsafe)
def unique(desired):
    result = desired.replace('/', '#')
    fileName, fileExt = os.path.splitext(desired)
    i = 0

    while os.path.exists(result):
        result = fileName + '-' + str(i) + fileExt
        i += 1

    return result

# Creates and navigates to a subdirectory unique('[[0]key] name')
# Returns the name of the new subdirectory
def subDir(name, key=None):
    if key != None:
        name = (key if len(key) > 1 else '0' + key) + ' ' + name

    name = unique(name)
    os.mkdir(name)
    os.chdir(name)
    logDir(1)
    return name

# Navigates to the parent directory
def parDir():
    os.chdir(os.pardir)
    logDir(-1)

# Loads a resource, if its mime is text/html
# Returns a BeautifulSoup object of the resource on success, False otherwise
def load(url):
    request = urllib2.Request(url)
    request.add_header('Cookie', cookies)
    urlHandle = None

    try:
        urlHandle = urllib2.urlopen(request)
    except:
        warning('LOAD: Failed to load ' + url)
        return False

    urlCode = urlHandle.getcode()

    if urlCode != 200:
        warning('LOAD: Failed to load (' + str(urlCode) + ') ' + url)
        return False

    urlInfo = urlHandle.info()
    result = False

    if 'Content-Type' in urlInfo and 'text/html' in urlInfo['Content-Type']:
        result = BeautifulSoup(urllib2.urlopen(request).read())

        if result != None:
            info('Loaded ' + url)
    else:
        warning('LOAD: Not an HTML file at ' + url)

    urlHandle.close()
    return result

# Downloads a file to the working dir if a name can be picked
# Returns True on success, False otherwise
def download(url, possibleName=None):
    request = urllib2.Request(url)
    request.add_header('Cookie', cookies)
    urlHandle = None

    try:
        urlHandle = urllib2.urlopen(request)
    except:
        warning('DOWNLOAD: Failed to load ' + url)
        return False

    urlCode = urlHandle.getcode()

    if urlCode != 200:
        warning('DOWNLOAD: Failed to load (' + str(urlCode) + ') ' + url)
        return False

    urlInfo = urlHandle.info()
    fileName = None

    if 'Content-Disposition' in urlInfo:
        fileName = re.search(
            'filename\=\"([^\"]+)\"', 
            urlInfo['Content-Disposition']
        )
        if fileName:
            fileName = fileName.group(1)
        else:
            warning('DOWNLOAD: No filename in Content-Disposition for ' + url)
    else:
        warning('DOWNLOAD: No Content-Disposition for ' + url)

    if not fileName and 'Content-Type' in urlInfo:
        mime = re.match('([^;]+)', urlInfo['Content-Type'])
        if mime:
            fileExt = mimetypes.guess_extension(mime.group(1))
            if fileExt != None:
                fileName = (
                    (possibleName if possibleName else str(uuid.uuid4())[:8]) + 
                    fileExt
                )
    else:
        warning('DOWNLOAD: No Content-Type for ' + url)

    if not fileName:
        urlHandle.close()
        return False

    fileName = unique(fileName)

    try:
        with open(unique(fileName), 'wb') as fileHandle:
            shutil.copyfileobj(urlHandle, fileHandle)
            os.utime(fileName, None) # Reset the access and modification time
            info('Downloaded ' + url)
            return True
    except:
        warning('DOWNLOAD: Failed to save ' + url)
        return False
