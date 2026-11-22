# The page

The script draws this. Read it to know what the page should look like, and to fix a fault in the right place: text in `overview.json`, never on the page.

## The picture

A fixed picture of 1760 by 1200 pixels, scaled to the width of the window. The buttons at the top right zoom in, zoom out and fit. Ctrl with the mouse wheel zooms, and dragging moves the zoomed picture.

```
+-------------+-------------------------------------------+-------------+
| Around it   | What it owns and what binds it            | What it says|
|             |  Assets      Capabilities      Limits     |             |
|  Market     +-------------------------------------------+   Story     |
|             |   lane 1 ─────────────────────────────    |             |
|  Customers  |   lane 2   +-------------------------+    |             |
|             |   lane 3   |      THE DECISION       |    +-------------+
|             |            +-------------------------+    |   Signal    |
|  Competitors+-------------------------------------------+             |
|             |  Invests      Cuts       Hires            |             |
|             | Where its money goes                      |             |
+-------------+-------------------------------------------+-------------+
```

- Each group sits on its own light color, with its name in a white label.
- A card shows its name in the group's color, the headline in bold, the body, and the source in gray at the foot.
- The middle box shows "The decision", the `what` sentence, who decides and by when, each option with who pays, and the numbered pull titles.

## The lines

- One line per pull, in the accent color, with its number in a round mark.
- A line leaves its card on the side that faces the middle: the right side of a left card, the bottom of a top card, the top of a bottom card, the left side of a right card.
- A line from a left or right card runs first along its own lane in the gap between the column and the rows. Every line then joins its own lane of the ring around the middle box. Pull 1, 2 and 3 each get a lane, 16 pixels apart.
- The script tries every order of lanes and both ways round the ring. It keeps the drawing with the fewest crossings, then the shortest lines.
- The number sits on the longest stretch of the line that is at least 14 pixels from any other line.
- Two lines that touch the same card leave it at two points, 22 pixels apart.

A line can never cross a card or the middle box, because the lanes run only through the gaps. The check proves this from the drawing, and the page proves it again in the browser.

## Under the picture

Plain text that reads on a phone: each pull in full with `Who pays:`, the decision with each option's cost and who pays it, what happens if nobody decides, the sources, the date of the evidence, the status and the draft note.

## The fit report

After the page loads, a short script measures every card and the middle box. A box whose text runs over gets smaller type, in two steps. A box that still runs over gets a red outline, and a red line at the top of the page names it. The script also walks along every line and tests each point against every card and the middle box. The result sits on `<body>` as `data-fit="ok"` or `data-fit="fault"`, with the list in `data-fit-report`.

## The type

The page uses the computer's own sans-serif font: Segoe UI on Windows, San Francisco on a Mac, Roboto or another sans-serif elsewhere. Text widths differ a little from one font to another, which is why the page measures itself.

## When text does not fit

The box does not grow. Cut the text in `overview.json` to the shortest true wording, and keep the figure. A headline that wraps to a fourth line is too long.
