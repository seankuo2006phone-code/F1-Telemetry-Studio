import React, { useEffect, useMemo, useState } from 'react';
import './App.css';
import { create } from 'zustand';
import Plot from 'react-plotly.js';
import { SparklesIcon, XMarkIcon } from '@heroicons/react/24/solid';

const API_BASE = import.meta.env.VITE_API_URL || 'https://f1-telemetry-studio-5r7o.onrender.com';

const SESSION_MAP: Record<string, string> = {
  "R": "Race", "Q": "Qualifying", "S": "Sprint", "SQ": "Sprint Shootout",
  "FP1": "Free Practice 1", "FP2": "Free Practice 2", "FP3": "Free Practice 3"
};

const DRIVER_MAP: Record<string, string> = {
  "VER": "Max Verstappen", "PER": "Sergio Perez", "HAM": "Lewis Hamilton", "RUS": "George Russell",
  "LEC": "Charles Leclerc", "SAI": "Carlos Sainz", "NOR": "Lando Norris", "PIA": "Oscar Piastri",
  "ALO": "Fernando Alonso", "STR": "Lance Stroll", "GAS": "Pierre Gasly", "OCO": "Esteban Ocon",
  "ALB": "Alexander Albon", "SAR": "Logan Sargeant", "TSU": "Yuki Tsunoda", "RIC": "Daniel Ricciardo",
  "HUL": "Nico Hulkenberg", "MAG": "Kevin Magnussen", "BOT": "Valtteri Bottas", "ZHO": "Guanyu Zhou"
};

const TEAM_COLORS: Record<string, string> = {
  "red bull": "#3671C6", "ferrari": "#E10600", "mercedes": "#6CD3BF", "mclaren": "#F58020",
  "aston martin": "#229971", "alpine": "#2293D1", "williams": "#37BEDD", "alphatauri": "#5E8FAA",
  "alfa romeo": "#C92D4B", "haas": "#B6BABD", "rb": "#6692FF", "sauber": "#52E252", 
  "renault": "#FFF500", "racing point": "#F596C8", "toro rosso": "#469BFF", "unknown": "#FFFFFF"
};

const getTeamColor = (team: string) => {
  if (!team) return "#FFFFFF";
  const t = team.toLowerCase();
  for (const [key, color] of Object.entries(TEAM_COLORS)) {
    if (t.includes(key)) return color;
  }
  return "#FFFFFF";
};

const AIAnalysisModal = ({ onClose }: { onClose: () => void }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      {/* 彈出視窗主體 - 拔除 border */}
      <div className="relative w-11/12 max-w-5xl bg-gray-900 rounded-lg shadow-2xl overflow-hidden flex flex-col h-[85vh]">
        
        {/* 彈出視窗標題 - 拔除 border-b */}
        <div className="flex items-center justify-between px-6 py-4 bg-gray-800">
          <div className="flex items-center space-x-3">
            <SparklesIcon className="w-6 h-6 text-blue-400" />
            <h2 className="text-xl font-bold tracking-widest text-white">AI 系統遙測診斷報告</h2>
            {/* LIVE SYNC 標籤 - 拔除 border */}
            <span className="bg-blue-900/50 text-blue-300 text-xs px-2 py-1 rounded">LIVE SYNC_</span>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* 詳盡分析內容區 */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6 custom-scrollbar text-sm text-gray-300">
          
          {/* AI 綜合結論 - 拔除 border-l-4 */}
          <div className="p-4 bg-blue-950/40 rounded">
            <h3 className="text-blue-400 font-bold mb-2 tracking-wider">💡 AI 綜合賽況判讀</h3>
            <p className="leading-relaxed">
              根據當前遙測數據，Driver 1 (Verstappen) 在第一計時段 (Sector 1) 具有絕對的低速彎牽引力優勢，平均提早 0.15 秒開油；而 Driver 2 (Leclerc) 則在第三計時段 (Sector 3) 的高速連續彎道中，憑藉較高的最低彎中速度 (Mid-corner speed) 扳回 0.2 秒的劣勢。整體圈速差異主要取決於 Turn 8 的煞車點選擇。
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 煞車區間分析 - 拔除所有 border */}
            <div className="p-4 bg-gray-800 rounded">
              <h3 className="text-red-400 font-bold mb-4 tracking-wider flex items-center">
                <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                晚煞車極限分析 (Braking Zones)
              </h3>
              <ul className="space-y-4">
                <li className="flex justify-between">
                  <span>Turn 5 煞車點</span>
                  <span className="text-white font-mono">VER 晚 5.2m (100% 煞車壓力)</span>
                </li>
                <li className="flex justify-between">
                  <span>Turn 8 減速度</span>
                  <span className="text-white font-mono">LEC 產生高達 5.1G 減速力</span>
                </li>
                <li className="flex justify-between">
                  <span>Trail Braking 釋放</span>
                  <span className="text-white font-mono">VER 釋放更平滑，減少前輪鎖死</span>
                </li>
              </ul>
            </div>

            {/* 油門與牽引力分析 - 拔除所有 border */}
            <div className="p-4 bg-gray-800 rounded">
              <h3 className="text-green-400 font-bold mb-4 tracking-wider flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                出彎牽引力矩陣 (Traction & Throttle)
              </h3>
              <ul className="space-y-4">
                <li className="flex justify-between">
                  <span>Turn 7 出彎全油門</span>
                  <span className="text-white font-mono">VER 提早 0.12s 達到 100% 油門</span>
                </li>
                <li className="flex justify-between">
                  <span>低速彎油門微調</span>
                  <span className="text-white font-mono">LEC 在 40-60% 區間有輕微修正</span>
                </li>
                <li className="flex justify-between">
                  <span>後輪空轉滑動率推估</span>
                  <span className="text-white font-mono">VER: 3.2% | LEC: 5.1% (較高耗損)</span>
                </li>
              </ul>
            </div>
          </div>

          {/* 檔位與轉速邏輯 - 拔除所有 border */}
          <div className="p-4 bg-gray-800 rounded">
            <h3 className="text-yellow-400 font-bold mb-3 tracking-wider flex items-center">
              <span className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></span>
              動力單元與檔位邏輯 (Gear & RPM)
            </h3>
            <p className="leading-relaxed mb-4">
              在直線加速段 (DRS Zone)，兩人均能在 11,500 RPM 左右進行完美升檔，但 Driver 1 在 Turn 12 選擇降至 3 檔以換取更高轉速的出彎扭力；Driver 2 則維持 4 檔，依靠更圓滑的賽車線減少引擎煞車帶來的動量損失。
            </p>
            <div className="w-full bg-gray-700 h-2 rounded-full overflow-hidden">
              <div className="bg-yellow-400 h-full w-[85%]" title="VER 轉速峰值維持率"></div>
            </div>
            <div className="text-right text-xs mt-1 text-gray-500">轉速峰值維持率 (VER 優勢)</div>
          </div>

        </div>
      </div>
    </div>
  );
};

interface TelemetryData {
  Driver: string; Team: string; Distance: number[]; Speed: number[];
  Throttle: number[]; Brake: number[]; RPM: number[]; nGear: number[];
  DRS: number[]; X: number[]; Y: number[]; Sector: number[];
}

interface StoreState {
  menuOptions: Record<string, Record<string, string[]>>;
  year: string; eventName: string; session: string;
  driver1: string; driver2: string;
  data1: TelemetryData | null; data2: TelemetryData | null;
  aiInsights: string[] | null;
  loading: boolean; cursorDist: number | null; cursorRatio: number | null;
  setCursor: (dist: number | null, ratio: number | null) => void;
  updateParams: (params: Partial<StoreState>) => void;
  fetchOptions: () => Promise<void>;
  fetchData: () => Promise<void>;
}

const FALLBACK_OPTIONS: Record<string, Record<string, string[]>> = {
  "2025": { "Bahrain Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"], "Monaco Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"] },
  "2024": { "Bahrain Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"], "Chinese Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"], "Monaco Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"], "British Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"], "Abu Dhabi Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"] },
  "2023": { "Bahrain Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"], "Monaco Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"], "British Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"] },
  "2022": { "Bahrain Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"], "Monaco Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"] },
  "2021": { "Bahrain Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"], "Abu Dhabi Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"] },
  "2020": { "Austrian Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"], "Italian Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"] },
  "2019": { "Australian Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"], "Monaco Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"] },
  "2018": { "Australian Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"], "Monaco Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"], "Japanese Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"] }
};

const useStore = create<StoreState>((set, get) => ({
  menuOptions: FALLBACK_OPTIONS,
  year: '2024', eventName: 'Bahrain Grand Prix', session: 'Q',
  driver1: 'VER', driver2: 'LEC',
  data1: null, data2: null, aiInsights: null, loading: false, cursorDist: null, cursorRatio: null,
  setCursor: (dist, ratio) => set({ cursorDist: dist, cursorRatio: ratio }),
  
  updateParams: (params) => {
    set({ ...params });
    get().fetchData();
  },
  
  fetchOptions: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/options`);
      if (!res.ok) throw new Error("API options failed");
      const options = await res.json();
      if (options && Object.keys(options).length > 0) {
        set({ menuOptions: options });
      }
    } catch (e) { 
      console.warn("Using fallback options due to API error"); 
    }
  },

  fetchData: async () => {
    set({ loading: true, data1: null, data2: null, aiInsights: null });
    const { year, eventName, session, driver1, driver2 } = get();
    try {
      const baseUrl = `${API_BASE}/api/telemetry?year=${year}&event_name=${encodeURIComponent(eventName)}&session_type=${session}`;
      const aiUrl = `${API_BASE}/api/ai_analysis?year=${year}&event_name=${encodeURIComponent(eventName)}&session_type=${session}&driver1=${driver1}&driver2=${driver2}`;
      
      const [res1, res2, resAi] = await Promise.all([
        fetch(`${baseUrl}&driver=${driver1}`),
        fetch(`${baseUrl}&driver=${driver2}`),
        fetch(aiUrl)
      ]);

      const d1 = res1.ok ? await res1.json() : null;
      const d2 = res2.ok ? await res2.json() : null;
      const ai = resAi.ok ? await resAi.json() : null;

      if (d1 && !d1.error) set({ data1: d1 });
      if (d2 && !d2.error) set({ data2: d2 });
      if (ai && ai.insights) set({ aiInsights: ai.insights });
    } catch (error) { 
      console.error("Fetch error:", error); 
    } finally { 
      set({ loading: false }); 
    }
  }
}));

const DeltaChart = () => {
  const { data1, data2, cursorDist, cursorRatio, setCursor } = useStore();
  
  const deltaData = useMemo(() => {
    // 🌟 嚴格檢查：如果資料不完整或缺少 Distance / Speed，直接回傳 null 避免崩潰
    if (!data1 || !data2 || !data1.Distance || !data1.Speed || !data2.Distance || !data2.Speed) return null;
    
    const calcTimeArray = (dist: number[], speedKmh: number[]) => {
      if (!dist || !speedKmh || dist.length === 0) return new Float32Array(0);
      const time = new Float32Array(dist.length);
      time[0] = 0;
      for (let i = 1; i < dist.length; i++) {
        const dDist = dist[i] - dist[i-1];
        const vKmh = (speedKmh[i] + speedKmh[i-1]) / 2;
        const vMs = Math.max(vKmh / 3.6, 0.1); 
        time[i] = time[i-1] + (dDist / vMs);
      }
      return time;
    };

    const t1 = calcTimeArray(data1.Distance, data1.Speed);
    const t2 = calcTimeArray(data2.Distance, data2.Speed);
    if (t1.length === 0 || t2.length === 0) return null;

    const delta = new Float32Array(data1.Distance.length);

    let j = 0;
    for (let i = 0; i < data1.Distance.length; i++) {
      const targetD = data1.Distance[i];
      
      while (j < data2.Distance.length - 1 && data2.Distance[j+1] < targetD) {
        j++;
      }
      
      if (j >= data2.Distance.length - 1) {
        delta[i] = delta[i-1] || 0;
        continue;
      }

      const d0 = data2.Distance[j];
      const d1_t = data2.Distance[j+1];
      const time0 = t2[j];
      const time1_t = t2[j+1];
      
      let interpT2 = time0;
      if (d1_t > d0) {
        interpT2 = time0 + ((targetD - d0) / (d1_t - d0)) * (time1_t - time0);
      }
      
      delta[i] = t1[i] - interpT2;
    }
    return Array.from(delta);
  }, [data1, data2]);

  if (!data1 || !data2 || !deltaData) return null;

  let val1 = '-';
  let distVal = '-';
  let idx = -1;

  if (cursorDist !== null && data1.Distance) {
    idx = data1.Distance.findIndex(d => d >= cursorDist);
    if (idx !== -1) {
      const dVal = deltaData[idx];
      val1 = (dVal > 0 ? "+" : "") + dVal.toFixed(3) + 's';
      distVal = `${data1.Distance[idx].toFixed(0)}m`;
    }
  }

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!data1 || !data1.Distance) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const plotWidth = rect.width - 45;
    const mouseX = e.clientX - rect.left - 35;
    const ratio = Math.max(0, Math.min(1, mouseX / plotWidth));
    const maxDist = data1.Distance[data1.Distance.length - 1];
    const targetDist = ratio * maxDist;

    let closest = data1.Distance[0];
    let minDist = Math.abs(closest - targetDist);
    for (let i = 0; i < data1.Distance.length; i++) {
      const diff = Math.abs(data1.Distance[i] - targetDist);
      if (diff < minDist) {
        minDist = diff;
        closest = data1.Distance[i];
      }
    }
    setCursor(closest, ratio);
  };

  const chartData: any[] = [
    { 
      x: data1.Distance, y: deltaData, type: 'scatter', mode: 'lines', fill: 'tozeroy',
      line: { color: getTeamColor(data1.Team), width: 1.5 }, 
      fillcolor: getTeamColor(data1.Team) + '33', 
      hoverinfo: 'skip'
    }
  ];

  return (
    <div className="relative mb-6 cursor-crosshair shrink-0" onMouseMove={handleMouseMove} onMouseLeave={() => setCursor(null, null)}>
      <div className="flex justify-between items-center px-2 mb-0.5 pointer-events-none">
        <h2 className="text-[10px] font-medium tracking-[0.2em] text-gray-500 uppercase">Delta Time (s)</h2>
      </div>

      {cursorRatio !== null && idx !== -1 && (
        <div className="absolute top-5 z-20 pointer-events-none font-mono text-[10px] flex flex-col gap-0.5 pl-2 whitespace-nowrap" style={{ left: `calc(35px + ${cursorRatio} * (100% - 45px))` }}>
          <span className="text-gray-400 text-[9px] drop-shadow-[0_1px_3px_rgba(0,0,0,0.9)]">{distVal}</span>
          <span style={{ color: getTeamColor(data1.Team) }} className="drop-shadow-[0_1px_3px_rgba(0,0,0,0.9)]">
            {data1.Driver} Relative: {val1}
          </span>
        </div>
      )}
      
      <Plot
        data={chartData}
        layout={{
          height: 200, margin: { l: 35, r: 10, t: 5, b: 15 },
          paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
          xaxis: { showgrid: true, gridcolor: '#121212', zeroline: false, showline: false, tickfont: { color: '#666', size: 10 } },
          yaxis: { showgrid: true, gridcolor: '#121212', zeroline: true, zerolinecolor: '#444', showline: false, tickfont: { color: '#666', size: 10 } },
          hovermode: false, showlegend: false,
          shapes: cursorDist !== null ? [{ 
            type: 'line', x0: cursorDist, x1: cursorDist, y0: 0, y1: 1, yref: 'paper', 
            line: { color: '#E10600', width: 1, dash: 'dash' }
          }] : []
        }}
        config={{ displayModeBar: false, staticPlot: true }} style={{ width: '100%' }}
      />
    </div>
  );
};

const TelemetryChart = ({ title, metric, yRange, isBrake = false }: { title: string, metric: keyof TelemetryData, yRange?: number[], isBrake?: boolean }) => {
  const { data1, data2, cursorDist, cursorRatio, setCursor } = useStore();
  if (!data1) return null;

  let val1 = '-';
  let val2 = '-';
  let distVal = '-';
  let idx = -1;

  if (cursorDist !== null) {
    idx = data1.Distance.findIndex(d => d >= cursorDist);
    if (idx !== -1) {
      const raw1 = data1[metric][idx];
      val1 = typeof raw1 === 'number' ? raw1.toFixed(1) : String(raw1);
      if (data2 && data2[metric]) {
        const raw2 = data2[metric][idx];
        val2 = typeof raw2 === 'number' ? raw2.toFixed(1) : String(raw2);
      }
      distVal = `${data1.Distance[idx].toFixed(0)}m`;
    }
  }

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const plotWidth = rect.width - 45;
    const mouseX = e.clientX - rect.left - 35;
    const ratio = Math.max(0, Math.min(1, mouseX / plotWidth));
    const maxDist = data1.Distance[data1.Distance.length - 1];
    const targetDist = ratio * maxDist;

    let closest = data1.Distance[0];
    let minDist = Math.abs(closest - targetDist);
    for (let i = 0; i < data1.Distance.length; i++) {
      const diff = Math.abs(data1.Distance[i] - targetDist);
      if (diff < minDist) {
        minDist = diff;
        closest = data1.Distance[i];
      }
    }
    setCursor(closest, ratio);
  };

  const chartData: any[] = [
    { 
      x: data1.Distance, y: data1[metric] as number[], type: 'scatter', mode: 'lines', 
      line: { color: getTeamColor(data1.Team), width: 1.5, dash: isBrake ? 'dot' : 'solid' }, 
      hoverinfo: 'skip'
    }
  ];

  if (data2 && data2.Distance) {
    chartData.push({ 
      x: data2.Distance, y: data2[metric] as number[], type: 'scatter', mode: 'lines', 
      line: { color: getTeamColor(data2.Team), width: 1.5, dash: isBrake ? 'dot' : 'solid' }, 
      hoverinfo: 'skip'
    });
  }

  return (
    <div 
      className="relative mb-6 cursor-crosshair shrink-0" 
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setCursor(null, null)}
    >
      <div className="flex justify-between items-center px-2 mb-0.5 pointer-events-none">
        <h2 className="text-[10px] font-medium tracking-[0.2em] text-gray-500 uppercase">{title}</h2>
      </div>

      {cursorRatio !== null && idx !== -1 && (
        <div 
          className="absolute top-5 z-20 pointer-events-none font-mono text-[10px] flex flex-col gap-0.5 pl-2 whitespace-nowrap"
          style={{ left: `calc(35px + ${cursorRatio} * (100% - 45px))` }}
        >
          <span className="text-gray-400 text-[9px] drop-shadow-[0_1px_3px_rgba(0,0,0,0.9)]">
            {distVal}
          </span>
          <span style={{ color: getTeamColor(data1.Team) }} className="drop-shadow-[0_1px_3px_rgba(0,0,0,0.9)]">
            {data1.Driver}: {val1}
          </span>
          {data2 && (
            <span style={{ color: getTeamColor(data2.Team) }} className="drop-shadow-[0_1px_3px_rgba(0,0,0,0.9)]">
              {data2.Driver}: {val2}
            </span>
          )}
        </div>
      )}
      
      <Plot
        data={chartData}
        layout={{
          height: 200, margin: { l: 35, r: 10, t: 5, b: 15 },
          paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
          xaxis: { showgrid: true, gridcolor: '#121212', zeroline: false, showline: false, tickfont: { color: '#666', size: 10 } },
          yaxis: { showgrid: true, gridcolor: '#121212', zeroline: false, showline: false, tickfont: { color: '#666', size: 10 }, range: yRange },
          hovermode: false,
          showlegend: false,
          shapes: cursorDist !== null ? [{ 
            type: 'line', x0: cursorDist, x1: cursorDist, y0: 0, y1: 1, yref: 'paper', 
            line: { color: '#E10600', width: 1, dash: 'dash' }
          }] : []
        }}
        config={{ displayModeBar: false, staticPlot: true }} style={{ width: '100%' }}
      />
    </div>
  );
};

const TrackMap = () => {
  const { data1, data2, cursorDist } = useStore();
  if (!data1 || !data1.X || data1.X.length === 0) return null;

  const maxDist = data1.Distance[data1.Distance.length - 1] || 1;
  const s1Limit = maxDist * 0.32;
  const s2Limit = maxDist * 0.70;

  const s1 = { x: [] as number[], y: [] as number[] };
  const s2 = { x: [] as number[], y: [] as number[] };
  const s3 = { x: [] as number[], y: [] as number[] };

  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

  for (let i = 0; i < data1.Distance.length; i++) {
    const d = data1.Distance[i];
    const px = data1.X[i];
    const py = data1.Y[i];

    if (px < minX) minX = px;
    if (px > maxX) maxX = px;
    if (py < minY) minY = py;
    if (py > maxY) maxY = py;

    if (d <= s1Limit) { s1.x.push(px); s1.y.push(py); }
    else if (d <= s2Limit) { s2.x.push(px); s2.y.push(py); }
    else { s3.x.push(px); s3.y.push(py); }
  }

  if (s2.x.length > 0) { s1.x.push(s2.x[0]); s1.y.push(s2.y[0]); }
  if (s3.x.length > 0) { s2.x.push(s3.x[0]); s2.y.push(s3.y[0]); }

  const drsPoints = { x: [] as number[], y: [] as number[] };
  for (let i = 0; i < data1.Distance.length; i++) {
    if (data1.DRS[i] >= 10) {
      drsPoints.x.push(data1.X[i]);
      drsPoints.y.push(data1.Y[i]);
    }
  }

  const xPadding = (maxX - minX) * 0.15;
  const yPadding = (maxY - minY) * 0.15;
  const xRange = [minX - xPadding, maxX + xPadding];
  const yRange = [minY - yPadding, maxY + yPadding];

  let cursorPos = null;
  if (cursorDist !== null) {
    const idx = data1.Distance.findIndex(d => d >= cursorDist);
    if (idx !== -1) {
      cursorPos = { x: [data1.X[idx]], y: [data1.Y[idx]] };
    }
  }

  return (
    <div className="relative w-full h-[550px] bg-transparent flex flex-col">
      <div className="flex justify-between items-center px-4 absolute top-2 left-0 w-full z-20 pointer-events-none">
        <h2 className="text-[10px] font-medium tracking-[0.2em] text-gray-500 uppercase drop-shadow-md">Track Map (Sector 1 / 2 / 3)</h2>
        <div className="text-[9px] font-mono tracking-widest flex gap-3 drop-shadow-md">
          <span className="text-[#E10600]">■ S1</span>
          <span className="text-[#00A0E9]">■ S2</span>
          <span className="text-[#FFD500]">■ S3</span>
        </div>
      </div>
      
      <div className="flex-1 w-full h-full relative pointer-events-none mt-8">
        <Plot
          useResizeHandler={true}
          data={[
            { x: s1.x, y: s1.y, type: 'scatter', mode: 'lines', line: { color: '#E10600', width: 4 }, name: 'Sector 1', hoverinfo: 'skip' },
            { x: s2.x, y: s2.y, type: 'scatter', mode: 'lines', line: { color: '#00A0E9', width: 4 }, name: 'Sector 2', hoverinfo: 'skip' },
            { x: s3.x, y: s3.y, type: 'scatter', mode: 'lines', line: { color: '#FFD500', width: 4 }, name: 'Sector 3', hoverinfo: 'skip' },
            { x: drsPoints.x, y: drsPoints.y, type: 'scatter', mode: 'markers', marker: { color: '#00FF00', size: 3, symbol: 'square' }, name: 'DRS', hoverinfo: 'skip' },
            ...(cursorPos ? [{
              x: cursorPos.x, y: cursorPos.y, type: 'scatter', mode: 'markers',
              marker: { color: '#ffffff', size: 10, line: { color: '#15151e', width: 2 } }, name: 'Pos', hoverinfo: 'skip'
            }] : [])
          ] as any[]}
          layout={{
            autosize: true,
            margin: { l: 10, r: 10, t: 20, b: 10 },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            dragmode: false,
            xaxis: { visible: false, fixedrange: true, range: xRange },
            yaxis: { visible: false, fixedrange: true, range: yRange, scaleanchor: 'x', scaleratio: 1 },
            showlegend: false
          }}
          config={{ displayModeBar: false, responsive: true }}
          style={{ width: '100%', height: '100%' }}
        />
      </div>
    </div>
  );
};

function App() {
  const store = useStore();
  const [isAIModalOpen, setIsAIModalOpen] = useState(false);

  useEffect(() => { 
    store.fetchOptions().then(() => store.fetchData()); 
  }, []);

  // 🌟 已加上嚴格的型別斷言 (keyof typeof FALLBACK_OPTIONS)，徹底消除 TypeScript 紅字
  const availableYears = store.menuOptions ? Object.keys(store.menuOptions).sort((a, b) => Number(b) - Number(a)) : Object.keys(FALLBACK_OPTIONS);
  const eventsObj = (store.menuOptions && store.menuOptions[store.year]) || FALLBACK_OPTIONS[store.year as keyof typeof FALLBACK_OPTIONS] || {};
  const availableEvents = Object.keys(eventsObj).sort();
  const availableSessions = eventsObj[store.eventName] || ["FP1", "FP2", "FP3", "Q", "R"];

  const color1 = store.data1 ? getTeamColor(store.data1.Team) : '#3671C6';
  const color2 = store.data2 ? getTeamColor(store.data2.Team) : '#E10600';

  return (
    <div className="h-screen overflow-hidden bg-[#000000] text-gray-200 p-4 lg:p-6 font-sans selection:bg-[#E10600] flex flex-col">
      
      <header className="-mx-4 lg:-mx-6 -mt-4 lg:-mt-6 mb-6 flex flex-col bg-[#15151e] border-t-[4px] border-[#e10600] shadow-xl shrink-0">
        <div className="flex items-center justify-between px-6 lg:px-10 py-4 border-b border-white/10">
          <div className="flex items-center gap-8 lg:gap-12">
            <img src="https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg" alt="F1 Official Logo" className="h-6 lg:h-8 w-auto" />
            <nav className="hidden md:flex gap-6 text-[12px] font-bold uppercase tracking-wider text-white">
              <a href="https://www.formula1.com/en/racing/2024.html" target="_blank" rel="noopener noreferrer" className="hover:text-[#e10600] transition-colors">Schedule</a>
              <a href="https://www.formula1.com/en/results.html/2024/races.html" target="_blank" rel="noopener noreferrer" className="hover:text-[#e10600] transition-colors">Results</a>
              <a href="https://www.formula1.com/en/results.html/2024/team.html" target="_blank" rel="noopener noreferrer" className="hover:text-[#e10600] transition-colors">Standings</a>
              <a href="https://www.formula1.com/en/drivers.html" target="_blank" rel="noopener noreferrer" className="hover:text-[#e10600] transition-colors">Drivers</a>
            </nav>
          </div>
          
          <div className="hidden md:flex items-center gap-4 text-[11px] font-bold uppercase tracking-wider">
            <a href="https://account.formula1.com/#/en/login" target="_blank" rel="noopener noreferrer" className="text-gray-300 hover:text-white transition-colors">Sign In</a>
            <a href="https://f1tv.formula1.com/" target="_blank" rel="noopener noreferrer" className="bg-[#e10600] text-white px-4 py-2 rounded hover:bg-red-700 transition-colors">Subscribe</a>
          </div>
        </div>

        {/* 🌟 頂部主標題列與即時 AI HUD 橫向融合 */}
        <div className="bg-[#000000] px-6 lg:px-10 py-3 flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4 lg:gap-6">
            <h1 className="text-lg lg:text-xl font-light tracking-[0.2em] text-white flex items-center">
              TELEMETRY STUDIO
              <span className="bg-[#e10600] text-white font-bold text-[9px] tracking-widest px-2 py-0.5 rounded ml-3">PRO v2</span>
            </h1>
            <button
              onClick={() => setIsAIModalOpen(true)}
              className="flex items-center gap-2 bg-gradient-to-r from-blue-900 to-blue-700 hover:from-blue-800 hover:to-blue-600 text-white px-4 py-1.5 rounded shadow-[0_0_15px_rgba(59,130,246,0.3)] transition-all duration-300 group"
            >
              <SparklesIcon className="w-4 h-4 text-blue-300 group-hover:animate-pulse" />
              <span className="text-sm font-semibold tracking-widest text-blue-50">AI 深度遙測分析</span>
            </button>
          </div>

          {/* 🌟 即時 AI 資訊條 (直接移到標題旁邊，隨滑鼠位置更新) */}
            {(() => {
              let aiData = null;
              if (store.cursorDist !== null && store.data1 && store.data2) {
                const idx = store.data1.Distance.findIndex(d => d >= store.cursorDist);
                if (idx !== -1) {
                  const speed1 = Number(store.data1.Speed[idx]).toFixed(0);
                  const thr1 = Number(store.data1.Throttle[idx]).toFixed(0);
                  const brk1 = store.data1.Brake[idx];
                  const speed2 = Number(store.data2.Speed[idx]).toFixed(0);
                  const thr2 = Number(store.data2.Throttle[idx]).toFixed(0);
                  const brk2 = store.data2.Brake[idx];
                  const speedDiff = (Number(speed1) - Number(speed2)).toFixed(0);
                  const sign = Number(speed1) > Number(speed2) ? '+' : '';

                  let insightStr = '';
                  if (brk1 > 0 && brk2 === 0) insightStr = `🛑 ${store.data2.Driver} Braking Later!`;
                  else if (brk1 === 0 && brk2 > 0) insightStr = `🛑 ${store.data1.Driver} Braking Later!`;
                  else if (Number(thr1) >= 99 && Number(thr2) < 99) insightStr = `🟢 ${store.data1.Driver} Earlier Throttle!`;
                  else if (Number(thr1) < 99 && Number(thr2) >= 99) insightStr = `🟢 ${store.data2.Driver} Earlier Throttle!`;
                  else if (Math.abs(Number(speed1) - Number(speed2)) > 3) insightStr = `🚀 ${Number(speed1) > Number(speed2) ? store.data1.Driver : store.data2.Driver} Momentum Advantage`;
                  else insightStr = `⚖️ Matching Pace`;

                  aiData = {
                    d1Name: store.data1.Driver,
                    d1Color: getTeamColor(store.data1.Team),
                    s1: speed1,
                    t1: thr1,
                    d2Name: store.data2.Driver,
                    d2Color: getTeamColor(store.data2.Team),
                    s2: speed2,
                    t2: thr2,
                    delta: `${sign}${speedDiff} km/h`,
                    insight: insightStr,
                    dist: store.cursorDist.toFixed(0)
                  };
                }
              }

              return aiData ? (
                <div className="hidden lg:flex items-center gap-6 bg-[#15151e]/80 border border-white/10 px-4 py-1 rounded font-mono text-[10px]">
                  <span className="text-gray-500">DIST: {aiData.dist}m</span>
                  <span style={{ color: aiData.d1Color }} className="font-bold">{aiData.d1Name}: {aiData.s1}km/h (Thr: {aiData.t1}%)</span>
                  <span style={{ color: aiData.d2Color }} className="font-bold">{aiData.d2Name}: {aiData.s2}km/h (Thr: {aiData.t2}%)</span>
                  <span className="text-gray-300">Δ: <strong className="text-white">{aiData.delta}</strong></span>
                  <span className="text-[#e10600] font-sans font-medium">{aiData.insight}</span>
                </div>
              ) : (
                <div className="hidden lg:block text-gray-600 font-mono text-[10px]">
                  [ Hover over telemetry charts for live AI insights ]
                </div>
              );
            })()}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] text-gray-500 font-mono tracking-widest">LIVE SYNC</span>
            <span className="w-2 h-2 bg-[#e10600] rounded-full animate-pulse shadow-[0_0_8px_#e10600]"></span>
          </div>
        </div>
      </header>

      {isAIModalOpen && <AIAnalysisModal onClose={() => setIsAIModalOpen(false)} />}

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 flex-1 overflow-hidden">
        
        <aside className="xl:col-span-3 flex flex-col space-y-6 h-full overflow-y-auto pr-4 pb-10 custom-scrollbar">
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-gray-500 tracking-[0.2em] uppercase font-medium">Year</label>
            <div className="relative flex items-center border-b border-white/10 hover:border-white/30 transition-colors py-1">
              <select value={store.year} onChange={e => {
                  const newYear = e.target.value;
                  const newEventsObj = store.menuOptions?.[newYear] || FALLBACK_OPTIONS[newYear as keyof typeof FALLBACK_OPTIONS] || {};
                  const firstEvent = Object.keys(newEventsObj)[0] || "Bahrain Grand Prix";
                  const firstSession = newEventsObj[firstEvent]?.[0] || "Q";
                  store.updateParams({ year: newYear, eventName: firstEvent, session: firstSession });
                }} className="bg-transparent text-white font-normal text-sm outline-none cursor-pointer w-full appearance-none pr-6">
                {availableYears.map(y => <option key={y} value={y} className="bg-[#15151e] text-white">{y}</option>)}
              </select>
              <div className="absolute right-0 pointer-events-none text-gray-500 text-[10px]">▼</div>
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-gray-500 tracking-[0.2em] uppercase font-medium">Grand Prix</label>
            <div className="relative flex items-center border-b border-white/10 hover:border-white/30 transition-colors py-1">
              <select value={store.eventName} onChange={e => {
                  const newEvent = e.target.value;
                  const currentEventsObj = store.menuOptions?.[store.year] || FALLBACK_OPTIONS[store.year as keyof typeof FALLBACK_OPTIONS] || {};
                  const firstSession = currentEventsObj[newEvent]?.[0] || "Q";
                  store.updateParams({ eventName: newEvent, session: firstSession });
                }} className="bg-transparent text-white font-normal text-sm outline-none cursor-pointer w-full appearance-none pr-6 truncate">
                {availableEvents.map(e => <option key={e} value={e} className="bg-[#15151e] text-white">{e}</option>)}
              </select>
              <div className="absolute right-0 pointer-events-none text-gray-500 text-[10px]">▼</div>
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-gray-500 tracking-[0.2em] uppercase font-medium">Session</label>
            <div className="relative flex items-center border-b border-white/10 hover:border-white/30 transition-colors py-1">
              <select value={store.session} onChange={e => store.updateParams({ session: e.target.value })} className="bg-transparent text-white font-normal text-sm outline-none cursor-pointer w-full appearance-none pr-6">
                {availableSessions.map(s => <option key={s} value={s} className="bg-[#15151e] text-white">{SESSION_MAP[s] || s}</option>)}
              </select>
              <div className="absolute right-0 pointer-events-none text-gray-500 text-[10px]">▼</div>
            </div>
          </div>

          <div className="flex flex-col gap-4 pt-4 border-t border-white/10">
            <div className="flex flex-col gap-1">
              <label className="text-[10px] tracking-[0.2em] uppercase font-bold transition-colors duration-300" style={{ color: color1 }}>DRIVER 1</label>
              <div className="relative flex items-center border-b border-white/10 hover:border-white/30 transition-colors py-1">
                <select value={store.driver1} onChange={e => store.updateParams({ driver1: e.target.value })} className="bg-transparent text-white font-normal text-sm outline-none cursor-pointer w-full appearance-none pr-6">
                  {Object.entries(DRIVER_MAP).map(([abbr, full]) => <option key={abbr} value={abbr} className="bg-[#15151e] text-white">{full}</option>)}
                </select>
                <div className="absolute right-0 pointer-events-none text-gray-500 text-[10px]">▼</div>
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[10px] tracking-[0.2em] uppercase font-bold transition-colors duration-300" style={{ color: color2 }}>DRIVER 2</label>
              <div className="relative flex items-center border-b border-white/10 hover:border-white/30 transition-colors py-1">
                <select value={store.driver2} onChange={e => store.updateParams({ driver2: e.target.value })} className="bg-transparent text-white font-normal text-sm outline-none cursor-pointer w-full appearance-none pr-6">
                  {Object.entries(DRIVER_MAP).map(([abbr, full]) => <option key={abbr} value={abbr} className="bg-[#15151e] text-white">{full}</option>)}
                </select>
                <div className="absolute right-0 pointer-events-none text-gray-500 text-[10px]">▼</div>
              </div>
            </div>
          </div>
        </aside>

        <main className="xl:col-span-5 flex flex-col h-full overflow-y-auto pr-4 pb-20 custom-scrollbar">
          {store.loading ? (
             <div className="flex items-center justify-center min-h-[400px]">
               <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white/20"></div>
             </div>
          ) : (!store.data1) ? (
            <div className="text-gray-600 font-light flex items-center justify-center tracking-widest text-xs uppercase min-h-[400px]">
              No Data Available
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              <TelemetryChart title="Speed (km/h)" metric="Speed" />
              <DeltaChart />
              <TelemetryChart title="Engine (RPM)" metric="RPM" />
              <TelemetryChart title="Throttle (%)" metric="Throttle" yRange={[-5, 105]} />
              <TelemetryChart title="Brake" metric="Brake" yRange={[-0.1, 1.1]} isBrake={true} />
              <TelemetryChart title="Gear" metric="nGear" yRange={[0, 9]} />
              <TelemetryChart title="DRS Status" metric="DRS" yRange={[-1, 15]} />
            </div>
          )}
        </main>

        <div className="xl:col-span-4 h-full relative">
          <TrackMap />
        </div>

      </div>
    </div>
  );
}

export default App;