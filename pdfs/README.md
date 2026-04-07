# PDF Directory

Place your PDF files here. The chatbot will automatically load all PDFs from this directory.

## Usage

1. **Single PDF Mode:**
   - Place a single PDF in the project root as `your_doc.pdf`
   - Or change `DEFAULT_PDF_PATH` in `config.py`

2. **Multiple PDF Mode (NEW):**
   - Place multiple PDFs in this `pdfs/` directory
   - The chatbot will automatically load and combine them
   - Perfect for menus + FAQs, contracts + policies, etc.

## Examples

### Restaurant Use Case

```
pdfs/
├── menu.pdf          ← Menu items & prices
├── hours.pdf         ← Operating hours & specials
└── faq.pdf           ← Common questions answered
```

Then ask:

- "What are your opening hours?"
- "Do you have vegetarian options?"
- "What's on your lunch special menu?"

### Legal Firm Use Case

```
pdfs/
├── contracts.pdf     ← Contract templates
├── policies.pdf      ← Business policies
└── faq.pdf          ← Common legal questions
```

## Tips

- **All PDFs combined** → Single vectorstore with everything
- **Smart caching** → Embeddings cached to `.chroma/`
- **PDF tracking** → Automatically detects new/updated files
- **Source attribution** → Bot shows which PDF it references

## Auto-Detection

The chatbot will:

1. Check for `pdfs/` directory on startup
2. If found, load all PDF files
3. If not found, fall back to single PDF mode
4. Automatic re-embedding if files change

## Troubleshooting

| Issue                | Solution                                          |
| -------------------- | ------------------------------------------------- |
| "No PDFs Found"      | Add PDF files to this directory                   |
| "Could not load PDF" | Ensure files are valid PDFs with searchable text  |
| "Mixed results"      | PDFs are working - this is normal!                |
| "Slow first startup" | Creating embeddings - subsequent runs are instant |

**For single-file mode:** Just place `your_doc.pdf` in the main project folder instead.
