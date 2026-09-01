import Markdown from './Markdown'

// Problem descriptions are one prose string with optional trailing
// "Example N:\nInput: ...\nOutput: ...\nExplanation: ..." blocks (seeded
// content, not user-generated -- see Markdown.jsx). This splits those
// blocks out so they can render as their own boxes, LeetCode-style,
// instead of running into the prose as plain text.
function parseDescription(text) {
  if (!text) return { intro: '', examples: [] }

  const segments = text.split(/\n\n(?=Example\s+\d+:)/)
  const intro = segments[0]

  const examples = segments.slice(1).map((block) => {
    const header = block.match(/^Example\s+(\d+):\n([\s\S]*)$/)
    const number = header ? header[1] : null
    const rest = header ? header[2] : block

    const input = rest.match(/^Input:\s*([\s\S]*?)\nOutput:/)
    const output = rest.match(/\nOutput:\s*([\s\S]*?)(?:\nExplanation:|$)/)
    const explanation = rest.match(/\nExplanation:\s*([\s\S]*)$/)

    return {
      number,
      input: input ? input[1].trim() : null,
      output: output ? output[1].trim() : null,
      explanation: explanation ? explanation[1].trim() : null,
    }
  })

  return { intro, examples }
}

export default function ProblemDescription({ text }) {
  if (!text) return null
  const { intro, examples } = parseDescription(text)

  return (
    <div className="problem-description">
      <Markdown text={intro} />
      {examples.map((ex, i) => (
        <div className="example-block" key={ex.number ?? i}>
          <p className="example-title">Example {ex.number ?? i + 1}:</p>
          {ex.input != null && (
            <p className="example-row">
              <span className="example-label">Input:</span> {ex.input}
            </p>
          )}
          {ex.output != null && (
            <p className="example-row">
              <span className="example-label">Output:</span> {ex.output}
            </p>
          )}
          {ex.explanation && (
            <p className="example-row">
              <span className="example-label">Explanation:</span> {ex.explanation}
            </p>
          )}
        </div>
      ))}
    </div>
  )
}
