# Transform message review

Reviewed transform entry announcements, `_transform_log` source literals, and the remaining complete dynamic transform messages.

- Generic form announcements use `transform.enter.<enum>` and preserve each form's complete canonical sentence. Draconian dragon entry has a separate `transform.enter.dragon_species` template.
- Fixed messages routed through `_transform_log` use `source_context: transform.log`.
- Dynamic item, monster, eye, and body-part messages have complete templates and typed named arguments. The vampire Chinese templates retain the structural `{reflexive}` slot; the producer supplies an empty localized reflexive so no English pronoun leaks into the sentence.
- Eel-hand and spore messages use `transform.bodypart.*` semantic atoms. Tag-34 porcupine and shadow forms are included.
- The existing shared lower-maximum-HP confirmation already has an active shared ID and remains outside this catalog.

No C++ source was changed in this review.
