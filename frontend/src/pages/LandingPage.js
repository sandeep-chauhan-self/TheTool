import React from 'react';
import { useNavigate } from 'react-router-dom';

function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen mesh-bg font-sans selection:bg-primary-200 selection:text-primary-900 overflow-x-hidden relative">
      {/* Global Mesh Background */}
      <div className="absolute inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-primary-300/10 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-accent-300/10 rounded-full blur-[120px]"></div>
      </div>

      <div className="relative z-10 font-sans">
        
        {/* 
          ======================================================================
          HERO SECTION
          ======================================================================
        */}
        <section className="relative pt-24 pb-20 lg:pt-36 lg:pb-32">
          <div className="max-w-7xl mx-auto px-6 text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/60 backdrop-blur-md border border-white/50 shadow-sm mb-10 animate-fade-in-up">
              <span className="w-2 h-2 rounded-full bg-success-500 animate-pulse"></span>
              <span className="text-[10px] font-bold tracking-[0.2em] text-slate-500 uppercase">System Active • High-Conviction Only</span>
            </div>
            
            <h1 className="text-6xl lg:text-8xl font-black text-slate-900 tracking-tighter mb-8 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
              Trading Efficiency.<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 via-primary-500 to-accent-500">
                Stripped of Bias.
              </span>
            </h1>
            
            <p className="text-xl text-slate-500 max-w-2xl mx-auto mb-12 animate-fade-in-up leading-relaxed" style={{ animationDelay: '200ms' }}>
              TheTool automates technical analysis by aggregating momentum, trend, and volume indicators into high-conviction mandates. Built for traders who value data over noise.
            </p>
            
            <div className="flex flex-col sm:flex-row justify-center items-center gap-6 animate-fade-in-up" style={{ animationDelay: '300ms' }}>
              <button 
                onClick={() => navigate('/dashboard')}
                className="px-10 py-5 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-[22px] shadow-2xl shadow-slate-900/30 transition-all hover:scale-105 active:scale-95 flex items-center gap-3 group"
              >
                Go to Dashboard
                <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
              </button>
              <a 
                href="#roadmap" 
                className="px-10 py-5 bg-white/40 hover:bg-white/60 backdrop-blur-md text-slate-700 font-bold rounded-[22px] border border-white/60 shadow-sm transition-all hover:shadow-md"
              >
                The Roadmap
              </a>
            </div>
          </div>
        </section>

        {/* 
          ======================================================================
          FEATURES GRID (CLEAN LIGHT DESIGN)
          ======================================================================
        */}
        <section className="py-24">
          <div className="max-w-7xl mx-auto px-6">
            <div className="grid md:grid-cols-3 gap-8">
              {[
                {
                  title: "Algorithmic Speed",
                  desc: "Analyze thousands of NSE symbols simultaneously. The engine handles the math; you handle the strategy.",
                  icon: <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>,
                  color: "primary"
                },
                {
                  title: "Technical Purity",
                  desc: "Normalized scores from MACD, ADX, and RSI, weighted by real-time market dynamics. Zero emotional interference.",
                  icon: <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>,
                  color: "accent"
                },
                {
                  title: "Smart Filtering",
                  desc: "Advanced screening to isolate high-conviction signals while discarding high-noise market behavior.",
                  icon: <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>,
                  color: "success"
                }
              ].map((item, id) => (
                <div key={id} className="p-10 rounded-[2.5rem] bg-white/40 backdrop-blur-sm border border-white hover:bg-white/60 transition-all hover:shadow-xl hover:-translate-y-1 group">
                  <div className={`w-14 h-14 rounded-2xl bg-${item.color}-50 text-${item.color}-500 flex items-center justify-center mb-8 border border-${item.color}-100 shadow-sm group-hover:scale-110 transition-transform`}>
                    {item.icon}
                  </div>
                  <h3 className="text-2xl font-bold text-slate-900 mb-4">{item.title}</h3>
                  <p className="text-slate-500 leading-relaxed text-sm">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 
          ======================================================================
          ARCHITECTURE ROADMAP (LIGHT MODE FLOW)
          ======================================================================
        */}
        <section id="roadmap" className="py-32 relative">
          <div className="max-w-7xl mx-auto px-6 relative z-10">
            <div className="text-center mb-24">
              <h2 className="text-4xl lg:text-5xl font-black text-slate-900 mb-6 tracking-tight">Technical Roadmap</h2>
              <p className="text-lg text-slate-500 max-w-2xl mx-auto leading-relaxed">
                Beyond static benchmarks. We are implementing agentic feedback loops that evolve with the market.
              </p>
            </div>

            {/* Light Mode Flowchart Diagram UI */}
            <div className="relative p-1 px-1 lg:p-12 rounded-[3rem] bg-white/20 backdrop-blur-md border border-white shadow-2xl shadow-primary-500/5">
              
              <div className="grid lg:grid-cols-3 gap-12 relative z-10 p-8">
                
                {/* Column 1: Ingestion */}
                <div className="space-y-6">
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-10 pl-2">Ingestion Layer</div>
                  
                  <div className="p-8 rounded-3xl bg-white border border-slate-100 shadow-sm relative group hover:shadow-lg transition-all">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-100 transition-opacity">
                      <div className="w-2 h-2 rounded-full bg-success-500 animate-pulse"></div>
                    </div>
                    <h4 className="font-bold text-slate-900 mb-2">NSE Data Feed</h4>
                    <p className="text-xs text-slate-500 leading-relaxed">Real-time OHLCV market streaming via high-throughput webhooks.</p>
                  </div>

                  <div className="p-8 rounded-3xl bg-white/40 border-2 border-dashed border-primary-200 shadow-sm relative group grayscale hover:grayscale-0 transition-all">
                     <div className="absolute top-4 right-4 text-[9px] font-black text-primary-500/40 uppercase tracking-tighter">Phase 4</div>
                     <h4 className="font-bold text-slate-900/60 mb-2">Sentiment Engine</h4>
                     <p className="text-xs text-slate-400 leading-relaxed">Multi-modal news and social aggregation for context augmentation.</p>
                  </div>
                </div>

                {/* Column 2: Central Processing */}
                <div className="space-y-6 flex flex-col justify-center">
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-10 pl-2 text-center">Processing Engine</div>
                  
                  <div className="p-10 rounded-[3rem] bg-gradient-to-br from-white to-slate-50 border border-primary-100 relative shadow-xl shadow-primary-500/10 group overflow-hidden">
                    <div className="absolute inset-0 bg-primary-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <div className="relative z-10">
                      <div className="w-12 h-12 bg-primary-100 text-primary-600 rounded-2xl flex items-center justify-center mb-6 shadow-inner">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
                      </div>
                      <h3 className="text-xl font-black text-slate-900 mb-4">Agentic AI Core</h3>
                      <p className="text-xs text-slate-500 leading-relaxed uppercase font-bold tracking-tight mb-4">Continuous Feedback Loop</p>
                      <p className="text-xs text-slate-500 leading-relaxed">
                        LLM-driven agents that dynamically rewrite sub-indicator weights based on prevailing market regimes (Trend vs. Choppy vs. Euphoria).
                      </p>
                    </div>
                  </div>
                </div>

                {/* Column 3: Output */}
                <div className="space-y-6">
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-10 pl-2">Mandate Output</div>
                  
                  <div className="p-8 rounded-3xl bg-white border border-slate-100 shadow-sm hover:shadow-glow-success transition-all duration-500 group">
                    <div className="flex items-center gap-3 mb-4">
                       <div className="w-2 h-2 rounded-full bg-success-500 shadow-glow-success group-hover:scale-150 transition-transform"></div>
                       <span className="text-[10px] font-black uppercase text-slate-700">Precision Signals</span>
                    </div>
                    <p className="text-xs text-slate-500 leading-relaxed">Single actionable mandates (BUY/SELL/HOLD) with confidence intervals and profit/stop-loss zones.</p>
                  </div>
                </div>
              </div>

              {/* Decorative Glow Dots */}
              <div className="absolute top-1/2 left-1/4 w-32 h-32 bg-primary-200/20 rounded-full blur-2xl pointer-events-none"></div>
              <div className="absolute bottom-1/4 right-1/3 w-32 h-32 bg-accent-200/20 rounded-full blur-2xl pointer-events-none"></div>
            </div>
          </div>
        </section>

        {/* 
          ======================================================================
          CREATOR & CREDENTIALS (REFINED GLASS HUB)
          ======================================================================
        */}
        <section className="py-32 relative overflow-hidden">
          <div className="max-w-5xl mx-auto px-6 relative z-10">
            
            <div className="bg-white/60 backdrop-blur-md rounded-[4rem] border border-white p-12 lg:p-20 shadow-2xl relative overflow-hidden group">
              {/* Internal Accent Glow */}
              <div className="absolute top-[-50%] left-[-20%] w-[60%] h-[120%] bg-primary-50 rounded-full blur-[60px] pointer-events-none opacity-40"></div>
              <div className="absolute bottom-[-50%] right-[-20%] w-[60%] h-[120%] bg-accent-50 rounded-full blur-[60px] pointer-events-none opacity-40"></div>

              <div className="flex flex-col items-center text-center relative z-10">
                <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-primary-500 to-accent-600 flex items-center justify-center text-white text-3xl font-black shadow-2xl mb-10 rotate-3 group-hover:rotate-0 transition-transform">
                  SC
                </div>
                
                <h2 className="text-4xl lg:text-5xl font-black text-slate-900 mb-8 tracking-tighter">Redefining Market Analytics.</h2>
                
                <p className="text-lg text-slate-500 max-w-2xl leading-relaxed mb-12">
                  My name is <b>Sandeep Chauhan</b>. I build high-concurrency architectures that solve real-world SaaS complexities. 
                  <br /><br />
                  "TheTool" represents my vision for a zero-emotion trading future. Whether you want to discuss algorithmic strategies, explore high-frequency pipelines, <b>or offer me a lucrative contract to build your next billion-dollar engine—I’m listening.</b>
                </p>

                <div className="flex flex-wrap justify-center gap-4 mb-20 w-full">
                  <a href="https://wa.me/919625401736" target="_blank" rel="noreferrer" className="flex-1 min-w-[160px] px-8 py-4 bg-[#25D366] text-white font-bold rounded-2xl shadow-lg shadow-success-500/20 hover:-translate-y-1 transition-all text-center">WhatsApp</a>
                  <a href="https://www.linkedin.com/in/sandeep-chauhan-243012181/" target="_blank" rel="noreferrer" className="flex-1 min-w-[160px] px-8 py-4 bg-[#0A66C2] text-white font-bold rounded-2xl shadow-lg shadow-primary-500/20 hover:-translate-y-1 transition-all text-center">LinkedIn</a>
                  <a href="tel:+919625401736" className="flex-1 min-w-[160px] px-8 py-4 bg-slate-900 text-white font-bold rounded-2xl shadow-lg shadow-slate-900/20 hover:-translate-y-1 transition-all text-center">Call Me</a>
                </div>

                <div className="grid sm:grid-cols-2 gap-8 text-left w-full mt-10">
                  {/* Project Card 1 */}
                  <div className="p-1 w-full bg-gradient-to-br from-primary-200 to-primary-100 rounded-[2.5rem]">
                    <div className="bg-white rounded-[2.4rem] p-8 h-full shadow-sm">
                      <div className="flex justify-between items-start mb-6">
                        <div className="w-10 h-10 bg-primary-50 rounded-xl flex items-center justify-center text-primary-500 border border-primary-100 italic font-black text-lg">P</div>
                        <a href="https://github.com/sandeep-chauhan-self/ThePromptTool" target="_blank" rel="noreferrer" className="text-slate-400 hover:text-slate-900 transition-colors">
                          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.041-1.416-4.041-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                        </a>
                      </div>
                      <h4 className="text-xl font-black text-slate-900 mb-2">ThePromptTool</h4>
                      <p className="text-sm text-slate-500 leading-relaxed mb-6">An intelligent prompt engineering hub that validates, grades, and enhances your prompts using a complex 5-layer rule system. It leverages Claude to transform basic ideas into high-performance AI instructions.</p>
                      <a href="https://the-prompt-tool.vercel.app/" target="_blank" rel="noreferrer" className="inline-flex items-center text-xs font-black uppercase text-primary-600 gap-2 border-b-2 border-primary-500 pb-1 hover:text-primary-800 transition-colors">
                        Launch Demo
                      </a>
                    </div>
                  </div>

                   {/* Project Card 2 */}
                   <div className="p-1 w-full bg-gradient-to-br from-accent-200 to-accent-100 rounded-[2.5rem]">
                    <div className="bg-white rounded-[2.4rem] p-8 h-full shadow-sm">
                      <div className="flex justify-between items-start mb-6">
                        <div className="w-10 h-10 bg-accent-50 rounded-xl flex items-center justify-center text-accent-500 border border-accent-100 italic font-black text-lg">T</div>
                        <a href="https://github.com/sandeep-chauhan-self/TheTool" target="_blank" rel="noreferrer" className="text-slate-400 hover:text-slate-900 transition-colors">
                          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.041-1.416-4.041-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                        </a>
                      </div>
                      <h4 className="text-xl font-black text-slate-900 mb-2">TheTool Dashboard</h4>
                      <p className="text-sm text-slate-500 leading-relaxed mb-6">A robust stock analysis and monitoring infrastructure that processes real-time NSE data across large asset universes. It evaluates high-conviction mandates using advanced technical models to provide traders with singular, data-driven edge.</p>
                      <a href="https://the-tool-theta.vercel.app/" target="_blank" rel="noreferrer" className="inline-flex items-center text-xs font-black uppercase text-accent-600 gap-2 border-b-2 border-accent-500 pb-1 hover:text-accent-800 transition-colors">
                        Live Server
                      </a>
                    </div>
                  </div>

                </div>
              </div>
            </div>

          </div>
        </section>

      </div>
    </div>
  );
}

export default LandingPage;
