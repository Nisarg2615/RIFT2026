export function saveToHistory(resultsData) {
  try {
    let history = JSON.parse(localStorage.getItem('pharmaguard_history') || '[]')
    const analysis = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      data: resultsData
    }
    history.unshift(analysis)
    if (history.length > 10) history = history.slice(0, 10)
    localStorage.setItem('pharmaguard_history', JSON.stringify(history))
  } catch (e) {
    console.error('Failed to save history:', e)
  }
}

export function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem('pharmaguard_history') || '[]')
  } catch (e) {
    return []
  }
}
