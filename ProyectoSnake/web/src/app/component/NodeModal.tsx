"use client"

import { Dialog } from "@headlessui/react"
import { Radar } from "react-chartjs-2"
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  type ChartOptions,
} from "chart.js"

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

type Props = {
  isOpen: boolean
  onClose: () => void
  nodeId: string
  stats: {
    cpu?: string
    ram?: string
    disk?: string
  }
}

export default function NodeModal({ isOpen, onClose, nodeId, stats }: Props) {
  const format = (val?: string) => Number.parseFloat(val?.replace("%", "") || "0")

  const data = {
    labels: ["CPU", "RAM", "DISK"],
    datasets: [
      {
        label: `${nodeId} Stats`,
        data: [format(stats.cpu), format(stats.ram), format(stats.disk)],
        backgroundColor: "rgba(99, 102, 241, 0.3)",
        borderColor: "rgba(129, 140, 248, 1)",
        pointBackgroundColor: "rgba(79, 70, 229, 1)",
        pointBorderColor: "#fff",
        pointHoverBackgroundColor: "#fff",
        pointHoverBorderColor: "rgba(129, 140, 248, 1)",
        borderWidth: 2,
      },
    ],
  }

  const options: ChartOptions<"radar"> = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        angleLines: {
          display: true,
          color: "rgba(148, 163, 184, 0.2)",
        },
        suggestedMin: 0,
        suggestedMax: 100,
        ticks: {
          stepSize: 20,
          backdropColor: "transparent",
          color: "rgba(203, 213, 225, 0.8)",
        },
        pointLabels: {
          color: "rgba(226, 232, 240, 1)",
          font: {
            size: 14,
            weight: "bold",
          },
        },
        grid: {
          color: "rgba(148, 163, 184, 0.2)",
        },
        backgroundColor: "rgba(30, 41, 59, 0.4)",
      },
    },
    plugins: {
      legend: {
        position: "top",
        labels: {
          color: "rgba(226, 232, 240, 1)",
          font: {
            size: 14,
            weight: "bold",
          },
          padding: 20,
        },
      },
      tooltip: {
        backgroundColor: "rgba(30, 41, 59, 0.8)",
        titleColor: "rgba(226, 232, 240, 1)",
        bodyColor: "rgba(226, 232, 240, 1)",
        borderColor: "rgba(99, 102, 241, 0.5)",
        borderWidth: 1,
        padding: 12,
        displayColors: true,
        callbacks: {
          label: (context) => `${context.dataset.label}: ${context.parsed.r}%`,
        },
      },
    },
  }

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-slate-900/80 backdrop-blur-sm" aria-hidden="true" />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="animate-pulse-slow opacity-20 blur-2xl">
            <div className="w-64 h-64 rounded-full bg-purple-600/20 absolute -top-10 -left-12"></div>
            <div className="w-96 h-96 rounded-full bg-blue-600/20 absolute top-40 left-40"></div>
          </div>
        </div>

       <Dialog.Panel className="relative w-full max-w-md overflow-hidden">
  <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 rounded-2xl blur opacity-30"></div>
  <div className="relative bg-slate-800/90 backdrop-blur-sm rounded-2xl border border-slate-700/50 shadow-2xl p-6">
    <Dialog.Title className="text-center mb-6 text-2xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
      {nodeId} Resource Usage
    </Dialog.Title>
    <div className="w-24 h-1 bg-gradient-to-r from-blue-400 via-purple-400 to-indigo-400 mx-auto rounded-full mt-2"></div>

    <div className="h-80 flex items-center justify-center mb-6">
      <Radar data={data} options={options} />
    </div>

    <div className="grid grid-cols-3 gap-4 mb-6">
      <div className="bg-slate-700/50 rounded-lg p-3 text-center border border-slate-600/50">
        <div className="text-xs text-slate-400 mb-1">CPU</div>
        <div
          className={`text-lg font-bold ${
            format(stats.cpu) < 40
              ? "text-green-400"
              : format(stats.cpu) < 70
                ? "text-yellow-400"
                : "text-red-400"
          }`}
        >
          {stats.cpu || "0%"}
        </div>
      </div>
      <div className="bg-slate-700/50 rounded-lg p-3 text-center border border-slate-600/50">
        <div className="text-xs text-slate-400 mb-1">RAM</div>
        <div
          className={`text-lg font-bold ${
            format(stats.ram) < 40
              ? "text-green-400"
              : format(stats.ram) < 70
                ? "text-yellow-400"
                : "text-red-400"
          }`}
        >
          {stats.ram || "0%"}
        </div>
      </div>
      <div className="bg-slate-700/50 rounded-lg p-3 text-center border border-slate-600/50">
        <div className="text-xs text-slate-400 mb-1">DISK</div>
        <div
          className={`text-lg font-bold ${
            format(stats.disk) < 40
              ? "text-green-400"
              : format(stats.disk) < 70
                ? "text-yellow-400"
                : "text-red-400"
          }`}
        >
          {stats.disk || "0%"}
        </div>
      </div>
    </div>

    <button
      onClick={onClose}
      className="group relative w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02]"
    >
      <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl blur opacity-30 group-hover:opacity-100 transition duration-300"></div>
      <span className="relative">Close</span>
    </button>
  </div>
</Dialog.Panel>
      </div>
    </Dialog>
  )
}
