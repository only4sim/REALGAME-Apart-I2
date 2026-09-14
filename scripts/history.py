"""Read exact historical file bytes without restoring obsolete working trees."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def read_historical(path, root=ROOT):
    """Resolve an indexed logical path, including old ZIP!/member names."""
    index_bytes = (root / 'archive/INDEX.json').read_bytes()
    index = json.loads(index_bytes)
    if path not in index['files']:
        raise ValueError('Historical path is not indexed: ' + path)
    record = index['files'][path]
    with zipfile.ZipFile(root / 'archive/history.zip') as archive:
        if archive.read('INDEX.json') != index_bytes:
            raise ValueError('Historical index differs from its archived copy')
        data = archive.read('objects/' + record['sha256'])
    if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
        raise ValueError('Historical content hash mismatch: ' + path)
    return data


def verify_history(root=ROOT):
    index_bytes = (root / 'archive/INDEX.json').read_bytes()
    index = json.loads(index_bytes)
    checked = set()
    with zipfile.ZipFile(root / 'archive/history.zip') as archive:
        if archive.testzip() is not None or archive.read('INDEX.json') != index_bytes:
            raise ValueError('Historical archive CRC or index mismatch')
        for path, record in index['files'].items():
            digest = record['sha256']
            if digest in checked:
                continue
            data = archive.read('objects/' + digest)
            if hashlib.sha256(data).hexdigest() != digest or len(data) != record['bytes']:
                raise ValueError('Historical content mismatch: ' + path)
            checked.add(digest)
        if set(archive.namelist()) != {'INDEX.json'} | {'objects/' + digest for digest in checked}:
            raise ValueError('Unexpected historical archive members')
    return {'logical_paths': len(index['files']), 'unique_objects_verified': len(checked),
            'baseline_commit': index['baseline_commit']}
