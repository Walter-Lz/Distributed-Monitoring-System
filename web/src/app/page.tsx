"use client";

import React, { useEffect, useState } from "react";
import "./globals.css";

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
    <div>
      <h1>Distributed Monitoring System</h1>

      <section>
        <h2>Node Status</h2>
        <table>
          <thead>
            <tr>
              <th>Node ID</th>
              <th>CPU Usage</th>
              <th>RAM Usage</th>
              <th>Disk Usage</th>
              <th>Active Tasks</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(nodes).map(([nodeId, stats]) => (
              <tr key={nodeId}>
                <td>{nodeId}</td>
                <td>{stats.cpu || "N/A"}%</td>
                <td>{stats.ram || "N/A"}%</td>
                <td>{stats.disk || "N/A"}%</td>
                <td>{stats.tasks || "0"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2>Tasks in Progress</h2>
        <ul>
          {Object.entries(tasks).map(([nodeId, taskList]) => (
            <li key={nodeId}>
              <strong>Node {nodeId}:</strong> {taskList.join(", ")}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Transcription Results</h2>
        <ul>
          {Object.entries(results).map(([nodeId, resultList]) => (
            <li key={nodeId}>
              <strong>Node {nodeId}:</strong> {resultList.join(", ")}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}