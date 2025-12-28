import React from 'react'
import ReactDOM from 'react-dom/client'
import Dashboard from './App.jsx' // Note: This imports the default export from App.jsx, which is now the Dashboard component.
import './index.css' // Global styles for index

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Dashboard />
  </React.StrictMode>,
)