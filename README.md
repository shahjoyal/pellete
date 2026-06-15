# Iron Ore Pelletization – Flask Application

Converts the static Iron Palette HTML dashboard into a Flask web application
with a REST API endpoint for ML model predictions.

## Project Structure

```
flask_app/
├── app.py                     # Flask application (routes + API)
├── requirements.txt
├── ml/
│   ├── __init__.py
│   └── model.py               # ← drop your ML model here
├── templates/
│   ├── index.html             # Landing page
│   ├── login.html             # Login (posts to Flask)
│   ├── dashboard_page1.html   # Feed → Thickener stages
│   ├── dashboard_page2.html   # Balling disc stages
│   └── dashboard_page3.html   # Induration → Pellet stages
└── static/
    ├── js/
    │   └── api_bridge.js      # Hooks UI into Flask API (no UI changes)
    ├── images/
    │   └── abhitech-logo.png  # (copy from original project)
    └── videos/
        └── *.mp4              # (copy from original project)
```

## Quick Start

```bash
pip install -r requirements.txt
python app.py
# → http://localhost:5000
```

Login: **admin / admin123** (change in app.py → DEMO_USERS before production)

## Copying Static Assets

Copy all media from the original project:

```bash
# From original "iron pallete/" folder:
cp abhitech-logo.png  flask_app/static/images/
cp img*.jpeg img*.png flask_app/static/images/
cp *.mp4              flask_app/static/videos/
```

## API Reference

### POST /api/predict

Accepts the full `stageParams` object (auto-sent when "Run Pelletization
Simulation" is clicked) and returns ML predictions.

**Request body:**
```json
{
  "plantName":     "Plant A",
  "plantCapacity": 200,
  "stageParams": { ...all stage params... }
}
```

**Response:**
```json
{
  "status": "ok",
  "predictions": {
    "pelletQuality": {
      "ccs": 320.5,
      "tumbler": 94.2,
      "abrasion": 4.1,
      "fe": 65.3,
      "porosity": 22.0
    },
    "sizeDistribution": {
      "size8_10": 5, "size10_12": 45,
      "size12_14": 40, "size14_16": 10
    },
    "operationalKPIs": {
      "yield": 87.3, "productivity": 174.6,
      "energyPerTon": 550, "blainAchieved": 2100
    },
    "recommendations": ["Parameters are within optimal ranges."]
  }
}
```

### Displaying Predictions in the UI

`api_bridge.js` automatically writes predictions into the DOM after a run.
Add any of these `id`s to your HTML to show the values:

| Element id            | Value shown                    |
|-----------------------|--------------------------------|
| `pred-ccs`            | Cold Crushing Strength (kg)    |
| `pred-tumbler`        | Tumbler Index (%)              |
| `pred-abrasion`       | Abrasion Index (%)             |
| `pred-fe`             | Fe content (%)                 |
| `pred-porosity`       | Porosity (%)                   |
| `pred-size8`          | Size 8–10 mm (%)               |
| `pred-size10`         | Size 10–12 mm (%)              |
| `pred-size12`         | Size 12–14 mm (%)              |
| `pred-size14`         | Size 14–16 mm (%)              |
| `p-yield`             | Yield (%) — already in UI      |
| `pred-energy`         | Energy per ton (kcal/t)        |
| `pred-blain`          | Blain achieved (cm²/g)         |
| `pred-prod`           | Productivity (t/h)             |
| `pred-recommendations`| `<ul>` of text recommendations|
| `predictions-panel`   | Shown/hidden container         |
| `pred-error`          | Error message container        |

## Plugging in Your ML Model

1. Edit `ml/model.py` and implement `predict(features: dict) -> dict`
2. In `app.py`, uncomment the import and replace `_stub_predict(...)` with:
   ```python
   from ml.model import predict
   predictions = predict(features)
   ```
3. Adjust `_build_feature_vector()` in `app.py` if your model expects
   different inputs or a specific feature order.

## Adding / Removing Input Parameters

- **Add a field in the UI** → add the `id` in the HTML modal, then add
  `stageParams.<stage>.<key> = document.getElementById('m-xxx').value;`
  in the save function (same pattern as existing fields).
- **Expose it to the model** → add an entry in `_build_feature_vector()`.
- **Remove a field** → delete it from the HTML modal and the `stageParams`
  object; remove the corresponding entry in `_build_feature_vector()`.

## Production Checklist

- [ ] Replace `app.secret_key` with `os.urandom(32)` stored in env var
- [ ] Replace `DEMO_USERS` with a proper user database + password hashing
- [ ] Add HTTPS (nginx / gunicorn + certbot)
- [ ] Set `debug=False` in `app.run()`
- [ ] Add rate-limiting on `/api/predict`
- [ ] Persist state in a database instead of session
