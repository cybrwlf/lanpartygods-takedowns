"""Posts one public issue per photo removed through the LanPartyGoDS removal form. Runs on a schedule in GitHub Actions with the repo's own token.
Reads the public list at /api/records (group, album, file, reason, date; never the picture, never the requester)."""
import json, os, subprocess, urllib.request

REPO = os.environ['REPO']
BASE = 'https://lpg-groups.cybrwlf.workers.dev'
req = urllib.request.Request(BASE + '/api/records', headers={'User-Agent': 'Mozilla/5.0 (lpg record sync)'})
records = json.load(urllib.request.urlopen(req, timeout=60))['records']


def run(*a):
    return subprocess.run(a, capture_output=True, text=True)


made = 0
for r in records:
    # one issue per removal EVENT: a photo removed, restored and removed again gets a new record, so match on the removal time too
    found = run('gh', 'issue', 'list', '--repo', REPO, '--state', 'all', '--search', '"%s" in:body' % r['id'], '--json', 'number,body', '--limit', '50')
    if any(r['t'] in (x.get('body') or '') for x in json.loads(found.stdout or '[]')):
        continue
    title = 'Removed: %s / %s / %s' % (r['group'], r['event'], r['f'])
    body = '\n'.join([
        '**Removed from the site on request.** No image is shown here on purpose.', '',
        '| | |', '|---|---|',
        '| Group | %s |' % r['group'], '| Album | %s, %s |' % (r['event'], r['d']), '| Section | %s |' % r['s'],
        '| File | `%s` |' % r['f'], '| Photo id | `%s` |' % r['id'], '| Published copy (sha256) | `%s` |' % r['sha'],
        '| Reason | %s |' % r['reason_text'], '| Removed | %s |' % r['t'], '| Status | Removed from the site. |', '',
        'Photo key: `%s`' % r['key']])
    out = run('gh', 'issue', 'create', '--repo', REPO, '--title', title, '--body', body, '--label', 'removal,group:%s,reason:%s' % (r['g'], r['reason']))
    if out.returncode:   # a label that does not exist yet must not lose the record
        out = run('gh', 'issue', 'create', '--repo', REPO, '--title', title, '--body', body)
    print(r['key'], '->', (out.stdout or out.stderr).strip())
    made += 1
print('records:', len(records), '| new issues:', made)
