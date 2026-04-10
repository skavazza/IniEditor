import pytest
import configparser
from utils import merge_config_with_raw

def test_merge_preserves_comments():
    raw_lines = [
        "; Comentario inicial\n",
        "[Section1]\n",
        "Key1=Value1\n",
        "; Comentario no meio\n",
        "Key2=Value2\n"
    ]
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.read_string("".join(raw_lines))
    
    # Modificar um valor
    config.set("Section1", "key1", "NewValue")
    
    result = merge_config_with_raw(raw_lines, config)
    
    assert "; Comentario inicial\n" in result
    assert "; Comentario no meio\n" in result
    assert "Key1= NewValue\n" in result
    assert "Key2= Value2\n" in result

def test_merge_adds_new_section():
    raw_lines = [
        "[Section1]\n",
        "Key1=Value1\n"
    ]
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.read_string("".join(raw_lines))
    
    config.add_section("NewSection")
    config.set("NewSection", "NewKey", "NewVal")
    
    result = merge_config_with_raw(raw_lines, config)
    
    assert "[NewSection]" in result
    assert "newkey=NewVal" in result # configparser minuscula chaves por padrao

def test_merge_deletes_key():
    raw_lines = [
        "[Section1]\n",
        "Key1=Value1\n",
        "Key2=Value2\n"
    ]
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.read_string("".join(raw_lines))
    
    config.remove_option("Section1", "key1")
    
    result = merge_config_with_raw(raw_lines, config)
    
    assert "Key1" not in result
    assert "Key2= Value2" in result

def test_merge_deletes_section():
    raw_lines = [
        "; Global comment\n",
        "[Section1]\n",
        "Key1=Value1\n",
        "; Section 1 comment\n",
        "[Section2]\n",
        "Key2=Value2\n"
    ]
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.read_string("".join(raw_lines))
    
    config.remove_section("Section1")
    
    result = merge_config_with_raw(raw_lines, config)
    
    assert "[Section1]" not in result
    assert "Key1=Value1" not in result
    assert "; Section 1 comment" not in result # Comentários dentro da seção deletada somem (comportamento esperado atual)
    assert "[Section2]" in result
    assert "; Global comment" in result
