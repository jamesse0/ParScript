export default function TestResultsList({ results, testKind = 'io_pairs' }) {
  if (!results) return null

  // pytest-graded (system_design): rows are named tests, not input/output pairs.
  // The solver may see which tests failed and the assertion message, never the
  // test source.
  if (testKind === 'pytest') {
    return (
      <ul className="test-results">
        {results.map((r, i) => (
          <li key={i} className={r.passed ? 'passed' : 'failed'}>
            <span className="status">{r.passed ? 'PASS' : 'FAIL'}</span>
            <code>{String(r.input)}</code>
            {!r.passed && r.error && <code>{r.error}</code>}
          </li>
        ))}
      </ul>
    )
  }

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
