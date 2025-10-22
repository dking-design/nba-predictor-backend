# 🏀 NBA Predictor Backend - Railway Deployment

## 🚀 Quick Start

### Railway Deployment

1. **Push zu GitHub**
2. **Railway importieren**
3. **Automatisch deployed!**

## 📁 Projekt-Struktur

```
nba-backend/
├── nba_flask_api.py           # Flask REST API
├── nba_lineup_predictor.py    # ML Prediction Logic
├── nba_synergy_system.py      # Team Synergy Calculator
├── nba_prediction_tracker.py  # Tracking System
├── nba_data_collector.py      # NBA API Data Collector
├── nba_ml_model.py            # Model Training
├── nba_model.pkl              # Trained ML Model (2.9 MB)
├── nba_players_2024-25.json   # Player Database (288 KB)
├── nba_training_data.csv      # Training Data
├── requirements.txt           # Python Dependencies
├── Procfile                   # Railway Start Command
├── railway.json               # Railway Config
└── README.md                  # This file
```

## 🔧 API Endpoints

### GET /
API Info und Status

### GET /api/players
Alle Spieler mit Stats

### GET /api/players/search?q=LeBron
Spieler suchen

### GET /api/player/<name>
Detaillierte Spieler-Info

### POST /api/predict
Vorhersage erstellen
```json
{
  "team1_lineup": ["LeBron James", "Anthony Davis", ...],
  "team2_lineup": ["Stephen Curry", "Klay Thompson", ...],
  "team1_name": "Lakers",
  "team2_name": "Warriors",
  "team1_abbr": "LAL",
  "team2_abbr": "GSW",
  "game_date": "2024-10-22",
  "team1_home": true
}
```

### GET /api/today-games
Heutige NBA-Spiele (Mock-Daten)

### GET /api/prediction-stats
Tracking-Statistiken

### GET /api/health
Health Check

## 🧠 ML Features

- **Team Synergy Calculation**
  - 3-Point Spacing
  - Playmaking
  - Rebounding
  - Defense
  - Ball Movement
  - Scoring Balance

- **Prediction Model**
  - Random Forest / Gradient Boosting
  - Rolling Averages (5 games)
  - Home/Away Advantage
  - Player Type Matching

## 🔄 Auto-Updates (Optional)

GitHub Actions können täglich ausgeführt werden:
- Player Stats Update
- Model Retraining (wöchentlich)

## 📊 Daten

- **450+ NBA Spieler** (2024-25 Season)
- **Trainiert auf historischen Spielen**
- **Mock-Games für Testing**

## 🐛 Debugging

Logs in Railway Dashboard:
```bash
railway logs
```

## 📞 Support

Falls Fehler auftreten:
1. Check Railway Logs
2. Verify alle Dateien vorhanden
3. Check requirements.txt Dependencies

---

**Version:** 2.0  
**Author:** NBA Predictor Team  
**License:** MIT
