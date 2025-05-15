"use client";

import React, { useEffect, useState } from "react";
import NodeModal from "./component/NodeModal";
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";
import "./globals.css";
ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

type Tasks = {
  [nodeId: string]: string[];
};
type Results = {
  [nodeId: string]: string[];
};
type Nodes = {
  [nodeId: string]: {
    cpu?: string;
    ram?: string;
    disk?: string;
    tasks?: string;
  };
};
export default function Home() {
  const [nodes, setNodes] = useState<Nodes>({});
  const [tasks, setTasks] = useState<Tasks>({});
  const [results, setResults] = useState<Results>({});
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [orderBy, setOrderBy] = useState<"node" | "timeAsc" | "timeDesc">("node");
  const allResults: string[] = Object.values(results).flat();

  const sortedResults = [...allResults].sort((a, b) => {
    if (orderBy === "timeAsc") {
      const timeA = parseFloat(a.match(/en ([\d.]+) s/)?.[1] || "0");
      const timeB = parseFloat(b.match(/en ([\d.]+) s/)?.[1] || "0");
      return timeA - timeB;
    } else if (orderBy === "timeDesc") {
      const timeA = parseFloat(a.match(/en ([\d.]+) s/)?.[1] || "0");
      const timeB = parseFloat(b.match(/en ([\d.]+) s/)?.[1] || "0");
      return timeB - timeA;
    } else {
      const nodeA = a.match(/Nodo (node\d+)/)?.[1] || "";
      const nodeB = b.match(/Nodo (node\d+)/)?.[1] || "";
      return nodeA.localeCompare(nodeB, undefined, { numeric: true });
    }
  });

  useEffect(() => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setNodes(data.nodes);
      setTasks(data.tasks);
      setResults(data.results);
      console.log("Mensaje recibido:", data);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("WebSocket cerrado.");
    };

    return () => {
      ws.close();
    };
  }, []);
  return (
    <div className="p-8 bg-gray-100 min-h-screen text-gray-800">
      <h1 className="text-3xl font-bold mb-6 text-center text-blue-600">Distributed Monitoring System</h1>

      <section className="mb-10">
        <h2 className="text-xl font-semibold mb-4 text-gray-700">Node Status</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white shadow rounded-lg">
            <thead>
              <tr className="bg-blue-200 text-left text-sm uppercase text-blue-800">
                <th className="p-3">Node ID</th>
                <th className="p-3">CPU Usage</th>
                <th className="p-3">RAM Usage</th>
                <th className="p-3">Disk Usage</th>
                <th className="p-3">Active Tasks</th>
              </tr>
               </thead>
            <tbody>
              {Object.entries(nodes).map(([nodeId, stats]) => (
                <tr
                  key={nodeId}
                  className="hover:bg-gray-200 cursor-pointer transition-colors"
                  onClick={() => setSelectedNode(nodeId)}
                >
                  <td className="p-3 font-semibold text-gray-700">{nodeId}</td>
                  <td className={`p-3 ${getColor(stats.cpu)} ${getBgColor(stats.cpu)} font-medium`}>
                    {stats.cpu || "N/A"}%
                  </td>
                  <td className={`p-3 ${getColor(stats.ram)} ${getBgColor(stats.ram)} font-medium`}>
                    {stats.ram || "N/A"}%
                  </td>
                  <td className={`p-3 ${getColor(stats.disk)} ${getBgColor(stats.disk)} font-medium`}>
                    {stats.disk || "N/A"}%
                  </td>
                  <td className="p-3 text-gray-700">{stats.tasks || "0"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-6">
        <h2 className="text-xl font-semibold mb-2">Tasks in Progress</h2>
        <ul className="list-disc list-inside text-sm space-y-1">
          {Object.entries(tasks).map(([nodeId, taskList]) => (
            <li key={nodeId}>
              <strong className="text-black-400">{nodeId}:</strong>{" "}
              {taskList
                .map((task) => {
                  try {
                    const parsed = JSON.parse(task);
                    // Extraer solo el nombre del archivo
                    const path = parsed.path || "";
                    const fileName = path.split(/[\\/]/).pop() || path;
                    return fileName;
                  } catch {
                    return task;
                  }
                })
                .join(", ")}
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-6">
        <h2 className="text-xl font-semibold mb-2">Completed tasks</h2>
        <select
          className="mb-2 px-3 py-1 rounded border border-gray-300"
          value={orderBy}
          onChange={e => setOrderBy(e.target.value as "node" | "timeAsc" | "timeDesc")}
        >
          <option value="node">Ordenar por nodo</option>
          <option value="timeAsc">Tiempo (menor a mayor)</option>
          <option value="timeDesc">Tiempo (mayor a menor)</option>
        </select>
        <ul className="list-disc list-inside text-sm space-y-1">
          {sortedResults.map((line, idx) => (
            <li key={idx}>{line}</li>
          ))}
        </ul>
      </section>

      {selectedNode && nodes[selectedNode] && (
        <NodeModal
          isOpen={true}
          onClose={() => setSelectedNode(null)}
          nodeId={selectedNode}
          stats={nodes[selectedNode]}
        />
      )}
    </div>
  );
}
function getColor(value?: string): string {
  const num = parseFloat(value || "0");
  if (num < 40) return "text-green-600";
  if (num < 70) return "text-yellow-600";
  return "text-red-600";
}
 const getBgColor = (value?: string): string => {
    const num = parseFloat(value || "0");
    if (num < 40) return "bg-green-100";
    if (num < 70) return "bg-yellow-100";
    return "bg-red-100";
  };