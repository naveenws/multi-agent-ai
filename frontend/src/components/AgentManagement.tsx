import { useEffect, useState } from 'react';
import { getAgents } from '../services/api';
import { Edit2, Power, X, Loader2, CheckCircle, XCircle, Trash2 } from 'lucide-react';
import axios from 'axios';

const AgentManagement = () => {
    const [agents, setAgents] = useState<any[]>([]);
    const [showModal, setShowModal] = useState(false);
    
    // Form state
    const [name, setName] = useState('');
    const [provider, setProvider] = useState('Google Gemini');
    const [apiKey, setApiKey] = useState('');
    const [baseUrl, setBaseUrl] = useState('');
    const [model, setModel] = useState('');
    const [capabilitiesStr, setCapabilitiesStr] = useState('');
    
    const [modelsList, setModelsList] = useState<string[]>([]);
    const [isTesting, setIsTesting] = useState(false);
    const [testResult, setTestResult] = useState<any>(null);
    const [isFetchingModels, setIsFetchingModels] = useState(false);
    
    const [providersInfo, setProvidersInfo] = useState<any[]>([]);

    const fetchAgents = () => {
        getAgents().then(setAgents).catch(console.error);
    };

    useEffect(() => {
        fetchAgents();
        // Fetch provider configs
        axios.get(`${API_BASE}/providers`).then(res => {
            if (res.data && res.data.providers) {
                setProvidersInfo(res.data.providers);
            }
        }).catch(console.error);
    }, []);

    const selectedProviderConfig = providersInfo.find(p => p.name === provider);

    // Reset when modal opens/closes
    useEffect(() => {
        if (!showModal) {
            setName('');
            setApiKey('');
            setBaseUrl('');
            setModel('');
            setCapabilitiesStr('');
            setTestResult(null);
            setModelsList([]);
            setEditingAgentId(null);
        } else {
            handleFetchModels(provider, apiKey, baseUrl);
        }
    }, [showModal]);

    // Handle provider change
    useEffect(() => {
        if (showModal) {
            setTestResult(null);
            if (selectedProviderConfig && selectedProviderConfig.default_base_url) {
                setBaseUrl(selectedProviderConfig.default_base_url);
            } else {
                setBaseUrl('');
            }
            handleFetchModels(provider, apiKey, baseUrl);
        }
    }, [provider, selectedProviderConfig]);
    
    const handleFetchModels = async (prov: string, key: string, url: string) => {
        setIsFetchingModels(true);
        try {
            const res = await axios.post(`${API_BASE}/providers/models`, {
                provider: prov,
                api_key: key,
                base_url: url
            });
            setModelsList(res.data.models || []);
            if (res.data.models?.length > 0 && !model) {
                setModel(res.data.models[0]);
            }
        } catch (e) {
            setModelsList([]);
        } finally {
            setIsFetchingModels(false);
        }
    };

    const handleTestConnection = async () => {
        setIsTesting(true);
        setTestResult(null);
        try {
            const res = await axios.post(`${API_BASE}/providers/test`, {
                provider,
                api_key: apiKey,
                base_url: baseUrl
            });
            setTestResult(res.data);
            if (res.data.success) {
                handleFetchModels(provider, apiKey, baseUrl);
            }
        } catch (e) {
            setTestResult({ success: false, message: 'Server error' });
        } finally {
            setIsTesting(false);
        }
    };

    const API_BASE = 'https://multi-agent-ai-ppko.onrender.com/api';
    
    const toggleAgentStatus = async (agent: any) => {
        try {
            await axios.put(`${API_BASE}/agents/${agent.id}`, {
                is_active: !agent.is_active
            });
            fetchAgents();
        } catch (e) {
            console.error(e);
        }
    };
    
    const [editingAgentId, setEditingAgentId] = useState<number | null>(null);

    const handleAddAgent = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const capabilities = capabilitiesStr.split(',').map(c => c.trim()).filter(c => c.length > 0);
            
            if (editingAgentId) {
                // Properly update the agent without destroying its API key
                await axios.put(`${API_BASE}/agents/${editingAgentId}`, {
                    name, provider, model, capabilities, base_url: baseUrl, 
                    ...(apiKey ? { api_key: apiKey } : {}) // Only send API key if user typed a new one
                });
            } else {
                await axios.post(`${API_BASE}/agents`, {
                    name, provider, model, capabilities, api_key: apiKey, base_url: baseUrl, is_active: true
                });
            }
            setShowModal(false);
            setEditingAgentId(null);
            fetchAgents();
        } catch (e) {
            console.error(e);
            alert("Error saving agent");
        }
    };

    const handleDeleteAgent = async (agentId: number) => {
        if (!confirm("Are you sure you want to PERMANENTLY delete this agent? This will completely wipe its execution history and analytics.")) return;
        try {
            await axios.delete(`${API_BASE}/agents/${agentId}`);
            fetchAgents();
        } catch (e) {
            console.error(e);
            alert("Error deleting agent.");
        }
    };

    const handleEditClick = (agent: any) => {
        setEditingAgentId(agent.id);
        setName(agent.name);
        setProvider(agent.provider);
        setModel(agent.model);
        setCapabilitiesStr(agent.capabilities.join(', '));
        setApiKey(''); 
        setBaseUrl(''); 
        setShowModal(true);
    };

    return (
        <div className="max-w-6xl mx-auto h-full pb-10 relative">
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-3xl font-bold">Agent Management</h1>
                <button 
                    onClick={() => setShowModal(true)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                    + Add Agent
                </button>
            </div>
            
            {showModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto">
                    <div className="bg-gray-900 border border-gray-700 p-8 rounded-xl w-full max-w-2xl shadow-2xl relative my-8">
                        <button onClick={() => setShowModal(false)} className="absolute top-4 right-4 text-gray-400 hover:text-white">
                            <X className="w-5 h-5" />
                        </button>
                        <h2 className="text-2xl font-bold mb-6 text-white">Add New AI Agent</h2>
                        <form onSubmit={handleAddAgent} className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Agent Name</label>
                                    <input required value={name} onChange={e => setName(e.target.value)} type="text" placeholder="e.g. Advanced Coder" className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-white outline-none focus:border-blue-500" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Provider</label>
                                    <select value={provider} onChange={e => setProvider(e.target.value)} className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-white outline-none focus:border-blue-500">
                                        {providersInfo.map((p: any) => (
                                            <option key={p.id} value={p.name}>{p.name}</option>
                                        ))}
                                        {providersInfo.length === 0 && <option value="Google Gemini">Google Gemini</option>}
                                    </select>
                                </div>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {selectedProviderConfig?.requires_api_key && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-1">API Key</label>
                                        <input value={apiKey} onChange={e => setApiKey(e.target.value)} type="password" placeholder="••••••••••••••••" className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-white outline-none focus:border-blue-500" />
                                    </div>
                                )}
                                {selectedProviderConfig?.requires_base_url && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-1">Base URL</label>
                                        <input value={baseUrl} onChange={e => setBaseUrl(e.target.value)} type="text" placeholder={selectedProviderConfig.default_base_url || "e.g. https://api.example.com/v1"} className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-white outline-none focus:border-blue-500" />
                                    </div>
                                )}
                            </div>
                            
                            <div className="flex gap-4 items-end bg-gray-800/50 p-4 rounded-lg border border-gray-700/50">
                                <button type="button" onClick={handleTestConnection} disabled={isTesting} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium transition-colors flex items-center gap-2 text-sm">
                                    {isTesting ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                                    Test Connection & Discover Models
                                </button>
                                {testResult && (
                                    <div className={`flex items-center gap-2 text-sm ${testResult.success ? 'text-green-400' : 'text-red-400'}`}>
                                        {testResult.success ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                                        {testResult.message}
                                    </div>
                                )}
                            </div>
                            
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1 flex items-center gap-2">
                                    Model Version
                                    {isFetchingModels && <Loader2 className="w-3 h-3 animate-spin text-blue-400" />}
                                </label>
                                <div className="flex flex-col gap-2">
                                    {modelsList.length > 0 ? (
                                        <select value={model} onChange={e => setModel(e.target.value)} className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-white outline-none focus:border-blue-500">
                                            {modelsList.map(m => <option key={m} value={m}>{m}</option>)}
                                        </select>
                                    ) : (
                                        <>
                                            {testResult?.success === false && <p className="text-xs text-red-400">Unable to automatically retrieve models. You can enter a model manually.</p>}
                                            <input required value={model} onChange={e => setModel(e.target.value)} type="text" placeholder="e.g. gpt-4o or enter manually" className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-white outline-none focus:border-blue-500" />
                                        </>
                                    )}
                                </div>
                            </div>
                            
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Capabilities (comma separated)</label>
                                <input required value={capabilitiesStr} onChange={e => setCapabilitiesStr(e.target.value)} type="text" placeholder="e.g. coding, debugging, data_analysis" className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-white outline-none focus:border-blue-500" />
                            </div>
                            
                            <div className="pt-4 flex justify-end gap-3 border-t border-gray-800 mt-6">
                                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 rounded-lg border border-gray-700 text-gray-300 hover:bg-gray-800 transition-colors">Cancel</button>
                                <button type="submit" className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors">Create Agent</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            <div className="space-y-4">
                {agents.map((agent: any) => (
                    <div key={agent.id} className="bg-gray-900 border border-gray-800 rounded-xl p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                        <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                                <h3 className="text-xl font-semibold text-gray-100">{agent.name}</h3>
                                <span className={`px-2 py-1 rounded text-xs font-medium ${agent.is_active ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                                    {agent.is_active ? 'Active' : 'Disabled'}
                                </span>
                            </div>
                            <div className="text-sm text-gray-400 mb-3">
                                <span className="mr-4"><strong>Provider:</strong> {agent.provider}</span>
                                <span><strong>Model:</strong> {agent.model}</span>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {agent.capabilities.map((cap: string, i: number) => (
                                    <span key={i} className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-300 border border-gray-700">
                                        {cap}
                                    </span>
                                ))}
                            </div>
                        </div>
                        
                        <div className="flex items-center gap-2 w-full md:w-auto">
                            <button 
                                onClick={() => handleEditClick(agent)}
                                className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg transition-colors border border-gray-700"
                            >
                                <Edit2 className="w-4 h-4" />
                                <span>Edit</span>
                            </button>
                            <button 
                                onClick={() => handleDeleteAgent(agent.id)}
                                className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-gray-800 hover:bg-red-900/50 text-gray-200 hover:text-red-400 rounded-lg transition-colors border border-gray-700 hover:border-red-500/50"
                                title="Delete Agent"
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                            <button 
                                onClick={() => toggleAgentStatus(agent)}
                                className={`flex items-center justify-center p-2 rounded-lg transition-colors border ${agent.is_active ? 'border-red-500/30 text-red-400 hover:bg-red-500/10' : 'border-green-500/30 text-green-400 hover:bg-green-500/10'}`}
                                title={agent.is_active ? 'Disable Agent' : 'Enable Agent'}
                            >
                                <Power className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                ))}

                
                {agents.length === 0 && (
                    <div className="text-center text-gray-500 py-10 bg-gray-900 border border-gray-800 rounded-xl">
                        No agents registered.
                    </div>
                )}
            </div>
        </div>
    );
};

export default AgentManagement;
