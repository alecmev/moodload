chrome.runtime.onMessage.addListener(function(message, sender, sendResponse)
{
    var url = document.URL.match(/(.+)\/course\/view\.php\?.*id\=(\d+)/i);
    var isMoodle = 
        document.getElementsByTagName('html')[0].innerHTML
        .match(/moodle/i) != null && url != null;
    
    if (message)
        sendResponse(isMoodle);
    else if (isMoodle)
    {
        var cookies = document.cookie
            .replace(/(__utm[abczv]|_ga)=[^;]*;?/g, '')
            .replace(/\s/g, '')
            .replace(/;$/, '')
            .replace(/\&/g, '%26')
            .replace(/;/g, '&');

        sendResponse(
            'http://moodload.jeremejevs.com/?moodload-auto=1&moodload-url=' + 
            encodeURIComponent(document.URL) +
            (cookies.length > 0 ? '&' + cookies : '')
        );
    }
});
