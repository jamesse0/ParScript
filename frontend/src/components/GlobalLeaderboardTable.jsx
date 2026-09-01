// Global leaderboard, ranked by handicap (avg tokens-vs-par ratio, ascending -- lower is better).
export default function GlobalLeaderboardTable({ rows }) {
  return (
    <table className="leaderboard-table">
      <thead>
        <tr>
          <th>#</th>
          <th>User</th>
          <th>Handicap</th>
          <th>Problems Solved</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i}>
            <td>{i + 1}</td>
            <td>{row.username}</td>
            <td>{row.handicap.toFixed(2)}</td>
            <td>{row.problems_solved}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
