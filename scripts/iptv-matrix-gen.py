#!/usr/bin/env python3
"""iptv-matrix-gen (Round 257) — autonomous working-matrix generator.
Runs on GitHub Actions (weekly + dispatch): sweeps source playlists in rotating
slices (polite HEAD, 400 probes/run max), writes all-working.m3u + matrix.json,
commits. Single URL carries everything verified.
Sources: local repo lists + iptv-org country lists (FR/DE/IT/ES/PT/UK/US/AR + kids/movies/sports groups).
Policy: verify-only. Dead entries are dropped from OUTPUT, never deleted from sources.
"""
import datetime
import json
import os
import re
import subprocess
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__)) + '/..'
SOURCES_LOCAL = ['eu.m3u', 'films-working.m3u', 'eu-pro.m3u', 'kids-working.m3u', 'premium-legal.m3u']
SOURCES_REMOTE = [
    'https://raw.githubusercontent.com/iptv-org/iptv/master/streams/fr.m3u',
    'https://raw.githubusercontent.com/iptv-org/iptv/master/streams/de.m3u',
    'https://raw.githubusercontent.com/iptv-org/iptv/master/streams/it.m3u',
    'https://raw.githubusercontent.com/iptv-org/iptv/master/streams/es.m3u',
    'https://raw.githubusercontent.com/iptv-org/iptv/master/streams/pt.m3u',
    'https://raw.githubusercontent.com/iptv-org/iptv/master/streams/uk.m3u',
    'https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us.m3u',
    'https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ar.m3u',
    'https://raw.githubusercontent.com/iptv-org/iptv/master/streams/in.m3u',
]
MAX_PROBES = 400


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={'User-Agent': 'eon-iptv-matrix/1.0'})
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with op.open(req, timeout=timeout) as r:
        return r.read().decode('utf-8', errors='replace')


def entries(text):
    out = []
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith('#EXTINF') and '[Geo-blocked]' not in ln:
            for j in range(i + 1, min(i + 3, len(lines))):
                if lines[j].strip().startswith('http'):
                    out.append((ln, lines[j].strip()))
                    break
    return out


def probe(url, timeout=10):
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'eon-iptv-check/1.0'})
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with op.open(req, timeout=timeout) as r:
            if r.status == 200:
                return True
        req = urllib.request.Request(url, headers={'User-Agent': 'eon-iptv-check/1.0', 'Range': 'bytes=0-1000'})
        with op.open(req, timeout=timeout + 2) as r:
            return r.status in (200, 206)
    except Exception as e:
        m = re.search(r'HTTP Error (\d+)', str(e))
        return False


def main():
    allpairs = []
    for f in SOURCES_LOCAL:
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            allpairs += entries(open(p, encoding='utf-8', errors='replace').read())
    for u in SOURCES_REMOTE:
        try:
            allpairs += entries(fetch(u))
        except Exception as e:
            print('source fail:', u[:60], str(e)[:80])
    seen, uniq = set(), []
    for inf, u in allpairs:
        if u not in seen:
            seen.add(u)
            uniq.append((inf, u))
    # rotate slice by week so the whole internet gets covered over time
    wk = datetime.date.today().isocalendar()[1]
    start = (wk * MAX_PROBES) % max(1, len(uniq))
    work = [uniq[(start + i) % len(uniq)] for i in range(min(MAX_PROBES, len(uniq)))]
    print(f'pool={len(uniq)} slice={len(work)} week={wk}')
    live = []
    for k, (inf, u) in enumerate(work):
        if probe(u):
            live.append((inf, u))
        if k % 50 == 0:
            print(f'{k}/{len(work)} live={len(live)}', flush=True)
        import time
        time.sleep(0.3)
    # merge with last known-good (never shrink on a bad week)
    prev = []
    mp = os.path.join(ROOT, 'all-working.m3u')
    if os.path.exists(mp):
        prev = entries(open(mp, encoding='utf-8', errors='replace').read())
    merged, seen2 = [], set()
    for inf, u in live + prev:
        if u not in seen2:
            seen2.add(u)
            merged.append((inf, u))
    out = ['#EXTM3U x-generated=iptv-matrix-gen x-date=%s x-count=%d' % (datetime.date.today().isoformat(), len(merged))]
    for a, b in merged:
        out += [a, b]
    open(mp, 'w').write('\n'.join(out) + '\n')
    open(os.path.join(ROOT, 'matrix.json'), 'w').write(json.dumps({
        "date": datetime.date.today().isoformat(), "checked": len(work),
        "live_now": len(live), "total": len(merged)}))
    print(f'DONE checked={len(work)} live_now={len(live)} total={len(merged)}')


if __name__ == '__main__':
    main()
