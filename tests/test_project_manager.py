import unittest
import os
import shutil
import tempfile
from project_manager import save_project_json, load_project_json

class TestProjectManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_save_load_project(self):
        file_path = os.path.join(self.test_dir, "test.rmproject")
        state = {
            "version": "1.0",
            "last_opened_ini": "C:/path/to/skin.ini",
            "dark_mode": True
        }
        
        # Test Save
        success, message = save_project_json(file_path, state)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(file_path))
        
        # Test Load
        success, result = load_project_json(file_path)
        self.assertTrue(success)
        self.assertEqual(result["version"], "1.0")
        self.assertEqual(result["last_opened_ini"], "C:/path/to/skin.ini")
        self.assertEqual(result["dark_mode"], True)

    def test_load_non_existent(self):
        file_path = os.path.join(self.test_dir, "ghost.rmproject")
        success, result = load_project_json(file_path)
        self.assertFalse(success)
        self.assertEqual(result, "Arquivo não encontrado.")

    def test_load_invalid_json(self):
        file_path = os.path.join(self.test_dir, "invalid.rmproject")
        with open(file_path, "w") as f:
            f.write("not a json")
            
        success, result = load_project_json(file_path)
        self.assertFalse(success)
        self.assertIn("Erro ao ler o projeto", result)

if __name__ == '__main__':
    unittest.main()
