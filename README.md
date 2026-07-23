# Football Analysis Dashboard

An interactive Streamlit dashboard built on FIFA 22 player data. This project uses Plotly for publication-ready, colorblind-safe analytics and includes 10 multi-dimensional visuals.

## Files
- `dashboard/app.py` — main Streamlit dashboard implementation with Plotly charts
- `streamlit_app.py` — Streamlit entrypoint
- `requirements.txt` — dependencies for running the app
- `.streamlit/config.toml` — Streamlit server configuration
- `data/players_22.csv` — FIFA 22 player dataset
- `notebook/football_analysis.ipynb` — exploratory notebook for data inspection

## Setup
1. Activate your virtual environment:
   ```bash
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Run locally
```bash
streamlit run streamlit_app.py
```

Then open the local URL shown in the terminal.

## Dashboard Features
The dashboard includes 10 interactive visuals, including:
- Age vs rating trends by position
- Market value vs wage scatter
- League skill group comparison
- Midfield club performance scatter
- Work rate distributions for pace and stamina
- Nation skill radar comparison
- Goalkeeper skill profile by league level
- Combined scoring/passing/pace top players
- Age, overall, and potential bubble chart
- Top-rated players bar chart

## Notes
- The dashboard uses Plotly only for all visualizations.
- Color palettes are selected for better accessibility.
- Filters support age range, position, club, nationality, and league level.

## Deployment
For deployment on Streamlit Community Cloud or another host, make sure the repository includes:
- `requirements.txt`
- `streamlit_app.py`
- `data/players_22.csv`

On Streamlit Cloud, set the app file to `streamlit_app.py`.
