function formatElapsed(totalSeconds) {
  const m = Math.floor(totalSeconds / 60)
  const s = Math.floor(totalSeconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

export default function Timer({ elapsedSeconds }) {
  return <div className="timer">{formatElapsed(elapsedSeconds)}</div>
}
