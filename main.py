from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import datetime

app = FastAPI()

# --- 数据模型 (对应您的 13 个传感器点) ---
class PultData(BaseModel):
    die_temp: float
    resin_temp: float
    motor_temp: float
    status: str

class EncapData(BaseModel):
    core_temp: float
    motor_temp: float
    psu_temp: float
    machine_temp: float
    status: str

class ConfData(BaseModel):
    strands_temp: float
    motor_temp: float
    psu_temp: float
    unit_temp: float
    status: str

class StrandData(BaseModel):
    psu_temp: float
    motor_temp: float
    status: str

class FullFactoryData(BaseModel):
    pultrusion: PultData
    encapsulation: EncapData
    conforming: ConfData
    stranding: StrandData
    image_base64: Optional[str] = None

# --- 全局状态 ---
global_state = {
    "data": None,
    "last_updated": "Waiting for Signal..."
}

# --- 接收数据接口 ---
@app.post("/api/upload")
async def receive_data(data: FullFactoryData):
    global global_state
    global_state["data"] = data
    global_state["last_updated"] = datetime.datetime.now().strftime("%H:%M:%S")
    return {"msg": "OK"}

# --- 前端查询接口 ---
@app.get("/api/status")
async def get_status():
    return global_state

# --- 网页前端 ---
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Process Monitor</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body { background-color: #0f172a; color: #e2e8f0; font-family: sans-serif; }
            .card { background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; transition: 0.3s; }
            .label { color: #94a3b8; font-size: 14px; margin-bottom: 4px; }
            .value { font-family: monospace; font-size: 24px; font-weight: bold; color: #f8fafc; }
            .unit { font-size: 14px; color: #64748b; margin-left: 4px; }
            .status-ok { border-left: 5px solid #10b981; }
            .status-warn { border-left: 5px solid #ef4444; }
        </style>
    </head>
    <body class="p-6">
        <header class="max-w-7xl mx-auto mb-8 flex justify-between items-end border-b border-gray-700 pb-4">
            <div>
                <h1 class="text-3xl font-bold text-blue-500">Factory Remote Monitor</h1>
                <p class="text-gray-400 text-sm mt-1">Real-time Sensor Array</p>
            </div>
            <div class="text-right text-xs text-gray-500 font-mono">
                Sync: <span id="sync-time" class="text-white">--:--:--</span>
            </div>
        </header>

        <main class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            <div class="lg:col-span-2 bg-black rounded-xl border border-gray-700 aspect-video flex items-center justify-center relative overflow-hidden">
                <img id="cam-feed" src="" class="w-full h-full object-contain hidden">
                <div id="no-signal" class="text-center text-gray-600 font-mono text-sm">
                    [ WAITING FOR CAMERA STREAM ]
                </div>
            </div>

            <div id="card-pult" class="card status-ok">
                <div class="flex justify-between mb-4 border-b border-gray-700 pb-2">
                    <h2 class="text-xl font-bold text-blue-400">Pultrusion</h2>
                    <span id="st-pult" class="text-xs bg-gray-800 px-2 py-1 rounded">WAIT</span>
                </div>
                <div class="space-y-2">
                    <div><div class="label">Die Temp</div><div class="value text-orange-400"><span id="pult-die">--</span><span class="unit">°C</span></div></div>
                    <div><div class="label">Resin Temp</div><div class="value text-emerald-400"><span id="pult-resin">--</span><span class="unit">°C</span></div></div>
                    <div><div class="label">Motor Temp</div><div class="value"><span id="pult-motor">--</span><span class="unit">°C</span></div></div>
                </div>
            </div>

            <div id="card-encap" class="card status-ok">
                <div class="flex justify-between mb-4 border-b border-gray-700 pb-2">
                    <h2 class="text-lg font-bold text-indigo-400">Encapsulation</h2>
                    <span id="st-encap" class="text-xs bg-gray-800 px-2 py-1 rounded">WAIT</span>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div><div class="label">Core Surface</div><div class="value"><span id="encap-core">--</span><span class="unit">°C</span></div></div>
                    <div><div class="label">Motor/Gear</div><div class="value"><span id="encap-motor">--</span><span class="unit">°C</span></div></div>
                    <div><div class="label">Power Unit</div><div class="value"><span id="encap-psu">--</span><span class="unit">°C</span></div></div>
                    <div><div class="label">Machine</div><div class="value"><span id="encap-machine">--</span><span class="unit">°C</span></div></div>
                </div>
            </div>

            <div id="card-conf" class="card status-ok">
                <div class="flex justify-between mb-4 border-b border-gray-700 pb-2">
                    <h2 class="text-lg font-bold text-yellow-400">Conforming</h2>
                    <span id="st-conf" class="text-xs bg-gray-800 px-2 py-1 rounded">WAIT</span>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div><div class="label">Strands</div><div class="value"><span id="conf-strands">--</span><span class="unit">°C</span></div></div>
                    <div><div class="label">Unit Temp</div><div class="value"><span id="conf-unit">--</span><span class="unit">°C</span></div></div>
                    <div><div class="label">Motor</div><div class="value"><span id="conf-motor">--</span><span class="unit">°C</span></div></div>
                    <div><div class="label">Power</div><div class="value"><span id="conf-psu">--</span><span class="unit">°C</span></div></div>
                </div>
            </div>

            <div id="card-strand" class="card status-ok">
                <div class="flex justify-between mb-4 border-b border-gray-700 pb-2">
                    <h2 class="text-lg font-bold text-purple-400">Stranding</h2>
                    <span id="st-strand" class="text-xs bg-gray-800 px-2 py-1 rounded">WAIT</span>
                </div>
                <div class="space-y-2">
                    <div><div class="label">Power Ctrl</div><div class="value"><span id="strand-psu">--</span><span class="unit">°C</span></div></div>
                    <div><div class="label">Motor & Gear</div><div class="value"><span id="strand-motor">--</span><span class="unit">°C</span></div></div>
                </div>
            </div>

        </main>

        <script>
            function updateVals(prefix, data) {
                if(!data) return;
                document.getElementById('st-' + prefix).innerText = data.status;
                const card = document.getElementById('card-' + prefix);
                
                if(data.status === 'Normal') {
                    card.className = "card status-ok";
                } else {
                    card.className = "card status-warn";
                }

                for (const [key, value] of Object.entries(data)) {
                    let simpleKey = key.replace('_temp', '');
                    let el = document.getElementById(prefix + '-' + simpleKey);
                    if(el) el.innerText = value;
                }
            }

            setInterval(async () => {
                try {
                    const res = await fetch('/api/status');
                    const json = await res.json();
                    if(json.data) {
                        document.getElementById('sync-time').innerText = json.last_updated;
                        updateVals('pult', json.data.pultrusion);
                        updateVals('encap', json.data.encapsulation);
                        updateVals('conf', json.data.conforming);
                        updateVals('strand', json.data.stranding);
                        
                        // 视频显示逻辑
                        if(json.data.image_base64 && json.data.image_base64.length > 50) {
                             document.getElementById('cam-feed').src = "data:image/jpeg;base64," + json.data.image_base64;
                             document.getElementById('cam-feed').classList.remove('hidden');
                             document.getElementById('no-signal').classList.add('hidden');
                        }
                    }
                } catch(e) {}
            }, 1000);
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)