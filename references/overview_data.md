# The data file

`{company}/overview.json`, UTF-8. Write plain text with real characters (`€`, `–`, `é`); the script escapes them. Every fix goes into this file. A hand edit on the page is lost the next time it is drawn.

Start from `{skill}/assets/overview_template.json`. The example in `{skill}/examples/alder-pipes/overview.json` is a finished one.

## The top

| Key | What to write | Limit |
|---|---|---|
| `company` | The company's name. | |
| `language` | The page's language code, such as `en`, `de`, `nl`. | |
| `title` | One sentence that states what is going on at the company and who it matters to. A stranger understands it on one reading. | 160 characters |
| `status` | `draft, not checked by a person`. Only the person changes it, to `checked by {name} on {date}`. | |
| `evidence_date` | The date of the newest source the chapters read. | |
| `sources` | One sentence that names the main sources and their dates. | |
| `stats` | Zero to two figures for the top right: the one that sets the company's size and the one the decision turns on. Each is `{"figure": "€84m", "label": "revenue, 2025"}`. | figure 16, label 50 |
| `labels` | Optional. Words for a page in another language; see the end of this file. | |
| `accent` | Optional. The color of the lines and the middle box, as `#RRGGBB`. | |

## The cards

`cards` has eleven keys. Each card is:

```json
"limits": {
  "headline": "One sentence that says what the facts mean for this company.",
  "body": "One to three plain sentences with the facts.",
  "source": "The documents and their dates, in reader words"
}
```

| Key | Group on the page | Written from |
|---|---|---|
| `market` | Around it | `01_context.md`, and `10_sector_rules.md` for how the trade works |
| `customers` | Around it | `02_customers.md`. Where the user and the payer differ, name both. |
| `competitors` | Around it | `03_competition.md`. Name who wins the same customer, and the floor: the buyer who does nothing or keeps what they have. |
| `assets` | What it owns and what binds it | `04_assets.md` |
| `capabilities` | What it owns and what binds it | `05_capabilities.md` |
| `limits` | What it owns and what binds it | `06_limitations.md`, and `07_operating_model.md` for who must approve what |
| `invests` | Where its money goes | `08_capital_moves.md`, the Invests part |
| `cuts` | Where its money goes | `08_capital_moves.md`, the Cuts part. When the chapter records none, say so in one sentence. |
| `hires` | Where its money goes | `08_capital_moves.md`, the Hires part |
| `story` | What it says | `09_narrative.md`. The headline is the `Narrative:` line, word for word when it fits. |
| `signal` | What it says | `09_narrative.md`. The headline is the `Signal:` line, word for word when it fits. |

Limits per card: headline 110 characters, body 300, source 80. The headline is one sentence with at most one figure. The headline says only what the body and the chapter show: when the body names a CEO, the headline cannot claim four hires. A thin chapter makes a short card: one true sentence is better than three padded ones.

## The pulls

`pulls` has two or three. A pull is a problem the head of the company would recognize as theirs today. It rests on two sourced facts that sit on two different cards.

```json
{
  "title": "Five words or fewer",
  "sentence": "One sentence that states both facts and the pull between them.",
  "from": "limits",
  "to": "market",
  "from_fact": "a short quote copied from one Evidence line of the limits chapter",
  "to_fact": "a short quote copied from one Evidence line of the market chapter",
  "who_pays": "Who carries the cost of the pull, and by when."
}
```

- `from` and `to` are two card keys. The line on the page joins those two cards.
- `from_fact` and `to_fact` are copied letter for letter from one Evidence line each, in the chapters the table above gives for those cards. The check looks for them there.
- The order is the order of weight: pull 1 is the one the decision turns on.
- Swap a competitor's name into the sentence. When the sentence stays true, it is too general, and it goes.
- Mark an inference `[INFERRED]`.
- Limits: title 40 characters, sentence 300, who_pays 200, each quote 200.

When `reading.md` exists, take its pulls, cut to these limits, and add the two cards and the two quotes.

## The decision

```json
"decision": {
  "who": "The body that decides, named under ### Who decides in 07_operating_model.md",
  "what": "One sentence: what it decides.",
  "by_when": "A date and what happens then, or: unknown, no source gives a date",
  "options": [
    {"option": "The option, as a fact", "cost": "What it costs.", "who_pays": "Who carries that cost"}
  ],
  "if_nobody": "What happens if nobody decides, with the date when it shows."
}
```

- Write `what` as a choice between named paths: "Whether Mozilla keeps X or moves to Y."
- Two or three options. They must be real choices the body can make, each with its cost.
- A figure keeps its year. A cost about the future quotes last year's figure as last year's: "Royalties were $498 million in 2024", never "royalties stay at $498 million".
- `who_pays` names a body the chapters show carrying that cost. When the link is your own inference, mark it `[INFERRED]`.
- `if_nobody` never contradicts `by_when`. When one weak source gives a year, say so.
- When no source gives a date, write that. Never build the decision on a date that rests on one weak source.
- Limits: who 80 characters, what 160, by_when 60, option 80, cost 200, who_pays 40, if_nobody 300.

The middle box shows `what`, `who`, `by_when`, each option with its `who_pays`, and the pull titles. The text under the picture shows the costs and `if_nobody`.

## Figures

Every number sits in an Evidence line that ends on a source with a year. A number on a card must sit in that card's own chapters. A number in a pull must sit in the chapters of its two cards. A number in the decision or the stats may sit in any chapter. Write the number in the same form as the chapter: `€3.8 million` when the chapter says `€3.8 million`. A year alone needs no source.

## Another language

Write every text in the page's language, from the chapters. Never translate an English draft. Put the page's fixed words under `labels`. Any key you leave out stays in English.

```json
"labels": {
  "around": "Rund um das Unternehmen", "owns": "Was es besitzt und was es bindet",
  "money": "Wohin sein Geld fließt", "says": "Was es sagt",
  "market": "Markt", "customers": "Kunden", "competitors": "Wettbewerber",
  "assets": "Vermögen", "capabilities": "Fähigkeiten", "limits": "Grenzen",
  "invests": "Investiert", "cuts": "Kürzt", "hires": "Stellt ein",
  "story": "Geschichte", "signal": "Signal",
  "decision": "Die Entscheidung", "who": "Wer entscheidet", "by_when": "Bis wann",
  "options": "Optionen", "who_pays": "Wer zahlt", "cost": "Kosten",
  "if_nobody": "Wenn niemand entscheidet", "pulls": "Wo die Fakten gegeneinander ziehen",
  "sources": "Quellen", "evidence_date": "Stand der Quellen", "status": "Status",
  "zoom_hint": "Strg und Mausrad zoomen. Ziehen verschiebt.",
  "fit_fault": "Text passt nicht in:", "line_fault": "Eine Linie kreuzt eine Karte:",
  "draft_note": "Ein Entwurf eines Sprachmodells aus öffentlichen Quellen. Ein Mensch prüft jede Zahl und jede Aussage an ihrer Quelle, bevor diese Seite jemanden erreicht."
}
```
