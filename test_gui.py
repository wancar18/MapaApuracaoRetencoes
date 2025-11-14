import unittest
from unittest.mock import patch
from gui import App

class TestGUI(unittest.TestCase):
    @patch('tkinter.Tk.__init__', return_value=None)
    def test_app_initialization(self, mock_tk_init):
        # We need to mock the methods that are called in App.__init__
        with patch('tkinter.Tk.title') as mock_title, \
             patch('tkinter.Tk.geometry') as mock_geometry, \
             patch('tkinter.Label') as mock_label, \
             patch('tkinter.Button') as mock_button:
            app = App()
            self.assertIsNotNone(app)
            mock_tk_init.assert_called_once()

if __name__ == '__main__':
    unittest.main()
