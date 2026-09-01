// mode 'prompt' -> rank by tokens (Tokens + Time columns)
// mode 'manual' -> rank by time (Time column only; no tokens, no par)
// onSelectRow(row): when given, rows become clickable to open that score's
// prompt trace (prompt mode only -- manual runs have no prompts).
export default function LeaderboardTable({ rows, mode = 'prompt', onSelectRow }) {
  const manual = mode === 'manual'
  const clickable = typeof onSelectRow === 'function'
  return (
    <table className={`leaderboard-table${clickable ? ' clickable' : ''}`}>
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
          <tr
            key={row.submission_id ?? i}
            className={clickable ? 'row-clickable' : undefined}
            onClick={clickable ? () => onSelectRow(row) : undefined}
            title={clickable ? "View this player's prompts" : undefined}
          >
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
