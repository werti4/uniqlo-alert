import base64
import json
import unittest
from unittest.mock import Mock, patch
from scanner.monitor import b64, decrypt, encrypt
from tools.telegram_commands import process, diagnostics, CommandStore, telegram


def update(uid, text='/logs', chat=123, sender=123, kind='private'):
    return {'update_id':uid,'message':{'text':text,'chat':{'id':chat,'type':kind},'from':{'id':sender}}}


class CommandTests(unittest.TestCase):
    def test_private_owner_only_and_bot_suffix(self):
        send,save=Mock(),Mock()
        messages=[update(1,chat=999),update(2,kind='group'),update(3,sender=999),update(4,'/logs@someone_else'),update(5,'/logs@MyBot'),update(6)]
        self.assertEqual(process(messages,'123','MyBot',None,lambda:'safe',send,save),2)
        self.assertEqual(send.call_count,2)
        self.assertEqual([c.args[0] for c in save.call_args_list],[5,6])

    def test_failed_delivery_remains_pending(self):
        save=Mock()
        with self.assertRaises(RuntimeError):
            process([update(10)],'123','MyBot',9,lambda:'safe',Mock(side_effect=RuntimeError()),save)
        save.assert_not_called()

    def test_processed_updates_not_replied_again(self):
        send,save=Mock(),Mock()
        self.assertEqual(process([update(8),update(9)],'123','MyBot',9,lambda:'safe',send,save),0)
        send.assert_not_called();save.assert_not_called()

    def test_bounded_replies_and_ignored_updates_batched(self):
        save=Mock()
        count=process([update(i) for i in range(1,10)],'123','MyBot',None,lambda:'safe',Mock(),save)
        self.assertEqual(count,3);self.assertEqual(save.call_args.args[0],3)
        save.reset_mock()
        process([update(i,chat=999) for i in range(1,101)],'123','MyBot',None,lambda:'safe',Mock(),save)
        save.assert_called_once_with(100)

    def test_report_does_not_include_arbitrary_private_fields(self):
        state={'lastScanAt':'2026-10-29T01:00:00+00:00','scanStats':{'succeeded':2,'failed':1,'deferred':0},'products':{'secret-product':{'name':'PRIVATE NAME','lastSuccessfulAt':'2026-10-29T00:55:00Z'}},'scanError':'SECRET TOKEN https://private.example','notificationError':'SECRET CHAT','settings':{'key':'SECRET KEY'}}
        runs=[{'id':42,'event':'push','status':'completed','conclusion':'success','created_at':'2026-10-29T01:00:00Z','html_url':'SECRET URL'}]
        text=diagnostics(state,runs,'owner/repo')
        self.assertIn('2 réussis',text);self.assertIn('29/10 01:55:00',text)
        self.assertIn('Aucun lancement planifié',text)
        self.assertIn('https://github.com/owner/repo/actions/runs/42',text)
        for value in ['PRIVATE NAME','SECRET','secret-product','private.example']:self.assertNotIn(value,text)

    def test_missing_data_and_schedule_shown_honestly(self):
        text=diagnostics({},[],'owner/repo',state_ok=False,runs_ok=False)
        self.assertIn('non accessible',text);self.assertIn('Historique Actions indisponible',text)
        text=diagnostics({},[{'id':3,'event':'schedule','status':'completed','conclusion':'failure'}],'owner/repo')
        self.assertIn('planifié · échec',text);self.assertNotIn('Aucun lancement planifié',text)

    def test_cursor_separate_encrypted_file_and_sha(self):
        key=b64(bytes(range(32)));github=Mock();github.api.side_effect=[None,{'content':{'sha':'new'}}]
        store=CommandStore(github,key);self.assertIsNone(store.load());store.save(7)
        path,method,payload=github.api.call_args.args
        self.assertEqual(path,'/contents/data/telegram-commands.enc.json');self.assertEqual(method,'PUT')
        self.assertEqual(payload['branch'],'monitor-data');self.assertNotIn('sha',payload)
        self.assertEqual(decrypt(json.loads(base64.b64decode(payload['content'])),key),{'schema':1,'lastUpdateId':7})
        github.api.side_effect=None;github.api.return_value={'sha':'old','content':base64.b64encode(json.dumps(encrypt({'schema':1,'lastUpdateId':7},key)).encode()).decode()}
        self.assertEqual(store.load(),7)
        github.api.return_value={'content':{'sha':'newer'}};store.save(8)
        self.assertEqual(github.api.call_args.args[2]['sha'],'old')

    def test_cloudflare_dispatch_is_not_misreported_as_manual_or_missing_github_schedule(self):
        runs=[{'id':42,'event':'workflow_dispatch','status':'completed','conclusion':'success'}]
        text=diagnostics({},runs,'owner/repo',webhook_mode=True)
        self.assertIn('dispatch (Cloudflare ou manuel)',text)
        self.assertIn('vérifier les événements scheduled',text.lower())
        self.assertNotIn('Aucun lancement planifié',text)

    def test_token_not_exposed_on_network_error(self):
        with patch('urllib.request.urlopen',side_effect=RuntimeError('https://api.telegram.org/botSECRET/sendMessage')):
            with self.assertRaises(RuntimeError) as error:telegram('SECRET','getUpdates',{})
        self.assertNotIn('SECRET',str(error.exception))

class WebhookUpdatesTests(unittest.TestCase):
    def test_trusted_queue_rebuilt_without_freeform_messages(self):
        from tools.telegram_commands import webhook_updates
        updates=webhook_updates({'commands':[{'id':9,'command':'/scan'}]},'123')
        scan=Mock()
        process(updates,'123','bot',None,lambda:'safe',Mock(),Mock(),scan=scan)
        scan.assert_called_once()
        for payload in [{'commands':[{'id':9,'command':'/unknown'}]},{'commands':[{'id':True,'command':'/scan'}]},{'commands':[{'id':1,'command':'/logs'}]*4}]:
            with self.assertRaises(ValueError):webhook_updates(payload,'123')

    def test_bridge_requires_https_and_hides_errors(self):
        from tools.telegram_commands import bridge
        with self.assertRaises(ValueError):bridge('http://example','secret','pending',{})
        with patch('urllib.request.urlopen',side_effect=RuntimeError('PRIVATE')):
            with self.assertRaises(RuntimeError) as error:bridge('https://example','secret','pending',{})
        self.assertNotIn('PRIVATE',str(error.exception))

class CatalogueTests(unittest.TestCase):
    def test_every_cloudflare_command_has_a_backend_handler(self):
        from tools.telegram_commands import COMMANDS, load_catalogue
        self.assertEqual(COMMANDS,load_catalogue())
        for name,definition in COMMANDS.items():
            send,scan=Mock(),Mock()
            count=process([update(1,'/'+name)],'123','bot',None,lambda:'safe',send,Mock(),scan=scan,favorites=lambda:['safe list'])
            self.assertEqual(count,1)
            self.assertEqual(scan.called,definition['handler']=='scan')
            self.assertTrue(send.called)

    def test_unsupported_handler_cannot_be_silently_deployed(self):
        from tools.telegram_commands import load_catalogue
        with patch('pathlib.Path.read_text',return_value='[{"name":"future","handler":"forgotten"}]'):
            with self.assertRaises(ValueError):load_catalogue()
