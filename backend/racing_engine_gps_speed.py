
import numpy as np
import json
from datetime import datetime
from collections import defaultdict, deque
from scipy.spatial.distance import cdist
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter
import pickle
import os
import warnings
warnings.filterwarnings('ignore')

class ProfessionalRacingEngine:
    """
    F1-Grade Professional Telemetry System
    Input: GPS (lat, lon) + Speed
    Features: Optimal lap, cornering analysis, racing line, tire prediction,
              race strategy, driver coaching, overtaking zones
    """
    
    def __init__(self, sector_definitions=None):
        # Core data structures
        self.sector_definitions = sector_definitions
        self.sectors_data = defaultdict(list)
        self.optimal_lap = {}
        self.lap_history = []
        self.current_lap_data = []
        self.sector_boundaries = []
        
        # Advanced analytics
        self.corner_data = defaultdict(list)
        self.brake_zones = []
        self.acceleration_zones = []
        self.tire_degradation_history = []
        self.consistency_analysis = []
        self.track_evolution = []
        self.driver_performance_metrics = []
        self.race_strategy_log = []
        self.overtaking_opportunities = []
        
        # Session data
        self.session_start_time = datetime.now()
        self.session_metadata = {}
        
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between GPS points in meters"""
        R = 6371000
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlambda = np.radians(lon2 - lon1)
        a = np.sin(dphi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        return R * c
    
    def calculate_bearing(self, lat1, lon1, lat2, lon2):
        """Calculate bearing between two points"""
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlon = lon2 - lon1
        x = np.sin(dlon) * np.cos(lat2)
        y = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dlon)
        bearing = np.arctan2(x, y)
        return (np.degrees(bearing) + 360) % 360
    
    def auto_detect_sectors(self, gps_points, num_sectors=3):
        """Intelligently divide track into sectors"""
        if len(gps_points) < num_sectors * 10:
            return None
        
        distances = []
        for i in range(1, len(gps_points)):
            d = self.haversine_distance(
                gps_points[i-1][0], gps_points[i-1][1],
                gps_points[i][0], gps_points[i][1]
            )
            distances.append(d)
        
        total_distance = sum(distances)
        sector_length = total_distance / num_sectors
        
        boundaries = [0]
        cumulative_dist = 0
        for i, d in enumerate(distances):
            cumulative_dist += d
            if cumulative_dist >= sector_length * len(boundaries) and len(boundaries) < num_sectors:
                boundaries.append(i)
        boundaries.append(len(gps_points) - 1)
        
        self.sector_boundaries = boundaries
        return boundaries
    
    def identify_sector(self, current_index):
        """Identify current sector"""
        if not self.sector_boundaries:
            return 0
        for i, boundary in enumerate(self.sector_boundaries[1:]):
            if current_index < boundary:
                return i
        return len(self.sector_boundaries) - 2
    
    # ========== CORNER DETECTION & ANALYSIS ==========
    
    def detect_corners_advanced(self, lap_data):
        """
        Advanced corner detection using GPS trajectory + speed
        Identifies: Entry, Apex, Exit for each corner
        """
        corners = []
        speeds = [p['speed'] for p in lap_data]
        
        # Smooth speed data
        if len(speeds) > 10:
            smoothed_speeds = savgol_filter(speeds, window_length=min(11, len(speeds)), polyorder=2)
        else:
            smoothed_speeds = speeds
        
        # Calculate trajectory curvature
        bearings = []
        for i in range(1, len(lap_data)):
            bearing = self.calculate_bearing(
                lap_data[i-1]['lat'], lap_data[i-1]['lon'],
                lap_data[i]['lat'], lap_data[i]['lon']
            )
            bearings.append(bearing)
        
        # Detect corners (high curvature + speed drop)
        for i in range(5, len(smoothed_speeds) - 5):
            # Check for speed drop (corner)
            if smoothed_speeds[i] < smoothed_speeds[i-3] and smoothed_speeds[i] < smoothed_speeds[i+3]:
                if smoothed_speeds[i] < 40:  # Corner threshold
                    
                    # Analyze corner characteristics
                    entry_speed = smoothed_speeds[i-5]
                    apex_speed = smoothed_speeds[i]
                    exit_speed = smoothed_speeds[i+5]
                    
                    # Calculate corner severity
                    speed_loss = entry_speed - apex_speed
                    corner_severity = speed_loss / entry_speed if entry_speed > 0 else 0
                    
                    # Calculate exit acceleration
                    exit_acceleration = exit_speed - apex_speed
                    
                    corner = {
                        'index': i,
                        'lat': lap_data[i]['lat'],
                        'lon': lap_data[i]['lon'],
                        'entry_speed': round(entry_speed, 1),
                        'apex_speed': round(apex_speed, 1),
                        'exit_speed': round(exit_speed, 1),
                        'speed_loss': round(speed_loss, 1),
                        'severity': round(corner_severity * 100, 1),
                        'exit_acceleration': round(exit_acceleration, 1),
                        'type': self._classify_corner(corner_severity, apex_speed)
                    }
                    
                    corners.append(corner)
        
        return corners
    
    def _classify_corner(self, severity, apex_speed):
        """Classify corner type"""
        if severity > 0.5:
            return "HAIRPIN"
        elif severity > 0.3:
            return "SLOW"
        elif apex_speed > 35:
            return "FAST"
        else:
            return "MEDIUM"
    
    def analyze_corner_performance(self, corners, lap_number):
        """
        ML-based corner performance analysis
        Identifies improvement opportunities per corner
        """
        corner_analysis = []
        
        for idx, corner in enumerate(corners):
            corner_id = f"corner_{idx}"
            
            # Calculate corner performance score
            # Higher exit speed + minimal speed loss = better
            performance_score = (corner['exit_acceleration'] * 2) - corner['speed_loss']
            
            # Store corner data for ML comparison
            self.corner_data[corner_id].append({
                'lap': lap_number,
                'performance_score': performance_score,
                'entry_speed': corner['entry_speed'],
                'apex_speed': corner['apex_speed'],
                'exit_speed': corner['exit_speed'],
                'location': (corner['lat'], corner['lon'])
            })
            
            # Compare to historical best
            if len(self.corner_data[corner_id]) > 1:
                all_scores = [c['performance_score'] for c in self.corner_data[corner_id]]
                best_score = max(all_scores)
                current_score = performance_score
                
                improvement_potential = ((best_score - current_score) / abs(best_score)) * 100 if best_score != 0 else 0
                
                if improvement_potential > 10:
                    corner_analysis.append({
                        'corner_id': corner_id,
                        'corner_number': idx + 1,
                        'improvement_potential': round(improvement_potential, 1),
                        'current_exit': corner['exit_speed'],
                        'best_exit': max([c['exit_speed'] for c in self.corner_data[corner_id]]),
                        'recommendation': self._get_corner_recommendation(corner, self.corner_data[corner_id]),
                        'location': (corner['lat'], corner['lon'])
                    })
        
        return corner_analysis
    
    def _get_corner_recommendation(self, current_corner, historical_data):
        """Generate corner-specific coaching"""
        best_corner = max(historical_data, key=lambda x: x['exit_speed'])
        
        entry_diff = current_corner['entry_speed'] - best_corner['entry_speed']
        exit_diff = current_corner['exit_speed'] - best_corner['exit_speed']
        
        if entry_diff < -3:
            return "⚠️ Entry too slow - brake later"
        elif exit_diff < -2:
            return "💡 Exit too slow - earlier throttle application"
        elif entry_diff > 3:
            return "⚠️ Entry too fast - brake earlier for better exit"
        else:
            return "✅ Good corner execution"
    
    # ========== BRAKE & ACCELERATION ZONES ==========
    
    def detect_brake_zones(self, lap_data):
        """Detect all braking zones with precision"""
        brake_zones = []
        speeds = [p['speed'] for p in lap_data]
        
        for i in range(1, len(speeds) - 1):
            deceleration = speeds[i-1] - speeds[i]
            
            if deceleration > 3:  # Braking detected
                brake_zones.append({
                    'index': i,
                    'lat': lap_data[i]['lat'],
                    'lon': lap_data[i]['lon'],
                    'speed_before': speeds[i-1],
                    'speed_after': speeds[i],
                    'deceleration_rate': round(deceleration, 2),
                    'brake_intensity': 'HARD' if deceleration > 10 else 'MODERATE'
                })
        
        return brake_zones
    
    def detect_acceleration_zones(self, lap_data):
        """Detect acceleration zones (corner exits, straights)"""
        accel_zones = []
        speeds = [p['speed'] for p in lap_data]
        
        for i in range(1, len(speeds) - 1):
            acceleration = speeds[i] - speeds[i-1]
            
            if acceleration > 2:  # Acceleration detected
                accel_zones.append({
                    'index': i,
                    'lat': lap_data[i]['lat'],
                    'lon': lap_data[i]['lon'],
                    'speed_before': speeds[i-1],
                    'speed_after': speeds[i],
                    'acceleration_rate': round(acceleration, 2),
                    'zone_type': 'CORNER_EXIT' if speeds[i-1] < 30 else 'STRAIGHT'
                })
        
        return accel_zones
    
    def optimize_brake_points(self, current_brake_zones):
        """Compare current braking to optimal braking"""
        if not self.brake_zones:
            return {}
        
        optimizations = []
        
        for current_bz in current_brake_zones:
            # Find closest historical brake zone
            for optimal_bz in self.brake_zones:
                distance = self.haversine_distance(
                    current_bz['lat'], current_bz['lon'],
                    optimal_bz['lat'], optimal_bz['lon']
                )
                
                if distance < 10:  # Same brake zone
                    speed_diff = optimal_bz['speed_before'] - current_bz['speed_before']
                    
                    if abs(speed_diff) > 2:
                        optimizations.append({
                            'location': (current_bz['lat'], current_bz['lon']),
                            'current_entry': current_bz['speed_before'],
                            'optimal_entry': optimal_bz['speed_before'],
                            'brake_earlier': speed_diff > 0,
                            'time_gain_potential': abs(speed_diff) * 0.05,  # Rough estimate
                            'recommendation': f"{'Brake earlier' if speed_diff > 0 else 'Brake later'} by ~{abs(speed_diff):.0f} km/h"
                        })
        
        return optimizations
    
    # ========== TIRE DEGRADATION PREDICTION ==========
    
    def predict_tire_degradation(self, lap_number, current_lap_avg_speed):
        """
        ML-based tire wear prediction using speed degradation
        Predicts: Grip level, laps remaining, pit recommendation
        """
        if len(self.lap_history) < 3:
            return {
                'grip_level': 100,
                'degradation_rate': 0,
                'laps_remaining': 999,
                'pit_recommended': False,
                'status': 'NEW_TIRES'
            }
        
        # Extract speed trend over laps
        recent_laps = self.lap_history[-min(10, len(self.lap_history)):]
        lap_numbers = [lap['lap_number'] for lap in recent_laps]
        avg_speeds = [lap['avg_speed'] for lap in recent_laps]
        
        # Linear regression for speed degradation
        if len(avg_speeds) >= 3:
            coeffs = np.polyfit(lap_numbers, avg_speeds, 1)
            degradation_rate = abs(coeffs[0])  # Speed loss per lap
        else:
            degradation_rate = 0
        
        # Calculate grip level
        initial_speed = avg_speeds[0]
        current_speed = current_lap_avg_speed
        speed_loss_percent = ((initial_speed - current_speed) / initial_speed) * 100 if initial_speed > 0 else 0
        
        grip_level = max(0, 100 - speed_loss_percent)
        
        # Predict laps to critical grip level (70%)
        critical_speed = initial_speed * 0.93  # 7% loss = 70% grip
        if degradation_rate > 0.01 and current_speed > critical_speed:
            laps_remaining = int((current_speed - critical_speed) / degradation_rate)
        else:
            laps_remaining = 999
        
        # Pit recommendation logic
        pit_recommended = (grip_level < 75) or (laps_remaining < 3)
        
        tire_status = {
            'lap': lap_number,
            'grip_level': round(grip_level, 1),
            'degradation_rate': round(degradation_rate, 3),
            'speed_loss_percent': round(speed_loss_percent, 2),
            'laps_remaining': laps_remaining,
            'pit_recommended': pit_recommended,
            'status': self._get_tire_status(grip_level)
        }
        
        self.tire_degradation_history.append(tire_status)
        return tire_status
    
    def _get_tire_status(self, grip):
        """Tire condition status"""
        if grip >= 95:
            return "EXCELLENT"
        elif grip >= 85:
            return "GOOD"
        elif grip >= 75:
            return "FAIR"
        elif grip >= 65:
            return "WORN"
        else:
            return "CRITICAL"
    
    # ========== DRIVER PERFORMANCE SCORING ==========
    
    def calculate_driver_performance(self, lap_info):
        """
        Comprehensive driver performance score (0-100)
        Factors: Speed, Consistency, Smoothness, Corner execution
        """
        if len(self.lap_history) < 2:
            return {'overall_score': 75, 'rating': 'B', 'status': 'INSUFFICIENT_DATA'}
        
        recent_laps = self.lap_history[-min(10, len(self.lap_history)):]
        
        # === 1. SPEED SCORE (40%) ===
        lap_times = [lap['total_time'] for lap in recent_laps]
        best_time = min(lap_times)
        current_time = lap_info['total_time']
        
        speed_score = max(0, 100 - ((current_time - best_time) / best_time) * 100)
        
        # === 2. CONSISTENCY SCORE (30%) ===
        time_std = np.std(lap_times)
        consistency_score = max(0, 100 - (time_std * 10))
        
        # === 3. SMOOTHNESS SCORE (30%) ===
        # Measure speed variance within lap
        lap_speeds = [p['speed'] for p in self.current_lap_data]
        if lap_speeds:
            speed_changes = [abs(lap_speeds[i] - lap_speeds[i-1]) for i in range(1, len(lap_speeds))]
            avg_change = np.mean(speed_changes) if speed_changes else 0
            smoothness_score = max(0, 100 - (avg_change * 5))
        else:
            smoothness_score = 75
        
        # === OVERALL SCORE ===
        overall_score = (speed_score * 0.4) + (consistency_score * 0.3) + (smoothness_score * 0.3)
        
        performance = {
            'lap': lap_info['lap_number'],
            'overall_score': round(overall_score, 1),
            'speed_score': round(speed_score, 1),
            'consistency_score': round(consistency_score, 1),
            'smoothness_score': round(smoothness_score, 1),
            'rating': self._get_performance_rating(overall_score),
            'trend': self._calculate_performance_trend()
        }
        
        self.driver_performance_metrics.append(performance)
        return performance
    
    def _get_performance_rating(self, score):
        """Convert score to letter grade"""
        if score >= 95:
            return 'S+'
        elif score >= 90:
            return 'S'
        elif score >= 85:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 75:
            return 'B+'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        else:
            return 'D'
    
    def _calculate_performance_trend(self):
        """Calculate if driver is improving or declining"""
        if len(self.driver_performance_metrics) < 3:
            return 'STABLE'
        
        recent_scores = [m['overall_score'] for m in self.driver_performance_metrics[-5:]]
        
        if len(recent_scores) >= 3:
            trend = recent_scores[-1] - recent_scores[0]
            if trend > 3:
                return 'IMPROVING'
            elif trend < -3:
                return 'DECLINING'
        
        return 'STABLE'
    
    # ========== RACE STRATEGY AI ==========
    
    def generate_race_strategy(self, lap_number, total_laps):
        """
        F1-Style Race Strategy Recommendations
        Analyzes: Pace, tire wear, track position, race phase
        """
        if not self.lap_history or lap_number < 2:
            return {
                'status': 'INSUFFICIENT_DATA',
                'recommendations': [],
                'race_phase': 'EARLY',
                'strategy_mode': 'SETTLE_IN'
            }
        
        recommendations = []
        priority_high = []
        priority_medium = []
        priority_low = []
        
        latest_lap = self.lap_history[-1]
        laps_remaining = total_laps - lap_number
        race_progress = lap_number / total_laps
        
        # === TIRE STRATEGY ===
        if self.tire_degradation_history:
            tire = self.tire_degradation_history[-1]
            
            if tire['pit_recommended']:
                priority_high.append({
                    'category': 'TIRES',
                    'icon': '🔴',
                    'message': f"Tire grip at {tire['grip_level']:.0f}% - PIT WITHIN {tire['laps_remaining']} LAPS",
                    'action': 'BOX_THIS_LAP' if tire['grip_level'] < 65 else 'PLAN_PIT_STOP',
                    'expected_gain': '+1.2s/lap with fresh tires'
                })
            elif tire['grip_level'] < 85:
                priority_medium.append({
                    'category': 'TIRES',
                    'icon': '🟡',
                    'message': f"Tire degradation detected ({tire['speed_loss_percent']:.1f}% pace loss)",
                    'action': 'MONITOR_CLOSELY',
                    'expected_gain': 'Consider pit window in 3-5 laps'
                })
        
        # === PACE ANALYSIS ===
        if len(self.lap_history) >= 5:
            recent_times = [lap['total_time'] for lap in self.lap_history[-5:]]
            pace_trend = recent_times[-1] - recent_times[0]
            
            if pace_trend > 1.0:  # Slowing significantly
                priority_high.append({
                    'category': 'PACE',
                    'icon': '⚠️',
                    'message': f"Pace dropping by {pace_trend:.2f}s over last 5 laps",
                    'action': 'CHECK_TIRE_PRESSURE',
                    'expected_gain': 'Investigate mechanical issues'
                })
            elif pace_trend < -0.3:  # Getting faster
                priority_low.append({
                    'category': 'PACE',
                    'icon': '✅',
                    'message': f"Pace improving by {abs(pace_trend):.2f}s - Excellent!",
                    'action': 'MAINTAIN_RHYTHM',
                    'expected_gain': 'Keep building confidence'
                })
        
        # === DRIVER PERFORMANCE ===
        if self.driver_performance_metrics:
            perf = self.driver_performance_metrics[-1]
            
            if perf['overall_score'] < 70:
                priority_medium.append({
                    'category': 'DRIVING',
                    'icon': '💡',
                    'message': f"Performance score: {perf['rating']} - Focus on consistency",
                    'action': 'SMOOTH_INPUTS',
                    'expected_gain': '+0.3s/lap potential'
                })
            elif perf['trend'] == 'IMPROVING':
                priority_low.append({
                    'category': 'DRIVING',
                    'icon': '📈',
                    'message': f"Performance improving - Rating: {perf['rating']}",
                    'action': 'KEEP_PUSHING',
                    'expected_gain': 'Momentum building'
                })
        
        # === RACE PHASE STRATEGY ===
        if race_progress < 0.3:  # Early race
            strategy_mode = "SETTLE_IN"
            phase_message = "Early race - Protect tires, find rhythm"
        elif race_progress < 0.7:  # Mid race
            strategy_mode = "MAINTAIN_PACE"
            phase_message = "Mid race - Consistent lap times, manage equipment"
        else:  # Late race
            strategy_mode = "ATTACK_MODE"
            phase_message = f"Final {laps_remaining} laps - PUSH FOR POSITION"
            
            priority_high.append({
                'category': 'STRATEGY',
                'icon': '🏁',
                'message': phase_message,
                'action': 'MAXIMUM_ATTACK',
                'expected_gain': 'Race is now'
            })
        
        # === LAP COUNT ALERTS ===
        if laps_remaining == 5:
            priority_high.append({
                'category': 'RACE_INFO',
                'icon': '⏱️',
                'message': "5 LAPS REMAINING - Final push",
                'action': 'GIVE_IT_EVERYTHING',
                'expected_gain': 'No tire saving needed'
            })
        elif laps_remaining == 1:
            priority_high.append({
                'category': 'RACE_INFO',
                'icon': '🏁',
                'message': "FINAL LAP - Maximum attack",
                'action': 'QUALIFYING_MODE',
                'expected_gain': 'Last chance for positions'
            })
        
        # Compile all recommendations
        recommendations = priority_high + priority_medium + priority_low
        
        strategy = {
            'lap': lap_number,
            'laps_remaining': laps_remaining,
            'race_progress': round(race_progress * 100, 1),
            'race_phase': self._get_race_phase(race_progress),
            'strategy_mode': strategy_mode,
            'recommendations': recommendations,
            'priority_action': recommendations[0] if recommendations else None
        }
        
        self.race_strategy_log.append(strategy)
        return strategy
    
    def _get_race_phase(self, progress):
        """Determine current race phase"""
        if progress < 0.25:
            return "OPENING"
        elif progress < 0.5:
            return "EARLY"
        elif progress < 0.75:
            return "MIDDLE"
        else:
            return "CLOSING"
    
    # ========== OVERTAKING OPPORTUNITIES ==========
    
    def detect_overtaking_zones(self, lap_data):
        """
        Identify optimal overtaking opportunities
        Based on: High-speed sections, post-corner acceleration zones
        """
        overtaking_zones = []
        speeds = [p['speed'] for p in lap_data]
        
        # Find high-speed sections (good for drafting/overtaking)
        for i in range(5, len(speeds) - 5):
            avg_speed = np.mean(speeds[i-5:i+5])
            
            if avg_speed > 50:  # High-speed zone
                overtaking_zones.append({
                    'index': i,
                    'lat': lap_data[i]['lat'],
                    'lon': lap_data[i]['lon'],
                    'type': 'HIGH_SPEED_STRAIGHT',
                    'avg_speed': round(avg_speed, 1),
                    'confidence': 0.85,
                    'recommendation': 'Use slipstream for overtake'
                })
        
        # Find corner exits (acceleration zones)
        for i in range(1, len(speeds) - 5):
            if speeds[i] < 35 and speeds[i+5] > speeds[i] + 10:  # Corner exit
                overtaking_zones.append({
                    'index': i,
                    'lat': lap_data[i]['lat'],
                    'lon': lap_data[i]['lon'],
                    'type': 'CORNER_EXIT',
                    'exit_speed': speeds[i+5],
                    'confidence': 0.70,
                    'recommendation': 'Better exit = overtake next straight'
                })
        
        self.overtaking_opportunities = overtaking_zones
        return overtaking_zones
    
    # ========== LAP PROCESSING ==========
    
    def process_lap(self, lap_data):
        """
        Complete lap processing with all advanced features
        Input: List of {timestamp, lat, lon, speed}
        """
        if len(lap_data) < 10:
            return None
        
        # Auto-detect sectors on first lap
        gps_points = [(d['lat'], d['lon']) for d in lap_data]
        if not self.sector_boundaries:
            self.auto_detect_sectors(gps_points)
        
        # === SECTOR ANALYSIS ===
        sector_times = {}
        sector_data = defaultdict(list)
        
        for i, point in enumerate(lap_data):
            sector_id = self.identify_sector(i)
            sector_data[sector_id].append(point)
        
        for sector_id, points in sector_data.items():
            if len(points) >= 2:
                sector_times[sector_id] = {
                    'time': points[-1]['timestamp'] - points[0]['timestamp'],
                    'data': points,
                    'avg_speed': np.mean([p['speed'] for p in points]),
                    'max_speed': max([p['speed'] for p in points]),
                    'min_speed': min([p['speed'] for p in points])
                }
        
        lap_number = len(self.lap_history) + 1
        lap_total_time = lap_data[-1]['timestamp'] - lap_data[0]['timestamp']
        avg_speed = np.mean([p['speed'] for p in lap_data])
        max_speed = max([p['speed'] for p in lap_data])
        
        # === ADVANCED ANALYSIS ===
        corners = self.detect_corners_advanced(lap_data)
        corner_analysis = self.analyze_corner_performance(corners, lap_number)
        brake_zones = self.detect_brake_zones(lap_data)
        accel_zones = self.detect_acceleration_zones(lap_data)
        brake_optimization = self.optimize_brake_points(brake_zones)
        tire_status = self.predict_tire_degradation(lap_number, avg_speed)
        overtaking_zones = self.detect_overtaking_zones(lap_data)
        
        # Store current lap data for smoothness calculation
        self.current_lap_data = lap_data
        
        # === COMPILE LAP INFO ===
        lap_info = {
            'lap_number': lap_number,
            'total_time': lap_total_time,
            'avg_speed': avg_speed,
            'max_speed': max_speed,
            'sectors': sector_times,
            'timestamp': datetime.now().isoformat(),
            
            # Advanced metrics
            'corners': corners,
            'corner_analysis': corner_analysis,
            'brake_zones': brake_zones,
            'accel_zones': accel_zones,
            'brake_optimization': brake_optimization,
            'tire_status': tire_status,
            'overtaking_zones': overtaking_zones
        }
        
        # Calculate driver performance
        if len(self.lap_history) >= 1:
            lap_info['performance'] = self.calculate_driver_performance(lap_info)
        
        self.lap_history.append(lap_info)
        self.update_optimal_lap(lap_info)
        
        # Update brake zones history
        if brake_zones:
            self.brake_zones.extend(brake_zones)
        
        return lap_info
    
    def update_optimal_lap(self, new_lap_info):
        """Update optimal lap with best sectors"""
        updated_sectors = []
        
        for sector_id, sector_data in new_lap_info['sectors'].items():
            current_best = self.optimal_lap.get(sector_id, {}).get('time', float('inf'))
            
            if sector_data['time'] < current_best:
                self.optimal_lap[sector_id] = {
                    'time': sector_data['time'],
                    'data': sector_data['data'],
                    'lap_number': new_lap_info['lap_number'],
                    'avg_speed': sector_data['avg_speed'],
                    'max_speed': sector_data['max_speed']
                }
                updated_sectors.append(sector_id)
        
        return updated_sectors
    
    def get_optimal_lap_time(self):
        """Calculate theoretical optimal lap time"""
        if not self.optimal_lap:
            return None
        
        total_time = sum(sector['time'] for sector in self.optimal_lap.values())
        return {
            'optimal_time': total_time,
            'sectors': self.optimal_lap,
            'improvement_potential': self.calculate_improvement_potential()
        }
    
    def calculate_improvement_potential(self):
        """Calculate potential time gain"""
        if not self.lap_history:
            return 0
        
        fastest_lap = min(self.lap_history, key=lambda x: x['total_time'])
        optimal_time = sum(sector['time'] for sector in self.optimal_lap.values())
        
        return fastest_lap['total_time'] - optimal_time
    
    def calculate_real_time_delta(self, current_position, current_sector, elapsed_time):
        """Real-time delta vs optimal lap"""
        if current_sector not in self.optimal_lap:
            return 0
        
        optimal_sector_data = self.optimal_lap[current_sector]['data']
        optimal_position_index = min(
            int((current_position / len(optimal_sector_data)) * len(optimal_sector_data)),
            len(optimal_sector_data) - 1
        )
        
        optimal_elapsed = optimal_sector_data[optimal_position_index]['timestamp'] - optimal_sector_data[0]['timestamp']
        return optimal_elapsed - elapsed_time
    
    def predict_lap_time(self, current_lap_data, current_sector):
        """ML-based lap time prediction"""
        if len(self.lap_history) < 3:
            return None
        
        completed_sectors = list(range(current_sector + 1))
        current_sector_times = []
        
        for sector_id in completed_sectors:
            sector_points = [p for i, p in enumerate(current_lap_data) 
                           if self.identify_sector(i) == sector_id]
            if len(sector_points) >= 2:
                sector_time = sector_points[-1]['timestamp'] - sector_points[0]['timestamp']
                current_sector_times.append(sector_time)
        
        # Build training data
        X, y = [], []
        for lap in self.lap_history:
            early_times = [lap['sectors'][sid]['time'] for sid in completed_sectors 
                          if sid in lap['sectors']]
            if len(early_times) == len(completed_sectors):
                X.append(early_times)
                y.append(lap['total_time'])
        
        if len(X) < 2:
            return None
        
        X = np.array(X)
        y = np.array(y)
        current_times = np.array(current_sector_times)
        
        # Weighted prediction based on similarity
        similarities = 1 / (1 + np.abs(X - current_times).sum(axis=1))
        weights = similarities / similarities.sum()
        predicted_time = np.sum(weights * y)
        
        return {
            'predicted_lap_time': predicted_time,
            'confidence': np.max(weights),
            'optimal_time': self.get_optimal_lap_time()['optimal_time'] if self.optimal_lap else None
        }
    
    def get_racing_line(self):
        """Extract optimal racing line from best sectors"""
        racing_line = []
        for sector_id in sorted(self.optimal_lap.keys()):
            racing_line.extend([(p['lat'], p['lon']) for p in self.optimal_lap[sector_id]['data']])
        return racing_line
    
    def identify_improvement_zones(self):
        """Identify sectors with most time loss"""
        if not self.lap_history or len(self.lap_history) < 3:
            return {}
        
        latest_lap = self.lap_history[-1]
        improvement_zones = {}
        
        for sector_id, sector_data in latest_lap['sectors'].items():
            if sector_id in self.optimal_lap:
                time_delta = sector_data['time'] - self.optimal_lap[sector_id]['time']
                improvement_zones[f'sector_{sector_id}'] = {
                    'time_loss': time_delta,
                    'percentage_loss': (time_delta / self.optimal_lap[sector_id]['time']) * 100,
                    'optimal_avg_speed': self.optimal_lap[sector_id]['avg_speed'],
                    'current_avg_speed': sector_data['avg_speed'],
                    'speed_deficit': self.optimal_lap[sector_id]['avg_speed'] - sector_data['avg_speed']
                }
        
        return dict(sorted(improvement_zones.items(), key=lambda x: x[1]['time_loss'], reverse=True))
    
    def save_session(self, filename=None):
        """Save complete session data"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'sessions/racing_session_{timestamp}.pkl'
        
        os.makedirs('sessions', exist_ok=True)
        
        session_data = {
            'lap_history': self.lap_history,
            'optimal_lap': self.optimal_lap,
            'sector_boundaries': self.sector_boundaries,
            'corner_data': dict(self.corner_data),
            'brake_zones': self.brake_zones,
            'tire_degradation_history': self.tire_degradation_history,
            'driver_performance_metrics': self.driver_performance_metrics,
            'race_strategy_log': self.race_strategy_log,
            'overtaking_opportunities': self.overtaking_opportunities,
            'session_metadata': {
                'date': datetime.now().isoformat(),
                'duration': str(datetime.now() - self.session_start_time),
                'total_laps': len(self.lap_history),
                'best_lap_time': min([l['total_time'] for l in self.lap_history]) if self.lap_history else None,
                'best_lap_number': min(self.lap_history, key=lambda x: x['total_time'])['lap_number'] if self.lap_history else None
            }
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(session_data, f)
        
        # Also save JSON version for easy viewing
        json_filename = filename.replace('.pkl', '.json')
        with open(json_filename, 'w') as f:
            # Convert numpy types to Python types for JSON
            json_safe_data = json.loads(json.dumps(session_data, default=str))
            json.dump(json_safe_data, f, indent=2)
        
        return filename
    
    def load_session(self, filename):
        """Load previous session"""
        with open(filename, 'rb') as f:
            session_data = pickle.load(f)
        
        self.lap_history = session_data.get('lap_history', [])
        self.optimal_lap = session_data.get('optimal_lap', {})
        self.sector_boundaries = session_data.get('sector_boundaries', [])
        self.corner_data = defaultdict(list, session_data.get('corner_data', {}))
        self.brake_zones = session_data.get('brake_zones', [])
        self.tire_degradation_history = session_data.get('tire_degradation_history', [])
        self.driver_performance_metrics = session_data.get('driver_performance_metrics', [])
        self.race_strategy_log = session_data.get('race_strategy_log', [])
        self.overtaking_opportunities = session_data.get('overtaking_opportunities', [])
        
        return True


# ========== API WRAPPER ==========

class RacingTelemetryAPI:
    """API wrapper for real-time telemetry processing"""
    
    def __init__(self, race_total_laps=20):
        self.engine = ProfessionalRacingEngine()
        self.current_lap_buffer = []
        self.lap_start_time = None
        self.race_total_laps = race_total_laps
        
    def process_telemetry_point(self, data_point):
        """Process real-time GPS + Speed data"""
        # Check for lap completion
        if self.should_start_new_lap(data_point):
            if self.current_lap_buffer:
                lap_result = self.engine.process_lap(self.current_lap_buffer)
                
                # Generate race strategy
                strategy = self.engine.generate_race_strategy(
                    lap_result['lap_number'],
                    self.race_total_laps
                )
                
                self.current_lap_buffer = []
                
                return {
                    'lap_completed': True,
                    'lap_data': lap_result,
                    'race_strategy': strategy
                }
            
            self.lap_start_time = data_point['timestamp']
        
        self.current_lap_buffer.append(data_point)
        
        # Real-time delta calculation
        if self.engine.optimal_lap and len(self.current_lap_buffer) > 5:
            current_sector = self.engine.identify_sector(len(self.current_lap_buffer) - 1)
            delta = self.engine.calculate_real_time_delta(
                len(self.current_lap_buffer) - 1,
                current_sector,
                data_point['timestamp'] - self.lap_start_time
            )
            
            prediction = self.engine.predict_lap_time(self.current_lap_buffer, current_sector)
            
            return {
                'lap_completed': False,
                'delta': delta,
                'current_sector': current_sector,
                'prediction': prediction,
                'optimal_lap_time': self.engine.get_optimal_lap_time()
            }
        
        return {'lap_completed': False, 'delta': 0}
    
    def should_start_new_lap(self, data_point):
        """Detect lap start/finish"""
        if not self.current_lap_buffer or not self.lap_start_time:
            return True
        
        if len(self.current_lap_buffer) < 50:  # Minimum points per lap
            return False
        
        # Check if returned to start position
        start_point = self.current_lap_buffer[0]
        distance = self.engine.haversine_distance(
            start_point['lat'], start_point['lon'],
            data_point['lat'], data_point['lon']
        )
        
        return distance < 20  # Within 20 meters of start
    
    def get_dashboard_data(self):
        """Get complete dashboard data for frontend"""

        latest_lap = self.engine.lap_history[-1] if self.engine.lap_history else None

        # 🔥 Add current live position
        current_position = None
        if self.current_lap_buffer:
            last_point = self.current_lap_buffer[-1]
            current_position = {
                "lat": last_point.get("lat"),
                "lon": last_point.get("lon")
            }

        return {
            'current_position': current_position,   # ✅ NEW FIELD
            'optimal_lap': self.engine.get_optimal_lap_time(),
            'lap_history': self.engine.lap_history[-15:],
            'racing_line': self.engine.get_racing_line(),
            'improvement_zones': self.engine.identify_improvement_zones(),
            'latest_lap': latest_lap,
            'tire_status': self.engine.tire_degradation_history[-1] if self.engine.tire_degradation_history else None,
            'performance': self.engine.driver_performance_metrics[-1] if self.engine.driver_performance_metrics else None,
            'race_strategy': self.engine.generate_race_strategy(
                len(self.engine.lap_history),
                self.race_total_laps
            ) if self.engine.lap_history else None,
            'overtaking_zones': self.engine.overtaking_opportunities,
            'session_stats': {
                'total_laps': len(self.engine.lap_history),
                'best_lap': min(self.engine.lap_history, key=lambda x: x['total_time']) if self.engine.lap_history else None,
                'avg_lap_time': np.mean([l['total_time'] for l in self.engine.lap_history]) if self.engine.lap_history else None
            }
        }


    def set_race_total_laps(self, total_laps):
        """Update total race laps"""
        self.race_total_laps = total_laps
