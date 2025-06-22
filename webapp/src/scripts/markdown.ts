import { marked, Renderer } from "marked";

export function renderMarkdown(text: string): string {
    const html = marked(text) as string;
    return html;
}