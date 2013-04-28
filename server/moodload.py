# Launch sequence:
# uwsgi --socket :8001 --wsgi-file moodload.py

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
noMessages = False
noWarnings = True

respond = None
cookies = None
modResource = None

# The entry point
def application(env, sr):
    global respond, cookies, modResource
    respond = sr

    if not 'url=' in env['QUERY_STRING']:
        return error('No url')

    params = env['QUERY_STRING'].split('&')
    paramsCount = len(params)
    url = None
    i = 0

    while i < paramsCount:
        if params[i][:4].lower() == 'url=':
            url = urllib.unquote(params[i][4:])
            del params[i]
            break
        i += 1

    if url == None or len(url) == 0:
        return error('No url')

    urlParsed = urlparse.urlparse(url)
    urlRoot = urlParsed.scheme + '://' + urlParsed.netloc
    cookies = '; '.join(params)
    courseID = urlparse.parse_qs(urlParsed.query)

    if not courseID.has_key('id'):
        return error('No id in ' + url)

    courseID = courseID['id'][0]
    courseDOM = load(url)
    courseName = re.search(':\s(.+)$', courseDOM.title.get_text());

    if courseName:
        courseName = fix(courseName.group(1))
    else:
        warning('The title does not look like \'%blah%: %course%\' at' + url)
        courseName = 'Some course'

    sections = {}
    sectionsDOM = courseDOM.select('tr.section.main')

    if sectionsDOM:
        for sectionDOM in sectionsDOM:
            keyDOM = sectionDOM.select('td.left.side')
            titleDOM = (
                sectionDOM.select('div.summary h2') +
                sectionDOM.select('div.summary h4')
            )

            if keyDOM and titleDOM:
                keyText = fix(keyDOM[0].get_text())
                titleText = fix(titleDOM[0].get_text())

                if len(keyText) and keyText != ' ' and len(titleText):
                    sections[keyText] = titleText;
    else:
        warning('No \'tr.section.main\' at ' + url)

    modResource = urlRoot + '/mod/resource/'
    resourceEntriesDOM = load(modResource + 'index.php?id=' + courseID).select(
        'table.generaltable.boxaligncenter tr'
    )

    if not resourceEntriesDOM:
        return error('No \'table.generaltable.boxaligncenter\' at ' + url)

    mainPath = os.path.dirname(os.path.realpath(__file__))

    # In case the previous request didn't end successfully
    if mainPath != os.getcwd():
        os.chdir(mainPath)

    tmpDir = unique(str(uuid.uuid4())[:8])
    tmpPath = os.path.join(mainPath, 'tmp', tmpDir)
    os.mkdir(tmpPath)
    os.chdir(tmpPath)

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
                    os.chdir(os.pardir)

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
                message('Parsed ' + resourceLink)
            else:
                subprocess.call([
                    'wget', '-E', '-H', '-k', '-p', '-nd', '-c', '-q',
                    '--header', 'Cookie: ' + cookies,
                    resourceLink
                ])
                message('Saved ' + resourceLink)

            os.chdir(os.pardir)
        else:
            if download(resourceLink, resourceName):
                hasSomething = True

    zipPath = os.path.join(mainPath, 'static', tmpDir, courseName)
    shutil.make_archive(zipPath, 'zip', tmpPath)
    os.chdir(mainPath)

    sr('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
    return open('moodload.html', 'rb').read().replace(
        '_HREF_',
        tmpDir + '/' + courseName + '.zip'
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
                    os.chdir(os.pardir)
                else:
                    os.chdir(os.pardir)
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
def message(comment):
    if verbose and not noMessages:
        print colors.BLUE + 'MESSAGE' + colors.END + ' ' + comment

# Prints a warning
def warning(comment):
    if verbose and not noWarnings:
        print colors.YELLOW + 'WARNING' + colors.END + ' ' + comment

# Prints an error and sets the code to 422
# Returns a message for output
def error(comment):
    print colors.RED + 'ERROR' + colors.END + ' ' + comment
    respond('422 Unprocessable Entity', [('Content-Type','text/plain')])
    return '422 Unprocessable Entity [' + str(comment) + ']'

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
    return name

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

    code = urlHandle.getcode()

    if code != 200:
        warning('LOAD: Failed to load (' + str(code) + ') ' + url)
        return False

    info = urlHandle.info()
    result = False

    if 'Content-Type' in info and 'text/html' in info['Content-Type']:
        result = BeautifulSoup(urllib2.urlopen(request).read())

        if result != None:
            message('Loaded ' + url)
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

    code = urlHandle.getcode()

    if code != 200:
        warning('DOWNLOAD: Failed to load (' + str(code) + ') ' + url)
        return False

    info = urlHandle.info()
    fileName = None

    if 'Content-Disposition' in info:
        fileName = re.search(
            'filename\=\"([^\"]+)\"', 
            info['Content-Disposition']
        )
        if fileName:
            fileName = fileName.group(1)
        else:
            warning('DOWNLOAD: No filename in Content-Disposition for ' + url)
    else:
        warning('DOWNLOAD: No Content-Disposition for ' + url)

    if not fileName and 'Content-Type' in info:
        mime = re.match('([^;]+)', info['Content-Type'])
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

    try:
        with open(unique(fileName), 'wb') as fileHandle:
            shutil.copyfileobj(urlHandle, fileHandle)
            message('Downloaded ' + url)
            return True
    except:
        warning('DOWNLOAD: Failed to save ' + url)
        return False
