from datetime import date, timedelta
import random
from users.models import PatientProfile

def build_indicators_context(patient: PatientProfile) -> dict:
    """
    构建“患者指标”Tab 所需的上下文数据：
    - 模拟30天数据
    """
    today = date.today()
    dates = [(today - timedelta(days=i)).strftime("%m-%d") for i in range(29, -1, -1)]
    
    # Simulate Medication Records
    # Just for simulation, let's create a row with date and status
    
    # Simulate Chart Data
    # 6 modules: SpO2, BP, Heart Rate, Weight, Temp, Steps
    charts = {}
    
    # SpO2 (95-100)
    charts['spo2'] = {
        "id": "chart-spo2",
        "title": "静息血氧 SpO2 (%)",
        "subtitle": "(10次) 依从性: 30%",
        "dates": dates,
        "series": [{"name": "静息血氧", "data": [random.randint(95, 100) for _ in range(30)], "color": "#3b82f6"}],
        "y_min": 80,
        "y_max": 100
    }
    
    # BP (Systolic 110-140, Diastolic 70-90)
    charts['bp'] = {
        "id": "chart-bp",
        "title": "血压 收缩压/舒张压 (mmHg)",
        "subtitle": "(10次) 依从性: 30%",
        "dates": dates,
        "series": [
            {"name": "收缩压", "data": [random.randint(110, 140) for _ in range(30)], "color": "#3b82f6"},
            {"name": "舒张压", "data": [random.randint(70, 90) for _ in range(30)], "color": "#10b981"}
        ],
        "y_min": 60,
        "y_max": 180
    }

    # Heart Rate (60-100)
    charts['hr'] = {
        "id": "chart-hr",
        "title": "静息心率 (次/min)",
        "subtitle": "(10次) 依从性: 30%",
        "dates": dates,
        "series": [{"name": "静息心率", "data": [random.randint(60, 100) for _ in range(30)], "color": "#3b82f6"}],
        "y_min": 40,
        "y_max": 140
    }
    
    # Weight (50-80)
    charts['weight'] = {
        "id": "chart-weight",
        "title": "体重 (KG)",
        "subtitle": "(10次) 依从性: 30%",
        "dates": dates,
        "series": [{"name": "体重", "data": [round(random.uniform(50, 80), 1) for _ in range(30)], "color": "#3b82f6"}],
        "y_min": 40,
        "y_max": 120
    }
    
    # Temperature (36.0-37.2)
    charts['temp'] = {
        "id": "chart-temp",
        "title": "体温 (℃)",
        "subtitle": "(25次) 依从性: 86%",
        "dates": dates,
        "series": [{"name": "体温", "data": [round(random.uniform(36.0, 37.2), 1) for _ in range(30)], "color": "#3b82f6"}],
        "y_min": 35,
        "y_max": 42
    }
    
    # Steps (1000-10000)
    charts['steps'] = {
        "id": "chart-steps",
        "title": "步数",
        "subtitle": "(25次) 依从性: 86%",
        "dates": dates,
        "series": [{"name": "步数", "data": [random.randint(1000, 10000) for _ in range(30)], "color": "#3b82f6"}],
        "y_min": 0,
        "y_max": 15000
    }
    
    medication_data = []
    for d in dates:
        medication_data.append({
            "date": d,
            "taken": random.choice([True, True, True, False])
        })

    return {
        "medication_data": medication_data,
        "charts": charts,
        "dates": dates
    }
