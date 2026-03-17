# YZM318-Portakal-Data-Mining-Application

Bu repository Ankara Üniversitesi 2026 dönemi YZM318 dersi kapsamında kurulmuştur. <br>
Dr. Öğr. Üyesi Bahaeddin Türkoğlu danışmanlığında AÜ YVZM öğrencileri tarafından geliştirilen "Portakal" veri madenciliği uygulamasının versiyonları burada tutulacaktır.<br>
Orijinal açık kaynaklı "Orange Data Mining" uygulamasından esinlenilmiştir (https://orangedatamining.com/). 

<br>
<br>

Created for the YZM318 course (2026 term) at Ankara University, this repository keeps the development versions of the "Portakal" data mining tool. <br>
The project is developed by AU AI&DE students and supervised by Asst. Prof. Bahaeddin Türkoğlu. <br>
The project draws inspiration from the open-source Orange Data Mining platform (https://orangedatamining.com/).

## Development

Orange-inspired desktop shell built with PySide6.

Create a virtual environment and install dependencies:

```powershell
python -m pip install -e .[dev]
```

Run the app:

```powershell
python -m portakal_app
```

Run tests:

```powershell
pytest
```

## Current UI Scope

- The app shell, workflow canvas, popup widget windows, and active `Data` widgets are implemented.
- Active `Data` widgets:
  - `File`
  - `Data Table`
  - `Data Info`
  - `Save Data`
- Placeholder widgets are intentionally empty. They preserve the Orange-like catalog, layout, and connection model for later teams.

## Frozen Popup Rules

- Popup size and centering behavior are intentionally standardized in `workflow_workspace.py`.
- Default widgets share one popup size profile.
- `Save Data` uses a smaller dedicated popup size profile.
- These sizing rules are considered frozen unless a later requirement explicitly changes popup UX.
