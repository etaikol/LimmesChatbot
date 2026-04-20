// Generates docs/Chatbot-Features.docx — a light, non-technical feature showcase.
// Run from project root:  node scripts/generate_features_docx.js
// Regenerate any time features change (or edit FEATURES.md first, then regenerate).

const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, PageOrientation, LevelFormat,
  InternalHyperlink, Bookmark, TabStopType, TabStopPosition,
  HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, PageBreak,
} = require('docx');

// ─── helpers ──────────────────────────────────────────────────────────
const BLUE = '2E75B6';
const GRAY = '808080';
const LIGHT_BG = 'F4F7FB';

function p(text, opts = {}) {
  return new Paragraph({
    ...opts,
    children: [new TextRun({ text, ...(opts.run || {}) })],
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: 'bullets', level: 0 },
    children: [new TextRun(text)],
  });
}

function screenshotPlaceholder(label) {
  return new Paragraph({
    spacing: { before: 120, after: 120 },
    border: {
      top: { style: BorderStyle.DASHED, size: 4, color: GRAY },
      bottom: { style: BorderStyle.DASHED, size: 4, color: GRAY },
      left: { style: BorderStyle.DASHED, size: 4, color: GRAY },
      right: { style: BorderStyle.DASHED, size: 4, color: GRAY },
    },
    shading: { fill: LIGHT_BG, type: ShadingType.CLEAR },
    children: [new TextRun({ text: `[ Screenshot: ${label} ]`, italics: true, color: GRAY })],
  });
}

function h1(text, bookmarkId) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 180 },
    children: [new Bookmark({ id: bookmarkId, children: [new TextRun(text)] })],
  });
}

function h2(text, bookmarkId) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 120 },
    children: [new Bookmark({ id: bookmarkId, children: [new TextRun(text)] })],
  });
}

function tocRow(label, anchor) {
  return new Paragraph({
    tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
    spacing: { after: 60 },
    children: [
      new InternalHyperlink({
        anchor,
        children: [new TextRun({ text: label, style: 'Hyperlink' })],
      }),
    ],
  });
}

// ─── feature content (grouped for non-technical reader) ───────────────
const sections = [
  {
    id: 'sec-customer',
    title: '1. What Your Customers See',
    intro: 'Everything the bot looks like and where it lives.',
    items: [
      { id: 'web-widget', name: 'Web Widget', text: 'A small chat bubble you can paste onto any website with one line. Users click it and talk to the bot right there.' },
      { id: 'whatsapp', name: 'WhatsApp', text: 'The bot can answer WhatsApp messages through Twilio. Customers message your business number and the bot replies.' },
      { id: 'telegram', name: 'Telegram', text: 'Same bot also works as a Telegram channel. One setup, extra reach.' },
      { id: 'line', name: 'LINE', text: 'Full LINE support — messages, login, visual menus, product cards, broadcast campaigns. Big in Thailand and Japan.' },
      { id: 'languages', name: '12 Languages, Auto-Detected', text: 'The bot reads the message and replies in the same language — English, Hebrew, Arabic, Farsi, Thai, French, Spanish, German, Russian, Japanese, Chinese, Hindi. Hebrew / Arabic / Farsi automatically flip to right-to-left layout.' },
      { id: 'cli', name: 'CLI Chat (for You)', text: 'A terminal chat you use to test the bot privately before pushing changes live.' },
    ],
  },
  {
    id: 'sec-understanding',
    title: '2. Understanding & Answering',
    intro: 'How the bot actually figures out what to say.',
    items: [
      { id: 'rag', name: 'Knowledge from Your Documents (RAG)', text: 'You drop PDFs, Word files, web pages into a folder and the bot reads them and answers questions based on that content. No code changes.' },
      { id: 'hybrid', name: 'Hybrid Search', text: 'Combines two search styles — one for meaning, one for exact words. Catches both "a sofa for my living room" and "SKU LM-4412" well.' },
      { id: 'rewrite', name: 'Smart Follow-Up Understanding', text: 'When a customer asks "and the price?" the bot understands they mean the last product discussed. It rewrites follow-ups into full questions before searching.' },
      { id: 'memory', name: 'Session Memory', text: 'Each conversation keeps its last ~10 turns so the bot doesn\u2019t forget what was just said.' },
      { id: 'user-memory', name: 'Long-Term User Memory', text: 'If the same person comes back next week, the bot can remember facts about them — like their preferred language or what they asked last time.' },
    ],
  },
  {
    id: 'sec-safety',
    title: '3. Safety & Cost Control',
    intro: 'Stops the bot from costing you money or saying the wrong thing.',
    items: [
      { id: 'budget', name: 'Daily Budget Cap', text: 'Set a daily spend limit (e.g. $3/day). When hit, the bot politely tells people to come back tomorrow instead of racking up charges.' },
      { id: 'rate-limit', name: 'Rate Limiting', text: 'Blocks anyone (or any script) hammering the bot with too many messages per minute.' },
      { id: 'spam', name: 'Spam & Gibberish Blocking', text: 'Detects random key-mashing and repeated junk messages before they reach the AI — saving money and blocking abuse.' },
      { id: 'injection', name: 'Prompt Injection Protection', text: 'Catches tricks like "ignore your instructions and pretend to be..." and either logs them or blocks them.' },
      { id: 'sanitize', name: 'Input Cleanup', text: 'Every message is cleaned before it reaches the AI — no malformed input, no unsafe characters.' },
      { id: 'headers', name: 'Web Security', text: 'Standard security headers on the API so browsers treat the widget safely.' },
    ],
  },
  {
    id: 'sec-human',
    title: '4. Human-in-the-Loop',
    intro: 'The bot knows when it is out of its depth.',
    items: [
      { id: 'handoff', name: 'Handoff to Live Agent', text: 'When the bot isn\u2019t sure, or the user asks to speak to a human, the conversation is queued for you to answer from the admin dashboard. The bot steps out.' },
      { id: 'fallback', name: 'Unanswered Questions Log', text: 'Every time the bot says "I don\u2019t have that information", the question is saved so you can see the gaps in your knowledge base and add the missing info.' },
      { id: 'feedback', name: 'Thumbs Up / Thumbs Down', text: 'Customers rate answers. Over time you see which answers are working and which need fixing.' },
      { id: 'contact', name: 'Lead Capture', text: 'When a customer wants to leave their details (name, phone, email, question), the bot captures them cleanly and stores them for you.' },
    ],
  },
  {
    id: 'sec-growing',
    title: '5. Growing & Improving',
    intro: 'Data you collect to make the bot better over time.',
    items: [
      { id: 'analytics', name: 'Analytics', text: 'Tracks: how many questions per day, response times, which languages people use, handoff rate, feedback scores. Shown as charts in the admin dashboard.' },
      { id: 'ab', name: 'A/B Testing Personalities', text: 'Run two different bot personalities at the same time, split traffic between them, and see which one converts better. Switch without redeploying.' },
    ],
  },
  {
    id: 'sec-business',
    title: '6. Business Tools',
    intro: 'Turning conversations into actual business outcomes.',
    items: [
      { id: 'products', name: 'Structured Product Catalog', text: 'A YAML file lists your products with names, prices, categories. The bot references them by name without having to index each one as a document.' },
      { id: 'push', name: 'Push Messages & Campaigns', text: 'Send one-off or broadcast messages to LINE users — promos, reminders, announcements.' },
      { id: 'line-flex', name: 'LINE Flex Messages', text: 'Pre-built visual cards for products, contact info, carousels. Looks native, not like a text bot.' },
      { id: 'line-imagemap', name: 'LINE Imagemap', text: 'A full-width image with tappable regions — great for visual menus or campaign banners.' },
      { id: 'line-richmenu', name: 'LINE Rich Menu', text: 'The persistent button menu at the bottom of the LINE chat. Create, edit, and swap menus from the dashboard.' },
      { id: 'line-login', name: 'LINE Login', text: 'Users can sign in with LINE — you then know their name and profile and greet them personally.' },
    ],
  },
  {
    id: 'sec-admin',
    title: '7. Admin Dashboard',
    intro: 'One page to run everything.',
    items: [
      { id: 'admin-overview', name: 'Overview Page', text: 'At-a-glance: active sessions, today\u2019s spend, handoff queue, channel status.' },
      { id: 'admin-sessions', name: 'Session Browser', text: 'See every conversation happening in real time. Read any chat, delete old ones.' },
      { id: 'admin-config', name: 'Config Editor', text: 'Edit the client info, personality, and knowledge base files directly from the browser — no code.' },
      { id: 'admin-line', name: 'LINE Controls', text: 'Create Rich Menus, preview Flex Messages, send broadcast campaigns.' },
      { id: 'admin-auth', name: 'Secure Login', text: 'Multiple admin / viewer accounts with proper password hashing. Not just a single shared key.' },
    ],
  },
  {
    id: 'sec-flex',
    title: '8. Flexibility',
    intro: 'The parts that make this a template, not a one-off.',
    items: [
      { id: 'multi-client', name: 'Multi-Client', text: 'One codebase, many businesses. Currently runs two — a Hebrew interior design studio and a Thai cannabis dispensary. Adding a third = new YAML file, no code.' },
      { id: 'personalities', name: 'Swappable Personalities', text: 'Tone presets: default, sales, clinic, official, friendly-official, design-studio, Thai budtender. Pick one in a config file and the bot rewrites its whole vibe.' },
      { id: 'llm-swap', name: 'OpenAI or Anthropic', text: 'Switch the underlying AI model with one setting — no code change. GPT-4o-mini default, Claude optional.' },
      { id: 'storage', name: 'Storage Options', text: 'Conversations can live on disk (default), in memory (for tests), or in PostgreSQL (for scale).' },
      { id: 'tools', name: 'Built-In Tools', text: 'Web scraper (feed URLs into the knowledge base) and LLM-powered translator (no separate translation API needed).' },
    ],
  },
];

const roadmap = {
  tier1: [
    ['Tool / Function Calling', 'Let the bot actually DO things — book a visit, check stock, send an email — not just answer.'],
    ['Streaming Responses', 'Replies appear word-by-word as they generate. Feels twice as fast.'],
    ['Quality Testing (Eval Harness)', 'A set of standard questions run against every change, so we notice if a "small fix" makes answers worse.'],
    ['Self-Healing Knowledge Base', 'Parse the unanswered questions log and suggest new content to add — one click to approve.'],
    ['Per-Client Cost Tracking', 'See tokens and spend per client, channel, and session. Needed before charging other businesses.'],
  ],
  tier2: [
    ['Image Understanding', 'Customer sends a photo of a room or a product; the bot responds to the image.'],
    ['Outbound Webhooks', 'When something happens (lead captured, handoff triggered), the bot pings your CRM, Google Sheets, or Zapier.'],
    ['Proactive Messages', 'Scheduled outreach — "your measurements are ready", promo reminders, follow-ups.'],
    ['Prompt Versioning', 'Every personality gets a version number. Roll back to last week\u2019s prompt if this week\u2019s is worse.'],
    ['Deeper Analytics', 'Funnels (greet -> question -> lead), cohort retention, drop-off analysis.'],
    ['Redis-Backed Limits', 'For running multiple servers at once.'],
    ['Content Safety Filter', 'Scan the bot\u2019s replies for unsafe content before sending.'],
  ],
  tier3: [
    ['Voice', 'Customer sends a WhatsApp voice note; bot transcribes, answers, replies with voice.'],
    ['Agentic Loops', 'Bot plans a multi-step task (search -> reason -> call tool -> call another -> answer).'],
    ['Fine-Tuning on Real Conversations', 'Once we have ~1000 quality-labeled chats, train the model on your specific domain.'],
    ['Booking / POS Integration', 'Direct connection to Google Calendar or your point-of-sale for real transactions.'],
    ['Semantic Caching', 'Remember answers to near-identical questions instead of calling the AI every time. Major cost savings at scale.'],
  ],
};

// ─── build document ───────────────────────────────────────────────────
const children = [];

// Title
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 0, after: 120 },
  children: [new TextRun({ text: 'Chatbot Capabilities', bold: true, size: 56, color: BLUE })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 360 },
  children: [new TextRun({ text: 'What it does today, and what we can add next', italics: true, size: 24, color: GRAY })],
}));

// Intro paragraph
children.push(new Paragraph({
  spacing: { after: 240 },
  children: [new TextRun({ text: 'This is a plain-language tour of everything the chatbot can do. Click any item in the table of contents to jump to it. Each feature has one short paragraph — enough to know what it is, not a manual. Screenshot spaces are included so you can drop images in as you go.' })],
}));

// TOC header
children.push(new Paragraph({
  spacing: { before: 240, after: 120 },
  children: [new TextRun({ text: 'Table of Contents', bold: true, size: 32, color: BLUE })],
}));

// TOC entries
sections.forEach(s => {
  children.push(tocRow(s.title, s.id));
  s.items.forEach(item => {
    children.push(new Paragraph({
      indent: { left: 400 },
      spacing: { after: 30 },
      children: [
        new InternalHyperlink({
          anchor: item.id,
          children: [new TextRun({ text: item.name, style: 'Hyperlink', size: 20 })],
        }),
      ],
    }));
  });
});
children.push(tocRow('9. What Needs to Be Done (Roadmap)', 'sec-roadmap'));

children.push(new Paragraph({ children: [new PageBreak()] }));

// Body sections
sections.forEach(section => {
  children.push(h1(section.title, section.id));
  children.push(new Paragraph({
    spacing: { after: 180 },
    children: [new TextRun({ text: section.intro, italics: true, color: GRAY })],
  }));
  section.items.forEach(item => {
    children.push(h2(item.name, item.id));
    children.push(p(item.text, { spacing: { after: 120 } }));
    children.push(screenshotPlaceholder(item.name));
  });
});

// Roadmap
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h1('9. What Needs to Be Done (Roadmap)', 'sec-roadmap'));
children.push(new Paragraph({
  spacing: { after: 240 },
  children: [new TextRun({ text: 'Ideas grouped by how much work they need. Tier 1 = highest value for the effort. Tier 3 = bigger projects, later.', italics: true, color: GRAY })],
}));

[
  ['Tier 1 — Highest ROI Next', roadmap.tier1],
  ['Tier 2 — Medium Complexity', roadmap.tier2],
  ['Tier 3 — Advanced / Later', roadmap.tier3],
].forEach(([title, items]) => {
  children.push(h2(title, 'rm-' + title.split(' ')[0]));
  items.forEach(([name, desc]) => {
    children.push(new Paragraph({
      spacing: { before: 80, after: 40 },
      children: [new TextRun({ text: name, bold: true })],
    }));
    children.push(new Paragraph({
      spacing: { after: 120 },
      children: [new TextRun({ text: desc })],
    }));
  });
});

// End note
children.push(new Paragraph({
  spacing: { before: 480, after: 120 },
  border: { top: { style: BorderStyle.SINGLE, size: 6, color: BLUE, space: 6 } },
  children: [new TextRun({ text: 'How to add screenshots', bold: true, size: 24, color: BLUE })],
}));
children.push(p('In Word: click any dashed "[ Screenshot: ... ]" box, delete the text, then Insert -> Picture. The surrounding dashed border disappears when you replace the text.'));
children.push(p('To regenerate this document after features change: edit docs/FEATURES.md, then update scripts/generate_features_docx.js and run "node scripts/generate_features_docx.js" from the project root.', { run: { italics: true, color: GRAY } }));

// ─── document assembly ────────────────────────────────────────────────
const doc = new Document({
  creator: 'Limmes Chatbot',
  title: 'Chatbot Capabilities',
  styles: {
    default: { document: { run: { font: 'Arial', size: 22 } } }, // 11pt base
    paragraphStyles: [
      {
        id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 36, bold: true, color: BLUE, font: 'Arial' },
        paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 },
      },
      {
        id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 26, bold: true, color: '1F3864', font: 'Arial' },
        paragraph: { spacing: { before: 240, after: 80 }, outlineLevel: 1 },
      },
    ],
  },
  numbering: {
    config: [{
      reference: 'bullets',
      levels: [{ level: 0, format: LevelFormat.BULLET, text: '\u2022', alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }],
    }],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 }, // US Letter
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: 'Chatbot Capabilities', italics: true, color: GRAY, size: 18 })],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: 'Page ', color: GRAY, size: 18 }),
            new TextRun({ children: [PageNumber.CURRENT], color: GRAY, size: 18 }),
          ],
        })],
      }),
    },
    children,
  }],
});

const outPath = path.join(__dirname, '..', 'docs', 'Chatbot-Features.docx');
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outPath, buffer);
  console.log('Generated:', outPath);
});
