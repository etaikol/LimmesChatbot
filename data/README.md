# `data/` — Knowledge base

This is where the chatbot reads its content from. **Drop files here** and run
the ingestion script — anything supported is automatically chunked, embedded,
and stored in the vector store.

## Supported file types

| Extension          | Loader                              |
| ------------------ | ----------------------------------- |
| `.pdf`             | `PyPDFLoader`                       |
| `.txt`             | UTF-8 text                          |
| `.md` / `.markdown`| Markdown (treated as text)          |
| `.html` / `.htm`   | BeautifulSoup → plain text          |
| `.docx`            | `Docx2txtLoader`                    |
| `.csv`             | `CSVLoader` (one chunk per row)     |
| `.json` / `.jsonl` | Raw text (write a custom loader for structured access) |

> Add a new format by registering it in `chatbot/rag/loaders.py`.

## Recommended folder structure (per client)

```
data/
├── README.md
└── <client-id>/
    ├── catalog/         # product PDFs, brochures
    ├── policies/        # returns, shipping, warranty, privacy
    ├── about/           # opening hours, address, contact, team
    └── faq/             # frequently asked questions
```

The chatbot walks the `data_paths` listed in your `config/clients/<id>.yaml`
recursively, so the depth and naming inside each folder is up to you.

## How re-ingestion works

The vector store under `.vectorstore/` keeps a content hash of the data
folder. The next time the app starts, if any file changed, was added, or
was removed, the store rebuilds itself automatically. You can also force a
rebuild by:

```bash
rm -rf .vectorstore
python -m scripts.ingest
```

## Adding a website instead of files

If a client has no documents, scrape their website:

```bash
python -m scripts.scrape --url https://example.com/
python -m scripts.ingest
```

The scraper writes cleaned `.txt` files into `data/scraped/`, which then
flow through the regular ingestion pipeline.
