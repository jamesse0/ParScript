export default function LeaderboardTable({ rows }) {
  return (
    <table className="leaderboard-table">
      <thead>
        <tr>
          <th>#</th>
          <th>User</th>
          <th>Tokens</th>
          <th>Time</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i}>
            <td>{i + 1}</td>
            <td>{row.username}</td>
            <td>{row.total_input_tokens + row.total_output_tokens}</td>
            <td>{row.elapsed_seconds.toFixed(1)}s</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
