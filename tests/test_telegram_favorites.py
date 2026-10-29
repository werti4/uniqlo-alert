import base64
import datetime as dt
import json
import unittest
from unittest.mock import Mock
from scanner.monitor import b64, encrypt
from tools.telegram_commands import process
from tools.telegram_favorites import render, messages

FAV={'id':'E479219-000-01','url':'https://www.uniqlo.com/fr/fr/products/E479219-000/01','name':'Pull bleu','enabled':True}
NOW=dt.datetime(2026,10,29,12,tzinfo=dt.timezone.utc)

class FavoritesTests(unittest.TestCase):
    def test_red_promotion_price_and_pause_included(self):
        state={'products':{FAV['id']:{'priceCents':1990,'regularCents':2990,'lastSuccessfulAt':'2026-10-29T11:55:00Z'}}}
        text='\n'.join(render([{**FAV,'enabled':False}],state,now=NOW))
        self.assertIn('🔴 1. Pull bleu · En pause',text)
        self.assertIn('19,90 € au lieu de 29,90 €',text)
        self.assertIn('29/10 12:55',text)
        self.assertNotIn('ancien',text)

    def test_missing_prices_and_old_errors_not_invented(self):
        text='\n'.join(render([FAV],{},now=NOW));self.assertIn('⚫',text);self.assertIn('Prix indisponible',text);self.assertNotIn('0,00',text)
        text='\n'.join(render([FAV],{'products':{FAV['id']:{'priceCents':1990,'regularCents':1990,'lastSuccessfulAt':'2026-10-28T12:00:00Z','status':'error','error':'PRIVATE TOKEN'}}},now=NOW))
        self.assertIn('⚪',text);self.assertNotIn('🔴 1.',text);self.assertIn('ancien',text);self.assertIn('dernier prix valide conservé',text);self.assertNotIn('PRIVATE',text)

    def test_fifty_favorites_paginated_without_loss(self):
        favorites=[{**FAV,'name':f'Article {i:02d} '+('x'*180)} for i in range(50)]
        parts=render(favorites,{},now=NOW)
        self.assertGreater(len(parts),1);self.assertTrue(all(len(part)<=3500 for part in parts))
        for i in range(50):self.assertEqual('\n'.join(parts).count(f'Article {i:02d} '),1)

    def test_empty_list_distinct_from_read_error(self):
        self.assertIn('aucun favori publié',render([],{},now=NOW)[0])
        github=Mock();github.api.side_effect=RuntimeError('PRIVATE TOKEN')
        text=messages(github,'synthetic')[0]
        self.assertIn('Impossible de lire',text);self.assertNotIn('aucun favori',text);self.assertNotIn('PRIVATE',text)

    def test_decrypted_published_list_retained_when_state_unavailable(self):
        key=b64(bytes(range(32)));github=Mock()
        github.api.return_value={'content':base64.b64encode(json.dumps(encrypt({'schema':1,'favorites':[FAV]},key)).encode()).decode()}
        github.load.side_effect=RuntimeError('PRIVATE TOKEN')
        text='\n'.join(messages(github,key))
        self.assertIn('Pull bleu',text);self.assertIn('Relevés non accessibles',text);self.assertNotIn('PRIVATE',text)
        github.save.assert_not_called()

    def test_private_command_only_and_no_scan(self):
        def update(chat,sender,text):return {'update_id':chat,'message':{'chat':{'type':'private','id':chat},'from':{'id':sender},'text':text}}
        read,send,scan,save=Mock(return_value=['page 1','page 2']),Mock(),Mock(),Mock()
        self.assertEqual(process([{**update(999,999,'/favoris'),'update_id':1},{**update(123,123,'/favoris@MyBot'),'update_id':2}],'123','MyBot',None,lambda:'logs',send,save,scan=scan,favorites=read),1)
        read.assert_called_once();scan.assert_not_called();self.assertEqual(send.call_count,2)
        self.assertEqual(save.call_args.args[0],2)
