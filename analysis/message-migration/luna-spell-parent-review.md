# Luna spell detail parent messages review

Added two complete fixed-action parents for spell detail failures: one for casting and one for memorising. Each accepts only `{reason:text}`, preserving the two distinct user actions and avoiding a freely interpolated action word. The current `spell.player.cannot_memorise` ID remains untouched; callers can migrate to the new fixed-action IDs independently. Existing generic spell-uselessness parent IDs remain reusable.
