# Architecture principles (Phase 3 knowledge base)

Drop design-theory documents here — `.pdf`, `.txt`, or `.md` files about
architectural principles, spatial design, composition, circulation theory,
precedent studies, etc.

`archcritic/knowledge/store.py` reads every supported file in this folder, splits
it into ~500-word chunks, embeds them with a local Sentence-Transformers model,
and stores the vectors in a ChromaDB collection. The critic then retrieves the
most relevant chunks for each project to ground its feedback in real
architectural thinking.

**After adding or editing files here, rebuild the index:**

```powershell
python rag_embed.py
```

Suggested starting sources:
- Notes on parti / concept-driven design
- Circulation and wayfinding principles
- Solid/void and transparency theory
- Massing, proportion, and composition fundamentals

> Keep documents focused and well-written — the quality of retrieval depends on
> the quality of what you put here.
