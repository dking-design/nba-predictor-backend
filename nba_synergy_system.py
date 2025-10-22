
import pandas as pd
import numpy as np
import json

class TeamSynergyCalculator:
    """
    Berechnet Team-Synergien basierend auf Spieler-Kombinationen
    """
    
    def __init__(self, player_data_file='nba_players_2024-25.json'):
        """Lädt Spieler-Daten"""
        with open(player_data_file, 'r') as f:
            self.players = json.load(f)
        print(f"✓ {len(self.players)} Spieler geladen")
    
    def get_player_stats(self, player_name):
        """Holt Stats für einen Spieler"""
        return self.players.get(player_name)
    
    def calculate_spacing_synergy(self, lineup):
        """
        SPACING: Gute 3-Point-Shooter schaffen Raum für Drives
        """
        three_point_threats = 0
        total_three_point_score = 0
        
        for player in lineup:
            if player['stats'].get('THREE_POINT_THREAT', 0) > 2.0:
                three_point_threats += 1
                total_three_point_score += player['stats'].get('THREE_POINT_THREAT', 0)
        
        # Bonus wenn 3+ gute Shooter
        spacing_bonus = 1.0
        if three_point_threats >= 3:
            spacing_bonus = 1.15
        elif three_point_threats >= 4:
            spacing_bonus = 1.25
        
        return total_three_point_score * spacing_bonus
    
    def calculate_playmaking_synergy(self, lineup):
        """
        PLAYMAKING: Gute Passer erhöhen die Effizienz aller Scorer
        """
        playmakers = [p for p in lineup if p['type'] == 'PLAYMAKER']
        scorers = [p for p in lineup if p['type'] in ['SCORER', 'SHOOTER']]
        
        if not playmakers:
            return 0
        
        # Je mehr Playmaker, desto besser die Offense
        playmaking_score = sum(p['stats'].get('PLAYMAKING_SCORE', 0) for p in playmakers)
        
        # Bonus wenn Scorer vorhanden sind die davon profitieren
        if scorers:
            synergy_multiplier = 1 + (len(scorers) * 0.1)
            return playmaking_score * synergy_multiplier
        
        return playmaking_score
    
    def calculate_rebounding_synergy(self, lineup):
        """
        REBOUNDING: Mehrere starke Rebounder dominieren das Glas
        """
        total_rebounds = sum(p['stats'].get('REB', 0) for p in lineup)
        
        # Zähle starke Rebounder (>6 RPG)
        strong_rebounders = sum(1 for p in lineup if p['stats'].get('REB', 0) > 6)
        
        # Bonus für multiple Rebounder
        if strong_rebounders >= 2:
            total_rebounds *= 1.2
        if strong_rebounders >= 3:
            total_rebounds *= 1.35
        
        return total_rebounds
    
    def calculate_defense_synergy(self, lineup):
        """
        DEFENSE: Kombination aus Rim Protection, Perimeter Defense, Versatility
        """
        bigs = [p for p in lineup if p['type'] == 'BIG']
        wings = [p for p in lineup if p['type'] == 'WING']
        
        defense_score = sum(p['stats'].get('DEFENSE_SCORE', 0) for p in lineup)
        
        # Rim Protection Bonus (Big Man mit guten Blocks)
        if bigs:
            rim_protector = max(bigs, key=lambda x: x['stats'].get('BLK', 0))
            if rim_protector['stats'].get('BLK', 0) >= 1.5:
                defense_score *= 1.15
        
        # Versatility Bonus (viele Wings können verschiedene Positionen verteidigen)
        if len(wings) >= 2:
            defense_score *= 1.1
        
        return defense_score
    
    def calculate_ball_movement_synergy(self, lineup):
        """
        BALL MOVEMENT: Hohe Assist-Raten führen zu besserer Effizienz
        """
        total_assists = sum(p['stats'].get('AST', 0) for p in lineup)
        avg_ast_ratio = np.mean([p['stats'].get('AST_RATIO', 0) for p in lineup])
        
        # Bonus wenn Team-Assists hoch sind
        ball_movement_score = total_assists * (1 + avg_ast_ratio)
        
        # Extra Bonus wenn kein Ball-Dominant Spieler (ausgeglichenes Spiel)
        high_usage_players = sum(1 for p in lineup if p['stats'].get('USAGE_RATE', 0) > 0.3)
        if high_usage_players <= 1:
            ball_movement_score *= 1.1
        
        return ball_movement_score
    
    def calculate_size_advantage(self, lineup):
        """
        SIZE: Größenvorteil bei Rebounds und Paint-Scoring
        """
        bigs = sum(1 for p in lineup if p['type'] == 'BIG')
        
        size_score = bigs * 5  # Basis-Score
        
        # Bonus für 2 Bigs (Twin Towers)
        if bigs >= 2:
            size_score *= 1.3
        
        return size_score
    
    def calculate_scoring_balance(self, lineup):
        """
        BALANCE: Ausgeglichenes Scoring ist schwerer zu verteidigen
        """
        scoring_volumes = [p['stats'].get('SCORING_VOLUME', 0) for p in lineup]
        
        # Standard-Abweichung als Maß für Ausgeglichenheit
        # Niedriger = ausgeglichener
        std_dev = np.std(scoring_volumes)
        
        # Invertiere: Je niedriger std_dev, desto höher der Score
        balance_score = 50 / (1 + std_dev)
        
        return balance_score
    
    def calculate_team_stats(self, lineup):
        """
        Berechnet Gesamt-Team-Stats aus 5 Spielern
        """
        team_stats = {
            'PTS': sum(p['stats'].get('PTS', 0) for p in lineup),
            'FG_PCT': np.mean([p['stats'].get('FG_PCT', 0) for p in lineup if p['stats'].get('FG_PCT', 0) > 0]),
            'FG3_PCT': np.mean([p['stats'].get('FG3_PCT', 0) for p in lineup if p['stats'].get('FG3_PCT', 0) > 0]),
            'REB': sum(p['stats'].get('REB', 0) for p in lineup),
            'AST': sum(p['stats'].get('AST', 0) for p in lineup),
            'TOV': sum(p['stats'].get('TOV', 0) for p in lineup),
            'STL': sum(p['stats'].get('STL', 0) for p in lineup),
            'BLK': sum(p['stats'].get('BLK', 0) for p in lineup),
        }
        
        return team_stats
    
    def calculate_all_synergies(self, lineup):
        """
        Berechnet alle Synergien für ein Lineup
        """
        synergies = {
            'spacing': self.calculate_spacing_synergy(lineup),
            'playmaking': self.calculate_playmaking_synergy(lineup),
            'rebounding': self.calculate_rebounding_synergy(lineup),
            'defense': self.calculate_defense_synergy(lineup),
            'ball_movement': self.calculate_ball_movement_synergy(lineup),
            'size': self.calculate_size_advantage(lineup),
            'balance': self.calculate_scoring_balance(lineup)
        }
        
        # Gesamt-Synergy-Score
        synergies['total'] = sum(synergies.values())
        
        return synergies
    
    def compare_lineups(self, lineup1_names, lineup2_names):
        """
        Vergleicht zwei Lineups und gibt detaillierte Analyse
        """
        # Lade Spieler-Daten
        lineup1 = [self.get_player_stats(name) for name in lineup1_names]
        lineup2 = [self.get_player_stats(name) for name in lineup2_names]
        
        # Prüfe ob alle Spieler gefunden wurden
        if None in lineup1:
            missing = [lineup1_names[i] for i, p in enumerate(lineup1) if p is None]
            print(f"❌ Spieler nicht gefunden in Team 1: {missing}")
            return None
        
        if None in lineup2:
            missing = [lineup2_names[i] for i, p in enumerate(lineup2) if p is None]
            print(f"❌ Spieler nicht gefunden in Team 2: {missing}")
            return None
        
        # Berechne Stats
        team1_stats = self.calculate_team_stats(lineup1)
        team2_stats = self.calculate_team_stats(lineup2)
        
        # Berechne Synergien
        team1_synergies = self.calculate_all_synergies(lineup1)
        team2_synergies = self.calculate_all_synergies(lineup2)
        
        return {
            'team1': {
                'lineup': lineup1_names,
                'stats': team1_stats,
                'synergies': team1_synergies
            },
            'team2': {
                'lineup': lineup2_names,
                'stats': team2_stats,
                'synergies': team2_synergies
            }
        }
    
    def print_comparison(self, comparison):
        """
        Zeigt detaillierten Vergleich
        """
        if not comparison:
            return
        
        team1 = comparison['team1']
        team2 = comparison['team2']
        
        print("\n" + "="*70)
        print("📊 TEAM VERGLEICH")
        print("="*70)
        
        # Team 1
        print("\n🏠 TEAM 1:")
        for name in team1['lineup']:
            print(f"   - {name}")
        
        print("\n  Basis-Stats:")
        for stat, value in team1['stats'].items():
            print(f"    {stat}: {value:.1f}")
        
        print("\n  Synergien:")
        for syn, value in team1['synergies'].items():
            print(f"    {syn.upper()}: {value:.1f}")
        
        # Team 2
        print("\n✈️  TEAM 2:")
        for name in team2['lineup']:
            print(f"   - {name}")
        
        print("\n  Basis-Stats:")
        for stat, value in team2['stats'].items():
            print(f"    {stat}: {value:.1f}")
        
        print("\n  Synergien:")
        for syn, value in team2['synergies'].items():
            print(f"    {syn.upper()}: {value:.1f}")
        
        # Vorteile
        print("\n" + "="*70)
        print("🎯 VORTEILE:")
        print("="*70)
        
        if team1['synergies']['total'] > team2['synergies']['total']:
            print(f"✓ Team 1 hat bessere Gesamt-Synergien (+{team1['synergies']['total'] - team2['synergies']['total']:.1f})")
        else:
            print(f"✓ Team 2 hat bessere Gesamt-Synergien (+{team2['synergies']['total'] - team1['synergies']['total']:.1f})")
        
        if team1['stats']['PTS'] > team2['stats']['PTS']:
            print(f"✓ Team 1 hat mehr Scoring-Power (+{team1['stats']['PTS'] - team2['stats']['PTS']:.1f} PPG)")
        else:
            print(f"✓ Team 2 hat mehr Scoring-Power (+{team2['stats']['PTS'] - team1['stats']['PTS']:.1f} PPG)")


# Beispiel-Nutzung
if __name__ == "__main__":
    calc = TeamSynergyCalculator()
    
    # Beispiel-Lineups
    lakers_lineup = [
        'LeBron James',
        'Anthony Davis',
        'Austin Reaves',
        'Rui Hachimura',
        "D'Angelo Russell"
    ]
    
    warriors_lineup = [
        'Stephen Curry',
        'Klay Thompson',
        'Andrew Wiggins',
        'Draymond Green',
        'Kevon Looney'
    ]
    
    comparison = calc.compare_lineups(lakers_lineup, warriors_lineup)
    calc.print_comparison(comparison)
