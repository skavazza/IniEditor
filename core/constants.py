"""
Global constants for the Rainmeter IDE.
"""

SUPPORTED_ENCODINGS = [
    ('utf-8-sig', 'UTF-8 com BOM'),
    ('utf-8', 'UTF-8'),
    ('utf-16', 'UTF-16'),
    ('utf-16-le', 'UTF-16 Little Endian'),
    ('utf-16-be', 'UTF-16 Big Endian'),
    ('cp1252', 'ANSI (Windows-1252)'),
    ('latin-1', 'Latin-1'),
]

DEFAULT_ENCODING = 'utf-8-sig'
VAR_FILE_ENCODING = 'utf-8'

# Lista abrangente de chaves comuns do Rainmeter para autocomplete
AUTOCOMPLETE_KEYS = [
    # Gerais
    "Meter", "Measure", "X", "Y", "W", "H", "Padding", "AntiAlias", "DynamicVariables",
    "UpdateDivider", "Group", "Hidden", "SolidColor", "SolidColor2", "GradientAngle",
    "BevelType", "TransformationMatrix", "MaskImageName", "UpdateRange",
    
    # String Meter
    "Text", "FontFace", "FontSize", "FontColor", "FontWeight", "StringAlign",
    "StringStyle", "StringCase", "ClipString", "Angle", "InlineSetting",
    "InlinePattern", "ClipStringW", "ClipStringH", "ToolTipText", "ToolTipTitle",
    
    # Image Meter
    "ImageName", "ImageAlpha", "ImageTint", "GreyScale", "ImageRotate",
    "PreserveAspectRatio", "Tile", "ImageCrop", "ImageFlip",
    
    # Shape Meter
    "Shape", "Shape2", "Shape3", "Active", "MyPath",
    
    # Bar / Roundline / Histogram / Line
    "BarColor", "BarOrientation", "BarBorder", "Flip", "MeasureName",
    "MeasureName2", "MeasureName3", "StartAngle", "RotationAngle", "LineColor",
    "LineWidth", "GraphStart", "GraphOrientation", "PrimaryColor", "SecondaryColor",
    
    # Button Meter
    "ButtonImage", "ButtonCommand",
    
    # Measures Gerais
    "Measure", "Type", "Disabled", "InvertMeasure", "MaxValue", "MinValue",
    "AverageSize", "Substitute", "RegExp", "URL", "StringIndex",
    
    # Ações / Eventos
    "OnUpdateAction", "OnChangeAction", "IfCondition", "IfTrueAction", "IfFalseAction",
    "IfMatch", "IfMatchAction", "IfBelowValue", "IfBelowAction", "IfAboveValue",
    "IfAboveAction", "IfEqualValue", "IfEqualAction",
    "LeftMouseUpAction", "LeftMouseDownAction", "RightMouseUpAction", "RightMouseDownAction",
    "MouseOverAction", "MouseLeaveAction", "MiddleMouseUpAction", "ScrollUpAction", "ScrollDownAction"
]
