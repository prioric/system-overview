---
name: prioric-system-overview
description: "Draws one wide HTML page that shows a company as one system: eleven cards of facts around the edge, two or three numbered lines between the facts that pull against each other, and the decision in front of the company in the middle, with each option and who pays for it. It reads the ten chapters the prioric-system-analysis skill writes. Use when the user asks for the system overview, the one-page overview, the overview page or the poster for {company}."
license: Apache-2.0
metadata:
  author: prioric
  version: "1.0"
---

# The system overview

## Where things are

- `{skill}` is this skill's own folder, the one this file sits in.
- The **working folder** is the folder the agent runs in. `setup.md`, when the system analysis made one, sits in it.
- `{company}/` is the company's folder inside the working folder. It holds `chapters/` from the system analysis. This skill adds `overview.json` and `system_overview.html` to it.

`{skill}/examples/alder-pipes/` is a finished company folder: the ten chapters, the data file and the page. Read it before the first run.

## What it makes

One HTML file, `{company}/system_overview.html`. It opens in any browser, offline. It uses the computer's own fonts and loads nothing from the web.

- **Eleven cards in four groups.** Around it: Market, Customers, Competitors. What it owns and what binds it: Assets, Capabilities, Limits. Where its money goes: Invests, Cuts, Hires. What it says: Story, Signal. Each card has a headline, one to three sentences of facts, and its source.
- **Two or three numbered lines.** Each joins two cards whose facts pull against each other. Under the picture, each pull is written out in full with who pays for it.
- **The decision in the middle.** Who decides, what, by when, and the options with who pays for each. Under the picture: what each option costs, and what happens if nobody decides.

The agent writes text only, into `overview.json`. The script draws the page. Every card has a fixed place, and the lines run in fixed lanes, so the page looks the same on every computer.

## What it needs

- The ten chapters in `{company}/chapters/`, made by the `prioric-system-analysis` skill. With no chapters, say that the system analysis runs first, and stop.
- Python 3. The scripts use its standard library only. Without Python the agent can write and check `overview.json` by hand with [references/checks.md](references/checks.md), but it cannot draw the page.

## The flow

### 1. Read

Read the ten chapters whole. Read `{company}/reading.md` when it exists: its pulls and its decision may have been checked by a person, so start from them. Read `setup.md` for the language and the second model. Read the example's `overview.json` beside its chapters.

### 2. Write the data file

Copy `{skill}/assets/overview_template.json` to `{company}/overview.json` and fill it in, part by part, as [references/overview_data.md](references/overview_data.md) says. Write every card from its own chapter. Take every figure from an Evidence line of that chapter, in the same form.

### 3. Check the data file

```
python {skill}/scripts/check_overview.py {company}
```

Fix every fault it names and run it again, as often as it takes. Stop only when the same fault is still there after two fixes; then give the person the open faults as a list.

### 4. Draw the page

```
python {skill}/scripts/build_overview.py {company}
```

It writes `{company}/system_overview.html` and prints any fault in the lines. Then run the check again; it now also checks the page.

### 5. Look at the page

When you can open a browser, open the page. The page measures itself after it loads. When text runs out of a box, the page first sets that box in smaller type. When the text still does not fit, the box gets a red outline and a red line at the top of the page names it. The same result sits in the page's `data-fit-report` attribute on `<body>`. Cut the named text in `overview.json`, draw again and look again. [references/page.md](references/page.md) describes the page.

### 6. Second read

When `setup.md` names a second model, send it `overview.json` and the ten chapters with this prompt, in one file, the way the system analysis sends its pack:

```
You read the data file of a one-page overview of {company}. After it come the ten chapters it was
written from. Return four lists. Quote the text you mean in each item. Return nothing else.

1. Text in a card, a pull or the decision that no chapter supports.
2. Pulls whose two facts do not pull against each other, or that stay true with a competitor's
   name swapped in.
3. Options or pulls that name no one who carries the cost, or the wrong one.
4. Any sentence that scores the company or gives advice.
```

Fix lists 1, 3 and 4. Give list 2 to the person beside the page. Run the check again after the fixes.

### 7. Hand over

Give the person the path of the page and one question: "Is this how the company works?" Beside it, in two lines: the decision and who makes it, and the weakest pull with the reason.

The page shows `Status: draft, not checked by a person`. When the person has checked it, they change `status` in `overview.json` to `checked by {name} on {date}`, or tell you to. Never change it on your own. Then draw the page again and run:

```
python {skill}/scripts/check_overview.py {company} --final
```

`--final` fails while the status still says draft.

## The rules

1. Every figure comes from a chapter Evidence line with a source and a date.
2. Name every actor: the firm, the buyer, the regulator, the body that decides.
3. Describe the company and score nothing. No grades, no advice.
4. Each pull and each option names who pays.
5. A person checks the page before it reaches anyone outside the run.

## What the check tests

`scripts/check_overview.py` tests the form and the length of every part; that each pull quotes one Evidence line from each of its two cards' chapters; that every number sits in a sourced Evidence line of the right chapter; that the page was drawn from the current data file and chapters; that the page loads nothing; and that no line crosses a card or the middle box. It exits 2 on a fault. It cannot tell whether a pull is real or whether the right party pays. The second read and the person do that. [references/checks.md](references/checks.md) lists every test.

## What this output is

A draft written by a language model from the chapters, which come from public sources. Figures can be wrong and causes can be invented. A person checks every figure and every claim against its source before the page reaches anyone. The authors of this skill take no responsibility for what is made with it.
