import React from 'react';
import { CheckCircle2, Circle, AlertCircle, RefreshCw, ChevronRight } from 'lucide-react';

const ExecutionTrace = ({ trace }: { trace: any[] }) => {
    return (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-6">Execution Pipeline</h3>
            <div className="relative pl-6 border-l border-gray-800 space-y-6">
                {trace.map((step, index) => {
                    const isSuccess = step.status === 'completed';
                    const isFailed = step.status === 'failed';
                    
                    return (
                        <div key={index} className="relative">
                            {/* Timeline dot */}
                            <div className={`absolute -left-[33px] p-1 rounded-full bg-gray-900 ${
                                isSuccess ? 'text-green-500' : isFailed ? 'text-red-500' : 'text-blue-500'
                            }`}>
                                {isSuccess ? <CheckCircle2 className="w-5 h-5" /> : 
                                 isFailed ? <AlertCircle className="w-5 h-5" /> : 
                                 <RefreshCw className="w-5 h-5 animate-spin" />}
                            </div>
                            
                            <div className="bg-gray-800/50 rounded-lg p-4">
                                <h4 className="font-medium text-gray-200">{step.step}</h4>
                                
                                {step.result && step.step === 'Analysis' && (
                                    <div className="mt-2 text-sm text-gray-400 font-mono bg-gray-950 p-2 rounded border border-gray-800">
                                        Type: {step.result.task_type} | Caps: {step.result.required_capabilities?.join(', ')}
                                    </div>
                                )}
                                
                                {step.selected_agent && (
                                    <div className="mt-2 text-sm text-blue-400 flex items-center gap-1">
                                        <ChevronRight className="w-4 h-4"/> Selected: {step.selected_agent}
                                    </div>
                                )}
                                
                                {step.evaluation && (
                                    <div className="mt-2 text-sm flex gap-4 text-gray-400">
                                        <span className={step.evaluation.quality_score >= 0.75 ? "text-green-400" : "text-amber-400"}>
                                            Score: {step.evaluation.quality_score}
                                        </span>
                                        <span>Retry: {step.evaluation.needs_retry ? "Yes" : "No"}</span>
                                    </div>
                                )}
                                
                                {step.latency && (
                                    <div className="mt-2 text-xs text-gray-500">
                                        Latency: {step.latency.toFixed(2)}s
                                    </div>
                                )}
                                
                                {step.error && (
                                    <div className="mt-2 text-sm text-red-400">
                                        Error: {step.error}
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default ExecutionTrace;
