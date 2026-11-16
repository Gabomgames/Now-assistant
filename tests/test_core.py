import unittest
from unittest.mock import patch
from now_engine.core import offline_command, route

class CoreTests(unittest.TestCase):
    def test_greeting(self):
        self.assertIn('NOW', offline_command('olá'))
    def test_time(self):
        self.assertIn('Agora são', offline_command('horas'))
    def test_date(self):
        self.assertIn('Hoje é', offline_command('data'))
    def test_offline_priority(self):
        with patch('now_engine.core.local_reply') as local:
            self.assertEqual(route('oi')['provider'], 'offline')
            local.assert_not_called()
    def test_local_priority(self):
        with patch('now_engine.core.local_reply', return_value='Tudo certo'):
            self.assertEqual(route('Minecraft')['provider'], 'local')
    def test_fallback_disabled(self):
        with patch('now_engine.core.local_reply', side_effect=OSError('offline')):
            with patch.dict('os.environ', {'ENABLE_GEMINI_FALLBACK': 'false'}):
                self.assertEqual(route('Minecraft')['provider'], 'unavailable')

if __name__ == '__main__':
    unittest.main()
