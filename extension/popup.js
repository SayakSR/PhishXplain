document.addEventListener('DOMContentLoaded', function() {
  const toggle = document.getElementById('extension-toggle');
  const statusText = document.getElementById('status-text');

  // Load the saved state
  chrome.storage.local.get(['enabled'], function(result) {
    const isEnabled = result.enabled !== undefined ? result.enabled : false;
    toggle.checked = isEnabled;
    updateStatus(isEnabled);
  });

  // Handle toggle changes
  toggle.addEventListener('change', function() {
    const isEnabled = toggle.checked;
    chrome.storage.local.set({ enabled: isEnabled }, function() {
      updateStatus(isEnabled);
      
      // Send message to background script
      chrome.runtime.sendMessage({ 
        action: 'toggleExtension', 
        enabled: isEnabled 
      });
    });
  });

  function updateStatus(isEnabled) {
    statusText.textContent = isEnabled ? 'Enabled' : 'Disabled';
    statusText.className = 'status ' + (isEnabled ? 'enabled' : 'disabled');
  }
}); 