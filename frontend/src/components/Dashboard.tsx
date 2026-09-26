import { useEffect, useState } from 'react';
import { getStatistics, getAgents, getRecentExecutions } from '../services/api';
import { Activity, CheckCircle, Clock, Zap } from 'lucide-react';

const StatCard = ({ title, value, icon: Icon, colorClass }: any) => (
  <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 flex items-center justify-between">
    <div>
      <p className="text-gray-400 text-sm font-medium mb-1">{title}</p>
      <h3 className="text-2xl font-bold text-gray-100">{value}</h3>
    </div>
    <div className={`p-3 rounded-lg ${colorClass}`}>
      <Icon className="w-6 h-6" />
    </div>
  </div>
);

const Dashboard = () => {
    const [stats, setStats] = useState<any>(null);
    const [agents, setAgents] = useState<any[]>([]);
    const [recentTasks, setRecentTasks] = useState<any[]>([]);

    useEffect(() => {
        getStatistics().then(setStats).catch(console.error);
        getAgents().then(setAgents).catch(console.error);
        getRecentExecutions().then(setRecentTasks).catch(console.error);
    }, []);

    return (
        <div className="max-w-6xl mx-auto h-full pb-10">
            <h1 className="text-3xl font-bold mb-8">System Dashboard</h1>
            
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
                    <StatCard title="Total Tasks" value={stats.total_tasks} icon={Activity} colorClass="bg-blue-500/10 text-blue-500" />
                    <StatCard title="Success Rate" value={stats.success_rate !== null ? `${stats.success_rate.toFixed(1)}%` : 'N/A'} icon={CheckCircle} colorClass="bg-green-500/10 text-green-500" />
                    <StatCard title="Fallback Rate" value={stats.fallback_rate !== null ? `${stats.fallback_rate.toFixed(1)}%` : 'N/A'} icon={Zap} colorClass="bg-amber-500/10 text-amber-500" />
                    <StatCard title="Avg Latency" value={stats.average_latency !== null ? `${stats.average_latency.toFixed(2)}s` : 'N/A'} icon={Clock} colorClass="bg-purple-500/10 text-purple-500" />
                </div>
            )}

            <h2 className="text-2xl font-bold mb-6">Agent Performance</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-10">
                {agents.map((agent: any) => (
                    <div key={agent.id} className="bg-gray-900 border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors flex flex-col">
                        <div className="flex justify-between items-start mb-4">
                            <h3 className="text-lg font-semibold text-gray-100">{agent.name}</h3>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${agent.is_active ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                                {agent.is_active ? 'Active' : 'Inactive'}
                            </span>
                        </div>
                        <div className="flex flex-wrap gap-2 mb-4">
                            {agent.capabilities.map((cap: string, i: number) => (
                                <span key={i} className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-300 border border-gray-700">
                                    {cap}
                                </span>
                            ))}
                        </div>
                        
                        {agent.executions === 0 ? (
                            <div className="mt-auto pt-4 border-t border-gray-800 text-sm text-gray-500 italic">
                                No execution data
                            </div>
                        ) : (
                            <div className="space-y-2 mt-auto pt-4 border-t border-gray-800">
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-500">Executions</span>
                                    <span className="text-gray-300">{agent.executions}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-500">Success Rate</span>
                                    <span className="text-gray-300">{agent.success_rate !== null ? `${agent.success_rate.toFixed(1)}%` : 'N/A'}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-500">Avg Quality</span>
                                    <span className="text-gray-300">{agent.quality_score !== null ? agent.quality_score.toFixed(2) : 'N/A'}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-500">Avg Latency</span>
                                    <span className="text-gray-300">{agent.average_latency !== null ? `${agent.average_latency.toFixed(2)}s` : 'N/A'}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-500">Fallbacks Triggered</span>
                                    <span className="text-gray-300">{agent.fallback_count || 0}</span>
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            <h2 className="text-2xl font-bold mb-6">Recent Executions</h2>
            <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                {recentTasks.length === 0 ? (
                    <div className="p-8 text-center text-gray-500 italic">No execution history yet. Run your first task to generate real performance data.</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse whitespace-nowrap min-w-[600px]">
                            <thead>
                                <tr className="bg-gray-800/50 border-b border-gray-800 text-gray-400 text-sm">
                                    <th className="p-4 font-medium">Task</th>
                                    <th className="p-4 font-medium">Type</th>
                                    <th className="p-4 font-medium">Agents Used</th>
                                    <th className="p-4 font-medium">Latency</th>
                                    <th className="p-4 font-medium">Quality</th>
                                    <th className="p-4 font-medium">Status</th>
                                </tr>
                            </thead>
                            <tbody className="text-sm">
                                {recentTasks.map((task: any) => (
                                    <tr key={task.id} className="border-b border-gray-800/50 hover:bg-gray-800/20">
                                        <td className="p-4 truncate max-w-[150px] md:max-w-[200px] text-gray-200" title={task.prompt}>{task.prompt}</td>
                                        <td className="p-4 text-gray-400">{task.type}</td>
                                        <td className="p-4 text-gray-400">{task.agents_used.join(', ')}</td>
                                        <td className="p-4 text-gray-400">{task.latency ? `${task.latency.toFixed(2)}s` : '-'}</td>
                                        <td className="p-4">
                                            {task.quality !== null ? (
                                                <span className={task.quality >= 0.75 ? "text-green-400" : "text-amber-400"}>{task.quality.toFixed(2)}</span>
                                            ) : '-'}
                                        </td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                                                task.status === 'completed' ? 'bg-green-500/10 text-green-400' :
                                                task.status === 'failed' ? 'bg-red-500/10 text-red-400' :
                                                'bg-blue-500/10 text-blue-400'
                                            }`}>
                                                {task.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
