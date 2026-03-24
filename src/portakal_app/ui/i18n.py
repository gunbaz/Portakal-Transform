from __future__ import annotations

import json
from pathlib import Path
from PySide6.QtCore import QObject, Signal

class I18nManager(QObject):
    language_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._lang = "en"
        self._translations: dict[str, dict[str, str]] = {
            "tr": {
                "File": "Dosya",
                "Data": "Veri",
                "Visualize": "Görselleştir",
                "Model": "Model",
                "Evaluate": "Değerlendir",
                "Unsupervised": "Gözetimsiz",
                "Send Automatically": "Otomatik Gönder",
                "Apply Automatically": "Otomatik Uygula",
                "Apply Domain": "Alanı Uygula",
                "Apply Import": "Veriyi Uygula",
                "Apply": "Uygula",
                "Reset": "Sıfırla",
                "Reload": "Yeniden Yükle",
                "Source": "Kaynak",
                "Info": "Bilgi",
                "Columns (Double click to edit)": "Sütunlar (Düzenlemek için çift tıkla)",
                "No dataset selected": "Veri seti seçilmedi",
                "Choose a local file or URL to inspect metadata.": "Meta verileri incelemek için dosya veya URL seçin.",
                "Variable X:": "Değişken X:",
                "Variable Y:": "Değişken Y:",
                "Add Label": "Etiket Ekle",
                "Remove Tool": "Silme Aracı",
                "Send Data": "Veriyi Gönder",
                "Refresh Ranking": "Sıralamayı Yenile",
                "Feature Ranking": "Özellik Sıralaması",
                "Controls": "Kontroller",
                "Target": "Hedef",
                "Feature Filter": "Özellik Filtresi",
                "Top N": "En İyi N",
                "Dataset: none": "Veri Seti: Yok",
            }
        }

    def set_language(self, lang: str) -> None:
        if lang not in ["en", "tr"]:
            lang = "en"
        if self._lang != lang:
            self._lang = lang
            self.language_changed.emit(lang)

    def current_language(self) -> str:
        return self._lang

    def t(self, text: str) -> str:
        if self._lang == "en":
            return text
        return self._translations.get(self._lang, {}).get(text, text)

# Global instance
_app_i18n = I18nManager()

def set_language(lang: str) -> None:
    _app_i18n.set_language(lang)

def current_language() -> str:
    return _app_i18n.current_language()

def t(text: str) -> str:
    return _app_i18n.t(text)

def on_language_changed(callback) -> None:
    _app_i18n.language_changed.connect(callback)
