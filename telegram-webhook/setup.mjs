// Administrative activation; no token, chat ID or API error body is returned/logged.
const ROOT = 'https://uniqlo-telegram-webhook.uniqlo-alert-werti4.workers.dev';
const encoder = new TextEncoder();
export async function proofOf(secret, token, chat) {
  const key = await crypto.subtle.importKey('raw', encoder.encode(secret), {name:'HMAC',hash:'SHA-256'}, false, ['sign']);
  return [...new Uint8Array(await crypto.subtle.sign('HMAC', key, encoder.encode(token+'\n'+chat)))].map(x=>x.toString(16).padStart(2,'0')).join('');
}
export async function telegramApi(env, method, body={}) {
  try {
    const r=await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/${method}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(6000)});
    const data=await r.json();
    if(!r.ok||data.ok!==true) throw Error();
    return data.result;
  } catch { throw Error('telegram_'+method+'_unavailable'); }
}
async function githubApi(env, suffix, body) {
  try {
    const r=await fetch(`https://api.github.com/repos/werti4/uniqlo-alert${suffix}`,{method:body?'POST':'GET',headers:{Authorization:`Bearer ${env.GITHUB_DISPATCH_TOKEN}`,Accept:'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json','User-Agent':'UniqloAlertSetup/1.0'},...(body?{body:JSON.stringify(body)}:{}),signal:AbortSignal.timeout(6000)});
    if(body){if(r.status!==204)throw Error();return true;}
    if(!r.ok)throw Error();return await r.json();
  }catch{throw Error('github_access_unavailable');}
}
export async function configure(env, body, equal) {
  if(env.GITHUB_REPOSITORY!=='werti4/uniqlo-alert'||env.GITHUB_BRANCH!=='main') throw Error('repository_configuration');
  if(!/^[A-Za-z0-9_-]{32,256}$/.test(env.WEBHOOK_SECRET||'')||!/^\d+$/.test(env.TELEGRAM_CHAT_ID||'')) throw Error('secret_format');
  if(body.root!==ROOT||body.enabled!==true||!await equal(body.proof,await proofOf(env.WEBHOOK_SECRET,env.TELEGRAM_BOT_TOKEN,env.TELEGRAM_CHAT_ID)))throw Error('github_cloudflare_values_differ');
  const bot=await telegramApi(env,'getMe');
  if(bot.is_bot!==true||typeof bot.username!=='string'||bot.username.toLowerCase()!==env.BOT_USERNAME?.toLowerCase())throw Error('bot_username_mismatch');
  const chat=await telegramApi(env,'getChat',{chat_id:env.TELEGRAM_CHAT_ID});
  if(chat.type!=='private'||String(chat.id)!==env.TELEGRAM_CHAT_ID)throw Error('private_owner_mismatch');
  for(const workflow of ['telegram-commands.yml','scan.yml']){
    const w=await githubApi(env,'/actions/workflows/'+workflow);
    if(w.state!=='active')throw Error('workflow_inactive');
  }
  const runs=await githubApi(env,'/actions/workflows/telegram-commands.yml/runs?per_page=100');
  if(!Array.isArray(runs.workflow_runs)||runs.workflow_runs.some(r=>r.status!=='completed'))throw Error('old_command_reader_running');
  // Prove Actions write using this dedicated, read-only verification workflow, never scan.yml.
  await githubApi(env,'/actions/workflows/configure-cloudflare.yml/dispatches',{ref:'main',inputs:{verify_only:true}});
  const current=await telegramApi(env,'getWebhookInfo');
  if(current.url&&current.url!==ROOT+'/telegram')throw Error('other_webhook_present');
  await telegramApi(env,'setWebhook',{url:ROOT+'/telegram',secret_token:env.WEBHOOK_SECRET,allowed_updates:['message'],max_connections:1,drop_pending_updates:false});
  const info=await telegramApi(env,'getWebhookInfo');
  if(info.url!==ROOT+'/telegram'||info.max_connections!==1||JSON.stringify(info.allowed_updates)!=='["message"]')throw Error('webhook_not_confirmed');
  return {ok:true,access_verified:true,dispatch_accepted:true,webhook_confirmed:true,pending_updates:info.pending_update_count||0};
}
export async function configurationStatus(env) {
  const info=await telegramApi(env,'getWebhookInfo');
  const inbox=env.INBOX.get(env.INBOX.idFromName('owner'));
  const r=await inbox.fetch(new Request('https://inbox/status',{method:'POST',body:'{}'}));
  if(!r.ok)throw Error('inbox_unavailable');
  return {ok:true,webhook_confirmed:info.url===ROOT+'/telegram'&&info.max_connections===1&&JSON.stringify(info.allowed_updates)==='["message"]',pending_updates:info.pending_update_count||0,last_error_date:info.last_error_date||null,hourly_enabled:env.HOURLY_SCAN_ENABLED==='true',...await r.json()};
}
