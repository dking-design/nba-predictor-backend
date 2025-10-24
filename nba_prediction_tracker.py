#!/usr/bin/env python3
"""
NBA Prediction Tracker
Speichert Vorhersagen und vergleicht mit echten Ergebnissen
"""

import json
import os
from datetime import datetime, timedelta
from nba_api.stats.endpoints import ScoreboardV2
import time

class PredictionTracker:
    """Trackt Vorhersagen und vergleicht mit Ergebnissen"""
    
    def __init__(self):
        # Use persistent volume
        data_dir = '/data'
        
        # Create directory if it doesn't exist
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
            except:
                data_dir = '.'  # Fallback
        
        self.predictions_file = os.path.join(data_dir, 'predictions_history.json')
        self.stats_file = os.path.join(data_dir, 'prediction_stats.json')
        
        # Initialize empty files if they don't exist
        if not os.path.exists(self.predictions_file):
            with open(self.predictions_file, 'w') as f:
                json.dump([], f)
        
        if not os.path.exists(self.stats_file):
            with open(self.stats_file, 'w') as f:
                json.dump({
                    'total_predictions': 0,
                    'correct_predictions': 0,
                    'accuracy': 0.0
                }, f)
    
    @property
    def stats(self):
        """Read and return stats from file"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            else:
                # Return default stats
                return {
                    'total_predictions': 0,
                    'correct_predictions': 0,
                    'accuracy': 0.0,
                    'last_7_days': [],
                    'best_day': None,
                    'worst_day': None
                }
        except Exception as e:
            print(f"Error reading stats: {e}")
            return {
                'total_predictions': 0,
                'correct_predictions': 0,
                'accuracy': 0.0,
                'last_7_days': [],
                'best_day': None,
                'worst_day': None
            }
    
    def get_all_predictions(self):
        """Gibt alle Vorhersagen zurück"""
        try:
            if os.path.exists(self.predictions_file):
                with open(self.predictions_file, 'r') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            print(f"Error reading predictions: {e}")
            return []
    
    def load_data(self):
        """Lädt gespeicherte Daten"""
        # Predictions History
        if os.path.exists(self.predictions_file):
            with open(self.predictions_file, 'r') as f:
                self.predictions = json.load(f)
        else:
            self.predictions = []
        
        # Stats
        if os.path.exists(self.stats_file):
            with open(self.stats_file, 'r') as f:
                self._stats = json.load(f)
        else:
            self._stats = {
                'total_predictions': 0,
                'correct_predictions': 0,
                'accuracy': 0.0,
                'by_confidence': {},
                'last_7_days': [],
                'best_day': None,
                'worst_day': None
            }
    
    def save_data(self):
        """Speichert Daten"""
        with open(self.predictions_file, 'w') as f:
            json.dump(self.predictions, f, indent=2)
        
        with open(self.stats_file, 'w') as f:
            json.dump(self._stats, f, indent=2)
    
    def log_prediction(self, team1, team2, predicted_winner, 
                      predicted_score, confidence, game_date=None, 
                      team1_name=None, team2_name=None):
        """Speichert eine neue Vorhersage"""
        if game_date is None:
            game_date = datetime.now().strftime('%Y-%m-%d')
        
        prediction = {
            'id': f"{team1}_vs_{team2}_{game_date}",
            'date': game_date,
            'team1': team1,
            'team2': team2,
            'team1_name': team1_name or team1,
            'team2_name': team2_name or team2,
            'predicted_winner': predicted_winner,
            'predicted_score': predicted_score,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat(),
            'actual_result': None,
            'was_correct': None,
            'checked': False
        }
        
        # Load existing predictions
        predictions = self.get_all_predictions()
        predictions.append(prediction)
        
        # Save
        with open(self.predictions_file, 'w') as f:
            json.dump(predictions, f, indent=2)
        
        print(f"✅ Vorhersage gespeichert: {team1} vs {team2}")
        return prediction
    
    def get_yesterdays_results(self):
        """Holt gestrige Spiel-Ergebnisse von NBA API"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        try:
            print(f"📊 Lade Ergebnisse vom {yesterday}...")
            scoreboard = ScoreboardV2(game_date=yesterday)
            time.sleep(1)  # Rate limiting
            
            games = scoreboard.game_header.get_data_frame()
            line_score = scoreboard.line_score.get_data_frame()
            
            results = []
            for _, game in games.iterrows():
                game_id = game['GAME_ID']
                
                # Teams und Scores
                game_scores = line_score[line_score['GAME_ID'] == game_id]
                
                if len(game_scores) == 2:
                    team1_score = game_scores.iloc[0]['PTS']
                    team2_score = game_scores.iloc[1]['PTS']
                    team1_name = game_scores.iloc[0]['TEAM_ABBREVIATION']
                    team2_name = game_scores.iloc[1]['TEAM_ABBREVIATION']
                    
                    winner = team1_name if team1_score > team2_score else team2_name
                    
                    results.append({
                        'date': yesterday,
                        'team1': team1_name,
                        'team2': team2_name,
                        'score': f"{team1_score}-{team2_score}",
                        'winner': winner
                    })
            
            print(f"✅ {len(results)} Spiele gefunden")
            return results
            
        except Exception as e:
            print(f"❌ Fehler beim Laden der Ergebnisse: {e}")
            return []
    
    def check_predictions(self):
        """Vergleicht Vorhersagen mit echten Ergebnissen"""
        results = self.get_yesterdays_results()
        
        if not results:
            print("ℹ️ Keine Ergebnisse zum Checken")
            return
        
        self.load_data()
        checked_count = 0
        correct_count = 0
        
        for result in results:
            # Finde passende Vorhersage
            for prediction in self.predictions:
                if (not prediction['checked'] and 
                    prediction['date'] == result['date'] and
                    prediction['team1'] == result['team1'] and
                    prediction['team2'] == result['team2']):
                    
                    # Update mit echtem Ergebnis
                    prediction['actual_result'] = {
                        'winner': result['winner'],
                        'score': result['score']
                    }
                    
                    # War die Vorhersage richtig?
                    prediction['was_correct'] = (
                        prediction['predicted_winner'] == result['winner']
                    )
                    prediction['checked'] = True
                    
                    checked_count += 1
                    if prediction['was_correct']:
                        correct_count += 1
                    
                    print(f"{'✅' if prediction['was_correct'] else '❌'} "
                          f"{prediction['team1']} vs {prediction['team2']}: "
                          f"Predicted {prediction['predicted_winner']}, "
                          f"Actual {result['winner']}")
        
        if checked_count > 0:
            self.save_data()
            self.update_stats()
            print(f"\n📊 Checked: {checked_count} | Correct: {correct_count}")
        else:
            print("ℹ️ Keine Vorhersagen zum Checken gefunden")
    
    def update_stats(self):
        """Aktualisiert Statistiken"""
        checked = [p for p in self.predictions if p['checked']]
        
        if not checked:
            return
        
        total = len(checked)
        correct = sum(1 for p in checked if p['was_correct'])
        accuracy = (correct / total * 100) if total > 0 else 0
        
        self._stats['total_predictions'] = total
        self._stats['correct_predictions'] = correct
        self._stats['accuracy'] = round(accuracy, 2)
        
        # Last 7 days
        last_7_days = {}
        for p in checked:
            date = p['date']
            if date not in last_7_days:
                last_7_days[date] = {'total': 0, 'correct': 0}
            
            last_7_days[date]['total'] += 1
            if p['was_correct']:
                last_7_days[date]['correct'] += 1
        
        self._stats['last_7_days'] = [
            {
                'date': date,
                'accuracy': round(data['correct'] / data['total'] * 100, 1),
                'correct': data['correct'],
                'total': data['total']
            }
            for date, data in sorted(last_7_days.items(), reverse=True)[:7]
        ]
        
        # Best/Worst day
        if self._stats['last_7_days']:
            self._stats['best_day'] = max(
                self._stats['last_7_days'], 
                key=lambda x: x['accuracy']
            )
            self._stats['worst_day'] = min(
                self._stats['last_7_days'], 
                key=lambda x: x['accuracy']
            )
        
        self.save_data()
    
    def show_stats(self):
        """Zeigt Statistiken"""
        self.load_data()
        
        print("\n" + "="*60)
        print("📊 PREDICTION TRACKER - STATISTIKEN")
        print("="*60)
        
        print(f"\n🎯 Gesamt-Accuracy:")
        print(f"   {self._stats['accuracy']}% "
              f"({self._stats['correct_predictions']}/{self._stats['total_predictions']})")
        
        if self._stats['last_7_days']:
            print(f"\n📅 Letzte 7 Tage:")
            for day in self._stats['last_7_days']:
                print(f"   {day['date']}: {day['accuracy']}% "
                      f"({day['correct']}/{day['total']})")
        
        if self._stats['best_day']:
            print(f"\n🏆 Bester Tag:")
            print(f"   {self._stats['best_day']['date']}: "
                  f"{self._stats['best_day']['accuracy']}%")
        
        if self._stats['worst_day']:
            print(f"\n📉 Schlechtester Tag:")
            print(f"   {self._stats['worst_day']['date']}: "
                  f"{self._stats['worst_day']['accuracy']}%")
        
        print("\n" + "="*60)


# CLI
if __name__ == "__main__":
    import sys
    
    tracker = PredictionTracker()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check":
            tracker.check_predictions()
        
        elif command == "stats":
            tracker.show_stats()
        
        elif command == "log":
            if len(sys.argv) >= 6:
                team1 = sys.argv[2]
                team2 = sys.argv[3]
                winner = sys.argv[4]
                score = sys.argv[5]
                confidence = float(sys.argv[6]) if len(sys.argv) > 6 else 50.0
                
                tracker.log_prediction(team1, team2, winner, score, confidence)
            else:
                print("Usage: python nba_prediction_tracker.py log <team1> <team2> <winner> <score> <confidence>")
        
        else:
            print("Commands: check, stats, log")
    
    else:
        print("Commands: check, stats, log")
        tracker.show_stats()
