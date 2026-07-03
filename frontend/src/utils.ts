function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderInlineMarkdown(text: string): string {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code>$1</code>");
}

function isOrderedListItem(line: string): boolean {
  return /^\d+\.\s+/.test(line);
}

function isUnorderedListItem(line: string): boolean {
  return /^[-*+]\s+/.test(line);
}

function stripListMarker(line: string): string {
  return line.replace(/^\d+\.\s+/, "").replace(/^[-*+]\s+/, "");
}

function renderParagraphWithLists(text: string): string {
  const parts = text.split(/(?=\d+\.\s+)/).map((part) => part.trim()).filter(Boolean);
  if (parts.length <= 1 || !/^\d+\.\s+/.test(parts[1] ?? "")) {
    return `<p>${renderInlineMarkdown(text)}</p>`;
  }

  const [intro, ...items] = parts;
  const listHtml = items
    .map((item) => `<li>${renderInlineMarkdown(item.replace(/^\d+\.\s+/, ""))}</li>`)
    .join("");
  const introHtml = intro && !/^\d+\.\s+/.test(intro) ? `<p>${renderInlineMarkdown(intro)}</p>` : "";
  const onlyList = intro && /^\d+\.\s+/.test(intro);
  const firstItem = onlyList
    ? `<li>${renderInlineMarkdown(intro.replace(/^\d+\.\s+/, ""))}</li>`
    : "";
  return `${introHtml}<ol>${firstItem}${listHtml}</ol>`;
}

export function renderMarkdown(content: string): string {
  const normalized = content.replace(/\r\n/g, "\n").trim();
  if (!normalized) return "";

  const lines = normalized.split("\n");
  const blocks: string[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index].trim();

    if (!line) {
      index += 1;
      continue;
    }

    const headingMatch = line.match(/^(#{1,4})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      blocks.push(`<h${level}>${renderInlineMarkdown(headingMatch[2])}</h${level}>`);
      index += 1;
      continue;
    }

    const sectionMatch = line.match(/^【(.+?)】\s*(.*)$/);
    if (sectionMatch) {
      const title = sectionMatch[1];
      const rest = sectionMatch[2];
      blocks.push(`<h3>${renderInlineMarkdown(title)}</h3>`);
      if (rest) {
        blocks.push(renderParagraphWithLists(rest));
      }
      index += 1;
      continue;
    }

    if (isOrderedListItem(line) || isUnorderedListItem(line)) {
      const ordered = isOrderedListItem(line);
      const items: string[] = [];
      while (index < lines.length) {
        const current = lines[index].trim();
        if (!current) break;
        if (ordered && !isOrderedListItem(current)) break;
        if (!ordered && !isUnorderedListItem(current)) break;
        items.push(`<li>${renderInlineMarkdown(stripListMarker(current))}</li>`);
        index += 1;
      }
      blocks.push(`<${ordered ? "ol" : "ul"}>${items.join("")}</${ordered ? "ol" : "ul"}>`);
      continue;
    }

    const paragraphLines = [line];
    index += 1;
    while (index < lines.length) {
      const next = lines[index].trim();
      if (!next) break;
      if (
        /^(#{1,4})\s+/.test(next) ||
        /^【.+?】/.test(next) ||
        isOrderedListItem(next) ||
        isUnorderedListItem(next)
      ) {
        break;
      }
      paragraphLines.push(next);
      index += 1;
    }
    blocks.push(renderParagraphWithLists(paragraphLines.join(" ")));
  }

  return blocks.join("");
}

export function stripMarkdownForSpeech(content: string): string {
  return content
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/\*(.+?)\*/g, "$1")
    .replace(/`(.+?)`/g, "$1")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^【(.+?)】\s*/gm, "$1：")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/^\s*\d+\.\s+/gm, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}
