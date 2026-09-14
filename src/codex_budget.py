"""Persistent outer allowance shared across all directories for this pilot."""
from __future__ import annotations

import datetime
import fcntl
import json
from pathlib import Path
import time

from codex_subscription import AccessBlocked


class GlobalPilotBudget:
    def __init__(self, path, scope, limit=140, seconds=2700):
        if type(limit) is not int or not 0 < limit <= 140:
            raise AccessBlocked('Invalid invocation cap')
        if type(seconds) is not int or not 0 < seconds <= 2700:
            raise AccessBlocked('Invalid wallclock cap')
        self.path, self.scope, self.limit, self.seconds = Path(path), scope, limit, seconds
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = self.path.with_suffix('.lock').open('a')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock.close()
            raise AccessBlocked('Another process holds the global pilot allowance') from None
        self.started = None
        self.monotonic_deadline = None
        self.invocations = 0
        self.turn_submissions = 0
        self.keys = set()
        self.turn_keys = set()
        try:
            rows = [json.loads(line) for line in self.path.read_text().splitlines()] if self.path.exists() else []
            for row in rows:
                if row.get('scope') != scope:
                    raise AccessBlocked('Global allowance scope mismatch')
                if row['event'] == 'invocation_started':
                    key = (row['run_id'], row['index'])
                    if key in self.keys:
                        raise AccessBlocked('Duplicate global invocation record')
                    self.keys.add(key)
                    self.invocations += 1
                    self.started = row['unix_time'] if self.started is None else min(self.started, row['unix_time'])
                elif row['event'] == 'turn_submitted':
                    key = (row['run_id'], row['index'])
                    if key not in self.keys or key in self.turn_keys:
                        raise AccessBlocked('Invalid global turn record')
                    self.turn_keys.add(key)
                    self.turn_submissions += 1
                else:
                    raise AccessBlocked('Unknown global allowance record')
            if self.started is not None:
                remaining = max(0., min(self.seconds, self.seconds-(time.time()-self.started)))
                self.monotonic_deadline = time.monotonic()+remaining
        except Exception:
            self.close()
            raise

    def close(self):
        if not self.lock.closed:
            fcntl.flock(self.lock, fcntl.LOCK_UN)
            self.lock.close()

    def _append(self, event, runid, index):
        row = {'scope': self.scope, 'event': event, 'run_id': runid, 'index': index,
               'unix_time': time.time(),
               'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        with self.path.open('a') as stream:
            stream.write(json.dumps(row, allow_nan=False)+'\n')
            stream.flush()
            import os
            os.fsync(stream.fileno())
        return row

    def remaining_seconds(self):
        if self.started is None:
            return self.seconds
        wall_remaining = self.seconds-(time.time()-self.started)
        monotonic_remaining = self.monotonic_deadline-time.monotonic()
        return max(0., min(wall_remaining, monotonic_remaining))

    def reserve(self, runid, index):
        if (runid, index) in self.keys:
            raise AccessBlocked('No replacement or resume invocation is allowed')
        if self.invocations >= self.limit:
            raise AccessBlocked('Client invocation cap reached')
        if self.remaining_seconds() <= 0:
            raise AccessBlocked('Experimental time cap reached')
        row = self._append('invocation_started', runid, index)
        if self.started is None:
            self.monotonic_deadline = time.monotonic()+self.seconds
        self.started = row['unix_time'] if self.started is None else self.started
        self.keys.add((runid, index))
        self.invocations += 1
        return self.invocations

    def note_turn_submission(self, runid, index):
        key = (runid, index)
        if key not in self.keys or key in self.turn_keys:
            raise AccessBlocked('Turn must belong to one reserved invocation')
        if self.turn_submissions >= self.limit or self.remaining_seconds() <= 0:
            raise AccessBlocked('Turn or time cap reached')
        self._append('turn_submitted', runid, index)
        self.turn_keys.add(key)
        self.turn_submissions += 1
