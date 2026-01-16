'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { Home, Search, ArrowLeft, AlertCircle, Compass, FileQuestion } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
      {/* Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -inset-10 opacity-50">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
          <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse animation-delay-2000"></div>
          <div className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse animation-delay-4000"></div>
        </div>
      </div>

      {/* Navigation Header */}
      <motion.nav 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="backdrop-blur-xl bg-white/5 border-b border-white/10 fixed top-0 left-0 right-0 z-50"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <Link href="/" className="flex items-center gap-3 hover:opacity-90 transition-opacity">
              <Image 
                src="/images/poissonai_logo.png"
                alt="POISSON AI Logo"
                width={40}
                height={40}
                className="rounded-lg shadow-lg shadow-purple-500/30"
                priority
              />
              <div>
                <h1 className="text-lg md:text-xl font-bold text-white">POISSON AI®</h1>
                <p className="text-xs text-gray-300 hidden sm:block">Vetting Intelligence</p>
              </div>
            </Link>
            <Link href="/">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-4 py-2 backdrop-blur-sm bg-white/10 border border-white/20 text-white rounded-xl hover:bg-white/20 font-medium transition-all duration-300 flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Home
              </motion.button>
            </Link>
          </div>
        </div>
      </motion.nav>

      {/* Main Content */}
      <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          {/* 404 Icon */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mb-8"
          >
            <div className="relative inline-block">
              <motion.div
                animate={{
                  rotate: [0, 10, -10, 0],
                }}
                transition={{
                  duration: 4,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
                className="w-32 h-32 mx-auto bg-gradient-to-r from-red-500 to-pink-500 rounded-3xl flex items-center justify-center shadow-2xl"
              >
                <FileQuestion className="w-16 h-16 text-white" />
              </motion.div>
              <motion.div
                animate={{
                  scale: [1, 1.2, 1],
                  opacity: [0.5, 0.2, 0.5],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
                className="absolute inset-0 bg-gradient-to-r from-red-500 to-pink-500 rounded-3xl blur-2xl -z-10"
              />
            </div>
          </motion.div>

          {/* Error Code */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mb-6"
          >
            <h1 className="text-8xl md:text-9xl font-bold bg-gradient-to-r from-red-400 via-pink-400 to-purple-400 bg-clip-text text-transparent mb-4">
              404
            </h1>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Page Not Found
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto leading-relaxed">
              Oops! The page you're looking for seems to have vanished into the digital void. 
              It might have been moved, deleted, or never existed in the first place.
            </p>
          </motion.div>

          {/* Suggestions Box */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="backdrop-blur-xl bg-white/10 rounded-2xl p-8 border border-white/20 shadow-2xl mb-8"
          >
            <div className="flex items-center gap-2 mb-6 justify-center">
              <Compass className="w-6 h-6 text-blue-400" />
              <h3 className="text-2xl font-bold text-white">Where Would You Like to Go?</h3>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Home Button */}
              <Link href="/">
                <motion.div
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  className="backdrop-blur-sm bg-white/5 border border-white/20 rounded-xl p-6 hover:bg-white/10 transition-all duration-300 cursor-pointer"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Home className="w-6 h-6 text-white" />
                    </div>
                    <div className="text-left">
                      <h4 className="text-lg font-semibold text-white mb-1">Home Page</h4>
                      <p className="text-sm text-gray-300">Go back to the main page</p>
                    </div>
                  </div>
                </motion.div>
              </Link>

              {/* Search Button */}
              <Link href="/app">
                <motion.div
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  className="backdrop-blur-sm bg-white/5 border border-white/20 rounded-xl p-6 hover:bg-white/10 transition-all duration-300 cursor-pointer"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Search className="w-6 h-6 text-white" />
                    </div>
                    <div className="text-left">
                      <h4 className="text-lg font-semibold text-white mb-1">Search Platform</h4>
                      <p className="text-sm text-gray-300">Start searching records</p>
                    </div>
                  </div>
                </motion.div>
              </Link>

              {/* Contact Button */}
              <Link href="/contact">
                <motion.div
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  className="backdrop-blur-sm bg-white/5 border border-white/20 rounded-xl p-6 hover:bg-white/10 transition-all duration-300 cursor-pointer"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg flex items-center justify-center flex-shrink-0">
                      <AlertCircle className="w-6 h-6 text-white" />
                    </div>
                    <div className="text-left">
                      <h4 className="text-lg font-semibold text-white mb-1">Contact Us</h4>
                      <p className="text-sm text-gray-300">Report a broken link</p>
                    </div>
                  </div>
                </motion.div>
              </Link>

              {/* API Docs Button */}
              <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noopener noreferrer">
                <motion.div
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  className="backdrop-blur-sm bg-white/5 border border-white/20 rounded-xl p-6 hover:bg-white/10 transition-all duration-300 cursor-pointer"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-amber-500 rounded-lg flex items-center justify-center flex-shrink-0">
                      <FileQuestion className="w-6 h-6 text-white" />
                    </div>
                    <div className="text-left">
                      <h4 className="text-lg font-semibold text-white mb-1">API Docs</h4>
                      <p className="text-sm text-gray-300">View documentation</p>
                    </div>
                  </div>
                </motion.div>
              </a>
            </div>
          </motion.div>

          {/* Help Text */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.7 }}
            className="text-gray-400 text-sm"
          >
            <p>
              If you believe this is a mistake, please{' '}
              <Link href="/contact" className="text-blue-400 hover:text-blue-300 underline">
                contact our support team
              </Link>
              .
            </p>
            <p className="mt-2">
              Error Code: 404 | Page Not Found
            </p>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
