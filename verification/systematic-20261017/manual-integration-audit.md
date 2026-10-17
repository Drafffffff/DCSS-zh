# Manual parts A–C integration audit

Reviewed source ranges:

- Part A: `native/crawl-ref/docs/crawl_manual.txt`, lines 1–1173.
- Part B: `native/crawl-ref/docs/crawl_manual.txt`, lines 1174–2200.
- Part C: `native/crawl-ref/docs/crawl_manual.txt`, lines 2201–3251.

## Boundaries and coverage

- Part A ends with the complete targeting instructions corresponding to source lines 1168–1172; its trailing newline represents source line 1173. Part B begins with the intact separator and J heading from source lines 1174–1176.
- Part B ends with the translated “Warrior-mage backgrounds” heading and its underline, corresponding to source lines 2199–2200. Part C begins with the paragraph continuing that heading at source line 2202; source line 2201 is only a blank separator. No prose is split, omitted, or duplicated at this boundary.
- Part C ends with the complete Sprint IX description corresponding to source lines 3247–3251.
- Chapter headings J–N and appendices 1–5 are present in the expected sequence across the files. The 72-hyphen section dividers that occur at the part boundaries are intact; appendix numbering is preserved.

## Findings

- **Fixed in Part B:** `Kobolds (Ko)` now consistently uses “狗头人” at `localization/manual-zh-part-b.txt` around lines 264–267, distinct from `Gnolls (Gn)` (“豺狼人”) at lines 207–212.
- Compared all Part B species names against the installed Chinese species descriptions in `pristine-zh/descript/zh/species.txt`; aligned established names including 甲马、蛙人、地底精灵、魔人、灯神、狗头人、鱼人、纳迦、章鱼、鬼、树精、藤蔓人 and 齿轮地精. Other translated species names already matched the available project terminology.
- The mutation section preserves the distinction between character levels and mutation levels: multi-level mutations count one mutation per level. It also retains temporary mutations, contamination causes, colour cues, and the Demonspawn/species intrinsic exceptions.
- Technical command names, key labels, option names, paths, and manual filenames in Part B remain identifiable and intact, including `Ctrl-O`, `?/G`, `macro.txt`, `macros_guide.txt`, `options_guide.txt`, `~/.crawlrc`, `init.txt`, `dat/clua/`, and `travel_delay = -1`.

No boundary omission, duplication, or other structural coverage issue was found. The translation and audit are now updated; no further species-name collision was found.
