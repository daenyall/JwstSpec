"use client";
import { useState, useEffect } from "react";
import {
    LineChart,
    ResponsiveContainer,
    Legend,
    Tooltip,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
} from "recharts";

interface LightCurvePoint  {
  "H2O": number;
  "CH4": number;
  "MJD-AVG": number;
  "TDB-MID": number;
}

interface GasAnalysisResult {
  "in_transit_median": number;
  "out_of_transit_median": number;
  "depth": number;
}

interface TransitInfo {
  midpoint: number;
  start: number;
  end: number;
  duration_hours: number;
}

interface AnalysisResponse {
  "target": string;
  "lightcurves": LightCurvePoint[];
  "analysis": Record<string, GasAnalysisResult>;
  "transit": TransitInfo;
}

export default function Home() {
  const[data, setData] = useState<AnalysisResponse | null>(null);
useEffect(() => {
  fetch("http://localhost:8000/analyze?target=WASP-96b")
    .then(response => response.json())
    .then(jsonData => setData(jsonData));
}, []);
const chartData = data
  ? data.lightcurves.map(point => ({
      ...point,
      hoursFromMidTransit:
        (point["TDB-MID"] - data.transit.midpoint) * 24,
    }))
  : [];
  return (
    
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
 
         <pre>
        {data ? data.target : "Loading data..."}

        {
          data ? Object.entries(data.analysis ).map(([gas, result]) => (
            <p key={gas}>{gas} {((result.depth * 100)).toFixed(3) + "%"} </p>
          )) : null
          
        }

      </pre>

      <div className="flex w-full">
        
        { data ? 
        <ResponsiveContainer width="100%" aspect={3}>
                <LineChart data={chartData}>
                    <CartesianGrid />
                    <XAxis dataKey="hoursFromMidTransit" type="number" domain={["dataMin", "dataMax"]} tickFormatter={(value) => value.toFixed(1)}/>
                    <YAxis domain={[0.96, 1.02]} ></YAxis>
                    <Legend />
                    <Tooltip />
                    <Line
                        dataKey="H2O"
                        stroke="blue"
                        activeDot={{ r: 8 }}
                    />
                    <Line dataKey="CH4" stroke="red" activeDot={{ r: 8 }} />
                </LineChart>
            </ResponsiveContainer>
            : null
      } 
      </div>
      </main>
    </div>
  );
}
