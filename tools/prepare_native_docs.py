#!/usr/bin/env python3
"""Validate Luna's document sources and stage Chinese help without altering English."""
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()

def navigation(text):
    lines = text.splitlines()
    return [lines[i + 1].lstrip()[0].lower() for i, line in enumerate(lines[:-1])
            if line.startswith('-' * 72) and lines[i + 1]
            and re.match(r'[A-Z0-9]', lines[i + 1])]

def wrap(text):
    result = []
    for line in text.splitlines():
        if not re.search(r'[\u3400-\u9fff]', line):
            result.append(line)
            continue
        indent = re.match(r' *', line).group()
        pending = indent
        width = len(indent)
        for token in re.findall(r'[A-Za-z0-9_./:+%<>~-]+|.', line[len(indent):]):
            columns = sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1 for c in token)
            if width + columns > 74 and pending.strip():
                # Reserve a few columns so closing punctuation stays with the
                # preceding word, rather than beginning the next Chinese line.
                if token in '，。！？；：、）】》」』”’!?;:)]}':
                    pending += token
                    width += columns
                    continue
                carry = ''
                while pending and pending[-1] in '（【《「『“‘':
                    carry = pending[-1] + carry
                    pending = pending[:-1]
                result.append(pending.rstrip())
                pending = indent + carry
                width = len(indent) + sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1 for c in carry)
            pending += token
            width += columns
        result.append(pending.rstrip())
    return '\n'.join(result) + '\n'

def prepare_docs():
    manifest = json.loads((ROOT / 'localization/luna-documents.json').read_text())
    target = ROOT / 'native/crawl-ref/docs/zh'
    target.mkdir(exist_ok=True)
    report = {}
    for document in manifest['documents']:
        source = ROOT / document['source']
        source_text = source.read_text()
        assert sha(source_text) == document['source_sha256'], f'Stale document review: {source}'
        pieces = []
        for segment in document['translations']:
            text = (ROOT / segment['path']).read_text()
            assert sha(text) == segment['sha256'], f'Changed reviewed document: {segment["path"]}'
            pieces.append(text)
        translated = wrap(''.join(pieces))
        assert navigation(source_text) == navigation(translated), f'Help navigation changed: {source}'
        assert '\ufffd' not in translated
        (target / source.name).write_text(translated)
        report[source.name] = {'source_sha256': sha(source_text), 'translated_sha256': sha(translated),
                               'characters': len(translated), 'navigation_keys': navigation(translated)}
    (ROOT / 'localization/document-coverage.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('Prepared Luna help documents:', len(report))

if __name__ == '__main__':
    prepare_docs()
