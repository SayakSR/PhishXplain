// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'toggleExtension') {
    // Handle extension toggle
    console.log('Extension ' + (message.enabled ? 'enabled' : 'disabled'));
  }
});

// Listen for tab updates to detect phishing warnings
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  // Check if extension is enabled
  const result = await chrome.storage.local.get(['enabled']);
  if (!result.enabled) {
    return; // Extension is disabled
  }

  // Check if the page title indicates a phishing warning
  if (changeInfo.title && changeInfo.title.includes("Security error")) {
    try {
      // Get the current tab's URL
      const url = tab.url;
      console.log('Phishing site detected:', url);

      // Send URL to Flask server first to get analysis ID
      console.log('Sending request to Flask server...');
      const response = await fetch('http://127.0.0.1:5000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url })
      });

      console.log('Response status:', response.status);
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Server error: ${errorText}`);
      }

      // Get the analysis ID
      const { analysis_id } = await response.json();
      console.log('Analysis ID:', analysis_id);

      // Open landing page in a new tab with analysis ID
      const landingTab = await chrome.tabs.create({
        url: `http://127.0.0.1:5000/landing?id=${analysis_id}`
      });

      // Wait for the landing tab to be fully loaded
      await new Promise((resolve) => {
        chrome.tabs.onUpdated.addListener(function listener(tabId, info) {
          if (tabId === landingTab.id && info.status === 'complete') {
            chrome.tabs.onUpdated.removeListener(listener);
            resolve();
          }
        });
      });

      // Close the original tab
      await chrome.tabs.remove(tab.id);

    } catch (error) {
      console.error('Error:', error);
      // Show error message in the landing tab if it exists
      if (landingTab) {
        try {
          await chrome.scripting.executeScript({
            target: { tabId: landingTab.id },
            func: (error) => {
              document.body.innerHTML = `
                <div style="text-align: center; padding: 20px;">
                  <h1 style="color: #dc3545;">Error</h1>
                  <p>${error.message}</p>
                  <p>Please check the console for more details.</p>
                </div>
              `;
            },
            args: [error]
          });
        } catch (scriptError) {
          console.error('Failed to show error message:', scriptError);
        }
      }
    }
  }
}); 