import paho.mqtt.client as mqtt
import ssl
import json

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from datetime import datetime
import os
import sys

# Import the racing engine
from racing_engine_gps_speed import RacingTelemetryAPI

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Initialize Racing Engine
telemetry_api = RacingTelemetryAPI(race_total_laps=20)

def on_connect(client, userdata, flags, rc):
    print("✅ Connected to HiveMQ from Flask")
    client.subscribe(MQTT_CONFIG["topic"])

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        # 🔥 Normalize data for engine
        clean_data = {
            "lat": float(payload.get("lat")),
            "lon": float(payload.get("lon")),
            "speed": float(payload.get("speed", 0)),
            "timestamp": float(payload.get("timestamp"))
        }

        telemetry_api.process_telemetry_point(clean_data)

    except Exception as e:
        print("MQTT Processing Error:", e)

def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_CONFIG["username"], MQTT_CONFIG["password"])
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_CONFIG["broker"], MQTT_CONFIG["port"], 60)
    client.loop_start()
    return client

MQTT_CONFIG = {
    "broker": "f08ca48a560941289a2893683c0ff7a6.s1.eu.hivemq.cloud",
    "port": 8883,
    "username": "teamtrydan",
    "password": "Trydan25",
    "topic": "kart/gps/teamXkart01/telemetry"
}

# ========== API ENDPOINTS ==========

@app.route('/api/telemetry', methods=['POST'])
def receive_telemetry():
    """
    Receive real-time telemetry from MQTT bridge
    Expected: {timestamp, lat, lon, speed}
    """
    try:
        data = request.json
        result = telemetry_api.process_telemetry_point(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get complete dashboard data"""
    try:
        data = telemetry_api.get_dashboard_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimal_lap', methods=['GET'])
def get_optimal_lap():
    """Get current optimal lap data"""
    try:
        optimal = telemetry_api.engine.get_optimal_lap_time()
        return jsonify(optimal if optimal else {'status': 'NO_DATA'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/racing_line', methods=['GET'])
def get_racing_line():
    """Get optimal racing line for map overlay"""
    try:
        racing_line = telemetry_api.engine.get_racing_line()
        return jsonify(racing_line)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/improvement_zones', methods=['GET'])
def get_improvement_zones():
    """Get sectors where driver is losing most time"""
    try:
        zones = telemetry_api.engine.identify_improvement_zones()
        return jsonify(zones)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/race_strategy', methods=['GET'])
def get_race_strategy():
    """Get AI race strategy recommendations"""
    try:
        lap_number = len(telemetry_api.engine.lap_history)
        strategy = telemetry_api.engine.generate_race_strategy(
            lap_number, 
            telemetry_api.race_total_laps
        )
        return jsonify(strategy)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tire_status', methods=['GET'])
def get_tire_status():
    """Get tire degradation status"""
    try:
        if telemetry_api.engine.tire_degradation_history:
            tire_status = telemetry_api.engine.tire_degradation_history[-1]
            return jsonify(tire_status)
        return jsonify({'status': 'NO_DATA'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/performance', methods=['GET'])
def get_performance():
    """Get driver performance metrics"""
    try:
        if telemetry_api.engine.driver_performance_metrics:
            performance = telemetry_api.engine.driver_performance_metrics[-1]
            return jsonify(performance)
        return jsonify({'status': 'NO_DATA'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/corner_analysis', methods=['GET'])
def get_corner_analysis():
    """Get corner-by-corner analysis"""
    try:
        if telemetry_api.engine.lap_history:
            latest_lap = telemetry_api.engine.lap_history[-1]
            corner_analysis = latest_lap.get('corner_analysis', [])
            return jsonify(corner_analysis)
        return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/overtaking_zones', methods=['GET'])
def get_overtaking_zones():
    """Get optimal overtaking opportunities"""
    try:
        zones = telemetry_api.engine.overtaking_opportunities
        return jsonify(zones)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/session_stats', methods=['GET'])
def get_session_stats():
    """Get session statistics"""
    try:
        if not telemetry_api.engine.lap_history:
            return jsonify({'status': 'NO_DATA'})
        
        lap_times = [lap['total_time'] for lap in telemetry_api.engine.lap_history]
        best_lap = min(telemetry_api.engine.lap_history, key=lambda x: x['total_time'])
        
        stats = {
            'total_laps': len(telemetry_api.engine.lap_history),
            'best_lap': best_lap,
            'best_lap_time': best_lap['total_time'],
            'best_lap_number': best_lap['lap_number'],
            'average_lap_time': sum(lap_times) / len(lap_times),
            'last_5_avg': sum(lap_times[-5:]) / len(lap_times[-5:]) if len(lap_times) >= 5 else None,
            'consistency': min(100, (1 - (max(lap_times) - min(lap_times)) / min(lap_times)) * 100)
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save_session', methods=['POST'])
def save_session():
    """Save current session"""
    try:
        filename = telemetry_api.engine.save_session()
        return jsonify({
            'status': 'SUCCESS',
            'filename': filename,
            'message': 'Session saved successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load_session', methods=['POST'])
def load_session():
    """Load previous session"""
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'No filename provided'}), 400
        
        success = telemetry_api.engine.load_session(filename)
        
        return jsonify({
            'status': 'SUCCESS' if success else 'FAILED',
            'message': 'Session loaded successfully' if success else 'Failed to load session'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/set_race_laps', methods=['POST'])
def set_race_laps():
    """Set total race laps"""
    try:
        data = request.json
        total_laps = data.get('total_laps', 20)
        telemetry_api.set_race_total_laps(total_laps)
        
        return jsonify({
            'status': 'SUCCESS',
            'total_laps': total_laps
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/lap_history', methods=['GET'])
def get_lap_history():
    """Get lap history"""
    try:
        limit = request.args.get('limit', 15, type=int)
        laps = telemetry_api.engine.lap_history[-limit:]
        return jsonify(laps)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ONLINE',
        'service': 'Professional Racing Telemetry API',
        'version': '2.0',
        'timestamp': datetime.now().isoformat()
    })

# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ========== RUN SERVER ==========

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏎️  PROFESSIONAL RACING TELEMETRY SYSTEM")
    print("="*60)
    print("✓ ML Engine: GPS + Speed Analysis")
    print("✓ Features: Optimal Lap, Race Strategy, Tire Prediction")
    print("✓ API Server: http://localhost:5000")
    print("="*60 + "\n")
    mqtt_client = start_mqtt()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
