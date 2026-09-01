import { marked } from 'marked'

marked.setOptions({ breaks: true, gfm: true })

// Problem descriptions are seeded content (not user-generated), so rendering
// the parsed HTML directly is fine -- no untrusted input reaches this.
export default function Markdown({ text }) {
  if (!text) return null
  return <div className="markdown" dangerouslySetInnerHTML={{ __html: marked.parse(text) }} />
}
