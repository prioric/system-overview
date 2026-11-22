# The checks

`scripts/check_overview.py {company}` runs every test below and prints one line per fault. It exits 2 on any fault and 0 when the files are clean. Without Python, go through the list by hand and write the result to `{company}/checks.md`. The page itself needs Python to be drawn.

## The data file

1. `overview.json` is valid JSON.
2. `company`, `title`, `evidence_date`, `sources` and `status` are present. The title is one sentence of at most 160 characters.
3. `status` starts with `draft` or `checked by`. With `--final`, a status that starts with `draft` is a fault.
4. `stats` holds zero to two figures, each with a `figure` of at most 16 characters and a `label` of at most 50.
5. `cards` holds the eleven keys `market`, `customers`, `competitors`, `assets`, `capabilities`, `limits`, `invests`, `cuts`, `hires`, `story`, `signal`, and no other.
6. Every card has a `headline` of one sentence and at most 110 characters, a `body` of one to three sentences and at most 300 characters, and a `source` of at most 80 characters.
7. `pulls` holds two or three. Each has a `title` of at most 40 characters that no other pull repeats, a `sentence`, a `who_pays`, and `from` and `to` naming two different cards.
8. Each pull's `from_fact` sits, letter for letter, in an Evidence line with a dated source in the chapters of its `from` card; the same for `to_fact` and the `to` card. Bold marks and curly quotes are ignored.
9. `decision` has `who`, `what`, `by_when` and `if_nobody`, and two or three options, each with `option`, `cost` and `who_pays`, within the limits in [overview_data.md](overview_data.md).
10. Every number in a card sits in an Evidence line with a dated source in that card's chapters. Every number in a pull sits in the chapters of its two cards. Every number in the decision and the stats sits in any chapter. A year alone is exempt. `5,323` and `5323` count as one number.
11. No text scores the company ("out of 10", "world-class", "strengths", "weaknesses") or gives advice ("should", "recommend").

## The page

12. The page carries a record of the files it was drawn from. The record matches the current `overview.json` and every chapter. When it does not, the page is older than its inputs and must be drawn again.
13. The page loads nothing: no `http:` or `https:` address, no address that starts with `//`, no `src` or `srcset`, no link other than one to a place on the page, no CSS `url()` or `@import`, no tag that loads a file, and no request in its script.
14. No line crosses a card or the middle box. No two lines share a stretch. Every number mark sits at least 12 pixels from every other line. Every line stays inside the picture. The lines cross each other at most three times.

## The last look, in a browser

15. Open the page. `<body>` says `data-fit="ok"`. No box has a red outline, and no red line sits at the top of the page.

The checks prove form, numbers, quotes and the drawing. They cannot tell whether a pull is real, whether a cause is true or whether the right party pays. The second read and the person do that.
