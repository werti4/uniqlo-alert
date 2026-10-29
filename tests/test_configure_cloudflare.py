import contextlib
import io
import json
import unittest
from unittest.mock import MagicMock, patch
from tools.configure_cloudflare import run, ROOT

ENV={'GITHUB_REPOSITORY':'werti4/uniqlo-alert','GITHUB_REF':'refs/heads/main','UA_TELEGRAM_ENABLED':'true','UA_TELEGRAM_WEBHOOK_URL':ROOT,'UA_TELEGRAM_WEBHOOK_SECRET':'s'*64,'TELEGRAM_BOT_TOKEN':'private-token','TELEGRAM_CHAT_ID':'123'}

class ConfigureTests(unittest.TestCase):
    def test_missing_or_wrong_configuration_stops_before_network(self):
        for changes in [{'UA_TELEGRAM_WEBHOOK_SECRET':''},{'UA_TELEGRAM_WEBHOOK_URL':'https://wrong.example'},{'UA_TELEGRAM_ENABLED':'false'},{'GITHUB_REF':'refs/heads/other'}]:
            with patch.dict('os.environ',{**ENV,**changes},clear=True),patch('urllib.request.urlopen') as net:
                with self.assertRaises(ValueError):run()
                net.assert_not_called()

    def test_registration_sends_only_proof_not_telegram_token_and_logs_only_safe_fields(self):
        response=MagicMock();response.__enter__.return_value.read.return_value=json.dumps({'ok':True,'webhook_confirmed':True,'private':'private-token'}).encode()
        output=io.StringIO()
        with patch.dict('os.environ',ENV,clear=True),patch('urllib.request.urlopen',return_value=response) as net,contextlib.redirect_stdout(output):
            run();req=net.call_args.args[0]
            self.assertEqual(req.full_url,ROOT+'/configure')
            self.assertNotIn(b'private-token',req.data)
            self.assertNotIn('private-token',output.getvalue())

    def test_readonly_hourly_check_does_not_register_or_scan(self):
        response=MagicMock();response.__enter__.return_value.read.return_value=b'{"ok":true,"webhook_confirmed":true,"lastHourlyDispatch":42}'
        with patch.dict('os.environ',{**ENV,'VERIFY_ONLY':'true','VERIFY_HOUR':'42'},clear=True),patch('urllib.request.urlopen',return_value=response) as net,contextlib.redirect_stdout(io.StringIO()):
            run();self.assertEqual(net.call_args.args[0].full_url,ROOT+'/configuration-status')
        with patch.dict('os.environ',{**ENV,'VERIFY_ONLY':'true','VERIFY_HOUR':'43'},clear=True),patch('urllib.request.urlopen',return_value=response):
            with self.assertRaises(ValueError):run()

    def test_invalid_format_reports_only_category_not_value(self):
        for value, category in [('short-private', 'trop court'), ('x'*257, 'trop long'), ('a'*40+':', 'caractères non autorisés')]:
            with patch.dict('os.environ', {**ENV, 'UA_TELEGRAM_WEBHOOK_SECRET':value}, clear=True), patch('urllib.request.urlopen') as net:
                with self.assertRaises(ValueError) as error: run()
                self.assertIn(category, str(error.exception))
                self.assertNotIn(value, str(error.exception))
                net.assert_not_called()

    def test_network_error_never_discloses_tokens(self):
        with patch.dict('os.environ',ENV,clear=True),patch('urllib.request.urlopen',side_effect=RuntimeError('private-token')):
            with self.assertRaises(ValueError) as error:run()
            self.assertNotIn('private-token',str(error.exception))
