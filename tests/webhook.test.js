import test from 'node:test';
import assert from 'node:assert/strict';
import worker, {commandOf, TelegramInbox} from '../telegram-webhook/worker.mjs';
const env={WEBHOOK_SECRET:'synthetic',TELEGRAM_CHAT_ID:'123',BOT_USERNAME:'mybot',GITHUB_REPOSITORY:'owner/repo',GITHUB_BRANCH:'main',GITHUB_DISPATCH_TOKEN:'private',TELEGRAM_BOT_TOKEN:'private'};
const update=(id=1,chat=123,text='/scan')=>({update_id:id,message:{chat:{id:chat,type:'private'},from:{id:chat},text}});
function context(){const data=new Map();return {blockConcurrencyWhile:f=>f(),storage:{get:async k=>data.get(k),put:async(k,v)=>{if(typeof k==='object')for(const [key,val] of Object.entries(k))data.set(key,structuredClone(val));else data.set(k,structuredClone(v));},setAlarm:async()=>{},deleteAlarm:async()=>{}},data};}
test('webhook authenticates Telegram before accessing persistent inbox',async()=>{
 const bindings={...env,INBOX:{idFromName:()=>1,get:()=>({fetch:async()=>Response.json({ok:true})})}};
 assert.equal((await worker.fetch(new Request('https://example/telegram',{method:'POST',body:JSON.stringify(update())}),bindings)).status,403);
 assert.equal((await worker.fetch(new Request('https://example/telegram',{method:'POST',headers:{'X-Telegram-Bot-Api-Secret-Token':'synthetic'},body:JSON.stringify(update())}),bindings)).status,200);
 assert.equal((await worker.fetch(new Request('https://example/pending',{method:'POST',headers:{'X-Telegram-Bot-Api-Secret-Token':'synthetic'},body:'{}'}),bindings)).status,403);
});
test('only private owner commands and correct bot suffix are accepted',()=>{
 assert.deepEqual(commandOf(update(),env),{id:1,command:'/scan'});
 assert.equal(commandOf(update(1,999),env),null);
 assert.equal(commandOf(update(1,123,'/scan@otherbot'),env),null);
 assert.equal(commandOf(update(1,123,'/scan arbitrary payload'),env),null);
 assert.deepEqual(commandOf(update(1,123,'/logs@MyBot'),env),{id:1,command:'/logs'});
 const forged=update();forged.message.from.id=999;assert.equal(commandOf(forged,env),null);
});
test('persistent queue retains commands across GitHub runs and deduplicates deliveries',async()=>{
 const original=globalThis.fetch,requests=[];
 globalThis.fetch=async(url,init)=>{requests.push({url,body:JSON.parse(init.body)});return url.startsWith('https://api.github.com')?new Response(null,{status:204}):Response.json({ok:true});};
 try{
  const ctx=context();const inbox=new TelegramInbox(ctx,env);
  const call=(path,body)=>inbox.fetch(new Request('https://inbox/'+path,{method:'POST',body:JSON.stringify(body)}));
  await call('enqueue',{id:2,command:'/scan'});await call('enqueue',{id:2,command:'/scan'});await call('enqueue',{id:3,command:'/logs'});
  assert.deepEqual((await (await call('pending',{})).json()).commands,[{id:2,command:'/scan'},{id:3,command:'/logs'}]);
  assert.equal(requests.filter(x=>x.url.includes('sendMessage')).length,2);
  assert.ok(requests[0].url.includes('sendMessage'));
  assert.deepEqual(requests.find(x=>x.url.includes('api.github.com')).body,{ref:'main'});
  await call('ack',{through:2});assert.equal(ctx.data.get('queue').length,1);
  await call('ack',{through:3});assert.equal(ctx.data.get('queue').length,0);
  await call('enqueue',{id:2,command:'/scan'});assert.equal(ctx.data.get('queue').length,0);
 }finally{globalThis.fetch=original;}
});
test('a failed dispatch leaves a durable command and can be retried',async()=>{
 const original=globalThis.fetch;const ctx=context();const inbox=new TelegramInbox(ctx,env);
 let receipts=0;
 try{
  globalThis.fetch=async url=>{if(url.includes('sendMessage')){receipts++;return Response.json({ok:true});}return new Response(null,{status:403});};
  await assert.rejects(inbox.fetch(new Request('https://inbox/enqueue',{method:'POST',body:JSON.stringify({id:5,command:'/scan'})})));
  assert.equal(ctx.data.get('queue')[0].id,5);
  assert.equal(ctx.data.get('queue')[0].receipt,true);
  globalThis.fetch=async url=>{assert.ok(url.startsWith('https://api.github.com'));return new Response(null,{status:204});};
  const response=await inbox.fetch(new Request('https://inbox/enqueue',{method:'POST',body:JSON.stringify({id:5,command:'/scan'})}));
  assert.equal(response.status,200);assert.equal(receipts,1);
 }finally{globalThis.fetch=original;}
});

test('hourly cron dispatches scanner once per confirmed hour without Telegram messages',async()=>{
 const original=globalThis.fetch,requests=[];const ctx=context();const inbox=new TelegramInbox(ctx,env);
 const bindings={...env,HOURLY_SCAN_ENABLED:'true',INBOX:{idFromName:()=>1,get:()=>inbox}};
 globalThis.fetch=async(url,init)=>{requests.push({url,body:JSON.parse(init.body)});return new Response(null,{status:204});};
 try{
  const event={scheduledTime:Date.UTC(2026,9,29,12,17)};
  await worker.scheduled(event,bindings);await worker.scheduled(event,bindings);
  assert.equal(requests.length,1);assert.match(requests[0].url,/workflows\/scan\.yml\/dispatches$/);
  assert.deepEqual(requests[0].body,{ref:'main'});
  await worker.scheduled({scheduledTime:event.scheduledTime+3600000},bindings);assert.equal(requests.length,2);
 }finally{globalThis.fetch=original;}
});
test('hourly switch is explicit and public HTTP requests cannot launch hourly scans',async()=>{
 const bindings={...env,HOURLY_SCAN_ENABLED:'false',INBOX:{idFromName:()=>{throw Error('must not dispatch');}}};
 await worker.scheduled({scheduledTime:1},bindings);
 assert.equal((await worker.fetch(new Request('https://example/hourly',{method:'POST',body:'{}',headers:{'X-Bridge-Secret':'synthetic'}}),bindings)).status,404);
});
test('refused hourly dispatch does not record a successful hour',async()=>{
 const original=globalThis.fetch;const ctx=context();const inbox=new TelegramInbox(ctx,env);
 globalThis.fetch=async()=>new Response(null,{status:403});
 try{
  await assert.rejects(inbox.fetch(new Request('https://inbox/hourly',{method:'POST',body:JSON.stringify({hour:42})})));
  assert.equal(ctx.data.get('lastHourlyDispatch'),undefined);
 }finally{globalThis.fetch=original;}
});

test('all catalogue commands are routed by Cloudflare and have receipts',async()=>{
 const {COMMANDS}=await import('../telegram-webhook/commands.mjs');
 for(const [name,entry] of Object.entries(COMMANDS)){
  assert.deepEqual(commandOf(update(1,123,'/'+name),env),{id:1,command:'/'+name});
  assert.deepEqual(commandOf(update(1,123,'/'+name+'@MyBot'),env),{id:1,command:'/'+name});
  assert.ok(entry.receipt.includes('/'+name));assert.ok(entry.description);
 }
 assert.equal(commandOf(update(1,123,'/unregistered_command'),env),null);
 assert.equal(commandOf(update(1,123,'/constructor'),env),null);
});

test('natural hourly verification dispatch uses only the read-only setup workflow',async()=>{
 const original=globalThis.fetch,requests=[];const ctx=context();const inbox=new TelegramInbox(ctx,{...env,HOURLY_VERIFY_ENABLED:'true'});
 globalThis.fetch=async(url,init)=>{requests.push({url,body:JSON.parse(init.body)});return new Response(null,{status:204});};
 try{
  await inbox.fetch(new Request('https://inbox/hourly',{method:'POST',body:'{"hour":42}'}));
  assert.equal(requests.length,2);assert.match(requests[0].url,/scan\.yml\/dispatches$/);assert.match(requests[1].url,/configure-cloudflare\.yml\/dispatches$/);
  assert.deepEqual(requests[1].body.inputs,{verify_only:true,hour:'42'});
  const status=await (await inbox.fetch(new Request('https://inbox/status',{method:'POST',body:'{}'}))).json();
  assert.deepEqual(status,{lastHourlyDispatch:42,queue_length:0});
 }finally{globalThis.fetch=original;}
});
