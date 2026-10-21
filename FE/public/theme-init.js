// Theme before the first paint (no white flash in dark mode). A file, not an inline script: the CSP only allows 'self'.
try {
  var m = (JSON.parse(localStorage.getItem('lingoprism-theme') || '{}').state || {}).mode || 'system'
  if (m === 'dark' || (m === 'system' && matchMedia('(prefers-color-scheme: dark)').matches)) document.documentElement.classList.add('dark')
} catch (e) { /* storage blocked: light theme */ }
