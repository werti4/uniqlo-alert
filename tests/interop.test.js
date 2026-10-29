import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {seal, unseal} from '../extension/core.js';

const cwd = fileURLToPath(new URL('..', import.meta.url));
const key = Buffer.from(Array.from({length: 32}, (_, i) => i)).toString('base64url');
const sample = {schema: 1, favorites: [{name: 'Pull écru à 29,90 €', enabled: true, targetCents: null}], products: {}, alerts: []};

function python(code, value) {
  const result = spawnSync('python3', ['-c', code], {
    cwd, input: JSON.stringify(value), encoding: 'utf8', timeout: 10000
  });
  assert.ifError(result.error);
  assert.equal(result.status, 0, result.stderr);
  return JSON.parse(result.stdout);
}

test('Chrome encrypted favorites are readable by the Python scanner', async () => {
  const box = await seal(sample, key);
  const decoded = python('import json,sys; from scanner.monitor import decrypt; x=json.load(sys.stdin); print(json.dumps(decrypt(x["box"],x["key"])))', {box, key});
  assert.deepEqual(decoded, sample);
});

test('Python encrypted state is readable by Chrome with the same key', async () => {
  const box = python('import json,sys; from scanner.monitor import encrypt; x=json.load(sys.stdin); print(json.dumps(encrypt(x["value"],x["key"])))', {value: sample, key});
  assert.deepEqual(await unseal(box, key), sample);
});
