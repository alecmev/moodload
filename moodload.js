var folderPath;

function download(resource)
{
    var click = document.createEvent("MouseEvents");
    click.initMouseEvent("click", true, false, self, 0, 0, 0, 0, 0, false, false, false, false, 0, null);

    var a = document.createElementNS("http://www.w3.org/1999/xhtml", 'a');
    a.href = resource;
    a.download = resource;
    a.dispatchEvent(click);
}

function parse(dataDOM)
{
    var folders = $('tr.folder > td.name > a', dataDOM);
    var links = $('tr.file > td.name > a', dataDOM);

    folders.each(function()
    {
        $.get(folderPath + $(this).attr("href"), function(data, textStatus, jqXHR)
        {
            parse($(data));
        });
    });

    links.each(function()
    {
        download($(this).attr("href"));
    });
}

chrome.runtime.onMessage.addListener(function(check, sender, respond)
{
    var url = document.URL.match(/(.+)\/course\/view\.php\?.*id\=(\d+)/i);
    var isMoodle = document.getElementsByTagName('html')[0].innerHTML.match(/moodle/i) != null && url != null;

    if (check)
        respond(isMoodle);

    else if (isMoodle)
    {
        folderPath = url[1] + "/mod/resource/";

        $.get(folderPath + "index.php?id=" + url[2], function(data)
        {
            $('td.cell.c1 > a', $(data)).each(function()
            {
                var resource = folderPath + $(this).attr("href");

                $.get(resource, function(data, textStatus, jqXHR)
                {
                    var mime = jqXHR.getResponseHeader('Content-Type');

                    if (mime == null || mime.indexOf("text/html") == -1)
                    {
                        download(resource);
                        return;
                    }

                    try
                    {
                        var dataDOM = $(data);

                        if ($('tr.file > td.name > a, tr.folder > td.name > a', dataDOM).length > 0)
                        {
                            parse(dataDOM);
                        }
                    }
                    catch (e)
                    {
                    }
                });
            });
        });
    }
});
