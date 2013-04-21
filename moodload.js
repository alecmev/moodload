chrome.runtime.onMessage.addListener(function(check, sender, respond)
{
    url = document.URL.match(/(.+)\/course\/view\.php\?.*id\=(\d+)/i);
    isMoodle = document.getElementsByTagName('html')[0].innerHTML.match(/moodle/i) != null && url != null;

    if (check)
        respond(isMoodle);
    else if (isMoodle)
        window.location = url[1] + "/mod/resource/index.php?id=" + url[2];
});
