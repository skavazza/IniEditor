from PyQt6.QtWidgets import QTextEdit, QCompleter
from PyQt6.QtCore import Qt, pyqtSignal

class RainmeterEdit(QTextEdit):
    focused = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.completer = None
        self.keywords = self.KEYWORDS # Initialize keywords here
        self.init_completer() # Call init_completer here

    KEYWORDS = [
        # === Seções comuns ===
        "[Rainmeter]", "[Variables]", "[Metadata]", "[MeterStyles]",

        # === Meters (tipos) ===
        "Meter=String", "Meter=Image", "Meter=Bar", "Meter=Line",
        "Meter=Histogram", "Meter=Roundline", "Meter=Shape", "Meter=Button",
        "Meter=Rotator", "Meter=Bitmap", "Meter=WebParser",

        # === Measures (tipos comuns) ===
        "Measure=Calc", "Measure=CPU", "Measure=Memory", "Measure=Net",
        "Measure=NetIn", "Measure=NetOut", "Measure=Time", "Measure=Uptime",
        "Measure=FreeDiskSpace", "Measure=Plugin", "Measure=String",
        "Measure=Process", "Measure=Registry", "Measure=WebParser", "Measure=",

        # === General Meter Options (quase todos os meters) ===
        "X=", "Y=", "W=", "H=", "MeterStyle=", "MeasureName=", "MeasureName2=",
        "MeasureName3=", "SolidColor=", "SolidColor2=", "GradientAngle=",
        "BevelType=", "BevelColor=", "BevelColor2=", "AutoScale=", "AntiAlias=", "AntiAlias=1",
        "DynamicVariables=", "DynamicVariables=1", "TransformationMatrix=",
        "Group=", "Hidden=", "Hidden=1", "Padding=", "Container=",
        "UpdateDivider=", "OnUpdateAction=", "ClipString=", "ClipString=1",
        "ClipString=2", "Shell:",

        # === String Meter (opções específicas mais usadas) ===
        "Text=", "TooltipText=", "TooltipTitle", "TooltipIcon=",
        "TooltipIcon=Info", "TooltipIcon=Warning", "TooltipIcon=Error", "TooltipIcon=Question",
        "TooltipIcon=Shield", "TooltipType=", "TooltipType=1",
        "FontFace=", "FontSize=", "FontColor=", "FontWeight=",
        "StringAlign=", "StringAlign=Left", "StringAlign=Center", "StringAlign=Right",
        "StringAlign=CenterCenter", "StringCase=", "StringEffect=", "StringStyle=",
        "FontEffectColor=", "NumOfDecimals=", "Scale=", "AutoScale=",
        "Percentual=", "InlineSetting=", "InlinePattern=", "InlineSetting2=",
        "InlinePattern2=",  # para formatação inline (cor, negrito, underline, etc.)

        # === Outras opções comuns em meters/measures ===
        "ImageName=", "ImagePath=", "ImageAlpha=", "ImageTint=", "ImageOpacity=", "Grayscale",
        "ImageFlip=", "ImageFlip=Horizontal", "ImageFlip=Vertical", "ImageFlip=Both",
        "ImageRotate=", "ImageRotate=90", "ImageRotate=180", "ImageRotate=270",
        "BarColor=", "BarImage=", "BarOrientation=",
        "StartAngle=", "RotationAngle=", "LineLength=", "Hollow=",
        "Shape=", "Shape2=", "Fill ", "StrokeWidth ",  # Shape syntax fragments
        "MinValue=", "MaxValue=", "InvertMeasure=", "AverageSize=",
        "OnChangeAction=", "IfCondition=", "IfTrueAction=", "IfFalseAction=",
        "RegHKey=", "RegPath=", "RegValue=", "RegKey=", "ProcessName=",
        "HKEY_CURRENT_CONFIG", "HKEY_CURRENT_USER", "HKEY_LOCAL_MACHINE", "HKEY_USERS", "HKEY_CLASSES_ROOT",
        "HKEY_PERFORMANCE_DATA", "HKEY_PERFORMANCE_OPTIONS", "HKEY_CURRENT_USER_LOCAL_SETTINGS",

        # === Built-in Variables (#...#) - as mais úteis ===
        "#@#", "#CURRENTPATH#", "#CURRENTFILE#", "#ROOTCONFIG#",
        "#ROOTCONFIGPATH#", "#CURRENTCONFIG#", "#SKINSPATH#", "#SETTINGSPATH#",
        "#WORKAREAX#", "#WORKAREAY#", "#WORKAREAWIDTH#", "#WORKAREAHEIGHT#",
        "#SCREENAREAX#", "#SCREENAREAY#", "#SCREENAREAWIDTH#", "#SCREENAREAHEIGHT#",
        "#CRLF#", "#TAB#", "#CURRENTSECTION#", "#VSCREENAREAX#", "#VSCREENAREAWIDTH#",
        "#MONITORWORKAREAX@1#", "#MONITORWORKAREAY@1#",  # multi-monitor comuns

        # === Bangs (!) - mais comuns e úteis ===
        "!Refresh", "!RefreshApp", "!Update", "!Redraw", "!ActivateConfig",
        "!DeactivateConfig", "!ToggleConfig", "!Show", "!Hide", "!Toggle",
        "!ShowFade", "!HideFade", "!ToggleFade", "!FadeDuration",
        "!SetVariable", "!SetOption", "!SetOptionGroup", "!WriteKeyValue",
        "!CommandMeasure", "!UpdateMeter", "!ShowMeter", "!HideMeter",
        "!ToggleMeter", "!UpdateMeasure", "!EnableMeasure", "!DisableMeasure",
        "!PauseMeasure", "!UnpauseMeasure", "!Log", "!Move", "!SetWindowPosition",
        "!ZPos", "!ClickThrough", "!Draggable", "!SkinMenu", "!About",
        "!Manage", "!Quit", "!Delay", "!SetTransparency",

        # === Outros comuns ===
        "Update=", "AccurateText=1", "DynamicWindowSize=1", "BackgroundMode=",
        "Blur=1", "BlurRadius=", "LeftMouseUpAction=", "RightMouseUpAction=", "MouseOverAction=",
        "MouseLeaveAction=", "MouseScrollUpAction=", "MouseScrollDownAction="
    ]

    def init_completer(self):
        self.completer = QCompleter(self.keywords, self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.activated.connect(self.insert_completion)

    def insert_completion(self, completion):
        if self.completer.widget() is not self:
            return
        tc = self.textCursor()
        # Seleciona o prefixo digitado e substitui pela conclusão completa
        tc.movePosition(tc.MoveOperation.Left, tc.MoveMode.KeepAnchor, len(self.completer.completionPrefix()))
        tc.insertText(completion)
        self.setTextCursor(tc)

    def text_under_cursor(self):
        tc = self.textCursor()
        tc.select(tc.SelectionType.WordUnderCursor)
        return tc.selectedText()

    def keyPressEvent(self, event):
        if self.completer and self.completer.popup().isVisible():
            if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Escape, Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
                event.ignore()
                return

        # Atalho Ctrl+Espaço ou Ctrl+E para forçar sugestões
        is_shortcut = (event.modifiers() & Qt.KeyboardModifier.ControlModifier) and \
                      (event.key() in (Qt.Key.Key_E, Qt.Key.Key_Space))
        
        if not is_shortcut:
            super().keyPressEvent(event)

        ctrl_or_shift = event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
        if not self.completer or (ctrl_or_shift and event.text() == ""):
            return

        eow = "~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-=" 
        completion_prefix = self.text_under_cursor()

        if not is_shortcut and (event.text() == "" or len(completion_prefix) < 1 or event.text()[-1] in eow):
            self.completer.popup().hide()
            return

        if completion_prefix != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(completion_prefix)
            self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))

        cr = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(cr)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.focused.emit()
