"use client";

import React, { useEffect, useState } from "react";
import NodeModal from "./component/NodeModal";
import SnakeViewer from "./SnakeViewer";
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

type CompletedTask = {
  id: number;
  nodo: string;
  path: string;
  duration: number;
};

export default function Home() {
  const [nodes, setNodes] = useState<Nodes>({});
  const [tasks, setTasks] = useState<Tasks>({});
  const [results, setResults] = useState<Results>({});
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [orderBy, setOrderBy] = useState<"node" | "timeAsc" | "timeDesc">("node");
  const allResults: string[] = Object.values(results).flat();
  const [completedTasks, setCompletedTasks] = useState<CompletedTask[]>([]);

  // --- Snake: enviar movimiento al backend ---
  async function sendMove(direction: string) {
    await fetch("http://localhost:8000/snake/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "snake_move",
        player_id: "player1",
        direction,
        timestamp: Date.now()
      }),
    });
  }

  async function sendReset() {
  await fetch("http://localhost:8000/snake/move", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      type: "reset_game",
      player_id: "player1",
      timestamp: Date.now()
    }),
  });
}


  // Escuchar teclas para Snake
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowUp") sendMove("up");
      if (e.key === "ArrowDown") sendMove("down");
      if (e.key === "ArrowLeft") sendMove("left");
      if (e.key === "ArrowRight") sendMove("right");
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const sortedResults = [...completedTasks].sort((a, b) => {
    if (orderBy === "timeAsc") {
      return a.duration - b.duration;
    } else if (orderBy === "timeDesc") {
      return b.duration - a.duration;
    } else {
      return a.nodo.localeCompare(b.nodo, undefined, { numeric: true });
    }
  });

  useEffect(() => {
    // WebSocket para nodos, tareas y resultados en tiempo real
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
      <SnakeViewer />
      <div className="flex justify-center my-4">
        <button
          onClick={sendReset}
          className="px-4 py-2 bg-blue-600 text-white rounded shadow hover:bg-blue-700 transition"
        >
          Reiniciar Juego
        </button>
      </div>
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
          {sortedResults.map((task, idx) => (
            <li key={task.id}>
              Nodo {task.nodo} terminó la tarea: {task.path} en {Number(task.duration).toFixed(2)} s
            </li>
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