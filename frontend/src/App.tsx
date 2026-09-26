import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom';
import { Activity, BrainCircuit, LayoutDashboard, Settings, WifiOff } from 'lucide-react';
import TaskInput from './components/TaskInput';
import Dashboard from './components/Dashboard';
import AgentManagement from './components/AgentManagement';
import { App as CapApp } from '@capacitor/app';
import { Network } from '@capacitor/network';

const NavLink = ({ to, icon: Icon, children }: any) => {
  const location = useLocation();
  const isActive = location.pathname === to;
  return (
    <Link to={to} className={`flex flex-col md:flex-row items-center justify-center md:justify-start gap-1 md:gap-3 px-3 py-2 md:py-2 rounded-lg transition-colors flex-1 md:flex-none ${isActive ? 'md:bg-blue-500/10 text-blue-400' : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'}`}>
      <Icon className="w-6 h-6 md:w-5 md:h-5" />
      <span className="text-[10px] md:text-base">{children}</span>
    </Link>
  );
};

const CapacitorHandler = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  useEffect(() => {
    const handleBackButton = async () => {
      // Check if there's a modal open (by checking DOM for a known class if needed)
      // Since modal logic is inside AgentManagement, we'll try a generic approach
      const hasModal = document.querySelector('.fixed.inset-0');
      if (hasModal) {
        // Find close button and click it to dismiss modal
        const closeBtn = document.querySelector('.fixed.inset-0 button');
        if (closeBtn) {
          (closeBtn as HTMLElement).click();
          return;
        }
      }
      
      if (location.pathname !== '/') {
        navigate(-1);
      } else {
        CapApp.exitApp();
      }
    };
    
    const listener = CapApp.addListener('backButton', handleBackButton);
    return () => { listener.then(l => l.remove()); };
  }, [location, navigate]);
  
  return null;
};

function App() {
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    const logCurrentNetworkStatus = async () => {
      const status = await Network.getStatus();
      setIsOffline(!status.connected);
    };
    logCurrentNetworkStatus();

    const listener = Network.addListener('networkStatusChange', status => {
      setIsOffline(!status.connected);
    });

    return () => { listener.then(l => l.remove()); };
  }, []);

  return (
    <Router>
      <CapacitorHandler />
      <div className="flex flex-col md:flex-row h-screen bg-gray-950 text-gray-100 overflow-hidden">
        
        {/* Top Header Mobile */}
        <div className="md:hidden flex items-center gap-2 p-4 bg-gray-900 border-b border-gray-800 shrink-0">
          <BrainCircuit className="text-blue-500 w-6 h-6" />
          <span className="font-bold text-lg tracking-tight">AI Orchestrator</span>
        </div>

        {/* Sidebar Desktop */}
        <div className="hidden md:block w-64 border-r border-gray-800 bg-gray-900 p-4 shrink-0">
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
        <div className="flex-1 overflow-auto bg-gray-950 p-4 md:p-8 relative">
          {isOffline && (
            <div className="absolute top-4 left-4 right-4 z-50 bg-red-500/90 text-white px-4 py-3 rounded-lg flex items-center gap-3 shadow-lg">
              <WifiOff className="w-5 h-5 shrink-0" />
              <div className="text-sm font-medium">No internet connection</div>
            </div>
          )}
          <Routes>
            <Route path="/" element={<TaskInput />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/agents" element={<AgentManagement />} />
          </Routes>
        </div>

        {/* Bottom Nav Mobile */}
        <div className="md:hidden flex items-center justify-around p-2 bg-gray-900 border-t border-gray-800 shrink-0 pb-safe">
          <NavLink to="/" icon={Activity}>Tasks</NavLink>
          <NavLink to="/dashboard" icon={LayoutDashboard}>Dashboard</NavLink>
          <NavLink to="/agents" icon={Settings}>Agents</NavLink>
        </div>

      </div>
    </Router>
  );
}

export default App;
