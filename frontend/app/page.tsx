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
  const [target, setTarget] = useState("WASP-96b");
  const [data, setData] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyzeTarget = async (targetName: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`http://localhost:8000/analyze?target=${encodeURIComponent(targetName)}`);

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const jsonData: AnalysisResponse = await response.json();
      setData(jsonData);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    analyzeTarget("WASP-96b");
  }, []);

  const spectrumChartData = data
    ? data.spectrum.map(point => ({
      ...point,
      depthPercent: point.depth * 100,
      uncertaintyPercent: point.uncertainty * 100
    }))
    : [];

  return (
  <div className="flex min-h-screen flex-col items-center bg-zinc-950 font-sans text-zinc-100">
    <main className="flex w-full max-w-4xl flex-1 flex-col gap-8 bg-zinc-900 px-8 py-20 sm:px-16">

      <form
        className="flex w-full gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          analyzeTarget(target);
        }}
      >
        <input
          type="text"
          value={target}
          onChange={(event) => setTarget(event.target.value)}
          placeholder="WASP-39b"
          className="flex-1 rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-2 text-zinc-100 outline-none placeholder:text-zinc-500 focus:border-cyan-500"
        />

        <button
          type="submit"
          disabled={loading || target.trim() === ""}
          className="rounded-lg bg-cyan-600 px-5 py-2 font-medium text-white transition hover:bg-cyan-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </form>

      {error ? (
        <p className="text-red-400">
          {error}
        </p>
      ) : null}

      <div>
        <p className="text-sm text-zinc-400">Current target</p>
        <p className="text-xl font-semibold text-zinc-100">
          {data ? data.target : loading ? "Loading data..." : "No data"}
        </p>
      </div>

      <div className="w-full rounded-xl border border-zinc-800 bg-zinc-950 p-4">
        {data ?
          <ResponsiveContainer width="100%" aspect={3}>
            <LineChart data={spectrumChartData} margin={{ top: 10, right: 20, bottom: 30, left: 50 }}>
              <CartesianGrid stroke="#3f3f46" />
              <XAxis
                dataKey="bin_center"
                type="number"
                domain={["dataMin", "dataMax"]}
                stroke="#a1a1aa"
                tick={{ fill: "#d4d4d8" }}
                tickFormatter={(value) => value.toFixed(1)}
                label={{ value: "Wavelength [µm]", position: "insideBottom", offset: -20, fill: "#d4d4d8" }}
              />
              <YAxis
                domain={["auto", "auto"]}
                stroke="#a1a1aa"
                tick={{ fill: "#d4d4d8" }}
                tickFormatter={(value) => value.toFixed(2)}
                label={{ value: "Transit depth [%]", angle: -90, position: "insideLeft", dx: -10, fill: "#d4d4d8" }}
              />
              <Tooltip contentStyle={{ backgroundColor: "#18181b", borderColor: "#3f3f46", color: "#f4f4f5" }} />
              <Legend />
              <Line type="linear" dataKey="depthPercent" name="Transit depth" stroke="#22d3ee" strokeWidth={2} dot={{ r: 2 }} activeDot={{ r: 5 }} isAnimationActive={false}>
                <ErrorBar dataKey="uncertaintyPercent" width={4} stroke="#a5f3fc" strokeWidth={1} direction="y" />
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
