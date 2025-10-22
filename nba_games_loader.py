#!/usr/bin/env python3
"""
NBA Live Games Loader
Lädt heutige und morgige NBA-Spiele von der offiziellen NBA API
"""

from nba_api.live.nba.endpoints import scoreboard
from datetime import datetime, timedelta
import time

class NBAGamesLoader:
    """Lädt aktuelle NBA Spiele"""
    
    def __init__(self):
        self.games = []
    
    def get_todays_games(self):
        """
        Holt heutige NBA Spiele
        """
        try:
            print("📡 Lade heutige NBA Spiele...")
            
            # NBA API Scoreboard
            board = scoreboard.ScoreBoard()
            games_data = board.games.get_dict()
            
            parsed_games = []
            
            for game in games_data:
                try:
                    # Game Info
                    game_id = game.get('gameId', '')
                    game_status = game.get('gameStatusText', '')
                    
                    # Home Team
                    home_team = game.get('homeTeam', {})
                    home_name = home_team.get('teamName', 'Home')
                    home_abbr = home_team.get('teamTricode', 'HOM')
                    
                    # Away Team
                    away_team = game.get('awayTeam', {})
                    away_name = away_team.get('teamName', 'Away')
                    away_abbr = away_team.get('awayTricode', 'AWY')
                    
                    # Game Date/Time
                    game_time_utc = game.get('gameTimeUTC', '')
                    game_date = datetime.now().strftime('%Y-%m-%d')
                    
                    # Format time
                    if game_time_utc:
                        try:
                            dt = datetime.fromisoformat(game_time_utc.replace('Z', '+00:00'))
                            game_time = dt.strftime('%I:%M %p ET')
                        except:
                            game_time = game_status
                    else:
                        game_time = game_status
                    
                    parsed_games.append({
                        'game_id': game_id,
                        'date': game_date,
                        'time': game_time,
                        'team1_abbr': home_abbr,
                        'team2_abbr': away_abbr,
                        'team1_name': home_name,
                        'team2_name': away_name,
                        'matchup': f"{home_abbr} vs {away_abbr}",
                        'status': game_status
                    })
                    
                except Exception as e:
                    print(f"⚠️ Fehler beim Parsen eines Spiels: {e}")
                    continue
            
            print(f"✓ {len(parsed_games)} Spiele gefunden")
            return parsed_games
            
        except Exception as e:
            print(f"❌ Fehler beim Laden der Spiele: {e}")
            return []
    
    def get_tomorrows_games(self):
        """
        Holt morgige Spiele (falls heute keine)
        """
        # NBA API hat leider keine direkte "tomorrow" Funktion
        # Wir müssten das über die Schedule API machen
        return []
    
    def get_games_with_fallback(self):
        """
        Holt Spiele mit Fallback auf Mock-Daten
        """
        games = self.get_todays_games()
        
        # Fallback auf Mock-Daten wenn keine Spiele
        if not games:
            print("⚠️ Keine Live-Spiele - verwende Mock-Daten")
            games = self._get_mock_games()
        
        return games
    
    def _get_mock_games(self):
        """Mock-Daten als Fallback"""
        return [
            {
                'game_id': 'mock_001',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': '7:30 PM ET',
                'team1_abbr': 'LAL',
                'team2_abbr': 'GSW',
                'team1_name': 'Lakers',
                'team2_name': 'Warriors',
                'matchup': 'LAL vs GSW',
                'status': 'Mock Game'
            },
            {
                'game_id': 'mock_002',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': '8:00 PM ET',
                'team1_abbr': 'BOS',
                'team2_abbr': 'MIA',
                'team1_name': 'Celtics',
                'team2_name': 'Heat',
                'matchup': 'BOS vs MIA',
                'status': 'Mock Game'
            },
            {
                'game_id': 'mock_003',
                'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'time': '7:00 PM ET',
                'team1_abbr': 'PHX',
                'team2_abbr': 'LAC',
                'team1_name': 'Suns',
                'team2_name': 'Clippers',
                'matchup': 'PHX vs LAC',
                'status': 'Mock Game'
            },
            {
                'game_id': 'mock_004',
                'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'time': '8:30 PM ET',
                'team1_abbr': 'DAL',
                'team2_abbr': 'DEN',
                'team1_name': 'Mavericks',
                'team2_name': 'Nuggets',
                'matchup': 'DAL vs DEN',
                'status': 'Mock Game'
            }
        ]


# Test
if __name__ == "__main__":
    loader = NBAGamesLoader()
    games = loader.get_games_with_fallback()
    
    print("\n=== HEUTIGE NBA SPIELE ===")
    for game in games:
        print(f"{game['matchup']} - {game['time']} ({game['status']})")
