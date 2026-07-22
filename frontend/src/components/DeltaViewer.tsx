import React, { useState, useEffect } from 'react';
import { parquetRead } from 'hyparquet';
import Plot from 'react-plotly.js';

interface DeltaViewerProps {
    year: number;
    eventName: string;
    sessionName: string;
    driverA: string;
    driverB: string;
}

export default function DeltaViewer({ year, eventName, sessionName, driverA, driverB }: DeltaViewerProps) {
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!year || !eventName || !sessionName || !driverA || !driverB) return;

        async function fetchAndComputeDelta() {
            setLoading(true);
            setError(null);
            try {
                const safeEvent = eventName.replace(/ /g, "_");
                const safeSession = sessionName.replace(/ /g, "_");
                const url = `https://huggingface.co/datasets/SeanKuo2006/F1-Telemetry-Data/resolve/main/${year}_${safeEvent}_${safeSession}.parquet`;

                const response = await fetch(url);
                if (!response.ok) throw new Error("無法從雲端載入該場次的 Parquet 檔案");
                
                const arrayBuffer = await response.arrayBuffer();

                parquetRead({
                    file: arrayBuffer,
                    onComplete: (data: any) => {
                        console.log("成功讀取資料列數：", data.length);
                    }
                });
                
            } catch (err: any) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        }

        fetchAndComputeDelta();
    }, [year, eventName, sessionName, driverA, driverB]);

    if (loading) return <div className="text-white">⏳ 正在從雲端載入並計算遙測 Delta...</div>;
    if (error) return <div className="text-red-500">❌ 錯誤: {error}</div>;

    return (
        <div className="bg-gray-900 p-4 rounded-xl border border-gray-800">
            <h3 className="text-white text-lg font-bold mb-2">
                ⚡ Delta Time Comparison: {driverA} vs {driverB}
            </h3>
            <Plot
                data={[
                    {
                        x: [0, 500, 1000, 1500, 2000],
                        y: [0.0, 0.15, -0.05, 0.3, 0.42],
                        type: 'scatter',
                        mode: 'lines',
                        line: { color: '#00f0ff', width: 2 },
                        name: `Delta (${driverA} relative to ${driverB})`
                    }
                ]}
                layout={{
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                    font: { color: '#ffffff' },
                    xaxis: { title: 'Track Distance (m)', gridcolor: '#333' },
                    yaxis: { title: 'Delta Time (s)', gridcolor: '#333' },
                    margin: { t: 20, r: 20, b: 40, l: 50 },
                    height: 350,
                }}
                useResizeHandler={true}
                style={{ width: '100%', height: '100%' }}
            />
        </div>
    );
}