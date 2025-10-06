# Fear Mongering Detection in TED Talks

A Streamlit web application that analyzes TED talk transcripts to detect fear-mongering content using AI-powered natural language processing. The application segments transcripts, applies machine learning classification, and visualizes results with interactive charts.

## Features

-  **AI-Powered Analysis**: Uses Hugging Face's `Falconsai/fear_mongering_detection` model
-  **Interactive Visualizations**: Dual chart system (Matplotlib + Plotly) with time-series analysis
-  **Performance Optimized**: Caching mechanisms for model and data loading
-  **Real-time Progress Tracking**: Visual feedback during batch processing
-  **Export Capabilities**: Download charts (PNG) and analysis results (CSV)
-  **Paragraph-level Analysis**: Intelligent text segmentation with timestamp mapping

## Table of Contents

- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Dependencies](#dependencies)
- [Configuration](#configuration)
- [Output Examples](#output-examples)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Git (for cloning the repository)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/fear-mongering-detection.git
cd fear-mongering-detection
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Download Data Files

Ensure your TED talks dataset is structured as follows:

```
project_root/
├── data/
│   └── transcripts/
│       └── ted_talks/
│           ├── ted_talks_transcripts.csv
│           └── ted_main.csv
├── src/
│   └── backend/
│       └── ted_talks_app/

```


## Project Structure

```
fear-mongering-detection/
├── backend/
│   └── src/
│       └── ted_talks_app/
│           ├── config.py
│           ├── models.py
│           ├── data_loader.py
│           ├── utils.py
│           ├── analysis.py
│           ├── charts.py
│           └── app.py          # Main Streamlit application
├── data/
│   └── transcripts/
│       └── ted_talks/
│           ├── ted_talks_transcripts.csv  # Transcript data
│           └── ted_main.csv               # Metadata (duration, speaker, etc.)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── .gitignore                  # Git ignore rules
```

## Usage

### Running the Application

1. Navigate to the project directory
2. Activate your virtual environment (if using one)
3. Run the Streamlit app:

```bash
streamlit run backend/src/app.py
```

4. Open your browser to `http://localhost:8501`

### Using the Interface

1. **Select a TED Talk**: Use the sidebar number input to choose a talk by index
2. **View Preview**: Review the transcript preview at the top
3. **Analyze**: The app automatically segments and analyzes the transcript
4. **Explore Results**:
   - View interactive Plotly chart with zoom and time range controls
   - Examine static Matplotlib chart for publication-quality output
   - Browse the detailed results table with timestamps and scores
5. **Export Data**:
   - Download charts as PNG images
   - Export analysis results as CSV

## How It Works

### 1. Text Segmentation

The application splits long transcripts into manageable paragraphs:
- Maximum 250 characters per segment
- Respects sentence boundaries using regex
- Prevents mid-sentence cuts for better context

### 2. AI Classification

Each paragraph is analyzed using the fear-mongering detection model:
- Returns a confidence score (0.0 to 1.0)
- Scores above 0.6 are classified as "Fear Mongering"
- Model handles truncation automatically for long inputs

### 3. Timestamp Assignment

Timestamps are evenly distributed across paragraphs:
- Based on total talk duration from metadata
- Formatted as HH:MM:SS for readability
- Used for time-series visualization

### 4. Visualization

Two complementary chart types:
- **Matplotlib**: High-resolution static charts for reports/papers
- **Plotly**: Interactive charts with hover details, zoom, and time range selectors

## Dependencies

Create a `requirements.txt` file with:

```txt
streamlit>=1.28.0
transformers>=4.30.0
torch>=2.0.0
pandas>=2.0.0
matplotlib>=3.7.0
plotly>=5.14.0
streamlit-aggrid>=0.3.4
kaleido>=0.2.1
```

### Optional Dependencies

For Plotly PNG export:
```bash
pip install kaleido
```

## Configuration

### Adjusting Paragraph Size

Modify the `max_chars` parameter in the segmentation call:

```python
paragraphs = segment_text_into_paragraphs(selected_transcript, max_chars=300)
```

### Changing Classification Threshold

Update the threshold in the analysis section:

```python
"Prediction": ["Fear Mongering" if r["score"] > 0.7 else "Not Fear Mongering" for r in results]
```

### Data Path Configuration

If your data is in a different location, update the path in `load_transcripts()`:

```python
base_dir = Path("/your/custom/path/to/data")
```

## Output Examples

### Analysis Results Table

| Timestamp | Paragraph | Fear Mongering Score | Prediction |
|-----------|-----------|---------------------|------------|
| 00:00:00  | In today's world, we face unprecedented challenges... | 0.72 | Fear Mongering |
| 00:02:15  | However, through innovation and collaboration... | 0.23 | Not Fear Mongering |

### Exported Files

- `fear_mongering_score_plot_0.png` - Matplotlib chart
- `fear_mongering_score_plot_0_plotly.png` - Plotly chart
- `fear_mongering_analysis_0.csv` - Complete results data

## Troubleshooting

### Model Loading Issues

**Problem**: Model fails to download or load

**Solution**:
```bash
# Ensure transformers and torch are installed
pip install --upgrade transformers torch

# Check internet connection for Hugging Face downloads
```

### File Not Found Errors

**Problem**: CSV files not found

**Solution**:
- Verify data files exist in `data/transcripts/ted_talks/`
- Check file names match exactly: `ted_talks_transcripts.csv` and `ted_main.csv`
- Ensure proper path structure from project root

### Plotly Export Fails

**Problem**: Cannot export Plotly charts as PNG

**Solution**:
```bash
pip install kaleido
```

### Memory Issues

**Problem**: Out of memory errors with large transcripts

**Solution**:
- Reduce `max_chars` parameter for smaller segments
- Process fewer talks at once
- Increase system RAM or use cloud deployment

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include unit tests for new features
- Update README for significant changes

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **Hugging Face**: For the `Falconsai/fear_mongering_detection` model
- **TED**: For providing transcript data
- **Streamlit**: For the excellent web framework
- **Open Source Community**: For the various libraries used

## Contact

For questions, issues, or suggestions:
- Open an issue on GitHub
- Email: your.email@example.com
- Project Link: https://github.com/yourusername/fear-mongering-detection

## Citation

If you use this project in research, please cite:

```bibtex
@software{fear_mongering_detection,
  author = {Your Name},
  title = {Fear Mongering Detection in TED Talks},
  year = {2025},
  url = {https://github.com/yourusername/fear-mongering-detection}
}
```

---

**Note**: This tool is for research and educational purposes. Fear-mongering detection is subjective and context-dependent. Always apply human judgment when interpreting results.