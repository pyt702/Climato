import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import WeatherWidget from './components/WeatherWidget';

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am Climato. How can I help you with the weather today?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const sessionRef = useRef(crypto.randomUUID());

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: userMessage.content,
          session_id: sessionRef.current
        })
      });
      
      const data = await response.json();
      
      setMessages((prev) => [
        ...prev,
        { 
          role: 'assistant', 
          content: data.answer || "Sorry, I couldn't understand that.",
          data: data.data // Add structured data
        }
      ]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: "Sorry, the backend server is unreachable. Please make sure FastAPI is running on port 8000." }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-white text-slate-800 font-sans selection:bg-blue-500/30">
      
      {/* Header */}
      <header className="px-6 py-4 bg-white/90 backdrop-blur-md sticky top-0 z-20 flex items-center border-b border-slate-100">
        <h1 className="text-[17px] font-medium tracking-wide">Climato</h1>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-8 scroll-smooth custom-scrollbar">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-4 duration-300`}
            >
              <div className="flex flex-col gap-2 w-full">
                {msg.content && (
                  <div
                    className={`max-w-[85%] sm:max-w-[75%] px-5 py-3.5 text-[15px] leading-relaxed rounded-2xl ${
                      msg.role === 'user'
                        ? 'bg-slate-100 text-slate-900 border border-slate-200 rounded-br-sm self-end'
                        : 'bg-transparent text-slate-800 self-start'
                    }`}
                  >
                    <div className="flex flex-col gap-2 [&>p]:m-0 [&>ul]:list-disc [&>ul]:pl-5 [&>ul]:m-0 [&>ol]:list-decimal [&>ol]:pl-5 [&>ol]:m-0 [&>table]:w-full [&>table]:border-collapse [&>table]:mt-2 [&_th]:border [&_th]:border-slate-300 [&_th]:px-3 [&_th]:py-1 [&_th]:bg-slate-100/50 [&_td]:border [&_td]:border-slate-300 [&_td]:px-3 [&_td]:py-1 [&_strong]:font-semibold">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}
                {msg.data && msg.data.length > 0 && (
                  <div className="w-full self-start">
                    <WeatherWidget data={msg.data} />
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start animate-in fade-in duration-300">
              <div className="px-5 py-4 flex gap-1.5 items-center">
                <div className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce"></div>
                <div className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="p-4 bg-gradient-to-t from-white via-white to-transparent pt-10 pb-6 relative z-10">
        <div className="max-w-3xl mx-auto">
          <form onSubmit={handleSend} className="relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything..."
              className="w-full bg-white border border-slate-200 text-slate-900 placeholder-slate-400 rounded-2xl py-4 pl-5 pr-14 focus:outline-none focus:border-slate-300 transition-colors shadow-sm"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-xl bg-blue-600 text-white hover:bg-blue-700 active:scale-95 transition-all disabled:opacity-50 disabled:hover:bg-blue-600 flex items-center justify-center h-10 w-10 cursor-pointer"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
              </svg>
            </button>
          </form>
          <div className="text-center mt-3">
             <p className="text-[11px] text-slate-500">Climato can make mistakes. Consider verifying important information.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
