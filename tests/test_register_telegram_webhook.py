"""Setup must not scan, send test messages or expose credential-bearing errors."""
import contextlib
import io
import json
import unittest
from unittest.mock import patch

from tools import register_telegram_webhook as setup

URL = 'https://example.workers.dev'
SECRET = 's' * 64
INFO = {'url': URL + '/telegram', 'allowed_updates': ['message'], 'max_connections': 1, 'pending_update_count': 0}


class SetupTests(unittest.TestCase):
    def invoke(self, args, api):
        output = io.StringIO()
        with patch('sys.argv', ['setup'] + args), patch.object(setup.getpass, 'getpass', side_effect=['synthetic-token', SECRET]), patch('builtins.input', return_value=URL), patch.object(setup, 'api', side_effect=api), contextlib.redirect_stdout(output):
            code = setup.main()
        return code, output.getvalue()

    def test_check_is_read_only_and_does_not_print_private_errors(self):
        calls = []
        def api(token, method, payload):
            calls.append(method)
            return {**INFO, 'last_error_message': 'private synthetic-token'}
        code, output = self.invoke(['--check'], api)
        self.assertEqual(code, 0)
        self.assertEqual(calls, ['getWebhookInfo'])
        self.assertNotIn('private', output)
        self.assertNotIn('synthetic-token', output)

    def test_register_preserves_pending_and_uses_official_secret(self):
        calls = []
        def api(token, method, payload):
            calls.append((method, payload))
            return INFO if method == 'getWebhookInfo' else True
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({'commands': []}).encode()
        with patch.object(setup.urllib.request, 'urlopen', return_value=response):
            code, _ = self.invoke([], api)
        self.assertEqual(code, 0)
        self.assertEqual([method for method, _ in calls], ['setWebhook', 'getWebhookInfo'])
        self.assertEqual(calls[0][1], {'url': URL + '/telegram', 'secret_token': SECRET, 'allowed_updates': ['message'], 'max_connections': 1, 'drop_pending_updates': False})

    def test_check_rejects_wrong_url_and_errors_are_sanitized(self):
        code, _ = self.invoke(['--check'], lambda *args: {**INFO, 'url': URL + '/wrong'})
        self.assertEqual(code, 1)
        code, output = self.invoke(['--check'], lambda *args: (_ for _ in ()).throw(RuntimeError('synthetic-token')))
        self.assertEqual(code, 1)
        self.assertNotIn('synthetic-token', output)

    def test_remove_preserves_pending_updates(self):
        calls = []
        def api(token, method, payload):
            calls.append((method, payload))
            return True
        code, _ = self.invoke(['--remove'], api)
        self.assertEqual(code, 0)
        self.assertEqual(calls, [('deleteWebhook', {'drop_pending_updates': False})])


if __name__ == '__main__':
    unittest.main()
