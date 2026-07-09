// Parses the simple GFM-style pipe tables used in the 표 field, e.g.
// "| 설명 |\n| :--- |\n| some text |" -> { headers: string[], rows: string[][] }
export function parsePipeTable(src) {
  if (!src) return null
  const lines = src
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)
  if (lines.length < 2) return null

  const parseRow = (line) =>
    line
      .replace(/^\|/, '')
      .replace(/\|$/, '')
      .split('|')
      .map((cell) => cell.trim())

  const headers = parseRow(lines[0])
  const isSeparator = (line) => /^\|?[\s:|-]+\|?$/.test(line)
  const bodyLines = isSeparator(lines[1]) ? lines.slice(2) : lines.slice(1)
  const rows = bodyLines.map(parseRow)

  return { headers, rows }
}
