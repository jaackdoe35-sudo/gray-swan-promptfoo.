# Scaffold Logs reading-view parser

## Status and scope

This parser consumes **text copied from the visible Scaffold Logs reading view**. It does not parse a native/exported Gray Swan Scaffold Logs JSON format; no such export or schema has been supplied or verified.

It currently recognizes only structures demonstrated in the supplied excerpts:

- scoreboard rows with a challenge identifier/name followed by an `INDIRECT` score;
- a visible `Used N tools` count;
- dotted tool labels such as `shopify.get-order-by-id`;
- JSON input before an `OUTPUT` marker and JSON output after it;
- visible text following `Scaffold Logs >` as a final-summary text block.

## Use

```bash
python scripts/parse_scaffold_reading_view.py copied-reading-view.txt -o parsed-reading-view.json
```

Copy the relevant reading-view text into a UTF-8 text file. Include the tool heading, input object, `OUTPUT` marker, and output object together where possible.

## Important limitations

- The parser does not infer missing fields, repair malformed/OCR-damaged JSON, or claim to recover hidden events.
- A copied excerpt may omit event boundaries, timestamps, run IDs, or intermediate calls.
- A tool label without expanded input/output is not treated as a fully captured call.
- Final-response narrative is retained as text and is not treated as proof of tool execution or side effects.
- `native_scaffold_json_schema_verified` intentionally remains `false`.
- Challenge score strings are recorded as displayed; the parser does not interpret them as proof of why a run received that score.

The fixture contains synthetic/redacted identifiers. Do not commit unredacted customer records, addresses, emails, phone numbers, tokens, or session data.
