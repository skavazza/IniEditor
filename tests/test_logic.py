import unittest
import os
import shutil
import tempfile
from logic import (
    find_variables_file, find_resources_dir, find_inc_files,
    create_backup, create_new_skin, add_skin_to_project
)

class TestLogic(unittest.TestCase):
    def setUp(self):
        # Criar um diretório temporário para os testes de arquivo
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remover o diretório temporário após os testes
        shutil.rmtree(self.test_dir)

    def test_find_resources_dir(self):
        # Setup: pasta/skin.ini e pasta/@Resources
        skin_path = os.path.join(self.test_dir, "MySkin", "Skin.ini")
        resources_path = os.path.join(self.test_dir, "MySkin", "@Resources")
        os.makedirs(os.path.dirname(skin_path))
        os.makedirs(resources_path)
        with open(skin_path, "w") as f: f.write("")

        found = find_resources_dir(skin_path)
        self.assertEqual(os.path.normpath(found), os.path.normpath(resources_path))

    def test_find_variables_file(self):
        # Setup: pasta/@Resources/Variables.inc
        skin_path = os.path.join(self.test_dir, "MySkin", "Skin.ini")
        resources_path = os.path.join(self.test_dir, "MySkin", "@Resources")
        var_file = os.path.join(resources_path, "Variables.inc")
        os.makedirs(resources_path)
        with open(var_file, "w") as f: f.write("[Variables]")
        
        # O find_variables_file costuma subir na árvore até achar @Resources
        found = find_variables_file(skin_path)
        self.assertEqual(os.path.normpath(found), os.path.normpath(var_file))

    def test_create_backup(self):
        file_to_back = os.path.join(self.test_dir, "test.txt")
        with open(file_to_back, "w") as f: f.write("original")
        
        success = create_backup(file_to_back)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(file_to_back + ".bak"))
        with open(file_to_back + ".bak", "r") as f:
            self.assertEqual(f.read(), "original")

    def test_create_new_skin(self):
        skin_name = "TestNewSkin"
        success, ini_path = create_new_skin(self.test_dir, skin_name, author="Tester")
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(ini_path))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, skin_name, "@Resources")))
        
        with open(ini_path, "r", encoding='utf-8') as f:
            content = f.read()
            self.assertIn(f"Name={skin_name}", content)
            self.assertIn("Author=Tester", content)

    def test_add_skin_to_project(self):
        # Setup: criar um projeto base primeiro
        project_name = "MyProject"
        project_path = os.path.join(self.test_dir, project_name)
        os.makedirs(project_path)
        os.makedirs(os.path.join(project_path, "@Resources"))
        
        # Testar adicionar skin ao projeto
        skin_name = "SubSkin"
        success, ini_path = add_skin_to_project(project_path, skin_name, author="Tester")
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(ini_path))
        self.assertIn(skin_name, ini_path)
        
        with open(ini_path, "r", encoding='utf-8') as f:
            content = f.read()
            self.assertIn(f"Name={skin_name}", content)
            self.assertIn("Author=Tester", content)

if __name__ == '__main__':
    unittest.main()
