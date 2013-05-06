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
            # ZIP is not compatible with years before 1980
            os.utime(fileName, None)
            info('Downloaded ' + url)
            return True
    except:
        warning('DOWNLOAD: Failed to save ' + url)
        return False
