import json
import unittest
from unittest.mock import Mock, patch
from scanner.monitor import b64, encrypt
from tools.telegram_commands import process
from tools.telegram_scan import execute, results

AT = '2026-10-29T12:00:00+00:00'
FAV = {'id':'E479219-000-01','url':'https://www.uniqlo.com/fr/fr/products/E479219-000/01','enabled':True,'name':'Pull bleu'}

def product(price=1990, base=2990, at=AT):
    return {'id':FAV['id'],'name':FAV['name'],'priceCents':price,'regularCents':base,'status':'ok','lastSuccessfulAt':at}

def command(uid, chat=123):
    return {'update_id':uid,'message':{'text':'/scan','chat':{'id':chat,'type':'private'},'from':{'id':chat}}}


class ScanCommandTests(unittest.TestCase):
    def test_scan_consumed_before_execution_and_only_once_per_pass(self):
        events=[]
        process([command(1,999),command(2),command(3)],'123','mybot',None,lambda:'logs',lambda text:events.append(text),lambda uid:events.append(uid),scan=lambda:events.append('execute'))
        self.assertEqual(events[0],2)
        self.assertIn('Scan en cours',events[1]);self.assertEqual(events[2],'execute')
        self.assertEqual(events.count('execute'),1)

    def test_consumed_scan_not_replayed_if_start_message_fails(self):
        saved=[];scan=Mock()
        with self.assertRaises(RuntimeError):
            process([command(2)],'123','bot',None,lambda:'logs',Mock(side_effect=RuntimeError()),saved.append,scan=scan)
        self.assertEqual(saved,[2]);scan.assert_not_called()
        process([command(2)],'123','bot',2,lambda:'logs',Mock(),saved.append,scan=scan)
        scan.assert_not_called()

    def test_current_promotions_include_first_observation(self):
        text='\n'.join(results({'products':{FAV['id']:product()}},[FAV],AT))
        self.assertIn('Pull bleu',text);self.assertIn('19,90 € au lieu de 29,90 €',text)
        self.assertIn('1 article(s)',text)

    def test_no_promo_only_after_complete_fresh_verification(self):
        text='\n'.join(results({'products':{FAV['id']:product(2990)}},[FAV],AT))
        self.assertIn('Aucun article en promo',text)
        for p in [product(at='2026-10-28T12:00:00+00:00'),product(base=None),{**product(),'status':'error'}]:
            text='\n'.join(results({'products':{FAV['id']:p}},[FAV],AT))
            self.assertNotIn('Aucun article en promo',text)
            self.assertNotIn('Pull bleu',text)
            self.assertIn('Impossible de conclure',text)

    def test_paused_and_empty_favorites(self):
        text='\n'.join(results({'products':{FAV['id']:product()}},[{**FAV,'enabled':False}],AT))
        self.assertIn('Aucun favori actif',text)
        self.assertNotIn('Pull bleu',text)

    def test_scan_uses_existing_engine_and_persists_before_reporting(self):
        key=b64(bytes(range(32)));send=Mock();store=Mock()
        state={'schema':1,'products':{},'alerts':[]};store.load.return_value=state
        def scan(s, favorites, at):
            s['products']={FAV['id']:product(at=at)};s['scanStats']={'succeeded':1,'failed':0,'deferred':0}
        env={'UA_ENCRYPTION_KEY':key,'GITHUB_TOKEN':'synthetic','GITHUB_REPOSITORY':'owner/repo','GITHUB_RUN_ID':'42'}
        with patch.dict('os.environ',env), patch('tools.telegram_scan.Path.read_text',return_value=json.dumps(encrypt({'schema':1,'favorites':[FAV]},key))), patch('tools.telegram_scan.monitor.GitHubState',return_value=store), patch('tools.telegram_scan.monitor.now',return_value=AT), patch('tools.telegram_scan.monitor.scan_products',side_effect=scan) as engine:
            execute(send)
        engine.assert_called_once();store.save.assert_called_once_with(state,key)
        self.assertEqual(state['persistedAt'],AT)
        self.assertEqual(send.call_args_list[0].args[0],'✅ Scan terminé.')
        self.assertIn('Pull bleu','\n'.join(c.args[0] for c in send.call_args_list))

    def test_failure_reports_error_without_secrets_or_false_no_promo(self):
        send=Mock()
        with patch('tools.telegram_scan.Path.read_text',side_effect=RuntimeError('PRIVATE TOKEN')), patch.dict('os.environ',{'UA_ENCRYPTION_KEY':'synthetic'}):
            execute(send)
        text=send.call_args.args[0]
        self.assertIn('erreur',text);self.assertNotIn('PRIVATE',text);self.assertNotIn('Aucun article en promo',text)
