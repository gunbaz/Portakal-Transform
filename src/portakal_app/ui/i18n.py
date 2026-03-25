from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class I18nManager(QObject):
    language_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._lang = "en"
        self._translations: dict[str, dict[str, str]] = {
            "tr": {
                "Language / Dil": "Dil",
                "Turkish": "Türkçe",
                "English": "İngilizce",
                "Documentation": "Dokümantasyon",
                "Settings": "Ayarlar",
                "Help": "Yardım",
                "File": "Dosya",
                "Edit": "Düzen",
                "View": "Görünüm",
                "Widget": "Bileşen",
                "Window": "Pencere",
                "Options": "Seçenekler",
                "New": "Yeni",
                "Open": "Aç",
                "Open and Freeze": "Aç ve Sabitle",
                "Open Recent": "Son Açılanlar",
                "Open Workflow": "İş Akışını Aç",
                "Open Workflow and Freeze": "İş Akışını Aç ve Sabitle",
                "Open Source": "Kaynağı Aç",
                "Close": "Kapat",
                "Close Window": "Pencereyi Kapat",
                "Quit": "Çıkış",
                "Remove": "Kaldır",
                "Rename": "Yeniden Adlandır",
                "Data": "Veri",
                "Transform": "Dönüştür",
                "CSV File Import": "CSV Dosya İçe Aktarma",
                "Datasets": "Veri Setleri",
                "Data Table": "Veri Tablosu",
                "Paint Data": "Veri Boyama",
                "Data Info": "Veri Bilgisi",
                "Rank": "Sırala",
                "Edit Domain": "Alanı Düzenle",
                "Color": "Renk",
                "Column Statistics": "Sütun İstatistikleri",
                "Select Columns": "Sütun Seç",
                "Normalize": "Normalleştir",
                "Scatter Plot": "Dağılım Grafiği",
                "Linear Regression": "Doğrusal Regresyon",
                "Test & Score": "Test ve Puanla",
                "Visualize": "Görselleştir",
                "Model": "Model",
                "Evaluate": "Değerlendir",
                "Unsupervised": "Gözetimsiz",
                "PCA": "PCA",
                "Reload Last Workflow": "Son İş Akışını Yeniden Yükle",
                "File:": "Dosya:",
                "URL:": "URL:",
                "File Type": "Dosya Türü",
                "Select a local dataset...": "Yerel bir veri seti seçin...",
                "Paste a remote dataset URL...": "Uzak veri seti URL'sini yapıştırın...",
                "Determine type from the file extension": "Türü dosya uzantısından belirle",
                "Basket file (*.basket *.bsk)": "Basket dosyası (*.basket *.bsk)",
                "Comma-separated values (*.csv *.csv.gz *.gz *.csv.bz2 *.bz2 *.csv.xz *.xz)": "Virgülle ayrılmış değerler (*.csv *.csv.gz *.gz *.csv.bz2 *.bz2 *.csv.xz *.xz)",
                "Microsoft Excel 97-2004 spreadsheet (*.xls)": "Microsoft Excel 97-2004 çalışma sayfası (*.xls)",
                "Microsoft Excel spreadsheet (*.xlsx)": "Microsoft Excel çalışma sayfası (*.xlsx)",
                "Pickled Orange data (*.pkl *.pickle *.pkl.gz *.pickle.gz *.gz *.pkl.bz2 *.pickle.bz2 *.bz2 *.pkl.xz *.pickle.xz *.xz)": "Pickle Orange verisi (*.pkl *.pickle *.pkl.gz *.pickle.gz *.gz *.pkl.bz2 *.pickle.bz2 *.bz2 *.pkl.xz *.pickle.xz *.xz)",
                "Tab-separated values (*.tab *.tsv *.tab.gz *.tsv.gz *.gz *.tab.bz2 *.tsv.bz2 *.bz2 *.tab.xz *.tsv.xz *.xz)": "Sekmeyle ayrılmış değerler (*.tab *.tsv *.tab.gz *.tsv.gz *.gz *.tab.bz2 *.tsv.bz2 *.bz2 *.tab.xz *.tsv.xz *.xz)",
                "Filter widgets...": "Bileşenleri filtrele...",
                "Coming soon": "Yakında",
                "Send Automatically": "Otomatik Gönder",
                "Apply Automatically": "Otomatik Uygula",
                "Apply Domain": "Alanı Uygula",
                "Apply Import": "Veriyi Uygula",
                "Apply": "Uygula",
                "Reset": "Sıfırla",
                "Reload": "Yeniden Yükle",
                "Source": "Kaynak",
                "Info": "Bilgi",
                "Summary": "Özet",
                "Summary card": "Özet kartı",
                "Column Profiles": "Sütun Profilleri",
                "AI Analysis": "YZ Analizi",
                "Columns (Double click to edit)": "Sütunlar (Düzenlemek için çift tıkla)",
                "No dataset selected": "Veri seti seçilmedi",
                "Choose a local file or URL to inspect metadata.": "Meta verileri incelemek için dosya veya URL seçin.",
                "Error loading URL": "URL yüklenirken hata oluştu",
                "Apply failed": "Uygulama başarısız oldu",
                "Kaggle notebook/code URLs are not supported. Use a dataset URL in the form https://www.kaggle.com/datasets/<owner>/<dataset-name>.": "Kaggle notebook/code bağlantıları desteklenmiyor. https://www.kaggle.com/datasets/<owner>/<dataset-name> biçiminde bir veri seti bağlantısı kullanın.",
                "Only Kaggle dataset URLs are supported. Use a URL in the form https://www.kaggle.com/datasets/<owner>/<dataset-name>.": "Yalnızca Kaggle veri seti bağlantıları destekleniyor. https://www.kaggle.com/datasets/<owner>/<dataset-name> biçiminde bir bağlantı kullanın.",
                "Select a file path or URL before applying.": "Uygulamadan önce dosya yolu veya URL seçin.",
                "Local file source": "Yerel dosya kaynağı",
                "Source path": "Kaynak yolu",
                "Detected extension": "Algılanan uzantı",
                "columns discovered": "sütun bulundu",
                "rows detected": "satır bulundu",
                "Cache file": "Önbellek dosyası",
                "unknown": "bilinmiyor",
                "No source selected yet.": "Henüz kaynak seçilmedi.",
                "Use Browse, Reload and Apply after the data backend is connected.": "Veri altyapısı bağlandıktan sonra Gözat, Yeniden Yükle ve Uygula kullanın.",
                "Name": "Ad",
                "Type": "Tür",
                "Role": "Rol",
                "Values": "Değerler",
                "Kaggle User:": "Kaggle Kullanıcı:",
                "Kaggle API Key:": "Kaggle API Anahtarı:",
                "Optional: your Kaggle username": "İsteğe bağlı: Kaggle kullanıcı adınız",
                "Optional: paste Kaggle API key": "İsteğe bağlı: Kaggle API anahtarınızı yapıştırın",
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
                "Dataset: {name}": "Veri Seti: {name}",
                "Analyze": "Analiz Et",
                "Analyzing...": "Analiz Ediliyor...",
                "Risks": "Riskler",
                "Suggestions": "Öneriler",
                "Save Data": "Veriyi Kaydet",
                "Save": "Kaydet",
                "Load": "Yükle",
                "Save as ...": "Farklı Kaydet ...",
                "Save As ...": "Farklı Kaydet ...",
                "Save Workflow": "İş Akışını Kaydet",
                "Save Workflow Image as SVG ...": "İş Akışı Görselini SVG Olarak Kaydet ...",
                "Export Workflow SVG": "İş Akışı SVG Dışa Aktar",
                "Autosave when receiving new data": "Yeni veri geldiğinde otomatik kaydet",
                "Add type annotations to header": "Başlığa tür açıklamaları ekle",
                "Dataset: none": "Veri seti: yok",
                "Delimited Source": "Ayrılmış Kaynak",
                "Import Options": "İçe Aktarma Seçenekleri",
                "Preview": "Önizleme",
                "Workflow": "İş Akışı",
                "Drag widgets from the catalog onto the canvas. Click a node to inspect it. Build connections by dragging from an output port onto a compatible input port.": "Bileşenleri katalogdan tuvale sürükleyin. İncelemek için bir düğüme tıklayın. Bir çıkış portundan uyumlu bir giriş portuna sürükleyerek bağlantı kurun.",
                "Search for data set ...": "Veri seti ara ...",
                "First parsed row is header": "İlk satır başlık olarak kullanılsın",
                "No imported dataset": "İçe aktarılan veri yok",
                "Choose a delimited file and preview it before importing.": "İçe aktarmadan önce ayrılmış dosya seçin ve önizleyin.",
                "Import options changed. Preview or apply to refresh the parsed dataset.": "İçe aktarma seçenekleri değişti. Ayrıştırılmış veriyi güncellemek için önizleme yapın veya uygulayın.",
                "Select a delimited file first.": "Önce ayrılmış bir dosya seçin.",
                "Current workflow dataset loaded. Import options are not available for this source.": "Mevcut iş akışı verisi yüklendi. Bu kaynak için içe aktarma seçenekleri kullanılamaz.",
                "Dataset": "Veri Seti",
                "Dataset: none": "Veri seti: yok",
                "Load a dataset to edit column names, types and roles.": "Sütun adlarını, türlerini ve rollerini düzenlemek için bir veri seti yükleyin.",
                "Columns": "Sütunlar",
                "Restore Inferred": "Tahmin Edileni Geri Yükle",
                "Domain changes applied to the workflow dataset.": "Alan değişiklikleri iş akışı verisine uygulandı.",
                "Restored inferred domain from the current dataset.": "Mevcut veri setinden tahmin edilen alan geri yüklendi.",
                "Load a dataset to rank feature usefulness.": "Özelliklerin önemini sıralamak için bir veri seti yükleyin.",
                "No target selected. Ranking uses heuristic mode.": "Hedef seçilmedi. Sıralama sezgisel modda yapılıyor.",
                "Search": "Ara",
                "Column": "Sütun",
                "Statistics": "İstatistikler",
                "Distribution": "Dağılım",
                "Top Values": "En Sık Değerler",
                "Load a dataset to inspect per-column statistics.": "Sütun bazlı istatistikleri görmek için bir veri seti yükleyin.",
                "No columns matched the current search.": "Mevcut aramaya uyan sütun bulunamadı.",
                "No warnings": "Uyarı yok",
                "Open Source": "Kaynağı Aç",
                "Download Preview": "Önizlemeyi İndir",
                "Description": "Açıklama",
                "Select a dataset to review its description and source.": "Açıklamasını ve kaynağını görmek için bir veri seti seçin.",
                "No datasets match the current filter.": "Mevcut filtreyle eşleşen veri seti yok.",
                "Domain:": "Alan:",
                "No dataset loaded.": "Veri seti yüklenmedi.",
                "No data loaded yet": "Henüz veri yüklenmedi",
                "No dataset": "Veri yok",
                "Load data to inspect it": "İncelemek için veri yükleyin",
                "Loading data...": "Veriler yükleniyor...",
                "Polars DataFrame is being prepared, please wait.": "Polars DataFrame hazırlanıyor, lütfen bekleyin.",
                "You can start by selecting a file from the File widget.": "File bileşeninden bir dosya seçerek başlayabilirsiniz.",
                "Variables": "Değişkenler",
                "Selection": "Seçim",
                "Show variable labels (if present)": "Değişken etiketlerini göster (varsa)",
                "Visualize numeric values": "Sayısal değerleri görselleştir",
                "Color by instance classes": "Sınıf etiketine göre renklendir",
                "Clear Selection": "Seçimi Temizle",
                "Select full rows": "Tam satır seç",
                "Restore Original Order": "Orijinal Sırayı Geri Yükle",
                "Data: none": "Veri: yok",
                "Data Subset: -": "Veri Alt Kümesi: -",
                "Selected": "Seçili",
                "Points": "Noktalar",
                "Selected: {count}": "Seçili: {count}",
                "Points: {count}": "Noktalar: {count}",
                "Names": "Adlar",
                "Source Columns": "Kaynak Sütunları",
                "Output Names": "Çıktı Adları",
                "X Column:": "X Sütunu:",
                "Y Column:": "Y Sütunu:",
                "Label Column:": "Etiket Sütunu:",
                "Labels": "Etiketler",
                "None": "Yok",
                "Tools": "Araçlar",
                "Brush": "Fırça",
                "Put": "Ekle",
                "Select": "Seç",
                "Jitter": "Titreşim",
                "Magnet": "Mıknatıs",
                "Clear": "Temizle",
                "Radius:": "Yarıçap:",
                "Intensity:": "Yoğunluk:",
                "Symbol:": "Sembol:",
                "Reset to Input Data": "Girdi Verisine Sıfırla",
                "Discrete Variables": "Ayrık Değişkenler",
                "Numeric Variables": "Sayısal Değişkenler",
                "No discrete variables available for manual color assignment.": "Elle renk ataması yapılabilecek ayrık değişken yok.",
                "No numeric variables available for gradient palettes.": "Renk geçişi uygulanabilecek sayısal değişken yok.",
                "Save Color Settings": "Renk Ayarlarını Kaydet",
                "Load Color Settings": "Renk Ayarlarını Yükle",
                "Select Color": "Renk Seç",
                "Sample Values": "Örnek Değerler",
                "No AI risks yet.": "Henüz YZ riski yok.",
                "No AI suggestions yet.": "Henüz YZ önerisi yok.",
                "No dataset loaded": "Veri seti yüklenmedi",
                "Load a dataset before running AI analysis.": "YZ analizini çalıştırmadan önce bir veri seti yükleyin.",
                "AI analysis in progress...": "YZ analizi sürüyor...",
                "AI analysis failed": "YZ analizi başarısız oldu",
                "AI analysis failed.": "YZ analizi başarısız oldu.",
                "not set": "ayarlanmadı",
                "Provider": "Sağlayıcı",
                "Model": "Model",
                "Provider: {provider} | Model: {model}": "Sağlayıcı: {provider} | Model: {model}",
                "Analyzed with {provider} ({model})": "{provider} ile analiz edildi ({model})",
                "Editing domain for {count} columns. Apply changes to update the workflow dataset.": "{count} sütun için alan düzenleniyor. İş akışı verisini güncellemek için değişiklikleri uygulayın.",
                "{target_label} ({count} values)": "{target_label} ({count} değer)",
                "{count} instances ({missing_summary})": "{count} gözlem ({missing_summary})",
                "{count} missing values": "{count} eksik değer",
                "{count} numeric features": "{count} sayısal özellik",
                "Target with {count} values": "{count} değerli hedef",
                "No meta attributes.": "Meta öznitelik yok.",
                "Data: {dataset_name}: {row_count} instances, {column_count} variables": "Veri: {dataset_name}: {row_count} gözlem, {column_count} değişken",
                "Selected Data: {dataset_name}: {row_count} instances, {column_count} variables": "Seçili Veri: {dataset_name}: {row_count} gözlem, {column_count} değişken",
                "Selected Data: {row_count} instances, {column_count} variables": "Seçili Veri: {row_count} gözlem, {column_count} değişken",
                "Features: {count} numeric ({missing_summary})": "Özellikler: {count} sayısal ({missing_summary})",
                "Target: {target_label}": "Hedef: {target_label}",
                "Showing all rows in the table": "Tablodaki tüm satırlar gösteriliyor",
                "no missing values": "eksik değer yok",
                "contains missing values": "eksik değer içeriyor",
                "no missing data": "eksik veri yok",
                "none": "yok",
                "Duplicate": "Çoğalt",
                "Copy": "Kopyala",
                "Paste": "Yapıştır",
                "Select all": "Tümünü Seç",
                "Load a file dataset.": "Bir dosya veri seti yükleyin.",
                "Preset-based import flow.": "Hazır ayarlara dayalı içe aktarma akışı.",
                "Explore packaged datasets.": "Paketli veri setlerini keşfedin.",
                "Inspect loaded rows.": "Yüklenen satırları inceleyin.",
                "Edit data manually.": "Veriyi elle düzenleyin.",
                "Profile the dataset.": "Veri setinin profilini çıkarın.",
                "Rank features.": "Özellikleri sıralayın.",
                "Manage column roles.": "Sütun rollerini yönetin.",
                "Assign color metadata.": "Renk meta verilerini atayın.",
                "Deep dive into column distributions.": "Sütun dağılımlarını ayrıntılı inceleyin.",
                "Export the current dataset.": "Geçerli veri setini dışa aktarın.",
                "Choose feature sets.": "Özellik kümelerini seçin.",
                "Scale numeric columns.": "Sayısal sütunları ölçekleyin.",
                "Explore points visually.": "Noktaları görsel olarak inceleyin.",
                "Train a baseline model.": "Temel bir model eğitin.",
                "Measure model performance.": "Model performansını ölçün.",
                "Reduce dimensionality.": "Boyutu azaltın.",
                "Transform widgets are planned but not part of this shell milestone.": "Dönüştürme bileşenleri planlandı ancak bu kabuk kilometre taşına dahil değil.",
                "Visualization widgets will be integrated by a later group.": "Görselleştirme bileşenleri daha sonraki bir grup tarafından entegre edilecek.",
                "Model widgets will be integrated by a later group.": "Model bileşenleri daha sonraki bir grup tarafından entegre edilecek.",
                "Evaluation widgets will be integrated by a later group.": "Değerlendirme bileşenleri daha sonraki bir grup tarafından entegre edilecek.",
                "Unsupervised widgets will be integrated by a later group.": "Gözetimsiz öğrenme bileşenleri daha sonraki bir grup tarafından entegre edilecek.",
                "Text Annotation": "Metin Notu",
                "Arrow Annotation": "Ok Notu",
                "Window Groups": "Pencere Grupları",
                "Expand Tool Dock": "Araç Bölmesini Genişlet",
                "Log": "Günlük",
                "Zoom in": "Yakınlaştır",
                "Zoom out": "Uzaklaştır",
                "Reset Zoom": "Yakınlaştırmayı Sıfırla",
                "Show Workflow Margins": "İş Akışı Kenar Boşluklarını Göster",
                "Bring Widgets to Front": "Bileşenleri Öne Getir",
                "Display Widgets on Top": "Bileşenleri Üstte Göster",
                "Workflow Info": "İş Akışı Bilgisi",
                "Title": "Başlık",
                "Cancel": "İptal",
                "Open widget menu": "Bileşen menüsünü aç",
                "Open data preview": "Veri önizlemesini aç",
                "Open selected data preview": "Seçili veri önizlemesini aç",
                "Open Dataset...": "Veri Seti Aç...",
                "Reload Source": "Kaynağı Yeniden Yükle",
                "Data Preview": "Veri Önizleme",
                "Selected Data Preview": "Seçili Veri Önizleme",
                "Status: {status}": "Durum: {status}",
                "Center": "Ortala",
                "Bring to Front": "Öne Getir",
                "Always on Top": "Her Zaman Üstte",
                "Widget Help": "Bileşen Yardımı",
                "No help available.": "Yardım içeriği yok.",
                "No preview available.": "Önizleme yok.",
                "Report": "Rapor",
                "Write a comment...": "Bir yorum yazın...",
                "Back to Last Schema": "Son Şemaya Dön",
                "Save Report": "Raporu Kaydet",
                "Comments": "Yorumlar",
                "Pan canvas": "Tuvali kaydır",
                "Reset zoom": "Yakınlaştırmayı sıfırla",
                "Add text annotation": "Metin notu ekle",
                "Add arrow annotation": "Ok notu ekle",
                "Show more tools": "Daha fazla araç göster",
                "Hide extra tools": "Ek araçları gizle",
                "Reset Widget Settings...": "Bileşen Ayarlarını Sıfırla...",
                "Add-ons...": "Eklentiler...",
                "About Portakal": "Portakal Hakkında",
                "Untitled": "Adsız",
                "Language changed. Open widgets were updated immediately.": "Dil değiştirildi. Açık bileşenler anında güncellendi.",
            }
        }
        self._reverse_translations: dict[str, dict[str, str]] = {
            lang: {translated: source for source, translated in values.items()}
            for lang, values in self._translations.items()
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
            reverse = self._reverse_translations.get("tr", {})
            return reverse.get(text, text)
        return self._translations.get(self._lang, {}).get(text, text)

    def tf(self, text: str, **kwargs) -> str:
        return self.t(text).format(**kwargs)

    def apply_to_widget(self, root) -> None:
        try:
            from PySide6.QtGui import QAction
            from PySide6.QtWidgets import QAbstractButton, QComboBox, QGroupBox, QLabel, QLineEdit, QTableWidget, QWidget
        except Exception:
            return

        if root is None:
            return

        widgets = [root] + list(root.findChildren(QWidget))
        for widget in widgets:
            if isinstance(widget, QGroupBox):
                widget.setTitle(self.t(widget.title()))
            if isinstance(widget, QLabel):
                widget.setText(self.t(widget.text()))
            if isinstance(widget, QAbstractButton):
                widget.setText(self.t(widget.text()))
            if isinstance(widget, QLineEdit):
                placeholder = widget.placeholderText()
                if placeholder:
                    widget.setPlaceholderText(self.t(placeholder))
            if isinstance(widget, QComboBox) and widget.count() > 0:
                current = widget.currentText()
                for index in range(widget.count()):
                    item_text = widget.itemText(index)
                    widget.setItemText(index, self.t(item_text))
                if current:
                    widget.setCurrentText(self.t(current))
            if isinstance(widget, QTableWidget):
                for index in range(widget.columnCount()):
                    header = widget.horizontalHeaderItem(index)
                    if header is not None:
                        header.setText(self.t(header.text()))

        for action in root.findChildren(QAction):
            action.setText(self.t(action.text()))

# Global instance
_app_i18n = I18nManager()

def set_language(lang: str) -> None:
    _app_i18n.set_language(lang)

def current_language() -> str:
    return _app_i18n.current_language()

def t(text: str) -> str:
    return _app_i18n.t(text)


def tf(text: str, **kwargs) -> str:
    return _app_i18n.tf(text, **kwargs)

def on_language_changed(callback) -> None:
    _app_i18n.language_changed.connect(callback)


def apply_to_widget(root) -> None:
    _app_i18n.apply_to_widget(root)
