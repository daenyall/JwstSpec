"use client";

import { useCallback, useEffect, useState } from "react";
import {
  CartesianGrid,
  ErrorBar,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface DatasetQuality {
  status: "good" | "caution" | "poor";
  median_oot_scatter: number | null;
  median_baseline_mismatch: number | null;
  bins_evaluated: number;
  reasons: string[];
}

interface AnalysisMetadata {
  status: "success" | "poor_quality";
  message?: string;
  bin_width: number;
  dataset_quality: DatasetQuality;
  ephemeris_reference?: string;
  time_system?: string;
  duration_source?: string;
}

interface TransitInfo {
  midpoint: number;
  start: number;
  end: number;
  duration_hours: number;
}

interface SpectrumPoint {
  bin_start: number;
  bin_center: number;
  bin_end: number;
  channels: number;
  in_transit_median: number;
  out_of_transit_median: number;
  depth: number;
  uncertainty: number;

  quality_status?: "valid" | "caution";
  quality_reasons?: string[];

  temporal_quality_status?: "valid" | "caution";
  temporal_quality_reasons?: string[];

  median_snr?: number | null;
  negative_fraction?: number | null;
  oot_scatter?: number | null;
  baseline_mismatch?: number | null;
}

interface AnalysisResponse {
  target: string;
  transit: TransitInfo;
  spectrum: SpectrumPoint[];
  analysis: AnalysisMetadata;
}

interface SpectrumDotProps {
    cx?: number;
    cy?: number;
    payload?: {
        depthPercent: number | null;
        isCaution: boolean;
    };
}

export default function Home() {
  const [target, setTarget] = useState("WASP-96b");
  const [data, setData] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyzeTarget = useCallback(async (targetName: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:8000/analyze?target=${encodeURIComponent(targetName)}`
      );

    if (!response.ok) {
    let message = `Backend returned ${response.status}`;

    try {
        const errorData = await response.json();

        if (typeof errorData.detail === "string") {
            message = errorData.detail;
        } else if (errorData.detail?.message) {
            message = errorData.detail.message;
        }
    } catch {
        // Keep the fallback HTTP status message.
    }

    throw new Error(message);
}
      const jsonData: AnalysisResponse = await response.json();

      setData(jsonData);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Unknown error"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void analyzeTarget("WASP-96b");
  }, [analyzeTarget]);

  const spectrumChartData = data
    ? data.spectrum.reduce<
      Array<
        SpectrumPoint & {
          depthPercent: number | null;
          uncertaintyPercent: number | null;
          isCaution: boolean;
        }
      >
    >((result, point, index) => {
      if (index > 0) {
        const previousPoint = data.spectrum[index - 1];

        const expectedGap =
          data.analysis.bin_width * 1.5;

        const actualGap =
          point.bin_center - previousPoint.bin_center;

        if (actualGap > expectedGap) {
          result.push({
            ...previousPoint,
            bin_center:
              previousPoint.bin_center +
              data.analysis.bin_width,
            depthPercent: null,
            uncertaintyPercent: null,
            isCaution: false,
          });
        }
      }

      const isCaution =
        point.quality_status === "caution" ||
        point.temporal_quality_status === "caution";

      result.push({
        ...point,
        depthPercent: point.depth * 100,
        uncertaintyPercent: point.uncertainty * 100,
        isCaution,
      });

      return result;
    }, [])
    : [];

  const isPoorQuality =
    data?.analysis?.status === "poor_quality";

  return (
    <div className="flex min-h-screen flex-col items-center bg-zinc-950 font-sans text-zinc-100">
      <main className="flex w-full max-w-4xl flex-1 flex-col gap-8 bg-zinc-900 px-8 py-20 sm:px-16">
        <form
          className="flex w-full gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            void analyzeTarget(target.trim());
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

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-red-300">
            {error}
          </div>
        )}

        <div>
          <p className="text-sm text-zinc-400">
            Current target
          </p>

          <p className="text-xl font-semibold text-zinc-100">
            {data
              ? data.target
              : loading
                ? "Loading data..."
                : "No data"}
          </p>
        </div>

        {data && isPoorQuality && (
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-6">
            <h2 className="mb-2 text-xl font-semibold text-amber-300">
              Observation quality too poor
            </h2>

            <p className="text-sm leading-relaxed text-zinc-300">
              {data.analysis.message ??
                "The current pipeline could not produce a reliable transmission spectrum from this observation."}
            </p>

            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg border border-zinc-800 bg-zinc-950/70 p-4">
                <p className="text-sm text-zinc-500">
                  Median OOT scatter
                </p>

                <p className="mt-1 font-mono text-lg text-zinc-100">
                  {data.analysis.dataset_quality
                    .median_oot_scatter !== null
                    ? `${(
                      data.analysis.dataset_quality
                        .median_oot_scatter * 100
                    ).toFixed(3)}%`
                    : "N/A"}
                </p>
              </div>

              <div className="rounded-lg border border-zinc-800 bg-zinc-950/70 p-4">
                <p className="text-sm text-zinc-500">
                  Baseline mismatch
                </p>

                <p className="mt-1 font-mono text-lg text-zinc-100">
                  {data.analysis.dataset_quality
                    .median_baseline_mismatch !== null
                    ? `${(
                      data.analysis.dataset_quality
                        .median_baseline_mismatch *
                      100
                    ).toFixed(3)}%`
                    : "N/A"}
                </p>
              </div>
            </div>

            {data.analysis.dataset_quality.reasons.length > 0 && (
              <div className="mt-6">
                <p className="mb-2 text-sm font-medium text-zinc-400">
                  Quality checks
                </p>

                <ul className="space-y-1 text-sm text-amber-200/80">
                  {data.analysis.dataset_quality.reasons.map(
                    (reason) => (
                      <li key={reason}>
                        • {reason}
                      </li>
                    )
                  )}
                </ul>
              </div>
            )}
          </div>
        )}

        {data && !isPoorQuality && (
          <div className="w-full rounded-xl border border-zinc-800 bg-zinc-950 p-4">
            <ResponsiveContainer width="100%" aspect={3}>
              <LineChart
                data={spectrumChartData}
                margin={{
                  top: 10,
                  right: 20,
                  bottom: 55,
                  left: 60,
                }}
              >
                <CartesianGrid stroke="#3f3f46" />

                <XAxis
                  dataKey="bin_center"
                  type="number"
                  domain={["dataMin", "dataMax"]}
                  stroke="#a1a1aa"
                  tick={{ fill: "#d4d4d8" }}
                  tickFormatter={(value: number) =>
                    value.toFixed(1)
                  }
                  label={{
                    value: "Wavelength [µm]",
                    position: "insideBottom",
                    offset: -35,
                    fill: "#d4d4d8",
                  }}
                />

                <YAxis
                  domain={["auto", "auto"]}
                  stroke="#a1a1aa"
                  tick={{ fill: "#d4d4d8" }}
                  tickFormatter={(value: number) =>
                    value.toFixed(2)
                  }
                  label={{
                    value: "Transit depth [%]",
                    angle: -90,
                    position: "insideLeft",
                    dx: -20,
                    fill: "#d4d4d8",
                  }}
                />

                <Tooltip
                  contentStyle={{
                    backgroundColor: "#18181b",
                    borderColor: "#3f3f46",
                    color: "#f4f4f5",
                  }}
                />

                <Legend verticalAlign="top" />

                <Line
                  type="linear"
                  dataKey="depthPercent"
                  name="Transit depth"
                  stroke="#22d3ee"
                  strokeWidth={2}
                  connectNulls={false}
                  isAnimationActive={false}
                  activeDot={{ r: 5 }}
                  dot={(props: SpectrumDotProps) => {
                    const { cx, cy, payload } = props;

                    if (
                      cx === undefined ||
                      cy === undefined ||
                      payload?.depthPercent === null
                    ) {
                      return <></>;
                    }

                    const isCaution = payload?.isCaution === true;

                    return (
                      <circle
                        cx={cx}
                        cy={cy}
                        r={isCaution ? 4 : 2.5}
                        fill={isCaution ? "#f59e0b" : "#22d3ee"}
                        stroke={isCaution ? "#fde68a" : "#22d3ee"}
                        strokeWidth={isCaution ? 1.5 : 1}
                      />
                    );
                  }}
                >
                  <ErrorBar
                    dataKey="uncertaintyPercent"
                    width={4}
                    stroke="#a5f3fc"
                    strokeWidth={1}
                    direction="y"
                  />
                </Line>
              </LineChart>
            </ResponsiveContainer>
            <div className="mt-4 flex items-center justify-center gap-6 text-xs text-zinc-400">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-cyan-400" />
                Valid
              </div>

              <div className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full border border-amber-200 bg-amber-500" />
                Caution
              </div>

              <div className="flex items-center gap-2">
                <span className="h-px w-5 bg-zinc-600" />
                Rejected / unavailable
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}