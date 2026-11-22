# System overview

An AI agent skill that draws one wide page showing a company as one system. It reads the ten chapters that the [prioric-system-analysis](https://github.com/prioric/system-analysis) skill writes, and makes one HTML file:

1. **Eleven cards of facts around the edge**, in four groups: around it (market, customers, competitors), what it owns and what binds it (assets, capabilities, limits), where its money goes (invests, cuts, hires), and what it says (story, signal). Every card names its source.
2. **Two or three numbered lines** between the cards whose facts pull against each other. Each pull names who pays for it.
3. **The decision in the middle**: who decides, what, by when, and the options with who pays for each.

The skill describes the company and scores nothing. It gives no advice.

The page opens in any browser, offline. It uses the computer's own fonts and loads nothing from the web. The agent writes text only, into one data file; a Python script draws the page. Every card has a fixed place and the lines run in fixed lanes, so the page looks the same on every computer. The scripts use Python 3 and its standard library only.

The skill follows the open [Agent Skills](https://agentskills.io) format: a `SKILL.md` with the instructions, reference files the agent reads, and two Python scripts, one that draws and one that checks.

## Install

Install the system analysis skill first. Then copy this folder into the folder your agent reads skills from, under the name `prioric-system-overview`. For Claude Code:

```
git clone https://github.com/prioric/system-overview.git ~/.claude/skills/prioric-system-overview
```

For another agent, copy the folder where that agent finds its skills, or point the agent at `SKILL.md`.

## First run

Run the system analysis for a company first, so its ten chapters exist. Then ask your agent: "Draw the system overview for {company}."

The agent reads the chapters, writes `{company}/overview.json`, checks it, draws `{company}/system_overview.html`, and checks the page. When you have a second model set up in the system analysis, it reads the data file against the chapters before you do.

## What you get

```
{company}/
  chapters/              from the system analysis
  overview.json          the text of every card, pull and option
  system_overview.html   the page
```

## What is here

| Path | What is in it |
|---|---|
| `SKILL.md` | The instructions the agent follows. |
| `references/overview_data.md` | The data file, part by part, and which chapter feeds each part. |
| `references/page.md` | What the page looks like and how the lines are drawn. |
| `references/checks.md` | Every check, in words. |
| `assets/overview_template.json` | The empty data file. |
| `scripts/build_overview.py` | Draws the page from the data file. |
| `scripts/check_overview.py` | Checks the data file and the page. Exits 2 on a fault. |
| `examples/alder-pipes/` | Alder Pipes, an invented pipeline builder: the ten chapters, the data file and the page. |

To draw and check the example:

```
python scripts/build_overview.py examples/alder-pipes
python scripts/check_overview.py examples/alder-pipes
```

## What this output is

A draft written by a language model from the chapters, which come from public sources. Figures can be wrong and causes can be invented. A person checks every figure and every claim against its source before the page reaches anyone. The page's status line records that check. The authors take no responsibility for what is made with it.

## License

Apache License 2.0. See `LICENSE`.
