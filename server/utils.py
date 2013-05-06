import logging

logger = logging.getLogger('utils')

# Replaces the unicode representation of a space with an actual space and
# trims at both sides
# Returns the resulting string
def fix(str):
    return str.replace(u'\xa0', u' ').strip()

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

# # Prints a message
# def info(comment):
#     if verbose and not noInfo:
#         print (
#             colors.BLUE + (dirSpace * dirLevel) + 'INFO ' + 
#             colors.END + comment
#         )

# # Prints a warning
# def warning(comment):
#     if verbose and not noWarnings:
#         print (
#             colors.YELLOW + (dirSpace * dirLevel) + 'WARNING ' + 
#             colors.END + comment
#         )

# # Prints an error and sets the code to 422
# # Returns a message for output
# def error(comment):
#     print colors.RED + (dirSpace * dirLevel) + 'ERROR ' + colors.END + comment
#     respond('422 Unprocessable Entity', [('Content-Type','text/plain')])
#     return '422 Unprocessable Entity [' + str(comment) + ']'

# # Prints current location and updates the indentation
# # delta = 1 is subdir, delta = -1 is pardir, delta = 0 is everything else
# def logDir(delta=0):
#     global dirLevel

#     # http://stackoverflow.com/a/3501408/242684
#     if isinstance(delta, (int, long)) and delta >= -1 and delta <= 1:
#         dirLevel += delta

#     if verbose and not noDir and not (delta == -1 and noParDir):
#         print colors.GREEN + (dirSpace * dirLevel) + os.getcwd() + colors.END
