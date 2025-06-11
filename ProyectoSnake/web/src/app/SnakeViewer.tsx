"use client"
import { useEffect, useState } from "react"

type SnakeState = {
  snake: [number, number][]
  food: [number, number]
  score: number
  game_over: boolean
}

export default function SnakeViewer() {
  const [state, setState] = useState<SnakeState | null>(null)

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/snake")
    ws.onmessage = (event) => {
      const newState = JSON.parse(event.data)
      setState(newState)
    }
    return () => ws.close()
  }, [])
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (
        event.key === "ArrowUp" ||
        event.key === "ArrowDown" ||
        event.key === "ArrowLeft" ||
        event.key === "ArrowRight"
      ) {
        event.preventDefault()
        // Aquí puedes enviar el movimiento al backend si quieres.
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [])

  return (
    <div className="flex flex-col items-center p-6 bg-gradient-to-br from-slate-800/50 via-purple-800/30 to-slate-800/50 backdrop-blur-sm rounded-2xl shadow-2xl border border-purple-500/20">
      <div className="mb-6 text-center">
        <h2 className="text-3xl font-bold bg-gradient-to-r from-green-400 to-blue-500 bg-clip-text text-transparent mb-2">
          🐍 Snake Game
        </h2>
        <p className="text-purple-300 text-sm font-medium">Distributed Gaming System</p>
      </div>

      <div className="relative mb-6">
        <div className="absolute -inset-1 bg-gradient-to-r from-green-400 via-blue-500 to-purple-600 rounded-lg blur opacity-30"></div>
        <div
          className="relative bg-slate-800 p-4 rounded-lg shadow-inner border border-slate-700"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(20, 20px)",
            gap: "1px",
            background: "linear-gradient(135deg, #1e293b 0%, #334155 100%)",
          }}
        >
          {[...Array(20 * 20)].map((_, idx) => {
            const x = idx % 20
            const y = Math.floor(idx / 20)
            const isSnake = state?.snake?.some(([sx, sy]) => sx === x && sy === y)
            const isSnakeHead = state?.snake?.[0]?.[0] === x && state?.snake?.[0]?.[1] === y
            const isFood = state?.food?.[0] === x && state?.food?.[1] === y

            let cellClass = "w-5 h-5 rounded-sm transition-all duration-150 border border-slate-600/30"

            if (isSnake) {
              if (isSnakeHead) {
                cellClass +=
                  " bg-gradient-to-br from-green-300 to-green-500 shadow-lg shadow-green-500/50 border-green-400"
              } else {
                cellClass += " bg-gradient-to-br from-green-400 to-green-600 border-green-500"
              }
            } else if (isFood) {
              cellClass +=
                " bg-gradient-to-br from-red-400 to-red-600 shadow-lg shadow-red-500/50 border-red-400 animate-pulse"
            } else {
              cellClass += " bg-slate-700/50 hover:bg-slate-600/50"
            }

            return <div key={idx} className={cellClass} />
          })}
        </div>
      </div>

      <div className="flex items-center justify-between w-full max-w-md bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-yellow-400 rounded-full animate-pulse"></div>
          <span className="text-slate-300 font-medium">Score:</span>
          <span className="text-2xl font-bold text-yellow-400 min-w-[3rem] text-center">{state?.score ?? 0}</span>
        </div>

        {state?.game_over && (
          <div className="flex items-center space-x-2 animate-bounce">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span className="text-red-400 font-bold text-lg">Game Over!</span>
          </div>
        )}

        {!state?.game_over && state?.snake && (
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-green-400 font-medium">Playing</span>
          </div>
        )}
      </div>

      <div className="mt-4 text-center">
        <p className="text-slate-400 text-sm">Use arrow keys to control the snake</p>
        <div className="flex justify-center mt-2 space-x-1">
          <kbd className="px-2 py-1 text-xs bg-slate-700 text-slate-300 rounded border border-slate-600">↑</kbd>
          <kbd className="px-2 py-1 text-xs bg-slate-700 text-slate-300 rounded border border-slate-600">↓</kbd>
          <kbd className="px-2 py-1 text-xs bg-slate-700 text-slate-300 rounded border border-slate-600">←</kbd>
          <kbd className="px-2 py-1 text-xs bg-slate-700 text-slate-300 rounded border border-slate-600">→</kbd>
        </div>
      </div>
    </div>
  )
}