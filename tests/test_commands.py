import pytest
from unittest.mock import MagicMock
import configparser
from commands import (
    AddSectionCommand, DeleteSectionCommand, 
    AddKeyCommand, DeleteKeyCommand,
    ChangeValueCommand, RenameSectionCommand
)

@pytest.fixture
def mock_editor():
    editor = MagicMock()
    editor.config = configparser.ConfigParser(interpolation=None, strict=False)
    editor.tree = MagicMock()
    editor.value_editor = MagicMock()
    editor.current_item = None
    return editor

def test_add_section_command(mock_editor):
    cmd = AddSectionCommand(mock_editor, "NewSection")
    
    cmd.redo()
    assert mock_editor.config.has_section("NewSection")
    assert mock_editor.update_tree.called
    
    cmd.undo()
    assert not mock_editor.config.has_section("NewSection")

def test_delete_section_command(mock_editor):
    mock_editor.config.add_section("ToDelete")
    mock_editor.config.set("ToDelete", "Key", "Val")
    
    cmd = DeleteSectionCommand(mock_editor, "ToDelete")
    
    cmd.redo()
    assert not mock_editor.config.has_section("ToDelete")
    
    cmd.undo()
    assert mock_editor.config.has_section("ToDelete")
    assert mock_editor.config.get("ToDelete", "Key") == "Val"

def test_add_key_command(mock_editor):
    mock_editor.config.add_section("Sec")
    cmd = AddKeyCommand(mock_editor, "Sec", "NewKey", "Val")
    
    cmd.redo()
    assert mock_editor.config.get("Sec", "NewKey") == "Val"
    
    cmd.undo()
    assert not mock_editor.config.has_option("Sec", "NewKey")

def test_change_value_command(mock_editor):
    mock_editor.config.add_section("Sec")
    mock_editor.config.set("Sec", "Key", "Old")
    
    # ChangeValueCommand espera que certas estruturas existam no mock_editor.tree
    # para o sync_ui funcionar, mas como estamos testando a lógica do config,
    # podemos apenas verificar se o config foi alterado.
    cmd = ChangeValueCommand(mock_editor, "Sec", "Key", "Old", "New")
    
    cmd.redo()
    assert mock_editor.config.get("Sec", "Key") == "New"
    
    cmd.undo()
    assert mock_editor.config.get("Sec", "Key") == "Old"

def test_rename_section_command(mock_editor):
    mock_editor.config.add_section("OldName")
    mock_editor.config.set("OldName", "Key", "Val")
    
    cmd = RenameSectionCommand(mock_editor, "OldName", "NewName")
    
    cmd.redo()
    assert not mock_editor.config.has_section("OldName")
    assert mock_editor.config.get("NewName", "Key") == "Val"
    
    cmd.undo()
    assert mock_editor.config.has_section("OldName")
    assert not mock_editor.config.has_section("NewName")
    assert mock_editor.config.get("OldName", "Key") == "Val"
