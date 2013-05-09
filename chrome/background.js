var _gaq = _gaq || [];
_gaq.push(['_setAccount', 'UA-40792111-1']);
_gaq.push(['_trackPageview']);

var ga = document.createElement('script');
ga.type = 'text/javascript';
ga.async = true;
ga.src = 'https://ssl.google-analytics.com/ga.js';
var s = document.getElementsByTagName('script')[0];
s.parentNode.insertBefore(ga, s);

chrome.pageAction.onClicked.addListener(function(tab)
{
    chrome.tabs.sendMessage(tab.id, false, function(url)
    {
        chrome.tabs.create({ url: url });
    });
});

chrome.tabs.onUpdated.addListener(function(tabId, changeInfo, tab)
{
    chrome.tabs.sendMessage(tabId, true, function(isMoodle)
    {
        if (isMoodle)
            chrome.pageAction.show(tabId);
        else
            chrome.pageAction.hide(tabId);
    });
});
