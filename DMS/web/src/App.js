import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [nodes, setNodes] = useState({});
  const [tasks, setTasks] = useState({});
  const [results, setResults] = useState({});

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [nodesResponse, tasksResponse, resultsResponse] = await Promise.all([
        axios.get('http://127.0.0.1:8000/nodes'),
        axios.get('http://127.0.0.1:8000/tasks'),
        axios.get('http://127.0.0.1:8000/results'),
        ]);

        setNodes(nodesResponse.data);
        setTasks(tasksResponse.data);
        setResults(resultsResponse.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 2000); // Refresh data every 2 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="App">
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
                <td>{stats.cpu_usage || 'N/A'}</td>
                <td>{stats.ram_usage || 'N/A'}</td>
                <td>{stats.disk_usage || 'N/A'}</td>
                <td>{stats.active_tasks || '0'}</td>
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
              <strong>Node {nodeId}:</strong> {taskList.join(', ')}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Transcription Results</h2>
        <ul>
          {Object.entries(results).map(([nodeId, resultList]) => (
            <li key={nodeId}>
              <strong>Node {nodeId}:</strong> {resultList.join(', ')}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

export default App;