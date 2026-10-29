import contextlib
import io
import json
import unittest
import urllib.error
from unittest.mock import patch, Mock

from tools.telegram_check import check, main, SetupError


class TelegramSetupTests(unittest.TestCase):
    def test_private_chat_and_bot_verified_before_send(self):
        replies = [
            {"ok": True, "result": {"is_bot": True}},
            {"ok": True, "result": {"id": 12345, "type": "private"}},
            {"ok": True, "result": {"message_id": 9, "chat": {"id": 12345}}},
        ]
        requests = []
        def respond(request, timeout):
            requests.append(request)
            response = Mock()
            response.__enter__ = Mock(return_value=io.StringIO(json.dumps(replies.pop(0))))
            response.__exit__ = Mock(return_value=False)
            return response
        with patch('urllib.request.urlopen', side_effect=respond):
            check('123:synthetic_token', '12345')
        self.assertEqual([r.full_url.rsplit('/', 1)[-1] for r in requests], ['getMe', 'getChat', 'sendMessage'])
        body = json.loads(requests[-1].data)
        self.assertIn('message de test', body['text'])
        self.assertIn('aucune baisse', body['text'])
        self.assertEqual(body['chat_id'], '12345')

    def test_missing_secrets_do_not_send_any_request(self):
        with patch('urllib.request.urlopen') as send:
            for token, chat in [('', '123'), ('123:synthetic', ''), ('123:synthetic', '-100123'), ('123:synthetic', '@channel')]:
                with self.assertRaises(SetupError): check(token, chat)
            send.assert_not_called()

    def test_group_or_wrong_identity_cannot_receive_test(self):
        for chat in [{'id':12345,'type':'group'}, {'id':54321,'type':'private'}]:
            with patch('tools.telegram_check.api', side_effect=[{'is_bot':True},chat]) as api:
                with self.assertRaises(SetupError): check('123:synthetic', '12345')
                self.assertEqual(api.call_count, 2)

    def test_api_errors_cannot_leak_token_or_chat(self):
        error = urllib.error.HTTPError('https://api.telegram.org/bot123:synthetic_token/getMe', 401, 'synthetic_token', {}, None)
        output = io.StringIO()
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN':'123:synthetic_token','TELEGRAM_CHAT_ID':'12345'}), patch('urllib.request.urlopen', side_effect=error), contextlib.redirect_stderr(output):
            self.assertEqual(main(), 1)
        self.assertNotIn('synthetic_token', output.getvalue())
        self.assertNotIn('12345', output.getvalue())
        self.assertIn('Jeton refusé', output.getvalue())

    def test_unconfirmed_send_is_not_reported_successful(self):
        with patch('tools.telegram_check.api', side_effect=[{'is_bot':True},{'id':12345,'type':'private'},{}]):
            with self.assertRaises(SetupError): check('123:synthetic','12345')
