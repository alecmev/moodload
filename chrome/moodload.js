var course, sections, randomKey = "##", modResource, zip, pending;

function safeName(name, usedNames)
{
    if (name.match(/^(?!^(PRN|AUX|CLOCK\$|NUL|CON|COM\d|LPT\d|\..*)(\..+)?$)[^\x00-\x1f\\?*:\"><|/]+$/i) == null)
        name = encodeURIComponent(name);

    var original = name;

    while ($.inArray(name, usedNames) != -1)
        name = original + Math.floor(Math.random() * 97033225);

    usedNames.push(name);
    return name;
}

function addPending()
{
    console.log(++pending);
}

function removePending()
{
    console.log(--pending);

    if (pending == 0)
        location.href = "data:application/zip;base64," + zip.generate();
}

function parseFolder(zipFolder, dataDOM)
{
    var folders = $('tr.folder > td.name > a', dataDOM);
    var links = $('tr.file > td.name > a', dataDOM);
    var usedNames = [];

    if (folders != null)
    {
        folders.each(function()
        {
            addPending();

            $.get(modResource + $(this).attr("href") + "&inpopup=true", function(data, textStatus, jqXHR)
            {
                parseFolder(zipFolder.folder($(this).text()), $(data));
                removePending();
            })
            .fail(function()
            {
                removePending();
            });
        });
    }

    if (links != null)
    {
        links.each(function()
        {
            addPending();

            $.get($(this).attr("href") + "&inpopup=true", function(data, textStatus, jqXHR)
            {
                zipFolder.file(jqXHR.getResponseHeader('Content-Disposition').match(/filename\=\"(.*)\"$/)[1], data);
                removePending();
            })
            .fail(function()
            {
                removePending();
            });
        });
    }
}

// Incoming message from the background process
chrome.runtime.onMessage.addListener(function(check, sender, respond)
{
    var url = document.URL.match(/(.+)\/course\/view\.php\?.*id\=(\d+)/i);
    var isMoodle = document.getElementsByTagName('html')[0].innerHTML.match(/moodle/i) != null && url != null;
    
    if (check)
        respond(isMoodle);

    // Start downloading the resources
    else if (isMoodle)
    {
        // Grab course's name from the title (the easiest way)
        var courseInTitle = document.title.match(/:\s(.+)$/);

        if (courseInTitle == null)
        {
            console.warn("WARNING: The title does not look like '%something%: %course%'");
            course = "Some course"; 
        }
        else
            course = courseInTitle[1];

        // Collect all the main sections of the course (optional)
        sections = [];
        var mainSection = $("tr.section.main");

        if (mainSection == null)
            console.warn("WARNING: There's no 'tr.section.main'");
        else
        {
            mainSection.each(function()
            {
                var number = $("td.left.side", $(this));
                var title = $("div.summary > h2", $(this));

                if (number != null && title != null)
                {
                    var numberText = number.text();
                    var titleText = title.text();

                    if (numberText.length && numberText != "&nbsp;" && titleText.length)
                        sections[numberText] = titleText;
                }
            });
        }
        
        pending = 0;
        modResource = url[1] + "/mod/resource/";
        zip = new JSZip();
        
        // Start processing the resources page
        $.get(modResource + "index.php?id=" + url[2], function(data)
        {
            var generalTable = $("table.generaltable.boxaligncenter tr", $(data));

            if (generalTable == null || !generalTable.length)
            {
                console.error("ERROR: There's no 'table.generaltable.boxaligncenter'");
                return;
            }

            var currentNumber = randomKey;
            var zipFolder = null;
            var usedNames = [];

            // Go through each row in the resources table
            generalTable.each(function()
            {
                // Get the nubmer of the section
                var number = $("td.cell.c0", $(this));

                if (number != null && number.length)
                {
                    var numberText = number.text();

                    if (numberText.length && numberText != "&nbsp;")
                    {
                        currentNumber = numberText;
                        folder = null;
                        usedNames = [];
                    }
                }

                // Get the resource
                var resource = $("td.cell.c1 > a", $(this));

                if (resource == null || !resource.length)
                    return;

                var resourceName = resource.text();
                var resourceLink = modResource + resource.attr("href") + "&inpopup=true";

                addPending();

                // Load the resource, examine it and take appropriate action
                $.get(resourceLink, function(data, textStatus, jqXHR)
                {
                    if (zipFolder == null)
                        zipFolder = zip.folder((currentNumber.length == 1 ? '0' : '') + currentNumber + ' ' + safeName(sections[currentNumber], []));

                    var fileName = jqXHR.getResponseHeader('Content-Disposition');

                    if (fileName != null)
                    {
                        zipFolder.file(fileName.match(/filename\=\"(.*)\"$/)[1], data);
                        removePending();
                        return;
                    }

                    try
                    {
                        var dataDOM = $(data);
                        var resources = $('tr.file > td.name > a, tr.folder > td.name > a', dataDOM);

                        if (resources != null && resources.length)
                        {
                            parseFolder(zipFolder.folder(safeName(resourceName), []), dataDOM);
                            removePending();
                            return;
                        }
                    }
                    catch (e)
                    {
                        console.warn("WARNING: failed to parse DOM (" + e.name + ": " + e.message.substring(0, 256) + ')');
                    }

                    zipFolder.file(safeName(resourceName, usedNames) + ".html",
                        "<!DOCTYPE html>\n" +
                        "<html>\n" +
                        "    <head>\n" +
                        "        <title> " + resourceName + " </title>\n" +
                        "        <script type=\"text/javascript\"> window.location = \"" + resourceLink + "\"; </script>\n" +
                        "    </head>\n" +
                        "    <body></body>\n" +
                        "</html>");

                    removePending();
                })
                .fail(function()
                {
                    removePending();
                });
            });
        });

        
    }
});

// function download(resource)
// {
//     var click = document.createEvent("MouseEvents");
//     click.initMouseEvent("click", true, false, self, 0, 0, 0, 0, 0, false, false, false, false, 0, null);

//     var a = document.createElementNS("http://www.w3.org/1999/xhtml", 'a');
//     a.href = resource;
//     a.download = resource;
//     a.dispatchEvent(click);
// }

// var title = data.match(/\<title[^\>]*\>([^\<]*)\</i);

// if (title != null)
//     title = title[1];
// else
//     title = resourceName;

// var mime = jqXHR.getResponseHeader('Content-Type');
// var isHTML = mime != null && mime.indexOf("text/html") != -1;
// var isLink = false;
// var fileName = null;
// var fileExt = null;

// if (isHTML)
// {
//     try
//     {
//         var dataDOM = $(data);
//         var resources = $('tr.file > td.name > a, tr.folder > td.name > a', dataDOM);

//         if (resources != null && resources.length)
//         {
//             parseFolder(zipFolder, dataDOM);
//             return;
//         }
//     }
//     catch (e)
//         console.warn("WARNING: failed to parse DOM (" + e.name + ": " + e.message + ')');

//     isLink = true;
// }
// else
// {
//     fileName = jqXHR.getResponseHeader('Content-Disposition');

//     if (fileName != null)
//     {
//         fileName = fileName.match(/filename\=\"(.*)\"$/);

//         if (fileName != null)
//         {
//             fileName = fileName[1];
//             fileExt = fileName.match(/\.(.*)/);

//             if (fileExt != null)
//             {
//                 fileExt = fileExt[1];
//                 fileName = fileName.replace('.' + fileExt, '');
//             }
//         }
//     }

//     if (fileName == null)
//         fileName = resourceName;

//     if (fileExt == null)
//     {
//         if (mime != null)
//         {
//             switch (mime):
//             {
//                 case "application/pdf":
//                     fileExt = "pdf";
//                     break;
//             }
//         }
//         else if (data.indexOf("%PDF") == 0)
//             fileExt = "pdf";
//         else
//             isLink = true;
//     }
// }

// if (isLink)
// {
//     zipFolder.file(safeName(resourceName, usedNames) + ".html",
//         "<!DOCTYPE html>\n" +
//         "<html>\n" +
//         "    <head>\n" +
//         "        <title> " + title + " </title>\n" +
//         "        <script type=\"text/javascript\"> window.location = \"" + resourceLink + "\"; </script>\n" +
//         "    </head>\n" +
//         "    <body></body>\n" +
//         "</html>");

//     return;
// }

// zipFolder.file(safeName(fileName, usedNames) + '.' + fileExt, data);

// console.groupCollapsed(resourceName + ": " + resourceLink);
// console.log(jqXHR.getAllResponseHeaders());
// if (isHTML)
//     console.log(data.match(/\<title[^\>]*\>([^\<]*)\</i));
// console.groupCollapsed("data");
// console.log(data);
// console.groupEnd();
// console.groupEnd();

// console.group(resourceName);
// test = jqXHR.getResponseHeader('Content-Disposition');
// if (test != null)
//     console.log(test.match(/filename\=\"(.*)\"$/)[1]);
// else
//     console.log(null);
// console.log(resourceLink);
// console.groupEnd();
