import copy
import datetime as dt
import io
import json
import unittest
import urllib.error
import urllib.request
from unittest.mock import Mock, patch
from scanner.monitor import (encrypt, decrypt, b64, parse_product, observe, canonical_url,
    Robots, cents, fingerprint, retry_after_seconds, BlockedError, NetworkError,
    scan_products, validate_favorites, GitHubState, SafeRedirect, get_page,
    deliver_outbox, TelegramError, telegram_send, validate_state, run)
from cryptography.exceptions import InvalidTag


class MonitorTests(unittest.TestCase):
    def setUp(self):
        clock=patch('scanner.monitor.now',return_value='2026-10-29T00:00:00+00:00')
        clock.start();self.addCleanup(clock.stop)
        self.product={'productId':'E479219-000','priceGroup':'01','name':'Collants HEATTECH','prices':{'base':{'value':14.9,'currency':{'code':'EUR'}},'promo':{'value':5.9,'currency':{'code':'EUR'}}},'sizes':[{'name':'M'}]}
        self.page='window.__PRELOADED_STATE__ = '+json.dumps({'entity':{'pdpEntity':{'E479219-000-01':{'product':self.product}}}})+';'
        self.fav={'id':'E479219-000-01','url':'https://www.uniqlo.com/fr/fr/products/E479219-000/01','enabled':True,'targetCents':None}
    def test_real_ssr_shape_and_group(self):
        p=parse_product(self.page,self.fav['id']);self.assertEqual(p['priceCents'],590);self.assertEqual(p['regularCents'],1490);self.assertIsNone(p['availability'])
        with self.assertRaises(ValueError):parse_product(self.page,'E479219-000-00')
    def test_invalid_and_non_eur_prices(self):
        for value in [None,0,-1,'nan','Infinity','oops','0.001']:
            with self.assertRaises(ValueError):cents(value)
        self.product['prices']['promo']['currency']['code']='USD'
        with self.assertRaises(ValueError):parse_product('window.__PRELOADED_STATE__ = '+json.dumps({'entity':{'pdpEntity':{self.fav['id']:{'product':self.product}}}}),self.fav['id'])
    def test_first_read_no_alert_equal_price_no_duplicate_all_drops(self):
        p=parse_product(self.page,self.fav['id']);s={}
        observe(s,self.fav,p,'2026-10-29T00:00:00+00:00');self.assertEqual(s['alerts'],[])
        observe(s,self.fav,p,'2026-10-29T00:05:00+00:00');self.assertEqual(len(s['products'][self.fav['id']]['history']),1)
        p['priceCents']=490;observe(s,self.fav,p,'2026-10-29T00:10:00+00:00');self.assertEqual(s['alerts'][0]['delivery'],'pending')
        observe(s,self.fav,p,'2026-10-29T00:15:00+00:00');self.assertEqual(len(s['alerts']),1)
        p['priceCents']=590;observe(s,self.fav,p,'2026-10-29T00:20:00+00:00')
        p['priceCents']=490;observe(s,self.fav,p,'2026-10-29T00:25:00+00:00');self.assertEqual(len(s['alerts']),2)
    def test_target_threshold(self):
        s={};p=parse_product(self.page,self.fav['id']);observe(s,self.fav,p,'a')
        self.fav['targetCents']=390;p['priceCents']=490;observe(s,self.fav,p,'b')
        self.assertEqual(len(s['alerts']),1);self.assertFalse(s['alerts'][0]['targetReached'])
        p['priceCents']=390;observe(s,self.fav,p,'c')
        self.assertEqual(len(s['alerts']),2);self.assertTrue(s['alerts'][1]['targetReached'])
    def test_aes_integrity(self):
        key=b64(bytes(range(32)));box=encrypt({'name':'Écru'},key)
        self.assertEqual(decrypt(box,key),{'name':'Écru'})
        with self.assertRaises(InvalidTag):decrypt(box,b64(bytes([1])*32))
        with self.assertRaises(ValueError):encrypt({},b64(bytes(16)))
    def test_url_whitelist(self):
        self.assertEqual(canonical_url(self.fav['url']+'?colorDisplayCode=04')[1],self.fav['id'])
        with self.assertRaises(ValueError):canonical_url('https://evil.test/fr/fr/products/E479219-000/01')
    def test_robots_wildcard_longest_rule_and_tie_allow(self):
        r=Robots('User-agent: *\nDisallow: /*/*/cart\nDisallow: /fr/fr/products/*\nAllow: /fr/fr/products/E479219-000/01\nDisallow: /fr/fr/products/E479219-000/01')
        self.assertFalse(r.allowed('https://www.uniqlo.com/fr/fr/cart'))
        self.assertFalse(r.allowed('https://www.uniqlo.com/fr/fr/products/E123456-000/01'))
        self.assertTrue(r.allowed(self.fav['url']))
    def test_time_only_changes_do_not_grow_git_history(self):
        a={'lastScanAt':'a','persistedAt':'a','products':{'x':{'priceCents':100,'lastCheckedAt':'a'}}}
        b=copy.deepcopy(a);b['lastScanAt']='b';b['products']['x']['lastCheckedAt']='b'
        self.assertEqual(fingerprint(a),fingerprint(b))

    def test_price_group_rejects_promo_above_base(self):
        self.product['prices']['promo']['value']=19.9
        page='window.__PRELOADED_STATE__ = '+json.dumps({'entity':{'pdpEntity':{self.fav['id']:{'product':self.product}}}})
        with self.assertRaises(ValueError):parse_product(page,self.fav['id'])
        with self.assertRaises(ValueError):cents(True)

    def test_robots_empty_directive_does_not_merge_agent_groups(self):
        self.assertTrue(Robots('User-agent: *\nDisallow:\nUser-agent: Googlebot\nDisallow: /').allowed(self.fav['url']))
        self.assertTrue(Robots('User-agent: *\nDisallow: /\nUser-agent: UniqloAlertPersonal\nDisallow:').allowed(self.fav['url']))

    def test_retry_after_http_date_and_seconds(self):
        at=dt.datetime(2026,10,29,tzinfo=dt.timezone.utc)
        self.assertEqual(retry_after_seconds('120',at),120)
        self.assertEqual(retry_after_seconds('Thu, 29 Oct 2026 00:30:00 GMT',at),1801)
        self.assertIsNone(retry_after_seconds('invalid',at))
        self.assertEqual(retry_after_seconds('Wed, 28 Oct 2026 00:30:00 GMT',at),0)

    def test_https_redirect_cannot_downgrade(self):
        request=urllib.request.Request(self.fav['url'])
        with self.assertRaises(BlockedError):
            SafeRedirect().redirect_request(request,None,302,'Moved',{},self.fav['url'].replace('https:','http:'))

    def test_http_429_exposes_only_safe_message_and_retry_delay(self):
        error=urllib.error.HTTPError(self.fav['url'],429,'Too many',{'Retry-After':'7200'},io.BytesIO(b''))
        with patch('scanner.monitor.urllib.request.build_opener') as opener:
            opener.return_value.open.side_effect=error
            with self.assertRaises(BlockedError) as captured:get_page(self.fav['url'])
        self.assertEqual(captured.exception.retry_after,7200)
        self.assertNotIn(self.fav['url'],str(captured.exception))

    def test_read_errors_preserve_last_valid_price_and_success_timestamp(self):
        state={};p=parse_product(self.page,self.fav['id'])
        observe(state,self.fav,p,'2026-10-29T00:00:00+00:00')
        with patch('scanner.monitor.get_page',side_effect=['User-agent: *\nDisallow:',ValueError('Données absentes')]),patch('scanner.monitor.time.sleep'):
            scan_products(state,[self.fav],'2026-10-29T00:15:00+00:00')
        item=state['products'][self.fav['id']]
        self.assertEqual(item['priceCents'],590)
        self.assertEqual(item['lastCheckedAt'],'2026-10-29T00:00:00+00:00')
        self.assertEqual(item['lastSuccessfulAt'],'2026-10-29T00:00:00+00:00')
        self.assertEqual(item['lastAttemptAt'],'2026-10-29T00:15:00+00:00')
        self.assertEqual(item['status'],'error')
        self.assertEqual(state['alerts'],[])
        self.assertEqual(state['scanStats']['failed'],1)

    def test_block_suspends_remaining_products_and_persists_server_cooldown(self):
        other={**self.fav,'id':'E123456-000-01','url':'https://www.uniqlo.com/fr/fr/products/E123456-000/01'}
        state={}
        with patch('scanner.monitor.get_page',side_effect=['User-agent: *\nDisallow:',BlockedError('UNIQLO limite HTTP 429',7200)]) as fetch,patch('scanner.monitor.time.sleep'):
            scan_products(state,[self.fav,other],'2026-10-29T00:00:00+00:00')
        self.assertEqual(fetch.call_count,2)
        self.assertEqual(state['cooldownUntil'],'2026-10-29T02:00:00+00:00')
        self.assertEqual(state['scanStats']['deferred'],1)
        with patch('scanner.monitor.get_page') as fetch:
            scan_products(state,[self.fav,other],'2026-10-29T00:15:00+00:00')
        fetch.assert_not_called()
        self.assertEqual(state['scanStats']['deferred'],2)

    def test_repeated_network_errors_stop_collection(self):
        favorites=[{**self.fav,'id':f'E12345{i}-000-01','url':f'https://www.uniqlo.com/fr/fr/products/E12345{i}-000/01'} for i in range(5)]
        state={}
        with patch('scanner.monitor.get_page',side_effect=['User-agent: *\nDisallow:']+[NetworkError('Erreur réseau')]*3) as fetch,patch('scanner.monitor.time.sleep'):
            scan_products(state,favorites,'2026-10-29T00:00:00+00:00')
        self.assertEqual(fetch.call_count,4)
        self.assertEqual(state['scanStats'],{'total':5,'attempted':3,'succeeded':0,'failed':3,'deferred':2})
        self.assertIn('cooldownUntil',state)

    def test_budget_rotates_to_first_unchecked_favorite(self):
        other={**self.fav,'id':'E123456-000-01','url':'https://www.uniqlo.com/fr/fr/products/E123456-000/01'}
        other_page=self.page.replace('E479219-000','E123456-000')
        state={}
        with patch('scanner.monitor.get_page',side_effect=['User-agent: *\nDisallow:',self.page]),patch('scanner.monitor.time.sleep'),patch('scanner.monitor.time.monotonic',side_effect=[0,0,300]):
            scan_products(state,[self.fav,other],'2026-10-29T00:00:00+00:00')
        self.assertEqual(state['nextScanCursor'],1)
        self.assertEqual(state['scanStats']['deferred'],1)
        self.assertNotIn('lastSuccessfulScanAt',state)
        with patch('scanner.monitor.get_page',side_effect=['User-agent: *\nDisallow:',other_page,self.page]) as fetch,patch('scanner.monitor.time.sleep'):
            scan_products(state,[self.fav,other],'2026-10-29T00:15:00+00:00')
        self.assertEqual(fetch.call_args_list[1].args[0],other['url'])
        self.assertEqual(state['scanStats']['succeeded'],2)
        self.assertEqual(state['lastSuccessfulScanAt'],'2026-10-29T00:15:00+00:00')

    def test_config_rejects_duplicate_ids_boolean_target_and_unknown_schema(self):
        valid={'schema':1,'favorites':[copy.deepcopy(self.fav)]}
        self.assertEqual(validate_favorites(valid),valid['favorites'])
        invalid=[{'schema':2,'favorites':[]},{'schema':1,'favorites':[self.fav,self.fav]},
                 {'schema':1,'favorites':[{**self.fav,'targetCents':True}]},
                 {'schema':1,'favorites':[{**self.fav,'enabled':'false'}]}]
        for config in invalid:
            with self.assertRaises(ValueError):validate_favorites(config)

    def test_missing_remote_history_fails_closed_on_existing_data_branch(self):
        storage=GitHubState('unused','owner/repo')
        storage.api=Mock(side_effect=[None,{'object':{'sha':'known'}}])
        with self.assertRaises(RuntimeError):storage.load(b64(bytes(range(32))))
        storage.api=Mock(side_effect=[None,None])
        self.assertEqual(storage.load(b64(bytes(range(32))))['products'],{})

    def test_telegram_outbox_waits_retries_and_never_resends_acknowledged_event(self):
        state={'telegramConfigured':True,'alerts':[{'id':'a','delivery':'pending'},{'id':'b','delivery':'pending'}]}
        storage=Mock()
        with patch.dict('os.environ',{'TELEGRAM_BOT_TOKEN':'unused','TELEGRAM_CHAT_ID':'unused'}),patch('scanner.monitor.telegram_send',side_effect=TelegramError(retry_after=3600)),patch('scanner.monitor.time.sleep'):
            deliver_outbox(state,storage,'unused','2026-10-29T00:00:00+00:00')
        self.assertEqual([e['delivery'] for e in state['alerts']],['pending','pending'])
        self.assertEqual(state['telegramRetryAfter'],'2026-10-29T01:00:00+00:00')
        storage.save.assert_called_once()
        with patch('scanner.monitor.telegram_send') as send:
            deliver_outbox(state,storage,'unused','2026-10-29T00:15:00+00:00')
        send.assert_not_called()
        with patch.dict('os.environ',{'TELEGRAM_BOT_TOKEN':'unused','TELEGRAM_CHAT_ID':'unused'}),patch('scanner.monitor.telegram_send',return_value=123) as send,patch('scanner.monitor.time.sleep'):
            deliver_outbox(state,storage,'unused','2026-10-29T01:15:00+00:00')
            deliver_outbox(state,storage,'unused','2026-10-29T01:30:00+00:00')
        self.assertEqual(send.call_count,2)
        self.assertEqual([e['delivery'] for e in state['alerts']],['sent','sent'])
        self.assertEqual(storage.save.call_count,3)
        self.assertNotIn('notificationError',state)

    def test_telegram_delivery_batch_is_bounded(self):
        state={'telegramConfigured':True,'alerts':[{'id':str(i),'delivery':'pending'} for i in range(80)]}
        with patch.dict('os.environ',{'TELEGRAM_BOT_TOKEN':'unused','TELEGRAM_CHAT_ID':'unused'}),patch('scanner.monitor.telegram_send',return_value=123) as send,patch('scanner.monitor.time.sleep'),patch('scanner.monitor.time.monotonic',return_value=0):
            deliver_outbox(state,Mock(),'unused','2026-10-29T00:00:00+00:00')
        self.assertEqual(send.call_count,50)
        self.assertEqual(sum(e['delivery']=='pending' for e in state['alerts']),30)

    def test_telegram_time_budget_defers_remaining_without_discard(self):
        state={'telegramConfigured':True,'alerts':[{'id':str(i),'delivery':'pending'} for i in range(8)]}
        with patch.dict('os.environ',{'TELEGRAM_BOT_TOKEN':'unused','TELEGRAM_CHAT_ID':'unused'}),patch('scanner.monitor.telegram_send',return_value=123) as send,patch('scanner.monitor.time.sleep'),patch('scanner.monitor.time.monotonic',side_effect=[0,0,51]):
            deliver_outbox(state,Mock(),'unused','2026-10-29T00:00:00+00:00')
        self.assertEqual(send.call_count,1)
        self.assertEqual(sum(e['delivery']=='pending' for e in state['alerts']),7)

    def test_telegram_http429_does_not_leak_token(self):
        event={'name':'Test','oldCents':1990,'newCents':1490,'url':self.fav['url']}
        error=urllib.error.HTTPError('https://api.telegram.org/botSECRET/sendMessage',429,'Too many',{},io.BytesIO(b'{"ok":false,"parameters":{"retry_after":600}}'))
        with patch('scanner.monitor.urllib.request.urlopen',side_effect=error):
            with self.assertRaises(TelegramError) as captured:telegram_send(event,'SECRET','unused')
        self.assertEqual(captured.exception.retry_after,600)
        self.assertNotIn('SECRET',str(captured.exception))

    def test_optional_null_metadata_does_not_hide_valid_price(self):
        self.product.update({'images':None,'representative':None,'colors':None,'sizes':None,'rating':None})
        page='window.__PRELOADED_STATE__ = '+json.dumps({'entity':{'pdpEntity':{self.fav['id']:{'product':self.product}}}})
        product=parse_product(page,self.fav['id'])
        self.assertEqual(product['priceCents'],590)
        self.assertEqual(product['colors'],[])
        self.assertEqual(product['sizes'],[])
        self.assertIsNone(product['image'])
        self.assertIsNone(product['rating'])

    def test_corrupt_cloud_history_is_rejected_before_replacement(self):
        state={'schema':1,'products':{},'alerts':[]}
        p=parse_product(self.page,self.fav['id'])
        observe(state,self.fav,p,'2026-10-29T00:00:00+00:00')
        p['priceCents']=490;observe(state,self.fav,p,'2026-10-29T00:15:00+00:00')
        self.assertIs(validate_state(state),state)
        for field,value in [('priceCents',True),('history',[{'at':'bad','priceCents':100}]),('id','E123456-000-01')]:
            broken=copy.deepcopy(state);broken['products'][self.fav['id']][field]=value
            with self.assertRaises(ValueError):validate_state(broken)
        broken=copy.deepcopy(state);broken['alerts'][0]['url']='https://evil.test'
        with self.assertRaises(ValueError):validate_state(broken)

    def test_run_persists_pending_outbox_before_sending_and_then_acknowledges(self):
        key=b64(bytes(range(32)));state={'schema':1,'products':{},'alerts':[]}
        observe(state,self.fav,parse_product(self.page,self.fav['id']),'2026-10-28T23:45:00+00:00')
        config=Mock();config.exists.return_value=True
        config.read_text.return_value=json.dumps(encrypt({'schema':1,'favorites':[self.fav]},key))
        storage=Mock();storage.load.return_value=state
        snapshots=[];storage.save.side_effect=lambda state,key:snapshots.append(copy.deepcopy(state))
        def send(*args):
            self.assertEqual(snapshots[0]['alerts'][0]['delivery'],'pending')
            return 123
        env={'UA_ENCRYPTION_KEY':key,'GITHUB_TOKEN':'unused','GITHUB_REPOSITORY':'owner/repo','GITHUB_RUN_ID':'123','TELEGRAM_BOT_TOKEN':'unused','TELEGRAM_CHAT_ID':'unused'}
        with patch('sys.argv',['monitor.py']),patch('scanner.monitor.Path',return_value=config),patch('scanner.monitor.GitHubState',return_value=storage),patch.dict('os.environ',env),patch('scanner.monitor.get_page',side_effect=['User-agent: *\nDisallow:',self.page.replace('5.9','4.9')]),patch('scanner.monitor.time.sleep'),patch('scanner.monitor.telegram_send',side_effect=send) as sender,patch('sys.stdout',new=io.StringIO()):
            run()
        sender.assert_called_once()
        self.assertEqual(snapshots[-1]['alerts'][0]['delivery'],'sent')
        self.assertEqual(snapshots[-1]['alerts'][0]['telegramMessageId'],123)

    def test_failed_outbox_persistence_prevents_telegram_send(self):
        key=b64(bytes(range(32)));state={'schema':1,'products':{},'alerts':[]}
        observe(state,self.fav,parse_product(self.page,self.fav['id']),'2026-10-28T23:45:00+00:00')
        config=Mock();config.exists.return_value=True
        config.read_text.return_value=json.dumps(encrypt({'schema':1,'favorites':[self.fav]},key))
        storage=Mock();storage.load.return_value=state;storage.save.side_effect=RuntimeError('Storage unavailable')
        env={'UA_ENCRYPTION_KEY':key,'GITHUB_TOKEN':'unused','GITHUB_REPOSITORY':'owner/repo','GITHUB_RUN_ID':'123','TELEGRAM_BOT_TOKEN':'unused','TELEGRAM_CHAT_ID':'unused'}
        with patch('sys.argv',['monitor.py']),patch('scanner.monitor.Path',return_value=config),patch('scanner.monitor.GitHubState',return_value=storage),patch.dict('os.environ',env),patch('scanner.monitor.get_page',side_effect=['User-agent: *\nDisallow:',self.page.replace('5.9','4.9')]),patch('scanner.monitor.time.sleep'),patch('scanner.monitor.telegram_send') as sender:
            with self.assertRaises(RuntimeError):run()
        sender.assert_not_called()

if __name__=='__main__':unittest.main()
