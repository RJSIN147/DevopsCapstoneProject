import { test } from 'node:test';
import assert from 'node:assert/strict';
import { errorMessage } from './api.js';
import { greeting, initials, nextActions, toIsoFromLocal, todayLocal } from './format.js';

test('initials drops the Dr. prefix', () => {
  assert.equal(initials('Dr. Ananya Rao'), 'AR');
  assert.equal(initials('Kabir'), 'K');
});

test('booked appointments can be checked in or cancelled', () => {
  assert.deepEqual(nextActions('BOOKED').map((a) => a.status), ['CHECKED_IN', 'CANCELLED']);
  assert.deepEqual(nextActions('COMPLETED'), []);
});

test('local date + time is converted to an ISO string', () => {
  const iso = toIsoFromLocal('2026-10-20', '09:30');
  const back = new Date(iso);
  assert.equal(back.getHours(), 9);
  assert.equal(back.getMinutes(), 30);
  assert.equal(toIsoFromLocal('', '09:30'), null);
});

test('todayLocal pads month and day', () => {
  assert.equal(todayLocal(new Date(2026, 0, 5)), '2026-01-05');
});

test('greeting changes through the day', () => {
  assert.equal(greeting(8), 'Good morning');
  assert.equal(greeting(14), 'Good afternoon');
  assert.equal(greeting(20), 'Good evening');
});

test('errorMessage understands both FastAPI error shapes', () => {
  assert.equal(errorMessage({ detail: 'Doctor not found' }), 'Doctor not found');
  assert.equal(
    errorMessage({ detail: [{ loc: ['body', 'patient_name'], msg: 'too short' }] }),
    'patient_name: too short',
  );
  assert.equal(errorMessage(null), '');
});
