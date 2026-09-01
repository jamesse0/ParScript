// mode 'prompt' -> rank by tokens (Tokens + Time columns)
// mode 'manual' -> rank by time (Time column only; no tokens, no par)
export default function LeaderboardTable({ rows, mode = 'prompt' }) {
  const manual = mode === 'manual'
  return (
    <table className="leaderboard-table">
      <thead>
        <tr>
          <th>#</th>
          <th>User</th>
          {!manual && <th>Tokens</th>}
          <th>Time</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i}>
            <td>{i + 1}</td>
            <td>{row.username}</td>
            {!manual && <td>{row.total_input_tokens + row.total_output_tokens}</td>}
            <td>{row.elapsed_seconds.toFixed(1)}s</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
