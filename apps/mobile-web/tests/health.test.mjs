import test from 'node:test'
import assert from 'node:assert/strict'
import {checkHealth} from '../src/health.ts'

test('reads server readiness', async () => {
  assert.equal(await checkHealth(async path => {
    assert.equal(path, '/api/v1/health')
    return Response.json({status:'ok'})
  }), true)
})
test('disconnected or unhealthy server', async () => {
  assert.equal(await checkHealth(async () => { throw new Error('offline') }), false)
  assert.equal(await checkHealth(async () => new Response(null, {status:503})), false)
})
