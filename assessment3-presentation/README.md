# ImageLab Assessment 3 presentation

Open **ImageLab_Assessment_3_Daryn_Forman.pptx** in PowerPoint or a compatible presentation application.
It is a 16:9 deck with editable text, diagrams, vector graphs and numerical tables.

- Slides 1–15: main presentation, approximately 12–15 minutes including a short live demonstration.
- Slides 16–20: backup tables, reproducibility notes and the required discussion questions.
- Speaker notes are embedded in every slide and also supplied in SPEAKER_NOTES.md.
- The PDF is a visual slide preview generated from the same layout primitives, not an application-exported PDF.
- slide-overview.png provides a quick view of all twenty slides.
- REQUIREMENTS_COVERAGE.md maps content to both supplied documents.
- source-data/ preserves the numerical inputs and recorded experiment metadata used by the deck.

## Evidence status

The numerical results are the retained 18-run experiment from 8 November 2026.
They were recorded using headless Firefox before the recent SSE format and timing fixes.
The slides explicitly disclose these limits; a foreground-browser rerun is still outstanding.
The live demo is a presentation activity, not an embedded DevTools recording.
Controlled stream interruption tests recoverable server-stream closure, not every network outage.

## Live demonstration preparation

Stop the existing app before running this command from the test3 project:

```bash
make run DEMO_CONTROLS=true WORKER_DELAY=5s SIMULATION_INTERVAL=200ms
```

Refresh ImageLab, select SSE, open DevTools and keep No Throttling selected.
Follow slide 7 and the embedded notes. Demo controls must be disabled for performance runs.
The five-second delay and ten-second simulated phase are demonstration settings.

## Rebuild

The builder needs Python 3 and Pillow. From this directory:

```bash
python3 build_presentation.py --project /path/to/test3 --out /path/to/new-output
```

The builder reuses only the existing Assessment 2 file's standard PowerPoint theme/layout
infrastructure; all Assessment 3 slide content, diagrams, tables and charts are rebuilt.

## Chart readability revision

Slides 10 and 11 now use three separate condition panels, direct method labels,
large median values, all three run values, and plotted repetitions plus min–max.
The GET panels use explicitly labelled 0–6 axes for A/B and 0–60 for C; compare
the numbers, not bar lengths, across conditions. Delay panels all share 0–50 ms.
The measurements have not changed.
