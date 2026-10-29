// Browser regression: real popup markup and strict manifest CSP, with local Chrome APIs simulated.
// Every HTTP request is fulfilled from fixtures; no UNIQLO or GitHub requests.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const project=path.resolve(__dirname,'..');
const output=path.join(project,'test-results','quick-ui');
fs.mkdirSync(output,{recursive:true});
(async()=>{
let listener;const store={};
global.chrome={storage:{local:{setAccessLevel:async()=>{},get:async keys=>structuredClone(Object.fromEntries(keys.filter(k=>k in store).map(k=>[k,store[k]]))),set:async changes=>Object.assign(store,structuredClone(changes))}},runtime:{id:'ui-test',getURL:p=>'chrome-extension://ui-test/'+p,onInstalled:{addListener(){}},onMessage:{addListener(fn){listener=fn;}}},tabs:{create:async()=>{}}};
global.fetch=async()=>new Response('',{status:404});
await import(pathToFileURL(path.join(project,'extension/background.js')).href);
const source=fs.readFileSync(path.join(project,'extension/quick.js'),'utf8');
const css=fs.readFileSync(path.join(project,'extension/quick-popup.css'),'utf8');
const csp=JSON.parse(fs.readFileSync(path.join(project,'extension/manifest.json'),'utf8')).content_security_policy.extension_pages;
const browser=await chromium.launch({...(process.env.CHROMIUM_EXECUTABLE ? {executablePath:process.env.CHROMIUM_EXECUTABLE} : {}),headless:true,args:['--no-sandbox']});
try{
const context=await browser.newContext({viewport:{width:1440,height:1000}});
await context.route('**/*',route=>{
 const pathname=new URL(route.request().url()).pathname;
 if(pathname==='/quick-test.js')return route.fulfill({contentType:'application/javascript; charset=utf-8',body:source});
 if(pathname==='/quick.js')return route.fulfill({contentType:'application/javascript; charset=utf-8',body:'((location)=>{'+source+'})({protocol:"chrome-extension:"});'});
 if(pathname==='/quick-popup.css')return route.fulfill({contentType:'text/css',body:css});
 if(pathname==='/quick.html')return route.fulfill({headers:{'Content-Security-Policy':csp},contentType:'text/html; charset=utf-8',body:fs.readFileSync(path.join(project,'extension/quick.html'),'utf8')});
 return route.fulfill({headers:{'Content-Security-Policy':csp},contentType:'text/html; charset=utf-8',body:'<!doctype html><html lang="fr"><title>Test CSP</title><body><h1>Pull bleu — fiche synthétique</h1></body></html>'});
});
await context.exposeBinding('extensionMessage',({frame},message)=>new Promise(resolve=>listener(message,{id:'ui-test',url:frame.url(),tab:{id:1}},resolve)));
await context.exposeBinding('popupMessage',(_,message)=>new Promise(resolve=>listener(message,{id:'ui-test',url:'chrome-extension://ui-test/quick.html'},resolve)));
await context.addInitScript(()=>{
 globalThis.chrome={runtime:{id:'ui-test',sendMessage:m=>location.pathname==='/quick.html' ? window.popupMessage(m) : window.extensionMessage(m)},tabs:{query:async()=>[{url:'https://www.uniqlo.com/fr/fr/products/E479219-000/01',title:'Article popup'}]}};
 const attach=Element.prototype.attachShadow;Element.prototype.attachShadow=function(options){return attach.call(this,{...options,mode:'open'})};
 window.cspViolations=[];document.addEventListener('securitypolicyviolation',e=>window.cspViolations.push(e.violatedDirective));
});
const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('https://www.uniqlo.com/fr/fr/products/E479219-000/01');
await page.addScriptTag({url:'https://www.uniqlo.com/quick-test.js'});
await page.getByRole('button',{name:'♡ Ajouter à mes favoris',exact:true}).click();
await page.getByRole('button',{name:'♥ Retirer de mes favoris',exact:true}).waitFor();
assert.equal(store.favorites.length,1);
assert.equal(await page.locator('.stats').evaluate(e=>getComputedStyle(e).display),'grid');
assert.equal(await page.locator('.primary').evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(245, 239, 237)');
await page.screenshot({path:path.join(output,'embedded.png')});
await page.getByRole('button',{name:'♥ Retirer de mes favoris',exact:true}).click();
await page.getByRole('button',{name:'♡ Ajouter à mes favoris',exact:true}).waitFor();
await page.getByRole('button',{name:'Réduire la fenêtre',exact:true}).click();
await page.getByRole('button',{name:'Ouvrir UNIQLO Alert',exact:true}).click();
await page.getByRole('button',{name:'♡ Ajouter à mes favoris',exact:true}).waitFor();
assert.deepEqual(await page.evaluate(()=>window.cspViolations),[]);
const popup=await context.newPage();
popup.on('pageerror',e=>errors.push(e.message));
await popup.setViewportSize({width:360,height:600});
await popup.goto('https://www.uniqlo.com/quick.html');
await popup.getByRole('button',{name:'♡ Ajouter à mes favoris',exact:true}).waitFor();
assert.equal(await popup.locator('body').evaluate(e=>e.getBoundingClientRect().width),360);
assert.equal(await popup.locator('.panel').evaluate(e=>Math.round(e.getBoundingClientRect().width)),360);
assert.equal(await popup.locator('.stats').evaluate(e=>getComputedStyle(e).display),'grid');
assert.equal(await popup.locator('.primary').evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(223, 70, 70)');
assert.equal(await popup.evaluate(()=>document.documentElement.scrollWidth),360);
await popup.getByRole('button',{name:'♡ Ajouter à mes favoris',exact:true}).click();
await popup.getByRole('button',{name:'♥ Retirer de mes favoris',exact:true}).waitFor();
await popup.screenshot({path:path.join(output,'popup.png')});
assert.deepEqual(await popup.evaluate(()=>window.cspViolations),[]);
assert.deepEqual(errors,[]);
console.log('CSP exacte du manifeste : popup 360px, cartes en grille, couleurs, ajout/retrait, réduction/réouverture ; zéro violation CSP.');
}finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
