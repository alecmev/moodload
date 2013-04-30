// Incoming message from the background process
chrome.runtime.onMessage.addListener(function(check, sender, respond)
{
    var url = document.URL.match(/(.+)\/course\/view\.php\?.*id\=(\d+)/i);
    var isMoodle = 
        document.getElementsByTagName('html')[0].innerHTML
        .match(/moodle/i) != null && url != null;
    
    if (check)
        respond(isMoodle);
    else if (isMoodle)
    {
        var cookies = document.cookie
            .replace(/(__utm[abczv]|_ga)=[^;]*;?/g, '')
            .replace(/\s/g, '')
            .replace(/;$/, '')
            .replace(/\&/g, '%26')
            .replace(/;/g, '&');

        respond(
            'http://moodload.jeremejevs.com/?moodload-auto=1&moodload-url=' + 
            encodeURIComponent(document.URL) +
            (cookies.length > 0 ? '&' + cookies : '')
        );

        // chrome.tabs.create({
        //     url: 
        //         'http://moodload.jeremejevs.com/?url=' + 
        //         encodeURIComponent(document.URL) +
        //         (cookies.length > 0 ? '&' + cookies : '')
        // });
    }
});
