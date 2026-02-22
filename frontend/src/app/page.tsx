'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { 
  Search, Building, DollarSign, Shield, Users, Globe, 
  BarChart3, Zap, Database, TrendingUp, CheckCircle, 
  ArrowRight, Sparkles, ExternalLink, FileText, Clock
} from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Animated Background Elements with Poisson Dot Pattern */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Large gradient orbs */}
        <div className="absolute -inset-10 opacity-50">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
          <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse animation-delay-2000"></div>
          <div className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse animation-delay-4000"></div>
        </div>
        
        {/* Poisson Distribution Inspired Dot Pattern */}
        <div className="absolute inset-0 pointer-events-none">
          {/* Top section dots */}
          <div className="absolute top-20 left-10 w-3 h-3 rounded-full bg-purple-500/30 blur-sm animate-pulse"></div>
          <div className="absolute top-32 left-24 w-2 h-2 rounded-full bg-violet-400/40 blur-sm"></div>
          <div className="absolute top-40 left-16 w-2.5 h-2.5 rounded-full bg-purple-600/35 blur-sm animate-pulse" style={{animationDelay: '1s'}}></div>
          <div className="absolute top-28 left-36 w-1.5 h-1.5 rounded-full bg-violet-500/45 blur-sm"></div>
          
          {/* Right section dots */}
          <div className="absolute top-24 right-20 w-3 h-3 rounded-full bg-purple-400/35 blur-sm animate-pulse" style={{animationDelay: '2s'}}></div>
          <div className="absolute top-44 right-32 w-2 h-2 rounded-full bg-violet-600/30 blur-sm"></div>
          <div className="absolute top-36 right-16 w-2.5 h-2.5 rounded-full bg-purple-500/40 blur-sm animate-pulse" style={{animationDelay: '1.5s'}}></div>
          <div className="absolute top-52 right-28 w-1.5 h-1.5 rounded-full bg-violet-400/35 blur-sm"></div>
          
          {/* Middle section dots */}
          <div className="absolute top-1/2 left-1/4 w-3 h-3 rounded-full bg-purple-600/30 blur-sm animate-pulse" style={{animationDelay: '0.5s'}}></div>
          <div className="absolute top-1/2 left-1/3 w-2 h-2 rounded-full bg-violet-500/40 blur-sm"></div>
          <div className="absolute top-1/2 right-1/3 w-2.5 h-2.5 rounded-full bg-purple-400/35 blur-sm animate-pulse" style={{animationDelay: '2.5s'}}></div>
          <div className="absolute top-1/2 right-1/4 w-2 h-2 rounded-full bg-violet-600/45 blur-sm"></div>
          
          {/* Bottom section dots */}
          <div className="absolute bottom-32 left-20 w-3 h-3 rounded-full bg-purple-500/35 blur-sm animate-pulse" style={{animationDelay: '1.8s'}}></div>
          <div className="absolute bottom-40 left-32 w-2 h-2 rounded-full bg-violet-400/40 blur-sm"></div>
          <div className="absolute bottom-28 right-24 w-2.5 h-2.5 rounded-full bg-purple-600/30 blur-sm animate-pulse" style={{animationDelay: '2.2s'}}></div>
          <div className="absolute bottom-44 right-36 w-1.5 h-1.5 rounded-full bg-violet-500/35 blur-sm"></div>
        </div>
      </div>

      <div className="relative z-10">
        {/* Navigation Header */}
        <motion.nav 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="backdrop-blur-xl bg-white/5 border-b border-white/10 sticky top-0 z-50"
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex justify-between items-center">
              <Link href="/" className="flex items-center gap-3 hover:opacity-90 transition-opacity">
                <motion.div
                  whileHover={{ scale: 1.1 }}
                  transition={{ duration: 0.2 }}
                >
                  <Image 
                    src="/images/poissonai_logo.png"
                    alt="POISSON AI Logo"
                    width={45}
                    height={45}
                    className="w-[35px] h-[35px] md:w-[40px] md:h-[40px] lg:w-[45px] lg:h-[45px] rounded-lg shadow-lg shadow-purple-500/30"
                    priority
                  />
                </motion.div>
                <div>
                  <h1 className="text-lg md:text-xl font-bold text-white">POISSON AI®</h1>
                  <p className="text-xs text-gray-300 hidden sm:block">Vetting Intelligence</p>
                </div>
              </Link>
              <Link href="/app">
                <motion.button
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-4 md:px-6 py-2 md:py-3 bg-gradient-to-r from-purple-600 to-violet-600 text-white rounded-xl hover:from-purple-700 hover:to-violet-700 font-semibold shadow-lg transition-all duration-300 flex items-center gap-2"
                >
                  <span className="hidden sm:inline">DEMO NOW</span>
                  <span className="sm:hidden">DEMO</span>
                  <ArrowRight className="w-4 h-4" />
                </motion.button>
              </Link>
            </div>
          </div>
        </motion.nav>

        {/* Hero Section - Reduced padding for more compact feel */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center"
          >
            {/* Floating decorative icons - Application relevant */}
            
            {/* Top Left - Shield (Security/Compliance) */}
            <motion.div
              animate={{ 
                y: [0, -10, 0],
                rotate: [0, 5, 0]
              }}
              transition={{ 
                duration: 4,
                repeat: Infinity,
                ease: "easeInOut"
              }}
              className="absolute top-20 left-20 w-16 h-16 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center shadow-2xl hidden lg:flex"
            >
              <Shield className="w-8 h-8 text-white" />
            </motion.div>
            
            {/* Top Right - Sparkles (AI Intelligence) */}
            <motion.div
              animate={{ 
                y: [0, 10, 0],
                rotate: [0, -5, 0]
              }}
              transition={{ 
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 1
              }}
              className="absolute top-32 right-32 w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-2xl hidden lg:flex"
            >
              <Sparkles className="w-6 h-6 text-white" />
            </motion.div>

            {/* Middle Left - FileText (Contracts/Documents) */}
            <motion.div
              animate={{ 
                y: [0, -8, 0],
                rotate: [0, 3, 0]
              }}
              transition={{ 
                duration: 3.5,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 0.5
              }}
              className="absolute top-1/2 left-12 w-14 h-14 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl flex items-center justify-center shadow-2xl hidden xl:flex"
            >
              <FileText className="w-7 h-7 text-white" />
            </motion.div>

            {/* Middle Right - TrendingUp (Analytics) */}
            <motion.div
              animate={{ 
                y: [0, 8, 0],
                rotate: [0, -3, 0]
              }}
              transition={{ 
                duration: 3.8,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 1.5
              }}
              className="absolute top-1/3 right-16 w-14 h-14 bg-gradient-to-r from-orange-500 to-amber-500 rounded-xl flex items-center justify-center shadow-2xl hidden xl:flex"
            >
              <TrendingUp className="w-7 h-7 text-white" />
            </motion.div>

            {/* Bottom Left - DollarSign (Financial Data) */}
            <motion.div
              animate={{ 
                y: [0, 12, 0],
                rotate: [0, 6, 0]
              }}
              transition={{ 
                duration: 4.2,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 2
              }}
              className="absolute bottom-32 left-24 w-12 h-12 bg-gradient-to-r from-green-500 to-teal-500 rounded-xl flex items-center justify-center shadow-2xl hidden lg:flex"
            >
              <DollarSign className="w-6 h-6 text-white" />
            </motion.div>

            {/* Bottom Right - Building (Government) */}
            <motion.div
              animate={{ 
                y: [0, -12, 0],
                rotate: [0, -4, 0]
              }}
              transition={{ 
                duration: 3.6,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 0.8
              }}
              className="absolute bottom-28 right-20 w-14 h-14 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center shadow-2xl hidden lg:flex"
            >
              <Building className="w-7 h-7 text-white" />
            </motion.div>

            {/* Upper Middle Left - Search (Discovery) */}
            <motion.div
              animate={{ 
                y: [0, -6, 0],
                rotate: [0, 4, 0]
              }}
              transition={{ 
                duration: 3.2,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 1.2
              }}
              className="absolute top-40 left-40 w-10 h-10 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg flex items-center justify-center shadow-2xl hidden xl:flex"
            >
              <Search className="w-5 h-5 text-white" />
            </motion.div>

            {/* Lower Middle Right - BarChart (Data Visualization) */}
            <motion.div
              animate={{ 
                y: [0, 9, 0],
                rotate: [0, -6, 0]
              }}
              transition={{ 
                duration: 4.5,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 2.5
              }}
              className="absolute bottom-40 right-36 w-11 h-11 bg-gradient-to-r from-pink-500 to-rose-500 rounded-lg flex items-center justify-center shadow-2xl hidden xl:flex"
            >
              <BarChart3 className="w-6 h-6 text-white" />
            </motion.div>

            {/* Main Hero Content - More compact padding */}
            <div className="backdrop-blur-xl bg-white/10 rounded-3xl p-8 md:p-10 border border-white/20 shadow-2xl max-w-5xl mx-auto">
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                className="flex flex-col items-center"
              >
                {/* Prominent Logo Display - Smaller for compactness */}
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.8, delay: 0.3 }}
                  className="relative mb-6 group"
                >
                  {/* Enhanced purple glow effect */}
                  <div className="absolute -inset-6 bg-gradient-to-r from-purple-600 via-violet-600 to-pink-600 rounded-full blur-3xl opacity-25 animate-pulse group-hover:opacity-35 transition-opacity"></div>
                  
                  {/* Logo with rounded corners and styling - Reduced size */}
                  <div className="relative z-10">
                    <Image 
                      src="/images/poissonai_logo.png"
                      alt="POISSON AI Logo"
                      width={250}
                      height={250}
                      priority
                      className="relative w-[160px] h-[160px] md:w-[200px] md:h-[200px] lg:w-[250px] lg:h-[250px] rounded-3xl shadow-2xl shadow-purple-500/50 border border-purple-400/20 backdrop-blur-sm"
                    />
                  </div>
                </motion.div>

                <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-3 text-center">
                  <span className="bg-gradient-to-r from-white via-purple-100 to-violet-100 bg-clip-text text-transparent">
                    Vetting Intelligence Search Hub
                  </span>
                </h1>
                
                <p className="text-lg md:text-xl text-purple-200 max-w-3xl mx-auto mb-4 leading-relaxed text-center">
                  Enterprise Government Transparency & Due Diligence Platform
                </p>

                <p className="text-base md:text-lg text-gray-300 max-w-3xl mx-auto mb-6 leading-relaxed">
                  Uncover hidden connections and insights across government transparency data. 
                  Search lobbying records, campaign finance, federal spending, and public contracts 
                  with AI-powered intelligence. Replace $10,000+/year tools with one unified platform.
                </p>

                {/* CTA Buttons */}
                <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-6">
                  <Link href="/app">
                    <motion.button
                      whileHover={{ scale: 1.05, y: -2 }}
                      whileTap={{ scale: 0.95 }}
                      className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 font-bold text-lg shadow-lg transition-all duration-300 flex items-center gap-2"
                    >
                      DEMO NOW
                      <ArrowRight className="w-5 h-5" />
                    </motion.button>
                  </Link>
                  <motion.button
                    whileHover={{ scale: 1.05, y: -2 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
                    className="px-8 py-4 backdrop-blur-sm bg-white/10 border border-white/20 text-white rounded-xl hover:bg-white/20 font-semibold text-lg transition-all duration-300"
                  >
                    Learn More
                  </motion.button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {[
                    { icon: Database, value: "15M+", label: "Government Records" },
                    { icon: Zap, value: "<2s", label: "Search Speed" },
                    { icon: TrendingUp, value: "$10K+", label: "Annual Savings" }
                  ].map((stat, index) => (
                    <motion.div
                      key={stat.label}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.4 + index * 0.1 }}
                      whileHover={{ scale: 1.05 }}
                      className="backdrop-blur-sm bg-white/5 rounded-xl p-6 border border-white/10"
                    >
                      <stat.icon className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                      <div className="text-3xl font-bold text-white">{stat.value}</div>
                      <div className="text-sm text-gray-300">{stat.label}</div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            </div>
          </motion.div>
        </section>

        {/* Live Data Ticker - Fills space with motion */}
        <section className="relative overflow-hidden py-6 bg-gradient-to-r from-purple-900/20 via-violet-900/20 to-purple-900/20 backdrop-blur-sm">
          <motion.div 
            animate={{ x: [-1000, 0] }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            className="flex gap-12 whitespace-nowrap"
          >
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex gap-12 items-center">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-gray-300 text-sm font-medium">15M+ Records Indexed</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" style={{animationDelay: '0.5s'}}></div>
                  <span className="text-gray-300 text-sm font-medium">Real-Time Data Feeds</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" style={{animationDelay: '1s'}}></div>
                  <span className="text-gray-300 text-sm font-medium">AI-Powered Analysis</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-pink-400 rounded-full animate-pulse" style={{animationDelay: '1.5s'}}></div>
                  <span className="text-gray-300 text-sm font-medium">99.9% Uptime</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" style={{animationDelay: '2s'}}></div>
                  <span className="text-gray-300 text-sm font-medium">SOC 2 Ready</span>
                </div>
              </div>
            ))}
          </motion.div>
        </section>

        {/* Data Sources Pills - Closer to hero */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="flex flex-wrap justify-center gap-3"
          >
            {[
              { icon: Globe, label: "Federal Lobbying (LDA)", color: "from-blue-500 to-blue-600" },
              { icon: Building, label: "NYC Contracts", color: "from-green-500 to-green-600" },
              { icon: DollarSign, label: "FEC Campaign Finance", color: "from-purple-500 to-purple-600" },
              { icon: Shield, label: "NY State Ethics", color: "from-orange-500 to-orange-600" },
              { icon: Users, label: "NYC Lobbying", color: "from-cyan-500 to-cyan-600" }
            ].map((item, index) => (
              <motion.div
                key={item.label}
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                whileHover={{ scale: 1.05, y: -2 }}
                className={`px-4 py-2 bg-gradient-to-r ${item.color} rounded-full text-white text-sm font-medium shadow-lg backdrop-blur-sm border border-white/20 flex items-center gap-2`}
              >
                <item.icon className="w-4 h-4" />
                {item.label}
              </motion.div>
            ))}
          </motion.div>
        </section>

        {/* Features Section - Tighter spacing */}
        <section id="features" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Enterprise-Grade Intelligence
            </h2>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              Powerful features designed for compliance teams, legal professionals, and investigative journalists
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: Globe,
                title: "Multi-Jurisdictional Analysis",
                description: "Search across federal, state, and local government databases simultaneously. Uncover connections that span multiple jurisdictions.",
                gradient: "from-blue-500 to-cyan-500"
              },
              {
                icon: TrendingUp,
                title: "Real-Time Correlation",
                description: "AI-powered entity resolution automatically identifies relationships between lobbying, contracts, and campaign finance.",
                gradient: "from-purple-500 to-pink-500"
              },
              {
                icon: BarChart3,
                title: "Advanced Visualizations",
                description: "Interactive charts, network diagrams, and timelines transform raw data into actionable insights.",
                gradient: "from-green-500 to-emerald-500"
              },
              {
                icon: Zap,
                title: "Sub-Second Search",
                description: "Lightning-fast full-text search across 15+ million government records with intelligent caching.",
                gradient: "from-orange-500 to-amber-500"
              },
              {
                icon: Shield,
                title: "Enterprise Security",
                description: "Role-based access control, audit logs, and SOC 2 compliance ready architecture.",
                gradient: "from-red-500 to-pink-500"
              },
              {
                icon: Database,
                title: "15+ Data Sources",
                description: "Senate LDA, FEC, CheckbookNYC, NYS Ethics, and more. Continuously updated with fresh data.",
                gradient: "from-indigo-500 to-purple-500"
              }
            ].map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ scale: 1.02, y: -4 }}
                className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-8 shadow-2xl"
              >
                <div className={`w-14 h-14 bg-gradient-to-r ${feature.gradient} rounded-xl flex items-center justify-center mb-6`}>
                  <feature.icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
                <p className="text-gray-300 leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Data Coverage Section */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="backdrop-blur-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-white/20 rounded-3xl p-12"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-12 text-center">
              Comprehensive Data Coverage
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[
                { label: "FEC Campaign Finance Records", value: "8M+", icon: DollarSign },
                { label: "NYC Contract Records", value: "10M+", icon: Building },
                { label: "Federal Lobbying Reports", value: "500K+", icon: Globe },
                { label: "NYC Lobbying Records", value: "100K+", icon: Users },
                { label: "NY State Ethics Records", value: "250K+", icon: Shield },
                { label: "Years of Historical Data", value: "15+", icon: Clock }
              ].map((stat, index) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, scale: 0.9 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ scale: 1.05 }}
                  className="backdrop-blur-sm bg-white/10 rounded-xl p-6 border border-white/10 text-center"
                >
                  <stat.icon className="w-8 h-8 text-blue-400 mx-auto mb-3" />
                  <div className="text-4xl font-bold text-white mb-2">{stat.value}</div>
                  <div className="text-sm text-gray-300">{stat.label}</div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </section>

        {/* Use Cases Section */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Built For Your Workflow
            </h2>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              Trusted by compliance teams, legal professionals, financial services, and investigative journalists
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {[
              {
                icon: Shield,
                title: "Compliance Teams",
                description: "Conduct comprehensive due diligence on vendors, partners, and third parties. Identify potential conflicts of interest and regulatory risks.",
                benefits: ["Third-party risk assessment", "Conflict of interest detection", "Regulatory compliance monitoring"]
              },
              {
                icon: FileText,
                title: "Legal Professionals",
                description: "Support litigation, M&A due diligence, and regulatory investigations with comprehensive government records research.",
                benefits: ["Discovery support", "M&A due diligence", "Regulatory defense"]
              },
              {
                icon: DollarSign,
                title: "Financial Services",
                description: "Enhanced customer due diligence (EDD) and know-your-customer (KYC) processes with government transparency data.",
                benefits: ["KYC/AML compliance", "PEP screening", "Reputation risk management"]
              },
              {
                icon: Search,
                title: "Investigative Journalists",
                description: "Uncover stories hidden in government data. Track money flows, identify relationships, and expose conflicts of interest.",
                benefits: ["Investigative research", "Data journalism", "Public accountability"]
              }
            ].map((useCase, index) => (
              <motion.div
                key={useCase.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ scale: 1.02, y: -4 }}
                className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-8 shadow-2xl"
              >
                <div className="w-14 h-14 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl flex items-center justify-center mb-6">
                  <useCase.icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">{useCase.title}</h3>
                <p className="text-gray-300 mb-6 leading-relaxed">{useCase.description}</p>
                <ul className="space-y-2">
                  {useCase.benefits.map((benefit) => (
                    <li key={benefit} className="flex items-center gap-2 text-gray-300">
                      <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                      <span>{benefit}</span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Social Proof / Stats Section */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-3xl p-12"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-12 text-center">
              Enterprise-Ready Performance
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              {[
                { value: "99.9%", label: "Uptime SLA", icon: Shield },
                { value: "<2s", label: "Average Search Time", icon: Zap },
                { value: "$10K+", label: "Annual Savings", icon: DollarSign },
                { value: "75%", label: "Faster Investigations", icon: TrendingUp }
              ].map((stat, index) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ scale: 1.05 }}
                  className="text-center backdrop-blur-sm bg-white/5 rounded-xl p-6 border border-white/10"
                >
                  <stat.icon className="w-10 h-10 text-blue-400 mx-auto mb-4" />
                  <div className="text-4xl font-bold text-white mb-2">{stat.value}</div>
                  <div className="text-sm text-gray-300">{stat.label}</div>
                </motion.div>
              ))}
            </div>

            <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                { icon: CheckCircle, label: "SOC 2 Ready" },
                { icon: Shield, label: "Enterprise Security" },
                { icon: Database, label: "Real-Time Updates" }
              ].map((badge, index) => (
                <motion.div
                  key={badge.label}
                  initial={{ opacity: 0, scale: 0.9 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.4 + index * 0.1 }}
                  className="backdrop-blur-sm bg-white/5 rounded-xl p-4 border border-white/10 flex items-center justify-center gap-3"
                >
                  <badge.icon className="w-6 h-6 text-green-400" />
                  <span className="text-white font-semibold">{badge.label}</span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </section>

        {/* Final CTA Section */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="backdrop-blur-xl bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-white/20 rounded-3xl p-16 text-center"
          >
            <div className="max-w-3xl mx-auto">
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
                Ready to Transform Your Due Diligence?
              </h2>
              <p className="text-xl text-gray-300 mb-10">
                See how POISSON AI® can streamline your vetting and compliance workflows
              </p>
              
              <Link href="/app">
                <motion.button
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-10 py-5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 font-bold text-xl shadow-2xl transition-all duration-300 flex items-center gap-3 mx-auto"
                >
                  DEMO NOW
                  <ArrowRight className="w-6 h-6" />
                </motion.button>
              </Link>

              <p className="text-sm text-gray-400 mt-6">
                No credit card required • Instant access
              </p>
            </div>
          </motion.div>
        </section>

        {/* Footer */}
        <footer className="backdrop-blur-xl bg-white/5 border-t border-white/10 mt-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
              <div className="col-span-1 md:col-span-2">
                <div className="flex items-center gap-3 mb-4">
                  <Image 
                    src="/images/poissonai_logo.png"
                    alt="POISSON AI Logo"
                    width={50}
                    height={50}
                    className="w-[50px] h-[50px] rounded-lg shadow-lg shadow-purple-500/20"
                  />
                  <div>
                    <h3 className="text-lg font-bold text-white">POISSON AI®</h3>
                    <p className="text-xs text-gray-400">Vetting Intelligence Search Hub</p>
                  </div>
                </div>
                <p className="text-gray-400 text-sm max-w-md">
                  Enterprise Government Transparency & Due Diligence Platform. 
                  Uncover hidden connections across 15+ million government records.
                </p>
              </div>
              
              <div>
                <h4 className="text-white font-semibold mb-4">Platform</h4>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li><Link href="/app" className="hover:text-white transition-colors">Search</Link></li>
                  <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                  <li><a href="https://api.poisson-ai.com/docs" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">API Documentation</a></li>
                </ul>
              </div>
              
              <div>
                <h4 className="text-white font-semibold mb-4">Company</h4>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li><Link href="/contact" className="hover:text-white transition-colors">Contact</Link></li>
                  <li><Link href="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link></li>
                  <li><Link href="/terms" className="hover:text-white transition-colors">Terms of Service</Link></li>
                </ul>
              </div>
            </div>
            
            <div className="border-t border-white/10 pt-8">
              <div className="flex flex-col items-center gap-4">
                <Image 
                  src="/images/poissonai_logo.png"
                  alt="POISSON AI Logo"
                  width={100}
                  height={100}
                  className="w-[80px] h-[80px] md:w-[100px] md:h-[100px] opacity-80 rounded-xl shadow-lg shadow-purple-500/20"
                />
                <p className="text-gray-400 text-sm text-center">
                  © 2024-2025 POISSON AI®, LLC. All Rights Reserved.
                </p>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
