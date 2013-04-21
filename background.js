chrome.pageAction.onClicked.addListener(function(tab)
{
    chrome.tabs.sendMessage(tab.id, false, null);
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
