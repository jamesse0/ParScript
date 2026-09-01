// Display label for a problem's `difficulty` value. The stored value stays
// slug-like (`system_design`) -- it's used in URLs, CSS class names, and the
// DB CHECK constraint -- so only the on-screen text is prettified here.
const LABELS = {
  easy: 'Easy',
  medium: 'Medium',
  hard: 'Hard',
  system_design: 'System Design',
}

export function difficultyLabel(value) {
  return LABELS[value] ?? value
}
