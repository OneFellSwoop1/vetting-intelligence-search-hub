'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { Mail, MessageSquare, Send, User, Building, Phone, MapPin, Clock, CheckCircle, AlertCircle, ArrowLeft } from 'lucide-react';

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    subject: '',
    message: '',
    inquiryType: 'general'
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitStatus('idle');

    // Simulate form submission (replace with actual API call)
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // For demo purposes - in production, send to your backend
    console.log('Form submitted:', formData);
    
    setIsSubmitting(false);
    setSubmitStatus('success');
    
    // Reset form after success
    setTimeout(() => {
      setFormData({
        name: '',
        email: '',
        company: '',
        subject: '',
        message: '',
        inquiryType: 'general'
      });
      setSubmitStatus('idle');
    }, 3000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -inset-10 opacity-50">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
          <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse animation-delay-2000"></div>
        </div>
      </div>

      {/* Navigation Header */}
      <motion.nav 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="backdrop-blur-xl bg-white/5 border-b border-white/10 sticky top-0 z-50"
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
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          {/* Header */}
          <div className="text-center mb-12">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.6 }}
              className="inline-block mb-6"
            >
              <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl flex items-center justify-center shadow-2xl mx-auto">
                <MessageSquare className="w-10 h-10 text-white" />
              </div>
            </motion.div>
            <h1 className="text-5xl font-bold text-white mb-4">Get in Touch</h1>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Have questions about our platform? We're here to help. Reach out and we'll get back to you as soon as possible.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Contact Form */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="lg:col-span-2"
            >
              <div className="backdrop-blur-xl bg-white/10 rounded-3xl p-8 border border-white/20 shadow-2xl">
                <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                  <Send className="w-6 h-6 text-blue-400" />
                  Send us a Message
                </h2>

                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* Inquiry Type */}
                  <div>
                    <label htmlFor="inquiryType" className="block text-sm font-medium text-gray-200 mb-2">
                      Inquiry Type
                    </label>
                    <select
                      id="inquiryType"
                      name="inquiryType"
                      value={formData.inquiryType}
                      onChange={handleInputChange}
                      required
                      className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition-all"
                    >
                      <option value="general" className="bg-gray-800">General Inquiry</option>
                      <option value="sales" className="bg-gray-800">Sales & Pricing</option>
                      <option value="support" className="bg-gray-800">Technical Support</option>
                      <option value="partnership" className="bg-gray-800">Partnership Opportunities</option>
                      <option value="press" className="bg-gray-800">Press & Media</option>
                      <option value="legal" className="bg-gray-800">Legal & Compliance</option>
                    </select>
                  </div>

                  {/* Name */}
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-gray-200 mb-2">
                      <User className="w-4 h-4 inline mr-1" />
                      Your Name *
                    </label>
                    <input
                      type="text"
                      id="name"
                      name="name"
                      value={formData.name}
                      onChange={handleInputChange}
                      required
                      placeholder="John Doe"
                      className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition-all"
                    />
                  </div>

                  {/* Email */}
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-200 mb-2">
                      <Mail className="w-4 h-4 inline mr-1" />
                      Email Address *
                    </label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      value={formData.email}
                      onChange={handleInputChange}
                      required
                      placeholder="john@company.com"
                      className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition-all"
                    />
                  </div>

                  {/* Company */}
                  <div>
                    <label htmlFor="company" className="block text-sm font-medium text-gray-200 mb-2">
                      <Building className="w-4 h-4 inline mr-1" />
                      Company / Organization
                    </label>
                    <input
                      type="text"
                      id="company"
                      name="company"
                      value={formData.company}
                      onChange={handleInputChange}
                      placeholder="Your Company Name"
                      className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition-all"
                    />
                  </div>

                  {/* Subject */}
                  <div>
                    <label htmlFor="subject" className="block text-sm font-medium text-gray-200 mb-2">
                      Subject *
                    </label>
                    <input
                      type="text"
                      id="subject"
                      name="subject"
                      value={formData.subject}
                      onChange={handleInputChange}
                      required
                      placeholder="How can we help you?"
                      className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition-all"
                    />
                  </div>

                  {/* Message */}
                  <div>
                    <label htmlFor="message" className="block text-sm font-medium text-gray-200 mb-2">
                      Message *
                    </label>
                    <textarea
                      id="message"
                      name="message"
                      value={formData.message}
                      onChange={handleInputChange}
                      required
                      rows={6}
                      placeholder="Tell us more about your inquiry..."
                      className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition-all resize-none"
                    />
                  </div>

                  {/* Submit Button */}
                  <div>
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      type="submit"
                      disabled={isSubmitting}
                      className="w-full px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold text-lg shadow-lg transition-all duration-300 flex items-center justify-center gap-2"
                    >
                      {isSubmitting ? (
                        <>
                          <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                          Sending...
                        </>
                      ) : (
                        <>
                          <Send className="w-5 h-5" />
                          Send Message
                        </>
                      )}
                    </motion.button>
                  </div>

                  {/* Success/Error Messages */}
                  {submitStatus === 'success' && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-4 bg-green-500/10 border border-green-400/30 rounded-lg flex items-center gap-2 text-green-200"
                    >
                      <CheckCircle className="w-5 h-5" />
                      <span>Thank you! Your message has been sent successfully. We'll get back to you soon.</span>
                    </motion.div>
                  )}

                  {submitStatus === 'error' && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-4 bg-red-500/10 border border-red-400/30 rounded-lg flex items-center gap-2 text-red-200"
                    >
                      <AlertCircle className="w-5 h-5" />
                      <span>Oops! Something went wrong. Please try again or email us directly.</span>
                    </motion.div>
                  )}
                </form>
              </div>
            </motion.div>

            {/* Contact Information */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
              className="space-y-6"
            >
              {/* Email Contact */}
              <div className="backdrop-blur-xl bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center">
                    <Mail className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-white">Email Us</h3>
                </div>
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-gray-300 mb-1">General Inquiries</p>
                    <a href="mailto:info@poissonai.com" className="text-blue-300 hover:text-blue-100 font-medium transition-colors">
                      info@poissonai.com
                    </a>
                  </div>
                  <div>
                    <p className="text-sm text-gray-300 mb-1">Support</p>
                    <a href="mailto:support@poissonai.com" className="text-blue-300 hover:text-blue-100 font-medium transition-colors">
                      support@poissonai.com
                    </a>
                  </div>
                  <div>
                    <p className="text-sm text-gray-300 mb-1">Sales</p>
                    <a href="mailto:sales@poissonai.com" className="text-blue-300 hover:text-blue-100 font-medium transition-colors">
                      sales@poissonai.com
                    </a>
                  </div>
                  <div>
                    <p className="text-sm text-gray-300 mb-1">Legal & Privacy</p>
                    <a href="mailto:legal@poissonai.com" className="text-blue-300 hover:text-blue-100 font-medium transition-colors">
                      legal@poissonai.com
                    </a>
                  </div>
                </div>
              </div>

              {/* Response Time */}
              <div className="backdrop-blur-xl bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl flex items-center justify-center">
                    <Clock className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-white">Response Time</h3>
                </div>
                <p className="text-gray-200 leading-relaxed">
                  We typically respond to all inquiries within <strong className="text-white">24-48 hours</strong> during business days. 
                  For urgent matters, please mark your inquiry as "Technical Support" or email us directly.
                </p>
              </div>

              {/* Office Hours */}
              <div className="backdrop-blur-xl bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
                    <Clock className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-white">Business Hours</h3>
                </div>
                <div className="space-y-2 text-gray-200">
                  <p><strong className="text-white">Monday - Friday:</strong> 9:00 AM - 6:00 PM EST</p>
                  <p><strong className="text-white">Saturday - Sunday:</strong> Closed</p>
                  <p className="text-sm text-gray-300 mt-3">
                    * Emergency support available 24/7 for enterprise customers
                  </p>
                </div>
              </div>

              {/* Additional Resources */}
              <div className="backdrop-blur-xl bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-amber-500 rounded-xl flex items-center justify-center">
                    <MapPin className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-white">Quick Links</h3>
                </div>
                <div className="space-y-3">
                  <Link href="/app" className="block text-blue-300 hover:text-blue-100 transition-colors">
                    → Try Demo
                  </Link>
                  <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noopener noreferrer" className="block text-blue-300 hover:text-blue-100 transition-colors">
                    → API Documentation
                  </a>
                  <Link href="/privacy" className="block text-blue-300 hover:text-blue-100 transition-colors">
                    → Privacy Policy
                  </Link>
                  <Link href="/terms" className="block text-blue-300 hover:text-blue-100 transition-colors">
                    → Terms of Service
                  </Link>
                </div>
              </div>
            </motion.div>
          </div>

          {/* FAQ Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="mt-12"
          >
            <div className="backdrop-blur-xl bg-white/10 rounded-3xl p-8 border border-white/20 shadow-2xl">
              <h2 className="text-3xl font-bold text-white mb-8 text-center">Frequently Asked Questions</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {[
                  {
                    q: "How quickly can I get started?",
                    a: "You can start searching immediately with our demo. For full access, contact our sales team for a personalized onboarding session."
                  },
                  {
                    q: "What data sources do you cover?",
                    a: "We aggregate data from FEC, NYC Open Data, Senate LDA, House LDA, NYS Ethics, and NYC Lobbying Bureau - covering 15M+ government records."
                  },
                  {
                    q: "Is my data secure?",
                    a: "Yes! We use enterprise-grade encryption, secure hosting, and comply with SOC 2 standards. Read our Privacy Policy for details."
                  },
                  {
                    q: "Do you offer enterprise plans?",
                    a: "Yes! We offer custom enterprise solutions with dedicated support, API access, and advanced features. Contact sales@poissonai.com"
                  }
                ].map((faq, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.7 + index * 0.1 }}
                    className="backdrop-blur-sm bg-white/5 rounded-xl p-6 border border-white/10"
                  >
                    <h3 className="text-lg font-semibold text-white mb-2">{faq.q}</h3>
                    <p className="text-gray-300 leading-relaxed">{faq.a}</p>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Footer Note */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="mt-8 text-center"
          >
            <p className="text-gray-400 text-sm">
              © 2024-2026 POISSON AI®, LLC. All Rights Reserved.
            </p>
            <div className="flex items-center justify-center gap-4 mt-4">
              <Link href="/privacy" className="text-gray-300 hover:text-white transition-colors text-sm underline">
                Privacy Policy
              </Link>
              <span className="text-gray-600">•</span>
              <Link href="/terms" className="text-gray-300 hover:text-white transition-colors text-sm underline">
                Terms of Service
              </Link>
              <span className="text-gray-600">•</span>
              <Link href="/" className="text-gray-300 hover:text-white transition-colors text-sm underline">
                Home
              </Link>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
