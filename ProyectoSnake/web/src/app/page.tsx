"use client"

import { useEffect, useState } from "react"
import NodeModal from "./component/NodeModal"
import SnakeViewer from "./SnakeViewer"
import { Chart as ChartJS, RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend } from "chart.js"
import "./globals.css"

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

type Tasks = {
  [nodeId: string]: string[]
}
type Results = {
  [nodeId: string]: string[]
}
type Nodes = {
  [nodeId: string]: {
    cpu?: string
    ram?: string
    disk?: string
    tasks?: string
  }
}

type CompletedTask = {
  id: number
  nodo: string
  path: string
  duration: number
}

export default function Home() {
  const [nodes, setNodes] = useState<Nodes>({})
  const [tasks, setTasks] = useState<Tasks>({})
  const [results, setResults] = useState<Results>({})
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [orderBy, setOrderBy] = useState<"node" | "timeAsc" | "timeDesc">("node")
  const allResults: string[] = Object.values(results).flat()
  const [completedTasks, setCompletedTasks] = useState<CompletedTask[]>([])

  // --- Snake: enviar movimiento al backend ---
  async function sendMove(direction: string) {
    await fetch("http://localhost:8000/snake/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "snake_move",
        player_id: "player1",
        direction,
        timestamp: Date.now(),
      }),
    })
  }

  async function sendReset() {
    await fetch("http://localhost:8000/snake/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "reset_game",
        player_id: "player1",
        timestamp: Date.now(),
      }),
    })
  }

  // Escuchar teclas para Snake
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowUp") sendMove("up")
      if (e.key === "ArrowDown") sendMove("down")
      if (e.key === "ArrowLeft") sendMove("left")
      if (e.key === "ArrowRight") sendMove("right")
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [])

  const sortedResults = [...completedTasks].sort((a, b) => {
    if (orderBy === "timeAsc") {
      return a.duration - b.duration
    } else if (orderBy === "timeDesc") {
      return b.duration - a.duration
    } else {
      return a.nodo.localeCompare(b.nodo, undefined, { numeric: true })
    }
  })

  useEffect(() => {
    // WebSocket para nodos, tareas y resultados en tiempo real
    const ws = new WebSocket("ws://127.0.0.1:8000/ws")

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setNodes(data.nodes)
      setTasks(data.tasks)
      setResults(data.results)
      console.log("Mensaje recibido:", data)
    }

    ws.onerror = (error) => {
      console.error("WebSocket error:", error)
    }

    ws.onclose = () => {
      console.log("WebSocket cerrado.")
    }

    return () => {
      ws.close()
    }
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      {/* Header */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 via-purple-600/20 to-pink-600/20"></div>
        <div className="relative px-8 py-12">
          <h1 className="text-5xl font-bold text-center mb-4">
            <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              🚀 Distributed Monitoring System
            </span>
          </h1>
          <p className="text-center text-slate-300 text-lg">Real-time Node Monitoring & Gaming Platform</p>
        </div>
      </div>

      <div className="px-8 pb-8 space-y-8">
        {/* Snake Game Section */}
        <div className="flex justify-center">
          <div className="w-full max-w-2xl">
            <SnakeViewer />
            <div className="flex justify-center mt-6">
              <button
                onClick={sendReset}
                className="group relative px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
              >
                <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl blur opacity-30 group-hover:opacity-100 transition duration-300"></div>
                <span className="relative">🔄 Reiniciar Juego</span>
              </button>
            </div>
          </div>
        </div>

        {/* Node Status Section */}
        <section className="space-y-6">
          <div className="text-center">
            <h2 className="text-3xl font-bold bg-gradient-to-r from-green-400 to-blue-500 bg-clip-text text-transparent mb-2">
              📊 Node Status
            </h2>
            <div className="w-24 h-1 bg-gradient-to-r from-green-400 to-blue-500 mx-auto rounded-full"></div>
          </div>

          <div className="relative">
            <div className="absolute -inset-1 bg-gradient-to-r from-green-400 via-blue-500 to-purple-600 rounded-2xl blur opacity-20"></div>
            <div className="relative bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/50 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="bg-gradient-to-r from-slate-800 to-slate-700 border-b border-slate-600">
                      <th className="p-4 text-left text-sm font-semibold text-slate-300 uppercase tracking-wider">
                        Node ID
                      </th>
                      <th className="p-4 text-left text-sm font-semibold text-slate-300 uppercase tracking-wider">
                        CPU Usage
                      </th>
                      <th className="p-4 text-left text-sm font-semibold text-slate-300 uppercase tracking-wider">
                        RAM Usage
                      </th>
                      <th className="p-4 text-left text-sm font-semibold text-slate-300 uppercase tracking-wider">
                        Disk Usage
                      </th>
                      <th className="p-4 text-left text-sm font-semibold text-slate-300 uppercase tracking-wider">
                        Active Tasks
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700/50">
                    {Object.entries(nodes).map(([nodeId, stats]) => (
                      <tr
                        key={nodeId}
                        className="hover:bg-slate-700/30 cursor-pointer transition-all duration-200 group"
                        onClick={() => setSelectedNode(nodeId)}
                      >
                        <td className="p-4">
                          <div className="flex items-center space-x-2">
                            <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                            <span className="font-semibold text-blue-300">{nodeId}</span>
                          </div>
                        </td>
                        <td className="p-4">
                          <div
                            className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getEnhancedColor(stats.cpu)} ${getEnhancedBgColor(stats.cpu)}`}
                          >
                            {stats.cpu || "N/A"}%
                          </div>
                        </td>
                        <td className="p-4">
                          <div
                            className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getEnhancedColor(stats.ram)} ${getEnhancedBgColor(stats.ram)}`}
                          >
                            {stats.ram || "N/A"}%
                          </div>
                        </td>
                        <td className="p-4">
                          <div
                            className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getEnhancedColor(stats.disk)} ${getEnhancedBgColor(stats.disk)}`}
                          >
                            {stats.disk || "N/A"}%
                          </div>
                        </td>
                        <td className="p-4">
                          <span className="text-slate-300 font-medium">{stats.tasks || "0"}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        {/* Tasks and Results Grid */}
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Tasks in Progress */}
          <section className="space-y-4">
            <div className="text-center lg:text-left">
              <h2 className="text-2xl font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent mb-2">
                ⚡ Tasks in Progress
              </h2>
              <div className="w-16 h-1 bg-gradient-to-r from-yellow-400 to-orange-500 mx-auto lg:mx-0 rounded-full"></div>
            </div>

            <div className="relative">
              <div className="absolute -inset-1 bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 rounded-xl blur opacity-20"></div>
              <div className="relative bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6">
                <div className="space-y-3">
                  {Object.entries(tasks).length === 0 ? (
                    <p className="text-slate-400 text-center py-4">No active tasks</p>
                  ) : (
                    Object.entries(tasks).map(([nodeId, taskList]) => (
                      <div key={nodeId} className="flex items-start space-x-3 p-3 bg-slate-700/30 rounded-lg">
                        <div className="w-2 h-2 bg-yellow-400 rounded-full mt-2 animate-pulse"></div>
                        <div>
                          <span className="font-semibold text-yellow-300">{nodeId}:</span>
                          <span className="ml-2 text-slate-300">
                            {taskList
                              .map((task) => {
                                try {
                                  const parsed = JSON.parse(task)
                                  const path = parsed.path || ""
                                  const fileName = path.split(/[\\/]/).pop() || path
                                  return fileName
                                } catch {
                                  return task
                                }
                              })
                              .join(", ")}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </section>

          {/* Completed Tasks */}
          <section className="space-y-4">
            <div className="text-center lg:text-left">
              <h2 className="text-2xl font-bold bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent mb-2">
                ✅ Completed Tasks
              </h2>
              <div className="w-16 h-1 bg-gradient-to-r from-green-400 to-emerald-500 mx-auto lg:mx-0 rounded-full"></div>
            </div>

            <div className="relative">
              <div className="absolute -inset-1 bg-gradient-to-r from-green-400 via-emerald-500 to-teal-500 rounded-xl blur opacity-20"></div>
              <div className="relative bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6">
                <div className="mb-4">
                  <select
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-300 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    value={orderBy}
                    onChange={(e) => setOrderBy(e.target.value as "node" | "timeAsc" | "timeDesc")}
                  >
                    <option value="node">Ordenar por nodo</option>
                    <option value="timeAsc">Tiempo (menor a mayor)</option>
                    <option value="timeDesc">Tiempo (mayor a menor)</option>
                  </select>
                </div>

                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {sortedResults.length === 0 ? (
                    <p className="text-slate-400 text-center py-4">No completed tasks</p>
                  ) : (
                    sortedResults.map((task) => (
                      <div key={task.id} className="flex items-start space-x-3 p-3 bg-slate-700/30 rounded-lg">
                        <div className="w-2 h-2 bg-green-400 rounded-full mt-2"></div>
                        <div className="text-sm text-slate-300">
                          <span className="font-semibold text-green-300">Nodo {task.nodo}</span> terminó la tarea:{" "}
                          <span className="text-slate-400">{task.path}</span> en{" "}
                          <span className="font-semibold text-blue-300">{Number(task.duration).toFixed(2)}s</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>

      {/* Modal */}
      {selectedNode && nodes[selectedNode] && (
        <NodeModal
          isOpen={true}
          onClose={() => setSelectedNode(null)}
          nodeId={selectedNode}
          stats={nodes[selectedNode]}
        />
      )}
    </div>
  )
}

function getEnhancedColor(value?: string): string {
  const num = Number.parseFloat(value || "0")
  if (num < 40) return "text-green-300"
  if (num < 70) return "text-yellow-300"
  return "text-red-300"
}

function getEnhancedBgColor(value?: string): string {
  const num = Number.parseFloat(value || "0")
  if (num < 40) return "bg-green-500/20 border border-green-500/30"
  if (num < 70) return "bg-yellow-500/20 border border-yellow-500/30"
  return "bg-red-500/20 border border-red-500/30"
}

// Mantener las funciones originales para compatibilidad
function getColor(value?: string): string {
  const num = Number.parseFloat(value || "0")
  if (num < 40) return "text-green-600"
  if (num < 70) return "text-yellow-600"
  return "text-red-600"
}

const getBgColor = (value?: string): string => {
  const num = Number.parseFloat(value || "0")
  if (num < 40) return "bg-green-100"
  if (num < 70) return "bg-yellow-100"
  return "bg-red-100"
}
