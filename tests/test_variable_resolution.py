import pytest
import os
from utils import resolve_rainmeter_variables, resolve_variable_references

def test_resolve_simple_variables():
    resolved_vars = {
        "color": "255,255,255",
        "size": "12"
    }
    props = {
        "fontcolor": "#Color#",
        "fontsize": "#Size#",
        "text": "Hello World"
    }
    
    result = resolve_rainmeter_variables(props, resolved_vars)
    
    assert result["fontcolor"] == "255,255,255"
    assert result["fontsize"] == "12"
    assert result["text"] == "Hello World"

def test_resolve_recursive_variables():
    resolved_vars = {
        "base_color": "255,0,0",
        "my_color": "#Base_Color#",
        "final_color": "#My_Color#,255"
    }
    # resolve_variable_references é necessário antes de passar para resolve_rainmeter_variables
    # se quisermos testar a resolução em cadeia das próprias variáveis.
    from utils import resolve_variable_references
    resolved_vars = resolve_variable_references(resolved_vars)
    
    props = {
        "color": "#Final_Color#"
    }
    
    result = resolve_rainmeter_variables(props, resolved_vars)
    assert result["color"] == "255,0,0,255"

def test_resolve_resources_dir():
    resources_dir = "C:\\Rainmeter\\Skins\\MySkin\\@Resources"
    resolved_vars = {}
    props = {
        "fontface": "#@#Fonts\\MyFont.ttf",
        "imagename": "#@#Images\\Logo.png"
    }
    
    result = resolve_rainmeter_variables(props, resolved_vars, resources_dir=resources_dir)
    
    # Nota: os.sep pode ser \ no Windows
    expected_font = os.path.join(resources_dir, "Fonts\\MyFont.ttf")
    assert result["fontface"] == expected_font

def test_resolve_nested_references():
    variables = {
        "a": "1",
        "b": "#a#",
        "c": "#b#",
        "d": "#c#"
    }
    resolved = resolve_variable_references(variables)
    assert resolved["d"] == "1"

def test_resolve_case_insensitivity():
    resolved_vars = {
        "myvar": "success"
    }
    props = {
        "test": "#MyVar#"
    }
    result = resolve_rainmeter_variables(props, resolved_vars)
    assert result["test"] == "success"
