export async function analyzeImage(imageBlob) {
  const form = new FormData()
  form.append('image', imageBlob, 'capture.jpg')

  const res = await fetch('/api/analyze', { method: 'POST', body: form })
  if (!res.ok) throw new Error(`analyze failed: ${res.status}`)
  return res.json()
}

export async function getRecommendations(skinVision) {
  const res = await fetch('/api/recommend', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(skinVision),
  })
  if (!res.ok) throw new Error(`recommend failed: ${res.status}`)
  return res.json()
}
