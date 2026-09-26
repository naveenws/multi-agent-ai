import React, { useState } from 'react';
import { Send, FileText, Loader2, Bot, AlertTriangle } from 'lucide-react';
import { submitTask } from '../services/api';
import ExecutionTrace from './ExecutionTrace';

const TaskInput = () => {
    const [prompt, setPrompt] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!prompt.trim()) return;

        setLoading(true);
        setError('');
        setResult(null);

        try {
            const data = await submitTask(prompt);
            setResult(data);
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto flex flex-col pb-10">
            <div className="mb-6">
                <h1 className="text-3xl font-bold mb-2">New Task</h1>
                <p className="text-gray-400">Describe your task and the orchestrator will select the best agents to solve it.</p>
            </div>

            <form onSubmit={handleSubmit} className="mb-8">
                <div className="relative border border-gray-700 bg-gray-900 rounded-xl overflow-hidden focus-within:ring-2 focus-within:ring-blue-500 transition-all">
                    <textarea 
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        placeholder="E.g., Analyze this data and summarize the trends..."
                        className="w-full bg-transparent p-4 text-gray-100 placeholder-gray-500 outline-none resize-none min-h-[120px]"
                    />
                    <div className="flex justify-between items-center p-3 border-t border-gray-800 bg-gray-800/50">
                        <button type="button" className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2">
                            <FileText className="w-4 h-4" />
                            <span className="text-sm">Attach File</span>
                        </button>
                        <button 
                            type="submit" 
                            disabled={loading || !prompt.trim()}
                            className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors"
                        >
                            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                            Execute
                        </button>
                    </div>
                </div>
            </form>

            {error && (
                <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-4 rounded-xl mb-6 flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 mt-0.5 shrink-0" />
                    <p>{error}</p>
                </div>
            )}

            {result && (
                <div className="flex-1 flex flex-col gap-6 pb-10">
                    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-xl">
                        <div className="flex items-center gap-2 mb-4 border-b border-gray-800 pb-4">
                            <Bot className="w-5 h-5 text-blue-400" />
                            <h2 className="text-xl font-semibold">Final Synthesis</h2>
                        </div>
                        <div className="prose prose-invert max-w-none text-gray-300 whitespace-pre-wrap">
                            {result.final_answer}
                        </div>
                    </div>
                    
                    <ExecutionTrace trace={result.trace} />
                </div>
            )}
        </div>
    );
};

export default TaskInput;
