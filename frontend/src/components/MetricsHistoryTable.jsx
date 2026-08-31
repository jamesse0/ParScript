export default function MetricsHistoryTable({ rows }) {
  return (
    <table className="metrics-history-table">
      <thead>
        <tr>
          <th>Problem</th>
          <th>Tokens</th>
          <th>Par</th>
          <th>Time</th>
          <th>Result</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i}>
            <td>{row.problem_title}</td>
            <td>{row.total_tokens}</td>
            <td>{row.par_tokens}</td>
            <td>{row.elapsed_seconds.toFixed(1)}s</td>
            <td>{row.passed ? 'Pass' : 'Fail'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
