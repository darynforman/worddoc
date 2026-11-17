# ImageLab Assessment 3 — speaker notes

19 main slides, approximately 13–15 minutes including the live demonstration, plus 5 minutes for questions. Slides 20–24 are backup material. Spend about 20 seconds on each chart slide.
The recorded experiment is historical; foreground-browser rerun remains outstanding.

## Slide 1: ImageLab

Target time: 25 seconds.

My project extends ImageLab with Server-Sent Events. I will show how one streaming response delivers changing job snapshots, demonstrate the observer lifecycle, and compare SSE with long polling using the recorded 18-run experiment. The main presentation is approximately 13–15 minutes; detailed tables and answers are in the appendix.

Evidence / references: Both supplied Assessment 3 documents; assessment3/results/measured-suite.

## Slide 2: The worker owns processing. PostgreSQL owns state.

Target time: 40 seconds.

The request validates the image, stores its original bytes and commits an image and queued job together. Only then does it return 202 Accepted. This guarantees durable acceptance, not successful processing. One background worker claims the job and generates the three required variants. Partial metadata may describe truthful progress, but result URLs and the browser result cards are available only after completed. A failed job gets a safe error. Disconnecting an observer never owns or cancels this worker.

Evidence / references: cmd/api/images.go; cmd/api/worker.go; internal/data/jobs.go; JOB-01 to JOB-06.

## Slide 3: Three observation modes. One job representation.

Target time: 40 seconds.

Short polling always replies promptly and the browser schedules another request after one second. Long polling sends the last observed version and holds an unchanged active job for up to twenty seconds. When the response ends, the client sends another GET. SSE is different: the server can flush several named updates through a single open response. All modes use the same authoritative job representation and browser renderer. This picture is conceptual rather than measured timing. Count HTTP requests, not TCP connections.

Evidence / references: cmd/api/jobs.go; web/assets/app.js; SSE-01; assessment3/README.md.

## Slide 4: A named event carries a complete current snapshot.

Target time: 50 seconds.

Show the request and response headers in DevTools. The response is UTF-8 event-stream with cache control and buffering disabled where supported. Each frame contains event: job-update, data containing the complete current JSON representation, and a blank line. The illustration wraps JSON only for readability; the real server serializes one data line. Flush makes buffered bytes available without ending the response. The JSON version is a snapshot revision; no SSE id fields or Last-Event-ID history replay are emitted. Idle heartbeat comments do not change version or count as job updates. An unknown public job ID must return ordinary 404 before the stream begins.

Evidence / references: cmd/api/events.go: jobEventsHandler and streamJobSnapshots; Version 3 requirements, section 3.

## Slide 5: Commit first. Notify every observer. Reread state.

Target time: 55 seconds.

The worker increments the persisted version in the same transaction as a visible state or progress change. Notifications happen only after commit. Each observer has a buffered channel, so both tabs can be woken rather than one tab consuming a shared message. A handler subscribes before reading PostgreSQL. If a commit happens around subscription, either the read sees it or the buffered signal causes another read. Signals may coalesce and the handler sends only a newer version. Mutexes protect bookkeeping, not database queries or network writes. Every exit releases the subscriber and timer.

Evidence / references: internal/data/jobs.go: committed and Milestone; internal/data/job_changes.go; cmd/api/events.go; SYNC-01 to SYNC-07.

## Slide 6: Connection state is separate from job state.

Target time: 45 seconds.

The EventSource object handles temporary disconnection itself. Its error handler reports reconnecting without marking the job failed or constructing duplicate EventSource objects. A new GET gets the latest authoritative snapshot. Explicit stop is different: it closes the source, and explicit resume creates a fresh source for the same accepted job. Completed and failed are terminal: render once and close the source so it does not reconnect. Firefox Offline can leave an existing stream intact or permanently close a failed initial source. Our controlled interruption demonstrates a recoverable server-stream closure; it does not establish behavior for every real network outage.

Evidence / references: web/assets/app.js: startSSE, stopObservation, startObservation; UI-01 to UI-08; native Firefox demo verification.

## Slide 7: Live demo: one job, independent observers.

Target time: 155 seconds.

Prepare a server with the displayed command before presenting. These are artificial demonstration settings: a five-second delay and ten seconds of labelled simulated updates. Keep the paired experiment separate and demo controls disabled there. Open Firefox DevTools before upload. Show POST /v1/images returning 202 and the single /events GET. Inspect its headers and Response entries; explain zero real variants during simulation and real milestones afterward. Use Open observer tab for the same job in a second tab. Show stop/resume without a new upload. For reconnection, start another active job and click Interrupt SSE streams; do not click Observe again. Watch reconnecting and a new GET from the same EventSource. For failure, click Create failed demo job. It creates a deliberately absent input rather than deleting an uploaded original. The real worker records failure and the client closes the terminal stream. A demonstration job finishes in around fifteen seconds plus real processing. Reuse the preparation delay to keep the live sequence under three minutes; if necessary demonstrate stop/resume on an already accepted job while preparing the next job. Save DevTools evidence after each case.

Evidence / references: README.md: Two remaining classroom checks; cmd/api/demo.go; recent native Firefox verification. This slide is a cue for a LIVE DevTools trace, not a claim that a recorded trace is embedded.

## Slide 8: 18 measured runs across three controlled workloads.

Target time: 50 seconds.

The experiment matrix is three conditions times two methods times three repetitions, eighteen runs in total. Predictions were saved before measurements. A keeps the processing job quiet for thirty seconds before real work. B reports progress only after each real output and its metadata are stored. C uses fifty labelled simulated updates at two hundred milliseconds, then runs the normal transformations. The simulation field is separate from variants_completed and a timer never completes the job. Every selected run used the same input image, one observer and an empty queue, and paired method order alternated. The retained browser was headless, so these records do not establish the explicit foreground-tab condition.

Evidence / references: assessment3/results/measured-suite/predictions.json, method.json, browser.json and runs.csv; MEAS-01 to MEAS-03.

## Slide 9: Measure processing and delivery separately.

Target time: 50 seconds.

Separate the work itself from noticing its completion. Processing uses PostgreSQL started_at and completed_at or failed_at. Detection delay subtracts the server timestamp recorded immediately after the terminal transaction commits from the browser receipt timestamp. Browser and server share one host, and integer-millisecond resolution includes scheduling and clock uncertainty. There is a small inconsistency in the retained build: SSE timestamps its event callback before parsing JSON while long polling records after response.json. The current code aligns both after JSON decoding, but the earlier recorded values have not been silently changed. Do not overinterpret differences of a few milliseconds. SSE stream GETs, named events and heartbeat comments are separate counts. Full version sequences are in raw client logs, with gaps summarized in CSV.

Evidence / references: internal/data/jobs.go: committed; assessment3/experiment.py: summarize; runs.csv; historical source hashes; current web/assets/app.js.

## Slide 10: Quiet interval: observation GETs

Target time: 20 seconds.

Condition A: Quiet interval. SSE used one observation GET; long polling used six. The vertical axis is explicitly labelled with count or milliseconds and the horizontal axis is Observation method. The compact legend denotes median columns, individual runs and min–max ranges. Slide subtitles and source footers are intentionally omitted; recorded source, build caveats and interpretation remain here in the notes. The coloured column height is the median. The three white circles are all individual repetitions, placed side by side when values repeat. The black whisker spans minimum to maximum. Exact values are in the run tables in appendix slides 20–22. Observation GETs exclude the upload POST and count HTTP requests, not TCP connections. A and B use a zero-to-six GET axis and C uses zero-to-sixty, so compare numerical values rather than column heights across those slides. Fewer GETs do not establish lower total resource use.

Evidence / references: assessment3/results/measured-suite/runs.csv and summary.csv; mandatory graph 1.

## Slide 11: Real progress: observation GETs

Target time: 20 seconds.

Condition B: Real progress. SSE used one observation GET; long polling used five. The vertical axis is explicitly labelled with count or milliseconds and the horizontal axis is Observation method. The compact legend denotes median columns, individual runs and min–max ranges. Slide subtitles and source footers are intentionally omitted; recorded source, build caveats and interpretation remain here in the notes. The coloured column height is the median. The three white circles are all individual repetitions, placed side by side when values repeat. The black whisker spans minimum to maximum. Exact values are in the run tables in appendix slides 20–22. Observation GETs exclude the upload POST and count HTTP requests, not TCP connections. A and B use a zero-to-six GET axis and C uses zero-to-sixty, so compare numerical values rather than column heights across those slides. Fewer GETs do not establish lower total resource use.

Evidence / references: assessment3/results/measured-suite/runs.csv and summary.csv; mandatory graph 1.

## Slide 12: Frequent updates: observation GETs

Target time: 20 seconds.

Condition C: Frequent updates. Median observation GETs: 1 with SSE, 55 with long polling. The vertical axis is explicitly labelled with count or milliseconds and the horizontal axis is Observation method. The compact legend denotes median columns, individual runs and min–max ranges. Slide subtitles and source footers are intentionally omitted; recorded source, build caveats and interpretation remain here in the notes. The coloured column height is the median. The three white circles are all individual repetitions, placed side by side when values repeat. The black whisker spans minimum to maximum. Exact values are in the run tables in appendix slides 20–22. Observation GETs exclude the upload POST and count HTTP requests, not TCP connections. A and B use a zero-to-six GET axis and C uses zero-to-sixty, so compare numerical values rather than column heights across those slides. Fewer GETs do not establish lower total resource use.

Evidence / references: assessment3/results/measured-suite/runs.csv and summary.csv; mandatory graph 1.

## Slide 13: Quiet interval: completion-detection delay

Target time: 20 seconds.

Condition A: Quiet interval. Median detection: 9 ms with SSE, 10 ms with long polling. The vertical axis is explicitly labelled with count or milliseconds and the horizontal axis is Observation method. The compact legend denotes median columns, individual runs and min–max ranges. Slide subtitles and source footers are intentionally omitted; recorded source, build caveats and interpretation remain here in the notes. The coloured column height is the median. The three white circles are all individual repetitions, placed side by side when values repeat. The black whisker spans minimum to maximum. Exact values are in the run tables in appendix slides 20–22. All three detection slides share the zero-to-fifty millisecond scale. These are local measurements with three repetitions and timing uncertainty. They do not establish a universal speed advantage. Processing duration is separate. The historical build used slightly different receipt-timestamp placement between the modes; see slide 9.

Evidence / references: assessment3/results/measured-suite/runs.csv and summary.csv; mandatory graph 2.

## Slide 14: Real progress: completion-detection delay

Target time: 20 seconds.

Condition B: Real progress. Long polling had the lower recorded median: 10 ms versus 13 ms. The vertical axis is explicitly labelled with count or milliseconds and the horizontal axis is Observation method. The compact legend denotes median columns, individual runs and min–max ranges. Slide subtitles and source footers are intentionally omitted; recorded source, build caveats and interpretation remain here in the notes. The coloured column height is the median. The three white circles are all individual repetitions, placed side by side when values repeat. The black whisker spans minimum to maximum. Exact values are in the run tables in appendix slides 20–22. All three detection slides share the zero-to-fifty millisecond scale. These are local measurements with three repetitions and timing uncertainty. They do not establish a universal speed advantage. Processing duration is separate. The historical build used slightly different receipt-timestamp placement between the modes; see slide 9.

Evidence / references: assessment3/results/measured-suite/runs.csv and summary.csv; mandatory graph 2.

## Slide 15: Frequent updates: completion-detection delay

Target time: 20 seconds.

Condition C: Frequent updates. Long polling ranged from 12–45 ms; SSE ranged from 8–20 ms. The vertical axis is explicitly labelled with count or milliseconds and the horizontal axis is Observation method. The compact legend denotes median columns, individual runs and min–max ranges. Slide subtitles and source footers are intentionally omitted; recorded source, build caveats and interpretation remain here in the notes. The coloured column height is the median. The three white circles are all individual repetitions, placed side by side when values repeat. The black whisker spans minimum to maximum. Exact values are in the run tables in appendix slides 20–22. All three detection slides share the zero-to-fifty millisecond scale. These are local measurements with three repetitions and timing uncertainty. They do not establish a universal speed advantage. Processing duration is separate. The historical build used slightly different receipt-timestamp placement between the modes; see slide 9.

Evidence / references: assessment3/results/measured-suite/runs.csv and summary.csv; mandatory graph 2.

## Slide 16: The summary table anchors both graphs.

Target time: 40 seconds.

Use this table to connect each graph back to the numerical summary. A shows a median of one SSE GET against six long-poll GETs, with nine versus ten milliseconds detection. B shows one against five and thirteen versus ten milliseconds. C shows one against fifty-five and nine versus twelve milliseconds. Observation database reads are also lower for SSE in this small sample, but request count is not itself a resource measurement. The appendix retains the eighteen rows including processing durations, version counts and stream durations, while the raw CSV retains all metrics.

Evidence / references: summary.csv; RESULTS.md; MEAS-06 to MEAS-09.

## Slide 17: Fewer GETs do not remove observer work.

Target time: 45 seconds.

Use C–SSE–1 as a concrete snapshot-coalescing example. The first and terminal revisions were one and fifty-six, fifty-four distinct versions arrived, and fifteen and sixteen were absent. That does not mean lost event history, because neither API promises event replay. PostgreSQL remains authoritative and the completed snapshot contains the full result. Condition C median observation reads were fifty-six for SSE and one hundred ten for long polling. SSE still held a subscriber and handler, with a median stream duration of ten point seven zero nine seconds, one heartbeat and peak one active handler. Peak one reflects the controlled one-observer run, not a scaling limit. Do not infer lower total memory or CPU cost.

Evidence / references: C-sse-1/client.json; runs.csv; summary.csv; MEAS-05 and MEAS-10; snapshot semantics in both briefs.

## Slide 18: Use SSE for progress; keep long polling available.

Target time: 45 seconds.

My recommendation is SSE where continuous progress over a held response fits the deployment, especially when updates are frequent. Long polling remains reasonable when request/response infrastructure or infrequent changes matter. Its local completion delay was competitive and it was faster at the median in B. Limitations must be explicit: only three repetitions per group on loopback with one headless Firefox observer. The explicit foreground-tab requirement has not yet been demonstrated by a rerun. The retained run source hashes describe the earlier build, before removal of prohibited SSE id fields, explicit charset, aligned receipt timing and later demo controls. These records are genuine historical evidence, not a claim that the latest build was remeasured. The original C clock anomaly was excluded and all six C runs repeated, with an audit trail. WAN, proxies, memory, CPU and scale remain unmeasured.

Evidence / references: run-selection.json; method.json; browser.json; assessment3/STATUS.md; both supplied briefs.

## Slide 19: Questions

Target time: 10 seconds.

Invite approximately five minutes of questions. Return to the wire-contract, synchronization, chart or appendix slide as needed. Do not read the appendix during the timed main presentation unless asked.

Evidence / references: Assessment 3 suggested allocation: 10–15 minutes presenting plus 5 minutes questions.

## Slide 20: Condition A — all six measured runs

Target time: 0 seconds.

Backup table only: this slide retains all six measured repetitions for condition A. GET count excludes upload. Delay is browser receipt minus server post-commit time. Processing time is persisted started-to-terminal time and is not delivery delay. Versions counts distinct received revisions. The source CSV also records explicit gaps, stream/event/heartbeat counts and peak handlers. See the appropriate per-run folder for full job identity and raw records.

Evidence / references: assessment3/results/measured-suite/runs.csv; six A run folders.

## Slide 21: Condition B — all six measured runs

Target time: 0 seconds.

Backup table only: this slide retains all six measured repetitions for condition B. GET count excludes upload. Delay is browser receipt minus server post-commit time. Processing time is persisted started-to-terminal time and is not delivery delay. Versions counts distinct received revisions. The source CSV also records explicit gaps, stream/event/heartbeat counts and peak handlers. See the appropriate per-run folder for full job identity and raw records.

Evidence / references: assessment3/results/measured-suite/runs.csv; six B run folders.

## Slide 22: Condition C — all six measured runs

Target time: 0 seconds.

Backup table only: this slide retains all six measured repetitions for condition C. GET count excludes upload. Delay is browser receipt minus server post-commit time. Processing time is persisted started-to-terminal time and is not delivery delay. Versions counts distinct received revisions. The source CSV also records explicit gaps, stream/event/heartbeat counts and peak handlers. See the appropriate per-run folder for full job identity and raw records.

Evidence / references: assessment3/results/measured-suite/runs.csv; six C run folders.

## Slide 23: Reproduce the evidence; keep demonstrations separate.

Target time: 0 seconds.

For a new experiment follow assessment3/README.md and use a dedicated initialized PostgreSQL database, the retained fixture, one foreground browser observer and an empty queue. Do not run two application workers against the same database. The existing runner is headless and needs adaptation before claiming a foreground rerun. Keep demo controls disabled during performance measurements. Go checks require Go, frontend checks require Node 18+ (the current local verification used the bundled VS Code Node runtime), browser recording needs Firefox/geckodriver, and the database uses PostgreSQL 18 UUID functions. Current verification checks controlled stream closure with the same EventSource object and safe terminal failure, not every type of network outage.

Evidence / references: README.md; Makefile; assessment3/README.md; assessment3/STATUS.md; recent demo verification.

## Slide 24: Five questions to be ready for.

Target time: 0 seconds.

These questions come directly from the two supplied documents. Explain Flush as delivery of buffered bytes, not as the mechanism that keeps a handler alive. Notifications are after commit and wake all registered observers. Disconnection cancels only the observer. Current snapshots avoid a promise of durable event history or Last-Event-ID replay. Graphs show spread and workload differences but cannot establish production resource savings. Other useful answers: queued-to-processing increments version even when real count stays zero; simulation uses a separate field and never completes the job; completed and failed close the source; no partial result cards before terminal completion.

Evidence / references: ImageLab_Assessment_3_SSE_Brief.docx sections 7–9; ImageLab_Version_3_SSE_Requirements.docx.pdf sections 7–8.
