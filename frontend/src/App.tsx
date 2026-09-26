import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Activity, BrainCircuit, LayoutDashboard, Settings } from 'lucide-react';
import TaskInput from './components/TaskInput';
import Dashboard from './components/Dashboard';
import AgentManagement from './components/AgentManagement';

const NavLink = ({ to, icon: Icon, children }: any) => {
  const location = useLocation();
  const isActive = location.pathname === to;
  return (
    <Link to={to} className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${isActive ? 'bg-blue-500/10 text-blue-400' : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'}`}>
      <Icon className="w-5 h-5" />
      <span>{children}</span>
    </Link>
  );
};

function App() {
  return (
    <Router>
      <div className="flex h-screen bg-gray-950 text-gray-100">
        {/* Sidebar */}
        <div className="w-64 border-r border-gray-800 bg-gray-900 p-4">
          <div className="flex items-center gap-2 mb-8">
            <BrainCircuit className="text-blue-500 w-8 h-8" />
            <span className="font-bold text-xl tracking-tight">AI Orchestrator</span>
          </div>
          
          <nav className="space-y-2">
            <NavLink to="/" icon={Activity}>Tasks</NavLink>
            <NavLink to="/dashboard" icon={LayoutDashboard}>Dashboard</NavLink>
            <NavLink to="/agents" icon={Settings}>Agents</NavLink>
          </nav>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-auto bg-gray-950 p-8">
          <Routes>
            <Route path="/" element={<TaskInput />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/agents" element={<AgentManagement />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
