"use client";

import { useState } from "react";
import { Bot, Send, User, Sparkles, Paperclip, Mic } from "lucide-react";
import { clsx } from "clsx";

export default function AssistantPage() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi there! I'm TaxEase AI. How can I help you optimize your taxes today?" }
  ]);
  const [input, setInput] = useState("");

  const handleSend = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim()) return;
    
    setMessages([...messages, { role: "user", content: input }]);
    const currentInput = input;
    setInput("");
    
    // Simulate thinking
    setTimeout(() => {
      setMessages(prev => [
        ...prev, 
        { 
          role: "assistant", 
          content: `Based on the latest tax slabs, regarding "${currentInput}", I recommend maximizing your 80C first. Your Form 16 shows you have maxed out 80C, so consider 80CCD(1B) for NPS which allows an extra ₹50,000 deduction. Would you like me to map how much tax that will save you?` 
        }
      ]);
    }, 1000);
  };

  const handleSuggest = (text: string) => {
    setInput(text);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-4xl mx-auto bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center border-2 border-primary-dark">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-800">TaxEase AI Assistant</h2>
            <p className="text-xs text-slate-500">Trained on Indian Income Tax Act</p>
          </div>
        </div>
        <button className="text-slate-400 hover:text-slate-600">
          <Sparkles className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50">
        {messages.map((msg, i) => (
          <div 
            key={i} 
            className={clsx(
              "flex gap-4 max-w-[80%]",
              msg.role === "user" ? "ml-auto flex-row-reverse" : ""
            )}
          >
            <div className={clsx(
              "w-8 h-8 rounded-full flex shrink-0 items-center justify-center mt-1",
              msg.role === "assistant" ? "bg-primary text-white" : "bg-slate-800 text-white"
            )}>
              {msg.role === "assistant" ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
            </div>
            
            <div className={clsx(
              "p-4 rounded-2xl text-sm leading-relaxed",
              msg.role === "user" 
                ? "bg-slate-900 text-white rounded-tr-none shadow-sm" 
                : "bg-white text-slate-700 border border-slate-100 rounded-tl-none shadow-sm"
            )}>
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      <div className="p-4 bg-white border-t border-slate-100">
        {messages.length === 1 && (
          <div className="flex gap-2 mb-4 overflow-x-auto pb-2 scrollbar-none">
            <button 
              onClick={() => handleSuggest("How to save tax?")}
              className="px-4 py-2 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-full text-xs font-medium text-slate-600 whitespace-nowrap transition-smooth"
            >
              How to save tax?
            </button>
            <button 
              onClick={() => handleSuggest("Explain HRA deduction")}
              className="px-4 py-2 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-full text-xs font-medium text-slate-600 whitespace-nowrap transition-smooth"
            >
              Explain HRA deduction
            </button>
            <button 
              onClick={() => handleSuggest("What is the old vs new tax regime?")}
              className="px-4 py-2 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-full text-xs font-medium text-slate-600 whitespace-nowrap transition-smooth"
            >
              Old vs New Regime
            </button>
          </div>
        )}

        <form onSubmit={handleSend} className="relative flex items-end gap-2 bg-slate-50 border border-slate-200 rounded-2xl p-2 focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary transition-smooth">
          <button type="button" className="p-2 text-slate-400 hover:text-slate-600 transition-smooth">
            <Paperclip className="w-5 h-5" />
          </button>
          
          <textarea 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything about taxes..."
            className="w-full max-h-32 bg-transparent border-none focus:ring-0 resize-none py-2.5 text-sm text-slate-800 placeholder-slate-400 min-h-[44px] outline-none"
            rows={1}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
          />
          
          <div className="flex gap-1 pb-1 pr-1">
             <button type="button" className="p-2 text-slate-400 hover:text-slate-600 transition-smooth">
               <Mic className="w-5 h-5" />
             </button>
            <button 
              type="submit" 
              disabled={!input.trim()}
              className="p-2 bg-primary hover:bg-primary-dark disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-xl transition-smooth"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </form>
        <div className="text-center mt-3">
          <span className="text-[10px] text-slate-400">AI can make mistakes. Consider verifying critical tax information.</span>
        </div>
      </div>
    </div>
  );
}
