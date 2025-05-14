// components/NodeModal.tsx
"use client";
import { Dialog } from "@headlessui/react";
import { Radar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  ChartOptions,
} from "chart.js";
import React from "react";

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

type Props = {
  isOpen: boolean;
  onClose: () => void;
  nodeId: string;
  stats: {
    cpu?: string;
    ram?: string;
    disk?: string;
  };
};

export default function NodeModal({ isOpen, onClose, nodeId, stats }: Props) {
  const format = (val?: string) => parseFloat(val?.replace("%", "") || "0");

  const data = {
    labels: ["CPU", "RAM", "DISK"],
    datasets: [
      {
        label: `${nodeId} Stats`,
        data: [
          format(stats.cpu),
          format(stats.ram),
          format(stats.disk),
        ],
        backgroundColor: "rgba(208, 233, 232, 0.2)",
        borderColor: "rgba(34, 197, 94, 1)",
        pointBackgroundColor: "rgba(11, 12, 11, 0.93)",
        pointBorderColor: "#fff",
        pointHoverBackgroundColor: "#fff",
        pointHoverBorderColor: "rgba(34, 197, 94, 1)",
      },
    ],
  };

  const options: ChartOptions<"radar"> = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        angleLines: {
          display: true,
          color: "rgba(200, 200, 200, 0.5)"
        },
        suggestedMin: 0,
        suggestedMax: 100,
        ticks: {
          stepSize: 20,
          backdropColor: "transparent",
          color: "#555",
        },
        pointLabels: {
          color: "#333",
          font: {
            size: 14,
            weight: "bold",
          },
        },
        grid: {
          color: "rgba(200, 200, 200, 0.5)"
        },
        backgroundColor: "rgba(245, 245, 245, 0.3)"
      }
    },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: "#6b3939",
          font: {
            size: 14,
          },
        },
      },
    },
  };

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" aria-hidden="true" />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="bg-white rounded-2xl p-6 shadow-xl w-full max-w-md">
          <Dialog.Title className="text-gray-800 text-lg font-bold mb-4">
            {nodeId} Resource Usage
          </Dialog.Title>
          <div className="h-64 flex items-center justify-center">
            <Radar data={data} options={options} />
          </div>
          <button
            onClick={onClose}
            className="mt-4 px-4 py-2 bg-green-500 hover:bg-green-600 rounded text-white w-full transition-colors"
          >
            Close
          </button>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
}