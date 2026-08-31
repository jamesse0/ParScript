export default function TestResultsList({ results }) {
  if (!results) return null
  return (
    <ul className="test-results">
      {results.map((r, i) => (
        <li key={i} className={r.passed ? 'passed' : 'failed'}>
          <span className="status">{r.passed ? 'PASS' : 'FAIL'}</span>
          <code>input: {JSON.stringify(r.input)}</code>
          <code>expected: {JSON.stringify(r.expected_output)}</code>
          {!r.passed && <code>actual: {JSON.stringify(r.actual_output)}</code>}
        </li>
      ))}
    </ul>
  )
}
