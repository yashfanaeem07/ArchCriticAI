# Manual Testing Checklist — AI Studio Critic

Run the app, then work top to bottom. There are **two passes**: a no-cost **Demo
pass** (no API key) and an optional **Live pass** (real model, needs a key).

```powershell
streamlit run app.py
```
Open the URL it prints (default http://localhost:8501).

---

## Pass A — Demo mode (no API key, no cost) — do this first

### 1. What image should I upload?
**None.** Demo mode ignores the image and loads a built-in sample critique of a
fictional *Riverside Community Library*. Leave the uploader empty.

### 2. What title should I enter?
`Riverside Community Library`

### 3. What keywords should I enter?
`permeable ground floor, timber structure, framing the river`

### 4. Which tabs should I test?
1. **Sidebar** → tick **🎭 Demo mode**.
2. **🔍 Analyse** → enter title + keywords → click **Critique my project 🎨**.
3. **✨ Generate** → click each of the four buttons:
   - 🎤 Presentation
   - ⚖️ Jury defence
   - 📜 Design narrative
   - 🏷️ Keywords
4. **📚 Knowledge** → confirm it shows the Phase 3 "coming soon" notice (no crash).

### 5. What successful output looks like
- **Analyse:** an "Overall score" metric (~**6.8/10** in demo), a bar chart of
  six categories, a "Concept interpretation" paragraph, six expandable category
  cards (Strengths / Weaknesses / Suggestions), and overall strengths/priorities.
  A yellow banner notes it's sample output.
- **Presentation:** a one-line **design thesis**, an estimated spoken length
  (~2.2 min), then sections (Site → Parti → Programme → Spatial sequence →
  Materiality → Closing), each with a 🎙️ delivery note.
- **Jury defence:** expandable Q&A cards, each tagged with a topic, a 🛡️ defence,
  and a ↪️ likely follow-up.
- **Design narrative:** an evocative headline, an italic concept statement, a
  multi-paragraph narrative, and a 📐 list of key design moves.
- **Keywords:** a **Parti** phrase, then keyword "chips" grouped into 🧠 Conceptual
  / 🧭 Spatial / 🧱 Tectonic / ✨ Experiential.

### 6. Errors to watch for
- Any red exception traceback on the page (there should be **none**).
- A generate tab that stays blank after clicking a button (nothing renders).
- The 🏷️ Keywords result failing to appear, or your typed keywords text
  disappearing after extraction *(this was a fixed bug — verify it stays fixed)*.
- "Run a critique first" persisting in the Generate tab **after** you've run one.

---

## Pass B — Live mode (real model) — optional, costs API tokens

### 1. What image should I upload?
A real architectural drawing of a single project: a **plan, section, massing
model photo, sketch, or render**. PNG/JPG/WEBP/GIF. One clear board works best;
avoid tiny or text-only images. (No sample image ships with the repo — use any
studio drawing you have.)

### 2. Title
The real project's name, e.g. `Harborfront Arts Pavilion`.

### 3. Keywords
The project's actual design intent, e.g. `folded roof plane, public courtyard,
exposed CLT, north light`.

### 4. Which tabs
Same four as Pass A, but **untick Demo mode** and provide an Anthropic API key
(sidebar field, or an `ANTHROPIC_API_KEY` in a local `.env`).

### 5. Successful output
Same shapes as Pass A, but the content should clearly reference **your** image —
the concept summary and category observations should describe what's actually in
the drawing, and the keywords should match your project's vocabulary.

### 6. Errors to watch for
- **No API key / Demo off:** a clear "add your key or use Demo mode" message
  (not a crash).
- **No image uploaded:** a clear "please upload an image" message.
- **Bad/expired key or network failure:** surfaced as a red "Something went
  wrong: …" message — not a silent hang.
- A generator failing while the critique succeeded (each generator is independent;
  one failing should show its own error, not break the others).
