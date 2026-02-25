// ========================================
// PROFESSIONAL RACING TELEMETRY SYSTEM
// COMPLETE WORKING VERSION - NMIT BANGALORE
// ========================================

const USE_LOCAL_DATA = false;
const OPTIMAL_LAP_API = 'http://localhost:5000/api';
const ENABLE_DUMMY_DATA = false;

// ========== GLOBAL STATE ==========
let dashboardData = null;
let racingLinePolyline = null;
let overtakingMarkers = [];
let sessionStartTime = Date.now();
let currentLap = 1;
let totalLaps = 20;
let bestLapTime = 85.789;
let kartMarker = null;
let map = null;
let speedChart = null;
let animationIndex = 0;
let smoothTrackPoints = [];

// ========== EXACT NMIT TRACK COORDINATES ==========
const NMIT_TRACK = [
    [13.129051169254026, 77.58824465835409],
    [13.127103188230876, 77.58793157446041],
    [13.127103188230876, 77.58792287768534],
    [13.12711165774725, 77.58755761314336],
    [13.127120127263268, 77.58756630991832],
    [13.127619828181466, 77.58609655497531],
    [13.127619828181466, 77.58610525175038],
    [13.127823096060482, 77.58600089045183],
    [13.127831565552, 77.58600089045183],
    [13.129186680403407, 77.58633136789558],
    [13.129186680403407, 77.58633136789558],
    [13.12904269980541, 77.58826205190411],
    [13.129051169254026, 77.58824465835409]
];

// ========== SMOOTH INTERPOLATION ==========
function createSmoothTrack(points, stepsPerSegment = 20) {
    const smoothPoints = [];
    
    for (let i = 0; i < points.length - 1; i++) {
        const start = points[i];
        const end = points[i + 1];
        
        for (let step = 0; step < stepsPerSegment; step++) {
            const progress = step / stepsPerSegment;
            const lat = start[0] + (end[0] - start[0]) * progress;
            const lon = start[1] + (end[1] - start[1]) * progress;
            smoothPoints.push([lat, lon]);
        }
    }
    
    smoothPoints.push(points[0]);
    return smoothPoints;
}

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', () => {
    console.log('🏎️ Initializing Professional Racing Telemetry System...');
    
    smoothTrackPoints = createSmoothTrack(NMIT_TRACK, 15);
    console.log(`✅ Created ${smoothTrackPoints.length} smooth track points`);
    
    initializeMap();
    initializeCharts();
    initializeEventListeners();
    startSessionTimer();
    
    setTimeout(() => {
    startBackendPolling();
    updateConnectionStatus('LIVE', true);
    }, 1500);
});


function startBackendPolling() {
    setInterval(async () => {
        try {
            const response = await fetch("http://localhost:5000/api/dashboard");
            const data = await response.json();

            dashboardData = data;
            updateAllDisplays();

            if (data.current_position) {
                updateKartPosition(data.current_position.lat, data.current_position.lon);
            }

        } catch (err) {
            console.error("Backend fetch error:", err);
            updateConnectionStatus("DISCONNECTED", false);
        }
    }, 300);
}

function updateKartPosition(lat, lon) {
    map.panTo([lat, lon], { animate: true });
    if (kartMarker) {
        kartMarker.setLatLng([lat, lon]);
    }
}

// ========== MAP INITIALIZATION ==========
function initializeMap() {
    console.log('🗺️ Initializing map...');
    
    // Exact center of NMIT track
    const centerLat = 13.128145;
    const centerLon = 77.58717;
    
    // Create map
    map = L.map('map', { 
        zoomControl: false,
        attributionControl: false,
        dragging: true,
        scrollWheelZoom: false,
        doubleClickZoom: false,
        touchZoom: false,
        boxZoom: false,
        keyboard: false
    }).setView([centerLat, centerLon], 16);
    
    // Add tiles
    L.tileLayer('https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png', {
        maxZoom: 20,
        minZoom: 15
    }).addTo(map);
    
    console.log('✅ Map tiles loaded');
    
    // Wait for map to be ready
    setTimeout(() => {
        map.invalidateSize();
        
        // Draw racing line FIRST
        
        console.log('✅ Racing line drawn');
        
        // Add START marker
        
        // Create kart marker LAST (on top)
        if (kartMarker) {
            map.removeLayer(kartMarker);
        }
        kartMarker = L.circleMarker([13.129051169254026, 77.58824465835409], {
                        radius: 10,
                        color: '#ffffff',
                        weight: 3,
                        fillColor: '#00ff88',
                        fillOpacity: 1,
                        className: 'kart-glow'
                    }).addTo(map);


        console.log('✅ Kart placed at START:', [13.129051, 77.588244]);
        
        // Fit bounds to show entire track
        const bounds = L.latLngBounds(NMIT_TRACK);
        map.fitBounds(bounds, { 
            padding: [30, 30],
            maxZoom: 16
        });
        
        console.log('✅ Map bounds fitted to track');
        
    }, 800);  // Give more time for map to load
}


// ========== KART ANIMATION ==========
let kartAnimationInterval = null;

function startKartAnimation() {
    console.log('🏎️ Starting kart animation...');
    
    if (kartAnimationInterval) {
        clearInterval(kartAnimationInterval);
    }
    
    animationIndex = 0;
    
    kartAnimationInterval = setInterval(() => {
        if (!smoothTrackPoints || smoothTrackPoints.length === 0) {
            console.error('❌ No track points available');
            return;
        }
        
        const currentPos = smoothTrackPoints[animationIndex];
        
        if (kartMarker) {
            kartMarker.setLatLng(currentPos);
        }
        
        animationIndex = (animationIndex + 1) % smoothTrackPoints.length;
        
        if (animationIndex === 0) {
            currentLap++;
            console.log(`🏁 Lap ${currentLap} completed`);
            document.getElementById('lap-counter').textContent = `${currentLap} / ${totalLaps}`;
        }
        
    }, 80);
}

// ========== REALTIME DATA UPDATES ==========
function startRealtimeDataUpdates() {
    setInterval(() => {
        const progress = animationIndex / smoothTrackPoints.length;
        const speed = calculateRealisticSpeed(progress);
        const sector = calculateCurrentSector(progress);
        const delta = calculateRealisticDelta(progress);
        
        updateSpeedDisplay(speed);
        updateSpeedChart(speed);
        updateRealtimeDelta(delta);
        updateCurrentSectorDisplay(sector);
        
        updatePrediction({
            predicted_lap_time: 86.5 + (Math.random() * 2 - 1),
            confidence: 0.75 + Math.random() * 0.2,
            optimal_time: 85.123
        });
    }, 200);
}

// ========== SPEED CALCULATIONS ==========
function calculateRealisticSpeed(progress) {
    if (progress < 0.15) return 68 + Math.random() * 5;
    else if (progress < 0.25) return 45 + Math.random() * 4;
    else if (progress < 0.35) return 48 + Math.random() * 3;
    else if (progress < 0.45) return 35 + Math.random() * 3;
    else if (progress < 0.65) return 55 + Math.random() * 5;
    else if (progress < 0.85) return 62 + Math.random() * 4;
    else return 66 + Math.random() * 4;
}

function calculateCurrentSector(progress) {
    if (progress < 0.33) return 1;
    else if (progress < 0.67) return 2;
    else return 3;
}

function calculateRealisticDelta(progress) {
    const baseVariation = Math.sin(progress * Math.PI * 4) * 0.4;
    const randomNoise = (Math.random() - 0.5) * 0.2;
    return baseVariation + randomNoise;
}

function updateCurrentSectorDisplay(sector) {
    const sectorDisplay = document.getElementById('current-sector-display');
    if (sectorDisplay) {
        sectorDisplay.textContent = `S${sector}`;
    }
}

// ========== CORNER MARKERS ==========

// ========== CHART INITIALIZATION ==========
function initializeCharts() {
    const speedCtx = document.getElementById('speedChart').getContext('2d');
    
    Chart.defaults.color = '#00cc6a';
    Chart.defaults.borderColor = '#003322';
    
    speedChart = new Chart(speedCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Speed',
                data: [],
                borderColor: '#00ff88',
                backgroundColor: 'rgba(0, 255, 136, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 80,
                    grid: { color: '#003322' },
                    ticks: { color: '#00cc6a' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#00cc6a', maxTicksLimit: 8 }
                }
            },
            animation: { duration: 0 }
        }
    });
}

// ========== EVENT LISTENERS ==========
function initializeEventListeners() {
    document.getElementById('toggle-racing-line')?.addEventListener('click', toggleRacingLine);
    document.getElementById('toggle-overtaking')?.addEventListener('click', () => {
        console.log('Toggle overtaking zones');
    });
}

// ========== DUMMY DATA ==========
function loadDummyData() {
    dashboardData = {
        optimal_lap: {
            optimal_time: 85.123,
            improvement_potential: 2.111,
            sectors: {
                0: { time: 28.456, lap_number: 3, avg_speed: 52.3, max_speed: 68.5 },
                1: { time: 30.234, lap_number: 5, avg_speed: 48.7, max_speed: 71.2 },
                2: { time: 26.433, lap_number: 7, avg_speed: 54.1, max_speed: 73.8 }
            }
        },
        latest_lap: {
            lap_number: currentLap,
            total_time: 87.234,
            avg_speed: 51.8,
            max_speed: 73.8,
            sectors: {
                0: { time: 28.756, avg_speed: 52.1, max_speed: 68.2 },
                1: { time: 30.845, avg_speed: 48.3, max_speed: 70.9 },
                2: { time: 27.633, avg_speed: 53.6, max_speed: 73.1 }
            },
            corner_analysis: [
                {
                    corner_number: 1,
                    improvement_potential: 15.3,
                    current_exit: 45.2,
                    best_exit: 52.8,
                    recommendation: '💡 Exit too slow - earlier throttle application'
                },
                {
                    corner_number: 2,
                    improvement_potential: 12.1,
                    current_exit: 58.3,
                    best_exit: 65.2,
                    recommendation: '⚠️ Entry too fast - brake earlier for better exit'
                },
                {
                    corner_number: 3,
                    improvement_potential: 8.7,
                    current_exit: 42.1,
                    best_exit: 46.5,
                    recommendation: '⚠️ Hairpin - focus on exit speed'
                }
            ]
        },
        tire_status: {
            grip_level: 83,
            degradation_rate: 0.023,
            speed_loss_percent: 2.3,
            laps_remaining: 7,
            pit_recommended: false,
            status: 'GOOD'
        },
        performance: {
            overall_score: 87,
            speed_score: 88,
            consistency_score: 85,
            smoothness_score: 87,
            rating: 'A',
            trend: 'IMPROVING'
        },
        race_strategy: {
            lap: currentLap,
            laps_remaining: totalLaps - currentLap,
            race_progress: (currentLap / totalLaps) * 100,
            race_phase: 'EARLY',
            strategy_mode: 'MAINTAIN PACE',
            recommendations: [
                {
                    category: 'PACE',
                    icon: '✅',
                    priority: 'LOW',
                    message: 'Pace improving by 0.34s - Excellent!',
                    action: 'MAINTAIN RHYTHM',
                    expected_gain: 'Keep building confidence'
                },
                {
                    category: 'TIRES',
                    icon: '🟡',
                    priority: 'MEDIUM',
                    message: 'Tire degradation detected (2.3% pace loss)',
                    action: 'MONITOR CLOSELY',
                    expected_gain: 'Consider pit window in 3-5 laps'
                },
                {
                    category: 'DRIVING',
                    icon: '💡',
                    priority: 'LOW',
                    message: 'Performance score: A - Focus on consistency',
                    action: 'SMOOTH INPUTS',
                    expected_gain: '+0.3s/lap potential'
                }
            ],
            priority_action: {
                category: 'PACE',
                message: 'Maintain current rhythm'
            }
        },
        improvement_zones: {
            sector_1: {
                time_loss: 0.611,
                percentage_loss: 2.03,
                optimal_avg_speed: 48.7,
                current_avg_speed: 48.3,
                speed_deficit: 0.4
            },
            sector_2: {
                time_loss: 1.200,
                percentage_loss: 4.54,
                optimal_avg_speed: 54.1,
                current_avg_speed: 53.6,
                speed_deficit: 0.5
            },
            sector_0: {
                time_loss: 0.300,
                percentage_loss: 1.05,
                optimal_avg_speed: 52.3,
                current_avg_speed: 52.1,
                speed_deficit: 0.2
            }
        },
        lap_history: generateDummyLapHistory(8),
        session_stats: {
            total_laps: currentLap,
            best_lap: {
                lap_number: 5,
                total_time: 85.789,
                avg_speed: 52.4
            },
            best_lap_time: 85.789,
            best_lap_number: 5,
            average_lap_time: 87.456,
            last_5_avg: 86.923,
            consistency: 96.2
        },
        racing_line: NMIT_TRACK,
        overtaking_zones: [
            { 
                lat: 13.128300, 
                lon: 77.58800, 
                type: 'MAIN STRAIGHT',
                avg_speed: 72.5,
                confidence: 0.90,
                recommendation: 'Long straight - perfect for slipstreaming'
            },
            { 
                lat: 13.127823, 
                lon: 77.58600, 
                type: 'HAIRPIN EXIT',
                exit_speed: 38.3,
                confidence: 0.85,
                recommendation: 'Better exit = overtake on back straight'
            }
        ]
    };
    
    updateAllDisplays();
}

function generateDummyLapHistory(numLaps) {
    const laps = [];
    const baseTimes = [88.234, 87.456, 86.789, 86.234, 85.789, 86.123, 85.956, 87.234];
    
    for (let i = 1; i <= numLaps; i++) {
        laps.push({
            lap_number: i,
            total_time: baseTimes[i - 1] || 87.0 + Math.random() * 2,
            avg_speed: 51.5 + Math.random() * 2,
            sectors: {
                0: { time: 28.5 + Math.random(), avg_speed: 52 + Math.random() * 2 },
                1: { time: 30.2 + Math.random(), avg_speed: 48 + Math.random() * 2 },
                2: { time: 26.5 + Math.random(), avg_speed: 54 + Math.random() * 2 }
            }
        });
    }
    
    return laps;
}

// ========== UPDATE ALL DISPLAYS ==========
function updateAllDisplays() {
    if (!dashboardData) return;
    
    updateOptimalLap();
    updateSectorTimes();
    updateTireStatus();
    updatePerformanceScore();
    updateRaceStrategy();
    updateCornerAnalysis();
    updateImprovementZones();
    updateLapHistory();
    updateSessionStats();
}

function updateOptimalLap() {
    if (dashboardData.optimal_lap) {
        document.getElementById('optimal-lap-time').textContent = 
            formatTime(dashboardData.optimal_lap.optimal_time);
    }
}

function updateSectorTimes() {
    if (!dashboardData.latest_lap?.sectors) return;
    
    const sectors = dashboardData.latest_lap.sectors;
    const sectorsContainer = document.getElementById('sectors-content');
    
    let sectorsHTML = '';
    
    Object.keys(sectors).sort().forEach((sectorId, index) => {
        const sector = sectors[sectorId];
        const isPersonalBest = dashboardData.optimal_lap?.sectors[sectorId] &&
            sector.time <= dashboardData.optimal_lap.sectors[sectorId].time;
        
        sectorsHTML += `
            <div class="sector-item ${isPersonalBest ? 'optimal' : ''}">
                <span class="sector-label">S${index + 1}</span>
                <span class="sector-time">${sector.time.toFixed(3)}s</span>
                <span class="sector-badge">${isPersonalBest ? 'BEST' : 'L' + dashboardData.latest_lap.lap_number}</span>
            </div>
        `;
    });
    
    if (dashboardData.optimal_lap) {
        sectorsHTML += `
            <div class="sector-divider"></div>
            <div class="sector-item optimal">
                <span class="sector-label">OPTIMAL</span>
                <span class="sector-time">${formatTime(dashboardData.optimal_lap.optimal_time)}</span>
                <span class="sector-badge">THEORETICAL</span>
            </div>
        `;
    }
    
    sectorsContainer.innerHTML = sectorsHTML;
}

function updateTireStatus() {
    if (!dashboardData.tire_status) return;
    
    const tire = dashboardData.tire_status;
    
    document.getElementById('grip-percentage').textContent = `${tire.grip_level.toFixed(0)}%`;
    
    const badge = document.getElementById('tire-status-badge');
    badge.textContent = tire.status;
    badge.className = `tire-status-badge ${tire.status.toLowerCase()}`;
    
    document.getElementById('tire-degradation').textContent = `${(tire.degradation_rate * 100).toFixed(2)}%/lap`;
    document.getElementById('tire-laps-remaining').textContent = tire.laps_remaining;
    document.getElementById('tire-pace-loss').textContent = `${tire.speed_loss_percent.toFixed(1)}%`;
    
    const pitRec = document.getElementById('pit-recommendation');
    if (pitRec) {
        pitRec.style.display = tire.pit_recommended ? 'flex' : 'none';
    }
}

function updatePerformanceScore() {
    if (!dashboardData.performance) return;
    
    const perf = dashboardData.performance;
    
    document.getElementById('performance-rating').textContent = perf.rating;
    
    const scoreCircle = document.getElementById('score-circle');
    const circumference = 2 * Math.PI * 45;
    const offset = circumference - (perf.overall_score / 100) * circumference;
    scoreCircle.style.strokeDashoffset = offset;
    
    document.getElementById('performance-score').textContent = Math.round(perf.overall_score);
    
    document.getElementById('speed-stat').style.width = `${perf.speed_score}%`;
    document.getElementById('consistency-stat').style.width = `${perf.consistency_score}%`;
    document.getElementById('smoothness-stat').style.width = `${perf.smoothness_score}%`;
}

function updateRaceStrategy() {
    if (!dashboardData.race_strategy) return;
    
    const strategy = dashboardData.race_strategy;
    
    document.getElementById('strategy-mode').textContent = strategy.strategy_mode;
    
    const strategyContent = document.getElementById('strategy-content');
    
    if (strategy.recommendations.length === 0) {
        strategyContent.innerHTML = `
            <div class="strategy-empty">
                <div class="empty-icon">🤖</div>
                <p>All systems optimal - maintain current pace</p>
            </div>
        `;
        return;
    }
    
    let strategyHTML = '';
    
    strategy.recommendations.forEach(rec => {
        const priorityClass = `priority-${rec.priority.toLowerCase()}`;
        
        strategyHTML += `
            <div class="strategy-item ${priorityClass}">
                <div class="strategy-header">
                    <span class="strategy-icon">${rec.icon}</span>
                    <span class="strategy-category">${rec.category}</span>
                </div>
                <div class="strategy-message">${rec.message}</div>
                <div class="strategy-action">→ ${rec.action}</div>
            </div>
        `;
    });
    
    strategyContent.innerHTML = strategyHTML;
}

function updateCornerAnalysis() {
    if (!dashboardData.latest_lap?.corner_analysis) return;
    
    const corners = dashboardData.latest_lap.corner_analysis;
    const cornerContent = document.getElementById('corner-content');
    
    if (corners.length === 0) {
        cornerContent.innerHTML = `
            <div class="corner-empty">
                <div class="empty-icon">🏁</div>
                <p>No improvement opportunities detected</p>
            </div>
        `;
        return;
    }
    
    document.getElementById('corner-count').textContent = `${corners.length} corners`;
    
    let cornerHTML = '';
    
    corners.forEach(corner => {
        cornerHTML += `
            <div class="corner-item">
                <div class="corner-header">
                    <span class="corner-number">Corner ${corner.corner_number}</span>
                    <span class="corner-potential">+${corner.improvement_potential.toFixed(1)}%</span>
                </div>
                <div class="corner-recommendation">${corner.recommendation}</div>
            </div>
        `;
    });
    
    cornerContent.innerHTML = cornerHTML;
}

function updateImprovementZones() {
    if (!dashboardData.improvement_zones) return;
    
    const zones = dashboardData.improvement_zones;
    const improvementContent = document.getElementById('improvement-content');
    
    const zoneEntries = Object.entries(zones);
    
    if (zoneEntries.length === 0) {
        improvementContent.innerHTML = `
            <div class="improvement-empty">
                <div class="empty-icon">✅</div>
                <p>All sectors at optimal pace</p>
            </div>
        `;
        return;
    }
    
    let improvementHTML = '';
    
    zoneEntries.slice(0, 3).forEach(([sector, data]) => {
        const sectorNum = sector.replace('sector_', '');
        
        improvementHTML += `
            <div class="improvement-item">
                <div class="improvement-header">
                    <span class="improvement-sector">Sector ${parseInt(sectorNum) + 1}</span>
                    <span class="improvement-loss">-${data.time_loss.toFixed(3)}s</span>
                </div>
                <div class="improvement-details">
                    Speed deficit: ${data.speed_deficit.toFixed(1)} km/h
                </div>
            </div>
        `;
    });
    
    improvementContent.innerHTML = improvementHTML;
}

function updateLapHistory() {
    if (!dashboardData.lap_history || dashboardData.lap_history.length === 0) return;
    
    const historyContent = document.getElementById('history-content');
    const laps = dashboardData.lap_history.slice().reverse();
    
    let historyHTML = '';
    
    laps.forEach(lap => {
        const isBest = bestLapTime && lap.total_time === bestLapTime;
        const delta = bestLapTime ? lap.total_time - bestLapTime : 0;
        
        historyHTML += `
            <div class="lap-history-item ${isBest ? 'best-lap' : ''}">
                <span class="lap-number">L${lap.lap_number}</span>
                <span class="lap-time">${formatTime(lap.total_time)}</span>
                <span class="lap-delta ${delta >= 0 ? 'slower' : 'faster'}">
                    ${delta !== 0 ? (delta > 0 ? '+' : '') + delta.toFixed(3) : 'BEST'}
                </span>
            </div>
        `;
    });
    
    historyContent.innerHTML = historyHTML;
}

function updateSessionStats() {
    if (!dashboardData.session_stats) return;
    
    const stats = dashboardData.session_stats;
    
    currentLap = stats.total_laps;
    document.getElementById('lap-counter').textContent = `${currentLap} / ${totalLaps}`;
    
    if (stats.best_lap) {
        bestLapTime = stats.best_lap_time;
        document.getElementById('best-lap-time').textContent = formatTime(bestLapTime);
    }
}

// ========== REAL-TIME UPDATES ==========
function updateSpeedDisplay(speed) {
    document.getElementById('current-speed-display').textContent = Math.round(speed);
}

function updateSpeedChart(speed) {
    const now = new Date().toLocaleTimeString().split(' ')[0];
    
    speedChart.data.labels.push(now);
    speedChart.data.datasets[0].data.push(speed);
    
    if (speedChart.data.labels.length > 50) {
        speedChart.data.labels.shift();
        speedChart.data.datasets[0].data.shift();
    }
    
    speedChart.update();
}

function updateRealtimeDelta(delta) {
    const deltaElement = document.getElementById('delta-value');
    const sign = delta >= 0 ? '+' : '';
    deltaElement.textContent = `${sign}${delta.toFixed(3)}`;
    
    deltaElement.className = 'delta-value';
    if (delta > 0.05) {
        deltaElement.classList.add('ahead');
    } else if (delta < -0.05) {
        deltaElement.classList.add('behind');
    }
    
    const deltaBar = document.getElementById('delta-bar');
    const percentage = Math.min(Math.abs(delta) * 20, 50);
    deltaBar.style.width = `${percentage}%`;
    
    if (delta > 0) {
        deltaBar.style.left = '50%';
        deltaBar.style.background = '#00ff88';
    } else {
        deltaBar.style.right = '50%';
        deltaBar.style.left = 'auto';
        deltaBar.style.background = '#ff3366';
    }
}

function updatePrediction(prediction) {
    if (!prediction || !prediction.predicted_lap_time) return;
    
    document.getElementById('predicted-time').textContent = 
        formatTime(prediction.predicted_lap_time);
    
    const confidence = Math.round(prediction.confidence * 100);
    document.getElementById('prediction-confidence').textContent = `${confidence}%`;
    
    if (prediction.optimal_time) {
        const vsOptimal = prediction.predicted_lap_time - prediction.optimal_time;
        document.getElementById('vs-optimal-delta').textContent = 
            (vsOptimal > 0 ? '+' : '') + vsOptimal.toFixed(3);
    }
    
    if (bestLapTime) {
        const vsBest = prediction.predicted_lap_time - bestLapTime;
        document.getElementById('vs-best-delta').textContent = 
            (vsBest > 0 ? '+' : '') + vsBest.toFixed(3);
    }
}

// ========== MAP HELPERS ==========
function toggleRacingLine() {
    if (racingLinePolyline) {
        if (map.hasLayer(racingLinePolyline)) {
            map.removeLayer(racingLinePolyline);
        } else {
            racingLinePolyline.addTo(map);
        }
    }
}

// ========== UTILITIES ==========
function startSessionTimer() {
    setInterval(() => {
        const elapsed = Date.now() - sessionStartTime;
        const hours = Math.floor(elapsed / 3600000);
        const minutes = Math.floor((elapsed % 3600000) / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);
        
        document.getElementById('session-time').textContent = 
            `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
    }, 1000);
}

function updateConnectionStatus(status, connected) {
    const indicator = document.getElementById('connection-indicator');
    const text = document.getElementById('connection-text');
    
    text.textContent = status;
    
    if (connected) {
        indicator.style.borderColor = '#00ff88';
        indicator.querySelector('.status-dot').style.background = '#00ff88';
    } else {
        indicator.style.borderColor = '#ff3366';
        indicator.querySelector('.status-dot').style.background = '#ff3366';
    }
}

function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(3);
    return `${minutes}:${secs.padStart(6, '0')}`;
}

function pad(num) {
    return num.toString().padStart(2, '0');
}

console.log('✅ Professional Racing Telemetry System Ready!');
