// Theme before the first paint (no white flash in dark mode). A file, not an inline script: the CSP only allows 'self'.
try {
  // dark first: the prism's light reads best on a dark ground ("v2": the redesign starts everyone on dark once)
  var m = (JSON.parse(localStorage.getItem('lingoprism-theme-v2') || '{}').state || {}).mode || 'dark'
  if (m === 'dark' || (m === 'system' && matchMedia('(prefers-color-scheme: dark)').matches)) document.documentElement.classList.add('dark')
} catch (e) { document.documentElement.classList.add('dark') }
