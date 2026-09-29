from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI(title="NFL Injury Risk Analyzer")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load precalculated probability tree
DATA_FILE = "nfl_injury_probabilities.json"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        INJURY_DATA = json.load(f)
else:
    INJURY_DATA = {}

@app.get("/api/query")
def query_injuries(
    team: str = Query(..., description="NFL Team Code (e.g. KC, BAL, SF)"),
    position: str = Query(..., description="Player Position (e.g. QB, WR, RB)"),
    status: str = Query(..., description="Injury Status (e.g. Out, Questionable, Doubtful)")
):
    """Retrieve top 3 primary injuries by percentage given filters."""
    team = team.upper().strip()
    position = position.upper().strip()
    status = status.title().strip()

    try:
        results = INJURY_DATA[team][position][status]
        top_3 = results[:3]
        return {
            "status": "success",
            "team": team,
            "position": position,
            "report_status": status,
            "top_3_injuries": top_3
        }
    except KeyError:
        return {
            "status": "error",
            "message": f"No historical records found for {team} - {position} listed as '{status}'."
        }

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    """Single-Page Web UI served directly by FastAPI."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NFL Injury Risk Analyzer</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-900 text-slate-100 min-h-screen p-4 md:p-8 font-sans">
        <div class="max-w-3xl mx-auto bg-slate-800 p-6 rounded-xl shadow-2xl border border-slate-700">
            <h1 class="text-3xl font-bold text-blue-400 mb-2">🏈 NFL Injury Risk Analyzer</h1>
            <p class="text-slate-400 mb-6">Select a team, position, and status to calculate top 3 historical primary injury probabilities (2010–Present).</p>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div>
                    <label class="block text-sm font-medium text-slate-300 mb-1">Team Abbreviation</label>
                    <input id="teamInput" type="text" placeholder="e.g. KC, BAL, SF" class="w-full bg-slate-700 p-2.5 rounded border border-slate-600 uppercase">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-300 mb-1">Position</label>
                    <input id="posInput" type="text" placeholder="e.g. QB, WR, RB" class="w-full bg-slate-700 p-2.5 rounded border border-slate-600 uppercase">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-300 mb-1">Report Status</label>
                    <input id="statusInput" type="text" placeholder="e.g. Out, Questionable" class="w-full bg-slate-700 p-2.5 rounded border border-slate-600">
                </div>
            </div>

            <button onclick="analyzeInjuries()" class="w-full bg-blue-600 hover:bg-blue-500 font-semibold py-3 rounded-lg transition">
                Analyze Top 3 Injury Risks
            </button>

            <div id="results" class="mt-6 space-y-4"></div>
        </div>

        <script>
            async function analyzeInjuries() {
                const team = document.getElementById('teamInput').value.trim();
                const pos = document.getElementById('posInput').value.trim();
                const status = document.getElementById('statusInput').value.trim();
                const resDiv = document.getElementById('results');

                if (!team || !pos || !status) {
                    resDiv.innerHTML = '<div class="p-4 bg-amber-900/40 border border-amber-500 rounded text-amber-200">Please enter a team, position, and status.</div>';
                    return;
                }

                resDiv.innerHTML = '<p class="text-slate-400">Querying database...</p>';

                try {
                    const res = await fetch(`/api/query?team=${encodeURIComponent(team)}&position=${encodeURIComponent(pos)}&status=${encodeURIComponent(status)}`);
                    const data = await res.json();

                    if (data.status === 'error') {
                        resDiv.innerHTML = `<div class="p-4 bg-red-900/40 border border-red-500 rounded text-red-200">${data.message}</div>`;
                        return;
                    }

                    let html = `<h2 class="text-xl font-bold text-slate-200 mb-3">Top 3 Likely Injuries (${data.team} ${data.position} - ${data.report_status}):</h2>`;
                    
                    data.top_3_injuries.forEach((item, idx) => {
                        html += `
                            <div class="bg-slate-700 p-4 rounded-lg flex justify-between items-center border border-slate-600">
                                <div>
                                    <span class="text-lg font-bold text-blue-300">#${idx + 1} ${item.injury}</span>
                                    <p class="text-xs text-slate-400 mt-1">Sample size: ${item.sample_size} records</p>
                                </div>
                                <div class="text-2xl font-black text-emerald-400">${item.percentage}%</div>
                            </div>
                        `;
                    });
                    resDiv.innerHTML = html;
                } catch (err) {
                    resDiv.innerHTML = '<div class="p-4 bg-red-900/40 border border-red-500 rounded text-red-200">Error connecting to server.</div>';
                }
            }
        </script>
    </body>
    </html>
    """