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
  ErrorBar,
} from "recharts";



interface TransitInfo {
  "midpoint": number;
  "start": number;
  "end": number;
  "duration_hours": number;
}

interface SpectrumPoint {
  "bin_start": number;
  "bin_center": number;
  "bin_end": number;
  "channels": number;
  "in_transit_median": number;
  "out_of_transit_median": number;
  "depth": number;
  "uncertainty": number;
}

interface AnalysisResponse {
  "target": string;

  "transit": TransitInfo;
  "spectrum": SpectrumPoint[];
}

export default function Home() {
  const [data, setData] = useState<AnalysisResponse | null>(null);
  useEffect(() => {
    fetch("http://localhost:8000/analyze?target=WASP-96b")
      .then(response => response.json())
      .then(jsonData => setData(jsonData));
  }, []);
  
  const spectrumChartData = data
    ? data.spectrum.map(point => ({
      ...point,
      depthPercent: point.depth * 100,
      uncertaintyPercent: point.uncertainty * 100
    }))
    : [];
  return (

    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">

        <pre>
          {data ? data.target : "Loading data..."}



        </pre>

        <div className="flex w-full">

          {data ?
               <ResponsiveContainer width="100%" aspect={3}>
        <LineChart data={spectrumChartData} margin={{ top: 10, right: 20, bottom: 30, left: 50 }}>
            <CartesianGrid />
            <XAxis dataKey="bin_center" type="number" domain={["dataMin", "dataMax"]} tickFormatter={(value) => value.toFixed(1)} label={{ value: "Wavelength [µm]", position: "insideBottom", offset: -20 }} />
            <YAxis domain={["auto", "auto"]} tickFormatter={(value) => value.toFixed(2)} label={{ value: "Transit depth [%]", angle: -90, position: "insideLeft", dx: -10 }} />
            <Tooltip />
            <Legend />
            <Line type="linear" dataKey="depthPercent" name="Transit depth" stroke="white" dot={{ r: 2 }} activeDot={{ r: 5 }} isAnimationActive={false}>
                <ErrorBar dataKey="uncertaintyPercent" width={4} strokeWidth={1} direction="y" />
            </Line>
        </LineChart>
    </ResponsiveContainer>
            : null
          }
        </div>
       
      </main>
    </div>
  );
}
