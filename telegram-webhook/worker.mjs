import {COMMANDS, definition} from './commands.mjs';
// No message contents or credentials are logged. One persistent inbox per bot.
const json = (data, status = 200) => Response.json(data, {status});
const equal = async (a, b) => {
  if (!a || !b) return false;
  const hash = async s => new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)));
  const [x, y] = await Promise.all([hash(a), hash(b)]);
  let diff = 0; for (let i = 0; i < x.length; i++) diff |= x[i] ^ y[i];
  return diff === 0;
};
export function commandOf(update, env) {
  const m = update?.message;
  if (m?.chat?.type !== 'private' || String(m.chat.id) !== env.TELEGRAM_CHAT_ID ||
      String(m.from?.id) !== env.TELEGRAM_CHAT_ID || m.from?.is_bot || !Number.isSafeInteger(update.update_id) || update.update_id < 0) return null;
  const match = typeof m.text === 'string' && m.text.trim().match(/^\/([a-z][a-z0-9_]{0,31})(?:@([\w]+))?\s*$/i);
  if (!match || !Object.hasOwn(COMMANDS, match[1].toLowerCase()) || (match[2] && match[2].toLowerCase() !== env.BOT_USERNAME?.toLowerCase())) return null;
  return {id: update.update_id, command: '/' + match[1].toLowerCase()};
}
export default {
  async scheduled(event, env) {
    if (env.HOURLY_SCAN_ENABLED !== 'true') return;
    const inbox = env.INBOX.get(env.INBOX.idFromName('owner'));
    const hour = Math.floor(event.scheduledTime / 3600000);
    const response = await inbox.fetch(new Request('https://inbox/hourly', {method: 'POST', body: JSON.stringify({hour})}));
    if (!response.ok) throw Error('Hourly dispatch not confirmed');
  },
  async fetch(request, env) {
    const path = new URL(request.url).pathname;
    if (request.method !== 'POST' || !['/telegram', '/pending', '/ack'].includes(path)) return json({ok: false}, 404);
    const header = path === '/telegram' ? 'X-Telegram-Bot-Api-Secret-Token' : 'X-Bridge-Secret';
    if (!await equal(request.headers.get(header), env.WEBHOOK_SECRET)) return json({ok: false}, 403);
    if (Number(request.headers.get('Content-Length') || 0) > 65536) return json({ok: false}, 413);
    try {
      const raw = await request.text(); if (raw.length > 65536) return json({ok: false}, 413);
      const body = JSON.parse(raw || '{}');
      const inbox = env.INBOX.get(env.INBOX.idFromName('owner'));
      if (path === '/telegram') {
        const command = commandOf(body, env);
        if (!command) return json({ok: true});
        return await inbox.fetch(new Request('https://inbox/enqueue', {method: 'POST', body: JSON.stringify(command)}));
      }
      return await inbox.fetch(new Request('https://inbox' + path, {method: 'POST', body: JSON.stringify(body)}));
    } catch { return json({ok: false}, 503); }
  }
};
export class TelegramInbox {
  constructor(ctx, env) { this.ctx = ctx; this.env = env; }
  async dispatch(workflow = 'telegram-commands.yml') {
    if (!['telegram-commands.yml', 'scan.yml'].includes(workflow)) throw Error('workflow refused');
    const repo = this.env.GITHUB_REPOSITORY;
    if (!/^[\w.-]+\/[\w.-]+$/.test(repo || '')) throw Error('configuration');
    const response = await fetch(`https://api.github.com/repos/${repo}/actions/workflows/${workflow}/dispatches`, {
      method: 'POST', signal: AbortSignal.timeout(6000),
      headers: {'Authorization': `Bearer ${this.env.GITHUB_DISPATCH_TOKEN}`, 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json', 'User-Agent': 'UniqloAlertWebhook'},
      body: JSON.stringify({ref: this.env.GITHUB_BRANCH || 'main'})
    }).catch(() => { throw Error('dispatch unavailable'); });
    if (response.status !== 204) throw Error('dispatch refused');
  }
  async receipt(command) {
    try {
    const response = await fetch(`https://api.telegram.org/bot${this.env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: 'POST', signal: AbortSignal.timeout(6000), headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({chat_id: this.env.TELEGRAM_CHAT_ID, text: definition(command)?.receipt || 'Commande indisponible.'})
    });
    const result = await response.json(); if (!response.ok || result.ok !== true) throw Error('receipt refused');
    } catch { throw Error('receipt unavailable'); }
  }
  async fetch(request) {
    return this.ctx.blockConcurrencyWhile(async () => {
      const path = new URL(request.url).pathname;
      const body = await request.json();
      if (path === '/hourly') {
        if (!Number.isSafeInteger(body.hour) || body.hour < 0) return json({ok: false}, 400);
        const lastHour = await this.ctx.storage.get('lastHourlyDispatch') ?? -1;
        if (body.hour <= lastHour) return json({ok: true});
        await this.dispatch('scan.yml');
        await this.ctx.storage.put('lastHourlyDispatch', body.hour);
        return json({ok: true});
      }
      let queue = await this.ctx.storage.get('queue') || [];
      if (path === '/pending') return json({commands: queue.slice(0, 3).map(({id, command}) => ({id, command}))});
      if (path === '/ack') {
        if (!Number.isSafeInteger(body.through) || body.through < 0) return json({ok: false}, 400);
        const last = await this.ctx.storage.get('last') ?? -1;
        queue = queue.filter(item => item.id > body.through);
        await this.ctx.storage.put({queue, last: Math.max(last, body.through)});
        if (!queue.length) await this.ctx.storage.deleteAlarm();
        else { await this.ctx.storage.setAlarm(Date.now() + 600000); await this.dispatch(); }
        return json({ok: true});
      }
      if (path !== '/enqueue') return json({ok: false}, 404);
      if (body.id <= (await this.ctx.storage.get('last') ?? -1)) return json({ok: true});
      let item = queue.find(item => item.id === body.id);
      if (!item) {
        if (queue.length >= 20) return json({ok: false}, 503);
        item = {...body, receipt: false}; queue.push(item); queue.sort((a, b) => a.id - b.id);
        await this.ctx.storage.put('queue', queue);
      }
      // Durable queue survives retries and replaced pending GitHub runs.
      await this.ctx.storage.setAlarm(Date.now() + 600000);
      await this.dispatch();
      if (!item.receipt) { await this.receipt(item.command); item.receipt = true; await this.ctx.storage.put('queue', queue); }
      return json({ok: true});
    });
  }
  async alarm() {
    const queue = await this.ctx.storage.get('queue') || [];
    if (!queue.length) return;
    await this.ctx.storage.setAlarm(Date.now() + 600000);
    await this.dispatch();
  }
}
