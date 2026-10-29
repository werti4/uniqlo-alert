import test from 'node:test';
import assert from 'node:assert/strict';
import {canonical, newKey, seal, unseal, money, relative, safeImage, normalizeFavorites, normalizeWatchlist, normalizeCloud, validBranch} from '../extension/core.js';

test('product identity includes price group and strips irrelevant query',()=>{
  assert.deepEqual(canonical('https://www.uniqlo.com/fr/fr/products/E479219-000/01?colorDisplayCode=04'),{id:'E479219-000-01',url:'https://www.uniqlo.com/fr/fr/products/E479219-000/01'});
  for(const url of ['https://evil.test/fr/fr/products/E479219-000/01','https://www.uniqlo.com@evil.test/fr/fr/products/E479219-000/01','https://user:secret@www.uniqlo.com/fr/fr/products/E479219-000/01','http://www.uniqlo.com/fr/fr/products/E479219-000/01','https://www.uniqlo.com/fr/fr/']) assert.throws(()=>canonical(url));
});
test('AES-GCM detects tampering and wrong key',async()=>{
  const key=newKey(),value={favorites:[{name:'Pull écru à 29,90 €'}]};
  const box=await seal(value,key);
  assert.deepEqual(await unseal(box,key),value);
  await assert.rejects(unseal(box,newKey()));
  box.data=(box.data[0]==='A'?'B':'A')+box.data.slice(1);
  await assert.rejects(unseal(box,key));
});
test('prices missing from the scanner never display as zero',()=>{
  assert.equal(money(undefined),'—'); assert.equal(money(null),'—');
  assert.equal(money(NaN),'—'); assert.equal(money(-590),'—'); assert.equal(money('590'),'—');
  assert.match(money(590),/5,90/);
});

const favorite = {id:'E479219-000-01',url:'https://www.uniqlo.com/fr/fr/products/E479219-000/01',name:'Article',enabled:true,targetCents:null};
const cloud = () => ({schema:1,products:{[favorite.id]:{...favorite,priceCents:1990,lastCheckedAt:'2026-10-29T00:00:00Z',history:[{at:'2026-10-29T00:00:00Z',priceCents:1990}]}},alerts:[]});
test('remote favorites reject duplicate IDs, mismatched URLs and unknown schemas',()=>{
  assert.deepEqual(normalizeWatchlist({schema:1,favorites:[favorite]}).favorites[0].id, favorite.id);
  assert.throws(()=>normalizeFavorites([favorite,favorite]));
  assert.throws(()=>normalizeFavorites([{...favorite,id:'E000000-000-01'}]));
  assert.throws(()=>normalizeFavorites([{...favorite,targetCents:-1}]));
  assert.throws(()=>normalizeFavorites([{...favorite,enabled:'false'}]));
  assert.throws(()=>normalizeFavorites(Array.from({length:51},()=>favorite)));
  assert.throws(()=>normalizeWatchlist({schema:2,favorites:[]}));
});
test('decrypted cloud validates prices, chart history and outbound alert links before storage',()=>{
  const state = cloud();
  assert.equal(normalizeCloud(state).products[favorite.id].priceCents,1990);
  state.products[favorite.id].history.push({at:'invalid',priceCents:1990});
  assert.throws(()=>normalizeCloud(state));
  const unsafe = cloud();
  unsafe.alerts.push({productId:favorite.id,url:'javascript:alert(1)',name:'Injected',at:'2026-10-29T00:00:00Z',oldCents:2990,newCents:1990,delivery:'pending'});
  assert.throws(()=>normalizeCloud(unsafe));
  const missingPrice = cloud();
  missingPrice.products[favorite.id].priceCents = null;
  assert.equal(normalizeCloud(missingPrice).products[favorite.id].priceCents,null);
  missingPrice.products[favorite.id].priceCents = 0;
  assert.throws(()=>normalizeCloud(missingPrice));
});
test('external images and malformed dates degrade safely',()=>{
  assert.equal(safeImage('https://image.uniqlo.com/a.jpg'),'https://image.uniqlo.com/a.jpg');
  for(const url of ['https://image.uniqlo.com.evil.test/a.jpg','https://user@image.uniqlo.com/a.jpg','data:text/html,hello',null]) assert.equal(safeImage(url),null);
  assert.equal(relative('not-a-date'),'Date indisponible');
});
test('branch validation accepts nested refs but rejects invalid Git names',()=>{
  assert.equal(validBranch('main'),true); assert.equal(validBranch('release/v1'),true);
  for(const branch of ['', '../main', 'main.lock', 'a//b', 'main.', 'main/', 'a b', '.hidden']) assert.equal(validBranch(branch),false);
});
test('large encrypted snapshots do not overflow the JavaScript argument stack',async()=>{
  const state = {products:Object.fromEntries(Array.from({length:50},(_,i)=>[i,{history:Array.from({length:120},()=>({at:'2026-10-29T00:00:00Z',priceCents:1990}))}]))};
  const key = newKey();
  const encrypted = await seal(state,key);
  assert.ok(encrypted.data.length > 200_000);
  assert.deepEqual(await unseal(encrypted,key),state);
});

test('background serializes changes and preserves local data on remote conflict or deletion',async t=>{
  const originalFetch = globalThis.fetch, originalChrome = globalThis.chrome;
  const key = newKey();
  const store = {settings:{repo:'werti4/uniqlo-alert',branch:'main',token:'test-token',key}};
  let listener, remoteConfig = null, remoteCloud = null, deniedRepo = false;
  const openedTabs = [];
  const encode = value => Buffer.from(JSON.stringify(value)).toString('base64');
  const response = (value,status=200) => new Response(JSON.stringify(value),{status});
  globalThis.chrome = {
    storage:{local:{setAccessLevel:async()=>{},get:async keys=>structuredClone(Object.fromEntries(keys.filter(k=>k in store).map(k=>[k,store[k]]))),set:async changes=>Object.assign(store,structuredClone(changes))}},
    runtime:{id:'mock-extension',getURL:path=>'chrome-extension://mock-extension/'+path,onInstalled:{addListener(){}},onMessage:{addListener(fn){listener=fn;}}},
    action:{onClicked:{addListener(){}}},tabs:{create:async options=>openedTabs.push(options)}
  };
  globalThis.fetch = async(raw,init={})=>{
    const path = new URL(raw).pathname.replace('/repos/werti4/uniqlo-alert','');
    if (deniedRepo) return response({},404);
    if (path==='/branches/main') return response({name:'main'});
    if (path==='/contents/data/watchlist.enc.json') {
      if (init.method==='PUT') {
        const body=JSON.parse(init.body);
        assert.equal(body.sha,remoteConfig?.sha);
        remoteConfig={sha:'config-1',content:body.content};
        return response({content:{sha:remoteConfig.sha}});
      }
      return remoteConfig ? response(remoteConfig) : response({},404);
    }
    if (path==='/contents/data/state.enc.json') return remoteCloud ? response(remoteCloud) : response({},404);
    if (path==='/actions/workflows/scan.yml/runs') return response({workflow_runs:[]});
    throw new Error('Unexpected mocked request: '+path);
  };
  try {
    await import('../extension/background.js?regression');
    const call=message=>new Promise(resolve=>listener(message,{id:'mock-extension',url:'chrome-extension://mock-extension/app.html'},resolve));
    await t.test('parallel favorite additions are retained',async()=>{
      const replies=await Promise.all([favorite.url,'https://www.uniqlo.com/fr/fr/products/E469847-000/00'].map(url=>call({type:'addUrl',favorite:{url,name:'Article'}})));
      assert.ok(replies.every(r=>r.ok)); assert.equal(store.favorites.length,2);
    });
    await t.test('publishing encrypts and syncing imports a valid cloud snapshot',async()=>{
      assert.equal((await call({type:'publish'})).ok,true);
      assert.equal(store.dirty,false);
      const config = await unseal(JSON.parse(Buffer.from(remoteConfig.content,'base64').toString()),key);
      assert.equal(config.favorites.length,2);
      remoteCloud={content:encode(await seal(cloud(),key))};
      assert.equal((await call({type:'sync'})).ok,true);
      assert.equal(store.cloud.products[favorite.id].priceCents,1990);
    });
    await t.test('a remote SHA conflict preserves unsaved local edits',async()=>{
      await call({type:'update',id:favorite.id,patch:{enabled:false}});
      remoteConfig.sha='changed-remotely';
      assert.equal((await call({type:'publish'})).ok,false);
      assert.equal(store.dirty,true); assert.equal(store.favorites.find(f=>f.id===favorite.id).enabled,false);
      // Explicit reload is allowed, and replaces favorites only after all remote reads succeed.
      assert.equal((await call({type:'reloadRemote'})).ok,true);
      assert.equal(store.dirty,false);
    });
    await t.test('deleted remote config cannot erase a known local watchlist even on reload',async()=>{
      const saved=remoteConfig, local=structuredClone(store);
      remoteConfig=null;
      assert.equal((await call({type:'sync'})).ok,false);
      assert.equal((await call({type:'reloadRemote'})).ok,false);
      assert.deepEqual(store,local); remoteConfig=saved;
    });
    await t.test('deleted or malformed remote state preserves the last successful local data',async()=>{
      const saved=remoteCloud, local=structuredClone(store);
      remoteCloud=null; assert.equal((await call({type:'sync'})).ok,false); assert.deepEqual(store,local);
      remoteCloud={content:encode(await seal({...cloud(),products:{[favorite.id]:{priceCents:0}}},key))};
      assert.equal((await call({type:'reloadRemote'})).ok,false); assert.deepEqual(store,local);
      remoteCloud=saved;
    });
    await t.test('site summary excludes credentials and site messages cannot read privileged state',async()=>{
      const siteCall=message=>new Promise(resolve=>listener(message,{id:'mock-extension',url:favorite.url,tab:{id:1}},resolve));
      const summary=await siteCall({type:'quickRead',url:'https://evil.test/'});
      assert.equal(summary.ok,true);
      assert.equal(summary.value.product.id,favorite.id);
      assert.equal(summary.value.product.saved,true);
      assert.equal(summary.value.count,2);
      assert.equal(JSON.stringify(summary).includes('test-token'),false);
      assert.equal(JSON.stringify(summary).includes(key),false);
      assert.equal('settings' in summary.value,false);
      assert.equal((await siteCall({type:'openDashboard',view:'favorites',filter:'drop'})).ok,true);
      assert.equal(openedTabs.at(-1).url,'chrome-extension://mock-extension/app.html?view=favorites&filter=drop');
      for (const type of ['read','settings','publish','remove','sync']) {
        assert.equal((await siteCall({type,id:favorite.id})).ok,false);
      }
      const denied=await new Promise(resolve=>listener({type:'quickRead'},{id:'mock-extension',url:'https://evil.test/'},resolve));
      assert.equal(denied.ok,false);
    });
    await t.test('one-click toggle follows the sender product and preserves other favorites',async()=>{
      const siteCall=message=>new Promise(resolve=>listener(message,{id:'mock-extension',url:favorite.url,tab:{id:1}},resolve));
      const removed=await siteCall({type:'quickToggle',url:'https://www.uniqlo.com/fr/fr/products/E469847-000/00'});
      assert.equal(removed.ok,true); assert.equal(removed.value.product.saved,false);
      assert.equal(store.favorites.length,1); assert.equal(store.dirty,true);
      const added=await siteCall({type:'quickToggle',name:'Pull bleu'});
      assert.equal(added.ok,true); assert.equal(added.value.product.saved,true);
      assert.equal(store.favorites.find(f=>f.id===favorite.id).name,'Pull bleu');
      assert.equal(store.favorites.length,2);
      const catalog=await new Promise(resolve=>listener({type:'quickToggle'},{id:'mock-extension',url:'https://www.uniqlo.com/fr/fr/'},resolve));
      assert.equal(catalog.ok,false);
      const [a,b]=await Promise.all([siteCall({type:'quickToggle'}),siteCall({type:'quickToggle'})]);
      assert.equal(a.value.product.saved,false); assert.equal(b.value.product.saved,true);
      assert.equal(store.favorites.length,2);
    });
    await t.test('empty encryption keys and inaccessible repos never report success',async()=>{
      assert.equal((await call({type:'settings',settings:{key:''}})).ok,false); assert.equal(store.settings.key,key);
      const local=structuredClone(store); deniedRepo=true;
      assert.equal((await call({type:'sync'})).ok,false); assert.deepEqual(store,local);
    });
  } finally {globalThis.fetch=originalFetch; globalThis.chrome=originalChrome;}
});
