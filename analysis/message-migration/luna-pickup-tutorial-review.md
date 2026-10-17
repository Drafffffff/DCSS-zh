# Pickup tutorial review

Reviewed the complete `HINT_SEEN_FIRST_OBJECT` tutorial in `dat/descript/hints.txt`.

- The catalog keeps `$1` for the item glyph and preserves the `<console>`, `<input>`, `<localtiles>`, `<tiles>`, and `<w>` tags, plus all `$cmd[...]` keys.
- Catalog text matches the `unwrap_desc` output shape: soft line breaks become spaces, paragraph breaks remain explicit `\n\n`, adjacent markup tags have no inserted whitespace, and the final newline is retained.
- The literal symbol example `%?!"=()[` is preserved exactly; the shortcut audit ignores square brackets inside markup tags.
- `HINT_PICKED_UP_ITEM` is not a key in the current hints database; the actual first-object tutorial key is `HINT_SEEN_FIRST_OBJECT`.

The remaining item acquisition hints have separate database keys and runtime Lua branches; they are not included in this first-object template.
