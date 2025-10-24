from nba_games_loader import NBAGamesLoader
games_loader = NBAGamesLoader()
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import numpy as np
from datetime import datetime, timedelta
from nba_synergy_system import TeamSynergyCalculator
from nba_lineup_predictor import NBALineupPredictor
import os

app = Flask(__name__)
CORS(app)

# Initialisiere Predictor
predictor = NBALineupPredictor()
players_data = predictor.players

class NumpyEncoder(json.JSONEncoder):
    """JSON Encoder für NumPy types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

app.json_encoder = NumpyEncoder

@app.route('/')
def home():
    """API Info"""
    return jsonify({
        'name': 'NBA Predictor API',
        'version': '2.0',
        'status': 'online',
        'players_loaded': len(players_data),
        'endpoints': {
            '/api/players': 'GET - Liste aller Spieler',
            '/api/players/search': 'GET - Spieler suchen',
            '/api/predict': 'POST - Vorhersage machen',
            '/api/prediction-stats': 'GET - Prediction Accuracy Stats',
            '/api/predictions-history': 'GET - Alle Vorhersagen',
            '/api/check-predictions': 'POST - Manueller Prediction Check',
            '/api/today-games': 'GET - Heutige NBA-Spiele',
            '/api/health': 'GET - Health Check'
        }
    })

@app.route('/api/players', methods=['GET'])
def get_players():
    """Gibt alle Spieler zurück"""
    players_list = []
    
    for name, data in players_data.items():
        players_list.append({
            'name': name,
            'team': data['team'],
            'pts': round(data['stats'].get('PTS', 0), 1),
            'type': data['type']
        })
    
    players_list.sort(key=lambda x: x['pts'], reverse=True)
    
    return jsonify({
        'success': True,
        'count': len(players_list),
        'players': players_list
    })

@app.route('/api/players/search', methods=['GET'])
def search_players():
    """Sucht Spieler"""
    query = request.args.get('q', '').lower()
    
    if not query:
        return jsonify({'success': False, 'error': 'Query parameter required'})
    
    matches = []
    for name, data in players_data.items():
        if query in name.lower():
            matches.append({
                'name': name,
                'team': data['team'],
                'pts': round(data['stats'].get('PTS', 0), 1),
                'type': data['type']
            })
    
    matches.sort(key=lambda x: x['pts'], reverse=True)
    
    return jsonify({
        'success': True,
        'count': len(matches),
        'players': matches[:10]
    })

@app.route('/api/player/<n>', methods=['GET'])
def get_player_details(name):
    """Gibt detaillierte Spieler-Info"""
    player = players_data.get(name)
    
    if not player:
        return jsonify({'success': False, 'error': 'Player not found'}), 404
    
    return jsonify({
        'success': True,
        'player': {
            'name': name,
            'team': player['team'],
            'type': player['type'],
            'stats': {
                'pts': round(player['stats'].get('PTS', 0), 1),
                'reb': round(player['stats'].get('REB', 0), 1),
                'ast': round(player['stats'].get('AST', 0), 1),
                'fg_pct': round(player['stats'].get('FG_PCT', 0) * 100, 1),
                'fg3_pct': round(player['stats'].get('FG3_PCT', 0) * 100, 1),
                'minutes': round(player['stats'].get('MIN', 0), 1)
            }
        }
    })

@app.route('/api/predict', methods=['POST'])
def make_prediction():
    """Macht eine Vorhersage"""
    print("=" * 60)
    print("🔵 PREDICTION REQUEST STARTED")
    print("=" * 60)
    
    data = request.get_json()
    
    if not data or 'team1_lineup' not in data or 'team2_lineup' not in data:
        return jsonify({
            'success': False,
            'error': 'team1_lineup and team2_lineup required'
        }), 400
    
    team1_lineup = data['team1_lineup']
    team2_lineup = data['team2_lineup']
    team1_name = data.get('team1_name', 'Team 1')
    team2_name = data.get('team2_name', 'Team 2')
    team1_home = data.get('team1_home', True)
    
    if len(team1_lineup) != 5 or len(team2_lineup) != 5:
        return jsonify({
            'success': False,
            'error': 'Each lineup must have exactly 5 players'
        }), 400
    
    for player in team1_lineup + team2_lineup:
        if player not in players_data:
            return jsonify({
                'success': False,
                'error': f'Player not found: {player}'
            }), 404
    
    try:
        print("🔵 Making prediction...")
        result = predictor.predict_game(team1_lineup, team2_lineup, team1_home)
        
        if not result:
            return jsonify({
                'success': False,
                'error': 'Prediction failed'
            }), 500
        
        comparison = result['comparison']
        
        matchups_t1 = []
        matchups_t2 = []
        
        for player in team1_lineup:
            p_data = players_data[player]
            matchups_t1.append({
                'player': player,
                'pts': round(p_data['stats'].get('PTS', 0), 1),
                'type': p_data['type']
            })
        
        for player in team2_lineup:
            p_data = players_data[player]
            matchups_t2.append({
                'player': player,
                'pts': round(p_data['stats'].get('PTS', 0), 1),
                'type': p_data['type']
            })
        
        # PREDICTION TRACKING
        print("=" * 60)
        print("🔵 STARTING PREDICTION TRACKING")
        print("=" * 60)
        
        try:
            print("🔵 Importing PredictionTracker...")
            from nba_prediction_tracker import PredictionTracker
            print("✅ Import successful")
            
            print("🔵 Initializing tracker...")
            tracker = PredictionTracker()
            print(f"✅ Tracker initialized")
            print(f"📁 predictions_file: {tracker.predictions_file}")
            
            team1_abbr = data.get('team1_abbr', team1_name)
            team2_abbr = data.get('team2_abbr', team2_name)
            game_date = data.get('game_date', datetime.now().strftime('%Y-%m-%d'))
            
            print(f"🔵 Logging prediction:")
            print(f"   {team1_abbr} vs {team2_abbr}")
            print(f"   Date: {game_date}")
            print(f"   Winner: {team1_name if result['winner'] == 1 else team2_name}")
            
            tracker.log_prediction(
                team1=team1_abbr,
                team2=team2_abbr,
                predicted_winner=team1_name if result['winner'] == 1 else team2_name,
                predicted_score=f"{result['team1_score']}-{result['team2_score']}",
                confidence=result['confidence'],
                game_date=game_date,
                team1_name=team1_name,
                team2_name=team2_name
            )
            
            print("=" * 60)
            print("✅ PREDICTION LOGGED SUCCESSFULLY!")
            print("=" * 60)
            
        except Exception as e:
            print("=" * 60)
            print("❌ TRACKING ERROR!")
            print(f"Error: {e}")
            print("=" * 60)
            import traceback
            traceback.print_exc()
        
        return jsonify({
            'success': True,
            'prediction': {
                'team1_name': team1_name,
                'team2_name': team2_name,
                'team1_score': result['team1_score'],
                'team2_score': result['team2_score'],
                'winner': team1_name if result['winner'] == 1 else team2_name,
                'team1_win_prob': round(result['team1_win_prob'] * 100, 1),
                'team2_win_prob': round(result['team2_win_prob'] * 100, 1),
                'confidence': round(result['confidence'] * 100, 1)
            },
            'synergies': {
                'team1': {
                    name: round(val, 1) for name, val in comparison['team1']['synergies'].items()
                },
                'team2': {
                    name: round(val, 1) for name, val in comparison['team2']['synergies'].items()
                }
            },
            'lineups': {
                'team1': matchups_t1,
                'team2': matchups_t2
            }
        })
    
    except Exception as e:
        print(f"❌ PREDICTION ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Gibt alle NBA Teams zurück"""
    teams = {}
    
    for player_name, player_data in players_data.items():
        team = player_data['team']
        if team not in teams:
            teams[team] = []
        teams[team].append(player_name)
    
    team_list = [
        {
            'abbreviation': abbr,
            'player_count': len(players)
        }
        for abbr, players in teams.items()
    ]
    
    team_list.sort(key=lambda x: x['abbreviation'])
    
    return jsonify({
        'success': True,
        'count': len(team_list),
        'teams': team_list
    })

@app.route('/api/today-games', methods=['GET'])
def get_today_games():
    """Lädt heutige NBA-Spiele"""
    games = games_loader.get_games_with_fallback()
    return jsonify({
        'success': True,
        'count': len(games),
        'games': games
    })

@app.route('/api/predictions-history', methods=['GET'])
def get_predictions_history():
    """Gibt alle Vorhersagen zurück"""
    try:
        from nba_prediction_tracker import PredictionTracker
        
        tracker = PredictionTracker()
        predictions = tracker.get_all_predictions()
        
        return jsonify({
            'success': True,
            'count': len(predictions),
            'predictions': predictions
        })
    except Exception as e:
        print(f"Error getting predictions history: {e}")
        return jsonify({
            'success': True,
            'count': 0,
            'predictions': []
        })

@app.route('/api/prediction-stats', methods=['GET'])
def get_prediction_stats():
    """Gibt Prediction-Tracking Statistiken zurück"""
    try:
        from nba_prediction_tracker import PredictionTracker
        import os
        
        tracker = PredictionTracker()
        
        if os.path.exists(tracker.stats_file):
            try:
                stats = tracker.stats
            except:
                stats = {
                    'total_predictions': 0,
                    'correct_predictions': 0,
                    'accuracy': 0.0,
                    'last_7_days': [],
                    'best_day': None,
                    'worst_day': None
                }
        else:
            stats = {
                'total_predictions': 0,
                'correct_predictions': 0,
                'accuracy': 0.0,
                'last_7_days': [],
                'best_day': None,
                'worst_day': None
            }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        print(f"Error in prediction-stats: {e}")
        return jsonify({
            'success': True,
            'stats': {
                'total_predictions': 0,
                'correct_predictions': 0,
                'accuracy': 0.0,
                'last_7_days': [],
                'best_day': None,
                'worst_day': None
            }
        })

@app.route('/api/check-predictions', methods=['POST'])
def trigger_check_predictions():
    """
    🔍 MANUELLER PREDICTION CHECK
    Checkt alle ausstehenden Vorhersagen gegen echte NBA Ergebnisse
    """
    print("\n" + "="*60)
    print("🔍 MANUELLER PREDICTION CHECK GESTARTET")
    print("="*60 + "\n")
    
    try:
        from nba_prediction_tracker import PredictionTracker
        
        # Initialize tracker
        tracker = PredictionTracker()
        tracker.load_data()
        
        print(f"📊 Lade Vorhersagen...")
        print(f"   Gesamt: {len(tracker.predictions)}")
        
        unchecked = [p for p in tracker.predictions if not p['checked']]
        print(f"   Unchecked: {len(unchecked)}")
        
        if len(unchecked) == 0:
            print("ℹ️ Keine ausstehenden Vorhersagen zum Checken")
            return jsonify({
                'success': True,
                'message': 'Keine ausstehenden Vorhersagen',
                'checked': 0,
                'correct': 0,
                'stats': tracker.stats
            })
        
        # Check predictions against real results
        print("\n🔍 Starte Checking...")
        tracker.check_predictions()
        
        # Update stats
        print("📊 Aktualisiere Statistiken...")
        tracker.update_stats()
        
        # Get results
        newly_checked = [p for p in tracker.predictions if p['checked']]
        correct = sum(1 for p in newly_checked if p['was_correct'])
        
        print("\n" + "="*60)
        print("✅ CHECK ABGESCHLOSSEN!")
        print(f"   Gecheckt: {len(newly_checked)}")
        print(f"   Korrekt: {correct}")
        print(f"   Accuracy: {tracker.stats.get('accuracy', 0)}%")
        print("="*60 + "\n")
        
        return jsonify({
            'success': True,
            'message': 'Predictions erfolgreich gecheckt',
            'checked': len(newly_checked),
            'correct': correct,
            'accuracy': tracker.stats.get('accuracy', 0),
            'stats': tracker.stats
        })
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ FEHLER BEIM CHECKEN!")
        print(f"Error: {e}")
        print("="*60 + "\n")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health Check für Deployment"""
    return jsonify({
        'status': 'healthy',
        'players_loaded': len(players_data),
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    
    print("\n" + "="*60)
    print("🏀 NBA PREDICTOR API - RAILWAY DEPLOYMENT")
    print("="*60)
    print(f"\nPort: {port}")
    print(f"Spieler geladen: {len(players_data)}")
    print("\nEndpoints:")
    print("  GET  /")
    print("  GET  /api/players")
    print("  GET  /api/players/search?q=LeBron")
    print("  GET  /api/player/<n>")
    print("  POST /api/predict")
    print("  GET  /api/teams")
    print("  GET  /api/today-games")
    print("  GET  /api/predictions-history")
    print("  GET  /api/prediction-stats")
    print("  POST /api/check-predictions  ← NEU!")
    print("  GET  /api/health")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=port)
