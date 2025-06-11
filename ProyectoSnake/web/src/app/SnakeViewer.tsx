"use client";
import React, { useEffect, useState } from "react";

type SnakeState = {
  snake: [number, number][];
  food: [number, number];
  score: number;
  game_over: boolean;
};

export default function SnakeViewer() {
  const [state, setState] = useState<SnakeState | null>(null);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/snake");
    ws.onmessage = (event) => {
      const newState = JSON.parse(event.data);
      setState(newState);
    };
    return () => ws.close();
  }, []);

  return (
    <div>
      <h2 className="text-xl font-bold mb-2">Snake Game (Distribuido)</h2>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(20, 16px)", gap: 1 }}>
        {[...Array(20 * 20)].map((_, idx) => {
          const x = idx % 20;
          const y = Math.floor(idx / 20);
          const isSnake = state?.snake?.some(([sx, sy]) => sx === x && sy === y);
          const isFood = state?.food?.[0] === x && state?.food?.[1] === y;
          return (
            <div
              key={idx}
              style={{
                width: 16,
                height: 16,
                background: isSnake ? "green" : isFood ? "red" : "#eee",
                border: "1px solid #ccc",
              }}
            />
          );
        })}
      </div>
      <div className="mt-2">
        <span>Puntaje: {state?.score ?? 0}</span>
        {state?.game_over && <span className="ml-4 text-red-600">Game Over</span>}
      </div>
    </div>
  );
}