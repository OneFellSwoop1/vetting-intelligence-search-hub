'use client';

import React, { useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { Home, RefreshCw, AlertTriangle, ArrowLeft, Mail, Bug } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error('Application error:', error);
  }, [error]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-red-900 to-slate-900 flex items-center justify-center">
      {/* Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -inset-10 opacity-50">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-red-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
          <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-orange-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse animation-delay-2000"></div>
          <div className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-yellow-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse animation-delay-4000"></div>
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
          {/* Error Icon */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mb-8"
          >
            <div className="relative inline-block">
              <motion.div
                animate={{
                  rotate: [0, 5, -5, 0],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
                className="w-32 h-32 mx-auto bg-gradient-to-r from-red-500 to-orange-500 rounded-3xl flex items-center justify-center shadow-2xl"
              >
                <AlertTriangle className="w-16 h-16 text-white" />
              </motion.div>
              <motion.div
                animate={{
                  scale: [1, 1.3, 1],
                  opacity: [0.5, 0.2, 0.5],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
                className="absolute inset-0 bg-gradient-to-r from-red-500 to-orange-500 rounded-3xl blur-2xl -z-10"
              />
            </div>
          </motion.div>

          {/* Error Message */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mb-6"
          >
            <h1 className="text-6xl md:text-7xl font-bold text-white mb-4">
              Oops!
            </h1>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Something Went Wrong
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto leading-relaxed">
              We encountered an unexpected error while processing your request. 
              Our team has been notified and is working on a fix.
            </p>
          </motion.div>

          {/* Error Details (for development) */}
          {process.env.NODE_ENV === 'development' && error && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="backdrop-blur-xl bg-red-500/10 rounded-2xl p-6 border border-red-400/30 mb-8 text-left"
            >
              <div className="flex items-center gap-2 mb-3">
                <Bug className="w-5 h-5 text-red-400" />
                <h3 className="text-lg font-semibold text-red-300">Development Error Details</h3>
              </div>
              <pre className="text-sm text-red-200 overflow-x-auto">
                {error.message}
              </pre>
              {error.digest && (
                <p className="text-xs text-red-300 mt-2">
                  Error ID: {error.digest}
                </p>
              )}
            </motion.div>
          )}

          {/* Action Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="backdrop-blur-xl bg-white/10 rounded-2xl p-8 border border-white/20 shadow-2xl mb-8"
          >
            <h3 className="text-2xl font-bold text-white mb-6">What Can You Do?</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Try Again Button */}
              <motion.button
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
                onClick={reset}
                className="backdrop-blur-sm bg-gradient-to-r from-blue-600 to-purple-600 border-0 rounded-xl p-6 hover:from-blue-700 hover:to-purple-700 transition-all duration-300 cursor-pointer"
              >
                <div className="flex flex-col items-center gap-3">
                  <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                    <RefreshCw className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-1">Try Again</h4>
                    <p className="text-sm text-gray-200">Reload the page</p>
                  </div>
                </div>
              </motion.button>

              {/* Home Button */}
              <Link href="/">
                <motion.div
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  className="backdrop-blur-sm bg-white/5 border border-white/20 rounded-xl p-6 hover:bg-white/10 transition-all duration-300 cursor-pointer"
                >
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg flex items-center justify-center">
                      <Home className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h4 className="text-lg font-semibold text-white mb-1">Go Home</h4>
                      <p className="text-sm text-gray-300">Back to safety</p>
                    </div>
                  </div>
                </motion.div>
              </Link>

              {/* Contact Support Button */}
              <Link href="/contact">
                <motion.div
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  className="backdrop-blur-sm bg-white/5 border border-white/20 rounded-xl p-6 hover:bg-white/10 transition-all duration-300 cursor-pointer"
                >
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-amber-500 rounded-lg flex items-center justify-center">
                      <Mail className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h4 className="text-lg font-semibold text-white mb-1">Contact Us</h4>
                      <p className="text-sm text-gray-300">Report the issue</p>
                    </div>
                  </div>
                </motion.div>
              </Link>
            </div>
          </motion.div>

          {/* Additional Information */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.7 }}
            className="backdrop-blur-xl bg-white/10 rounded-xl p-6 border border-white/20"
          >
            <h4 className="text-lg font-semibold text-white mb-3">Why did this happen?</h4>
            <ul className="text-gray-300 text-sm space-y-2 text-left max-w-2xl mx-auto">
              <li className="flex items-start gap-2">
                <span className="text-yellow-400 mt-1">•</span>
                <span>The page might be experiencing technical difficulties</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-yellow-400 mt-1">•</span>
                <span>Your internet connection might be unstable</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-yellow-400 mt-1">•</span>
                <span>The server might be temporarily unavailable</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-yellow-400 mt-1">•</span>
                <span>We might be performing maintenance (check our status page)</span>
              </li>
            </ul>
          </motion.div>

          {/* Footer Note */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.9 }}
            className="mt-8 text-gray-400 text-sm"
          >
            <p>
              If the problem persists, please{' '}
              <a href="mailto:support@poissonai.com" className="text-blue-400 hover:text-blue-300 underline">
                email our support team
              </a>{' '}
              with details about what you were doing when the error occurred.
            </p>
            {error.digest && (
              <p className="mt-2">
                Error Reference: {error.digest}
              </p>
            )}
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
