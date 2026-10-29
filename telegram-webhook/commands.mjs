// Cloudflare owns the command catalogue. Python uses the same JSON, never a second list.
import definitions from './commands.json' with {type: 'json'};
export const COMMANDS = Object.freeze(Object.fromEntries(definitions.map(item => {
  if (!/^[a-z][a-z0-9_]{0,31}$/.test(item.name) || !item.handler || !item.description || !item.receipt) throw Error('invalid command catalogue');
  return [item.name, Object.freeze(item)];
})));
if (Object.keys(COMMANDS).length !== definitions.length) throw Error('duplicate command');
export function definition(command) {
  return typeof command === 'string' && command.startsWith('/') && Object.hasOwn(COMMANDS, command.slice(1)) ? COMMANDS[command.slice(1)] : undefined;
}
