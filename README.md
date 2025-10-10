# FearSense: Video Fear-Mongering & Stress Correlation Demo

This project demonstrates how to detect **fear-mongering in video transcripts** and correlate it with **biometric stress signals** (e.g., heart rate, HRV, EDA) collected from wearables such as Fitbit, Apple Health, or Google Fit.

<p align="center">
  <img src="assets/falsconai-fear-sensor.png" alt="Fear Analysis" width="500" style="border: 2px solid #d3d3d3; border-radius: 10px;"/>
</p>

---

## Features

* **Transcript ingestion**: Upload subtitles (SRT/VTT) or transcribe MP4 videos with Whisper.
* **Fear-mongering detection**: NLP pipeline combining emotion classification, zero-shot NLI, and lexical cue analysis.
* **Biometric integration**: Import data via Fitbit API, Apple Health export, Google Fit API, or CSV.
* **Correlation analytics**: Aligns transcript segments with biometric data to explore correlations.
* **Interactive visualization**: Overlays fear intensity and stress signals on a timeline, with lagged cross-correlation plots.

---

## Architecture

<!-- ```
Video Transcript → NLP Fear Score → Alignment → Analytics → Visualization
                    ↑                        ↑
        Biometrics (Fitbit/Apple/Google/CSV) │
``` -->

<!-- ![Alt text](assets/architecture_diagram-v1.jpg) -->

<p align="center">
  <img src="assets/architecture_diagram-v1.jpg" alt="Architecture Diagram" style="width:75%;"/>
</p>

* **Backend**: FastAPI + Celery for async processing
* **Storage**: Postgres/TimescaleDB + MinIO (object storage)
* **NLP**: [Falconsai/fear_mongering_detection](https://huggingface.co/Falconsai/fear_mongering_detection)
* **Frontend**: Streamlit (MVP) or Next.js (scalable)

---

## Example Insights

* Fear intensity timeline with highlighted transcript segments.
* Overlay of heart rate/HRV against fear spikes.
* Lagged cross-correlation plots to see if fear spikes precede stress responses.

<!-- ![Alt text](assets/fear-analysis.png) -->

<p align="center">
  <img src="assets/fear-analysis.png" alt="Fear Analysis" width="450" style="border: 2px solid #d3d3d3; border-radius: 10px;"/>
</p>

---

## 🚀 Getting Started

### Prerequisites

* Python 3.10+
* Docker & docker-compose (for running services)
* Fitbit/Google API credentials (if using live connectors)

---

## ⚠️ Disclaimer

This project is for **research and demo purposes only**. It is not a medical device and does not provide medical advice. Correlation does not imply causation.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you’d like to change.

---


