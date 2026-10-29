import test from 'node:test';
import assert from 'node:assert/strict';
import worker from '../telegram-webhook/worker.mjs';
import {proofOf} from '../telegram-webhook/setup.mjs';
const root='https://uniqlo-telegram-webhook.uniqlo-alert-werti4.workers.dev';
const env={WEBHOOK_SECRET:'s'.repeat(64),TELEGRAM_BOT_TOKEN:'synthetic-token',TELEGRAM_CHAT_ID:'123',BOT_USERNAME:'mybot',GITHUB_DISPATCH_TOKEN:'synthetic-pat',GITHUB_REPOSITORY:'werti4/uniqlo-alert',GITHUB_BRANCH:'main',SETUP_ENABLED:'true',SETUP_EXPIRES_AT:'2099-01-01T00:00:00Z'};
const call=async(body={},extra={})=>worker.fetch(new Request(root+'/configure',{method:'POST',headers:{'X-Bridge-Secret':env.WEBHOOK_SECRET},body:JSON.stringify(body)}),{...env,...extra});
const proof=()=>proofOf(env.WEBHOOK_SECRET,env.TELEGRAM_BOT_TOKEN,env.TELEGRAM_CHAT_ID);
function mockNetwork({running=false,badBot=false,otherWebhook=false}={}){
 const calls=[];
 const fetch=async(url,init)=>{
  const body=init.body?JSON.parse(init.body):null;calls.push({url,body});
  assert.ok(!url.includes('/sendMessage')&&!url.includes('/getUpdates')&&!url.includes('/workflows/scan.yml/dispatches'));
  if(url.endsWith('/getMe'))return Response.json({ok:true,result:{is_bot:true,username:badBot?'other':'mybot'}});
  if(url.endsWith('/getChat'))return Response.json({ok:true,result:{id:123,type:'private'}});
  if(url.includes('/runs?'))return Response.json({workflow_runs:running?[{status:'in_progress'}]:[]});
  if(url.endsWith('/dispatches'))return new Response(null,{status:204});
  if(url.startsWith('https://api.github.com'))return Response.json({state:'active'});
  if(url.endsWith('/setWebhook'))return Response.json({ok:true,result:true});
  if(url.endsWith('/getWebhookInfo'))return Response.json({ok:true,result:{url:otherWebhook?'https://other.example/telegram':root+'/telegram',allowed_updates:['message'],max_connections:1,pending_update_count:0}});
  throw Error('unexpected request');
 };return {fetch,calls};
}
test('administrative setup is closed by default, expires and authenticates before I/O',async()=>{
 assert.equal((await call({}, {SETUP_ENABLED:'false'})).status,404);
 assert.equal((await call({}, {SETUP_EXPIRES_AT:'2020-01-01'})).status,404);
 assert.equal((await call({}, {SETUP_EXPIRES_AT:''})).status,404);
 const r=await worker.fetch(new Request(root+'/configure',{method:'POST',body:'{}'}),env);assert.equal(r.status,403);
});
test('GitHub token/chat proof must match Worker before any upstream request',async()=>{
 const original=globalThis.fetch;globalThis.fetch=async()=>{throw Error('must not call');};
 try{const r=await call({root,enabled:true,proof:'0'.repeat(64)});assert.equal(r.status,409);assert.equal((await r.json()).error,'github_cloudflare_values_differ');}finally{globalThis.fetch=original;}
});
test('setup checks access, dispatches only read-only verification and preserves pending updates',async()=>{
 const original=globalThis.fetch;const mock=mockNetwork();globalThis.fetch=mock.fetch;
 try{
  const r=await call({root,enabled:true,proof:await proof()});assert.equal(r.status,200);assert.equal((await r.json()).webhook_confirmed,true);
  assert.deepEqual(mock.calls.find(x=>x.url.endsWith('/setWebhook')).body,{url:root+'/telegram',secret_token:env.WEBHOOK_SECRET,allowed_updates:['message'],max_connections:1,drop_pending_updates:false});
  const dispatch=mock.calls.find(x=>x.url.endsWith('/dispatches'));assert.ok(dispatch.url.includes('/configure-cloudflare.yml/'));assert.deepEqual(dispatch.body,{ref:'main',inputs:{verify_only:true}});
 }finally{globalThis.fetch=original;}
});
test('old getUpdates reader, wrong bot and other webhook prevent activation',async()=>{
 const original=globalThis.fetch;
 try{for(const options of [{running:true},{badBot:true},{otherWebhook:true}]){const mock=mockNetwork(options);globalThis.fetch=mock.fetch;const r=await call({root,enabled:true,proof:await proof()});assert.equal(r.status,409);assert.ok(!mock.calls.some(x=>x.url.endsWith('/setWebhook')));}}finally{globalThis.fetch=original;}
});
test('upstream credential errors are never returned raw',async()=>{
 const original=globalThis.fetch;globalThis.fetch=async()=>{throw Error('synthetic-token synthetic-pat');};
 try{const r=await call({root,enabled:true,proof:await proof()});const text=await r.text();assert.equal(r.status,409);assert.ok(!text.includes('synthetic'));}finally{globalThis.fetch=original;}
});
