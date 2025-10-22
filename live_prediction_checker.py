#!/usr/bin/env python3
"""
NBA Prediction Checker
Checkt gestrige Vorhersagen gegen echte Ergebnisse
"""

from nba_api.live.nba.endpoints import scoreboard
from datetime import datetime, timedelta
import json
import os

class LivePredictionChecker:
    """Checkt Vorhersagen gegen Live-Ergebnisse"""
    
    def __init__(self):
        self.predictions_file = 'predictions_history.json'
        self.stats_file = 'prediction_stats.json'
        self.load_data()
    
    def load_data(self):
        """Lädt gespeicherte Vorhersagen"""
        if os.path.exists(self.predictions_file):
            with open(self.predictions_file, 'r') as f:
                self.predictions = json.load(f)
        else:
            self.predictions = []
        
        if os.path.exists(self.stats_file):
            with open(self.stats_file, 'r') as f:
                self.stats = json.load(f)
        else:
            self.stats = {
                'total_predictions': 0,
                'correct_predictions': 0,
                'accuracy': 0.0,
                'last_7_days': [],
                'best_day': None,
                'worst_day': None
            }
    
    def save_data(self):
        """Speichert Daten"""
        with open(self.predictions_file, 'w') as f:
            json.dump(self.predictions, f, indent=2)
        
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def get_yesterdays_results(self):
        """Holt gestrige Spiel-Ergebnisse"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        try:
            print(f"📊 Lade Ergebnisse vom {yesterday}...")
            
            # NBA Live Scoreboard
            board = scoreboard.ScoreBoard()
            games = board.games.get_dict()
            
            results = []
            for game in games:
                try:
                    home_team = game.get('homeTeam', {})
                    away_team = game.get('awayTeam', {})
                    
                    home_score = home_team.get('score', 0)
                    away_score = away_team.get('score', 0)
                    home_abbr = home_team.get('teamTricode', '')
                    away_abbr = away_team.get('teamTricode', '')
                    
                    # Bestimme Gewinner
                    if home_score > away_score:
                        winner = home_abbr
                    else:
                        winner = away_abbr
                    
                    results.append({
                        'date': yesterday,
                        'home_team': home_abbr,
                        'away_team': away_abbr,
                        'home_score': home_score,
                        'away_score': away_score,
                        'winner': winner,
                        'final_score': f"{home_score}-{away_score}"
                    })
                    
                except Exception as e:
                    print(f"⚠️ Fehler beim Parsen: {e}")
                    continue
            
            print(f"✓ {len(results)} Ergebnisse gefunden")
            return results
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            return []
    
    def check_predictions(self):
        """Vergleicht Vorhersagen mit Ergebnissen"""
        results = self.get_yesterdays_results()
        
        if not results:
            print("ℹ️ Keine Ergebnisse zum Checken")
            return
        
        checked_count = 0
        correct_count = 0
        
        for result in results:
            # Finde passende Vorhersage
            for prediction in self.predictions:
                if (not prediction.get('checked', False) and
                    prediction.get('date') == result['date']):
                    
                    # Prüfe ob Teams übereinstimmen
                    pred_teams = {prediction.get('team1'), prediction.get('team2')}
                    result_teams = {result['home_team'], result['away_team']}
                    
                    if pred_teams == result_teams:
                        # Match gefunden!
                        prediction['actual_result'] = {
                            'winner': result['winner'],
                            'score': result['final_score']
                        }
                        
                        # War Vorhersage richtig?
                        predicted_winner = prediction.get('predicted_winner', '')
                        actual_winner = result['winner']
                        
                        # Vergleiche (berücksichtige Team-Namen vs Abkürzungen)
                        is_correct = (
                            predicted_winner == actual_winner or
                            actual_winner in predicted_winner
                        )
                        
                        prediction['was_correct'] = is_correct
                        prediction['checked'] = True
                        
                        checked_count += 1
                        if is_correct:
                            correct_count += 1
                        
                        status = '✅' if is_correct else '❌'
                        print(f"{status} {pred_teams}: "
                              f"Predicted {predicted_winner}, "
                              f"Actual {actual_winner} ({result['final_score']})")
        
        if checked_count > 0:
            self.save_data()
            self.update_stats()
            print(f"\n📊 Checked: {checked_count} | Correct: {correct_count}")
            print(f"🎯 Accuracy: {(correct_count/checked_count*100):.1f}%")
        else:
            print("ℹ️ Keine Vorhersagen zum Checken")
    
    def update_stats(self):
        """Aktualisiert Statistiken"""
        checked = [p for p in self.predictions if p.get('checked', False)]
        
        if not checked:
            return
        
        total = len(checked)
        correct = sum(1 for p in checked if p.get('was_correct', False))
        accuracy = (correct / total * 100) if total > 0 else 0
        
        self.stats['total_predictions'] = total
        self.stats['correct_predictions'] = correct
        self.stats['accuracy'] = round(accuracy, 2)
        
        # Last 7 days
        last_7_days = {}
        for p in checked:
            date = p.get('date', '')
            if date not in last_7_days:
                last_7_days[date] = {'total': 0, 'correct': 0}
            
            last_7_days[date]['total'] += 1
            if p.get('was_correct', False):
                last_7_days[date]['correct'] += 1
        
        self.stats['last_7_days'] = [
            {
                'date': date,
                'accuracy': round(data['correct'] / data['total'] * 100, 1),
                'correct': data['correct'],
                'total': data['total']
            }
            for date, data in sorted(last_7_days.items(), reverse=True)[:7]
        ]
        
        # Best/Worst day
        if self.stats['last_7_days']:
            self.stats['best_day'] = max(
                self.stats['last_7_days'],
                key=lambda x: x['accuracy']
            )
            self.stats['worst_day'] = min(
                self.stats['last_7_days'],
                key=lambda x: x['accuracy']
            )
        
        self.save_data()
        print(f"✓ Stats aktualisiert: {accuracy:.1f}% Accuracy")
    
    def show_stats(self):
        """Zeigt aktuelle Statistiken"""
        print("\n" + "="*60)
        print("📊 PREDICTION ACCURACY STATS")
        print("="*60)
        
        print(f"\n🎯 Gesamt-Accuracy:")
        print(f"   {self.stats['accuracy']}% "
              f"({self.stats['correct_predictions']}/{self.stats['total_predictions']})")
        
        if self.stats['last_7_days']:
            print(f"\n📅 Letzte 7 Tage:")
            for day in self.stats['last_7_days']:
                print(f"   {day['date']}: {day['accuracy']}% "
                      f"({day['correct']}/{day['total']})")
        
        if self.stats['best_day']:
            print(f"\n🏆 Bester Tag:")
            print(f"   {self.stats['best_day']['date']}: "
                  f"{self.stats['best_day']['accuracy']}%")
        
        print("\n" + "="*60)


if __name__ == "__main__":
    import sys
    
    checker = LivePredictionChecker()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check":
            checker.check_predictions()
        
        elif command == "stats":
            checker.show_stats()
        
        else:
            print("Commands: check, stats")
    
    else:
        print("🏀 NBA Prediction Checker")
        print("\nCommands:")
        print("  python live_prediction_checker.py check  - Check yesterday's predictions")
        print("  python live_prediction_checker.py stats  - Show current stats")
