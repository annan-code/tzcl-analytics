#!/usr/bin/env python3
"""Take a monthly snapshot and add it to the archive.

WHY THIS EXISTS
---------------
Most of the "Usage detail" page comes from panels on claude.ai/analytics that
only ever report a rolling 30 days. The 1W/1M/3M/1Y control next to them
redraws the chart underneath — it does not change the headline figures or the
member tables. This was tested on 11 Aug 2026: clicking 1Y left every stat and
every table identical.

Per-user spend is worse. claude.ai/admin-settings/usage shows actual billed
amounts per person, but only for the current period, and it resets. Once the
period rolls over, that split is gone. There is no endpoint that returns it for
a past month.

So none of it can be back-filled. The only way to get history is to copy the
numbers down each month and keep them. That is all this script does.

RULES
-----
1. Never edit a capture that has already been written. If a figure was wrong on
   the day, it was still what the product reported on the day — leave it and
   note the correction separately.
2. Never invent a capture for a month that was missed. A gap in the table is
   honest; a made-up column is not.
3. Every value here must be read from the product, not calculated or estimated.

USAGE
-----
    python3 capture.py            # capture today into history/
    python3 capture.py --list     # show what is archived

Then rebuild:  python3 build_data.py && python3 assemble.py && python3 encrypt.py "<password>"
"""
import json
import os
import sys
from datetime import date

HISTORY_DIR = '/tmp/v5/history'
DATA = '/tmp/v5/data.json'


def capture(today=None):
    """Pull the snapshot-only metrics out of the current build and archive them."""
    today = today or date.today().isoformat()
    path = os.path.join(HISTORY_DIR, '%s.json' % today)
    if os.path.exists(path):
        sys.exit('refusing to overwrite an existing capture: %s\n'
                 'captures are immutable — delete it by hand if it is genuinely wrong' % path)

    d = json.load(open(DATA))
    s = d['snapshot']
    c = s['cost']
    cap = {
        'capturedAt': today,
        'window': s['window'],
        'dataAsOf': s['dataAsOf'],
        'actionsPerPrompt': s['agentic']['actionsPerPrompt'],
        'adoptionLevel': s['adoptionLevel'],
        'stickiness': {x['product']: x['dauMau'] for x in s['stickiness']},
        'outputs': s['outputs'],
        'timeSavedHours': s['timeSaved']['hours'],
        'skillsInUse': len(s.get('skills') or []),
        'connectorsInUse': len(s.get('connectors') or []),
        'projectsTotal': s['projectsMeta']['totalProjects'],
        'projectsShared': s['projectsMeta']['sharedProjects'],
        'projectsSingleConversation': s['projectsMeta']['singleConversation'],
        'meteredPeriod': c['metered']['period'],
        'meteredTotalGBP': c['metered']['total'],
        'meteredUsersBilled': c['metered']['usersBilled'],
        'meteredTop': c['metered']['top'],
        'seats': {k: d['meta'][k] for k in
                  ('seatsPurchased', 'seatsInUse', 'seatsUnused', 'members', 'invitesPending')},
    }
    os.makedirs(HISTORY_DIR, exist_ok=True)
    json.dump(cap, open(path, 'w'), indent=1)
    print('captured %s -> %s' % (today, path))
    return cap


def show():
    import glob
    files = sorted(glob.glob(os.path.join(HISTORY_DIR, '*.json')))
    if not files:
        print('no captures yet')
        return
    print('%-12s  %-34s  %8s  %6s  %s' % ('captured', 'window', 'metered', 'a/p', 'projects'))
    for f in files:
        c = json.load(open(f))
        print('%-12s  %-34s  %8.2f  %6.1f  %d (%d shared)' % (
            c['capturedAt'], c['window'][:34], c['meteredTotalGBP'],
            c['actionsPerPrompt'], c['projectsTotal'], c['projectsShared']))
    print('\n%d captures archived' % len(files))


if __name__ == '__main__':
    if '--list' in sys.argv:
        show()
    else:
        capture()
        show()
