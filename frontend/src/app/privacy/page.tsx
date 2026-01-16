'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { Shield, Lock, Eye, Database, UserCheck, FileText, AlertCircle, Mail, ArrowLeft } from 'lucide-react';

export default function PrivacyPolicy() {
  const lastUpdated = "January 13, 2026";

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
      <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          {/* Header */}
          <div className="backdrop-blur-xl bg-white/10 rounded-3xl p-8 border border-white/20 shadow-2xl mb-8">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl flex items-center justify-center shadow-lg">
                <Shield className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-4xl font-bold text-white mb-2">Privacy Policy</h1>
                <p className="text-gray-300">Last Updated: {lastUpdated}</p>
              </div>
            </div>
            
            <p className="text-lg text-gray-200 leading-relaxed">
              At POISSON AI®, we are committed to protecting your privacy and ensuring the security of your personal information. 
              This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our 
              Vetting Intelligence Search Hub platform.
            </p>
          </div>

          {/* Content Sections */}
          <div className="space-y-6">
            {/* Section 1 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="backdrop-blur-xl bg-white/10 rounded-2xl p-8 border border-white/20 shadow-xl"
            >
              <div className="flex items-center gap-3 mb-4">
                <Database className="w-6 h-6 text-blue-400" />
                <h2 className="text-2xl font-bold text-white">1. Information We Collect</h2>
              </div>
              
              <div className="space-y-4 text-gray-200">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">1.1 Information You Provide</h3>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li><strong>Account Information:</strong> Name, email address, company name, and professional details when you create an account</li>
                    <li><strong>Search Queries:</strong> The searches you perform on our platform</li>
                    <li><strong>Communications:</strong> Messages you send us through contact forms or support channels</li>
                    <li><strong>Payment Information:</strong> Billing details processed securely through third-party payment processors</li>
                  </ul>
                </div>
                
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">1.2 Automatically Collected Information</h3>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li><strong>Usage Data:</strong> Pages viewed, features used, search patterns, and interaction with the platform</li>
                    <li><strong>Device Information:</strong> IP address, browser type, operating system, device identifiers</li>
                    <li><strong>Cookies and Similar Technologies:</strong> Session data, preferences, and analytics information</li>
                    <li><strong>Log Data:</strong> Access times, error logs, and performance metrics</li>
                  </ul>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">1.3 Third-Party Data Sources</h3>
                  <p>We access and display publicly available government data from:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4 mt-2">
                    <li>Federal Election Commission (FEC)</li>
                    <li>NYC Open Data (Checkbook NYC)</li>
                    <li>U.S. Senate LDA Database</li>
                    <li>U.S. House of Representatives LDA Database</li>
                    <li>New York State Ethics Commission</li>
                    <li>NYC Lobbying Bureau</li>
                  </ul>
                  <p className="mt-2 text-gray-300 italic">This data is public information and subject to the privacy policies of the respective government agencies.</p>
                </div>
              </div>
            </motion.div>

            {/* Section 2 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="backdrop-blur-xl bg-white/10 rounded-2xl p-8 border border-white/20 shadow-xl"
            >
              <div className="flex items-center gap-3 mb-4">
                <Eye className="w-6 h-6 text-purple-400" />
                <h2 className="text-2xl font-bold text-white">2. How We Use Your Information</h2>
              </div>
              
              <div className="space-y-3 text-gray-200">
                <p>We use the information we collect for the following purposes:</p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li><strong>Provide Services:</strong> Deliver search results, analytics, and platform features</li>
                  <li><strong>Account Management:</strong> Create and maintain your account, process payments</li>
                  <li><strong>Improve Platform:</strong> Analyze usage patterns to enhance functionality and user experience</li>
                  <li><strong>Communication:</strong> Send service updates, security alerts, and respond to inquiries</li>
                  <li><strong>Security:</strong> Detect, prevent, and address fraud, abuse, and security issues</li>
                  <li><strong>Legal Compliance:</strong> Comply with legal obligations and enforce our Terms of Service</li>
                  <li><strong>Research & Development:</strong> Develop new features and improve existing services</li>
                  <li><strong>Marketing:</strong> Send promotional communications (with your consent, where required)</li>
                </ul>
              </div>
            </motion.div>

            {/* Section 3 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="backdrop-blur-xl bg-white/10 rounded-2xl p-8 border border-white/20 shadow-xl"
            >
              <div className="flex items-center gap-3 mb-4">
                <UserCheck className="w-6 h-6 text-green-400" />
                <h2 className="text-2xl font-bold text-white">3. Information Sharing and Disclosure</h2>
              </div>
              
              <div className="space-y-3 text-gray-200">
                <p>We do not sell your personal information. We may share your information in the following circumstances:</p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li><strong>Service Providers:</strong> Third-party vendors who assist with hosting, analytics, payment processing, and customer support</li>
                  <li><strong>Legal Requirements:</strong> When required by law, subpoena, or government request</li>
                  <li><strong>Business Transfers:</strong> In connection with a merger, acquisition, or sale of assets</li>
                  <li><strong>With Your Consent:</strong> When you explicitly authorize us to share specific information</li>
                  <li><strong>Aggregated Data:</strong> Non-personally identifiable, aggregated statistics for business purposes</li>
                </ul>
                
                <div className="mt-4 p-4 bg-blue-500/10 border border-blue-400/30 rounded-lg">
                  <p className="flex items-center gap-2 text-blue-200">
                    <AlertCircle className="w-5 h-5" />
                    <strong>Important:</strong> We never share your personal search queries or account details with government agencies or third parties for marketing purposes.
                  </p>
                </div>
              </div>
            </motion.div>

            {/* Section 4 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="backdrop-blur-xl bg-white/10 rounded-2xl p-8 border border-white/20 shadow-xl"
            >
              <div className="flex items-center gap-3 mb-4">
                <Lock className="w-6 h-6 text-red-400" />
                <h2 className="text-2xl font-bold text-white">4. Data Security</h2>
              </div>
              
              <div className="space-y-3 text-gray-200">
                <p>We implement industry-standard security measures to protect your information:</p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li><strong>Encryption:</strong> Data transmitted via HTTPS/TLS encryption</li>
                  <li><strong>Access Controls:</strong> Strict internal access policies and authentication requirements</li>
                  <li><strong>Regular Audits:</strong> Periodic security assessments and vulnerability testing</li>
                  <li><strong>Data Minimization:</strong> We collect only the data necessary for our services</li>
                  <li><strong>Secure Infrastructure:</strong> Enterprise-grade hosting with redundancy and backup systems</li>
                  <li><strong>Incident Response:</strong> Procedures for detecting and responding to security breaches</li>
                </ul>
                
                <p className="mt-4 text-gray-300 italic">
                  While we strive to protect your personal information, no method of transmission over the Internet 
                  or electronic storage is 100% secure. We cannot guarantee absolute security.
                </p>
              </div>
            </motion.div>

            {/* Section 5 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="backdrop-blur-xl bg-white/10 rounded-2xl p-8 border border-white/20 shadow-xl"
            >
              <div className="flex items-center gap-3 mb-4">
                <FileText className="w-6 h-6 text-yellow-400" />
                <h2 className="text-2xl font-bold text-white">5. Your Privacy Rights</h2>
              </div>
              
              <div className="space-y-4 text-gray-200">
                <p>Depending on your location, you may have the following rights:</p>
                
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">5.1 General Rights</h3>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li><strong>Access:</strong> Request a copy of your personal information</li>
                    <li><strong>Correction:</strong> Update or correct inaccurate information</li>
                    <li><strong>Deletion:</strong> Request deletion of your personal information</li>
                    <li><strong>Data Portability:</strong> Receive your data in a structured, machine-readable format</li>
                    <li><strong>Opt-Out:</strong> Unsubscribe from marketing communications</li>
                    <li><strong>Restriction:</strong> Request restriction of processing in certain circumstances</li>
                  </ul>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">5.2 GDPR Rights (EU Users)</h3>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Right to object to processing based on legitimate interests</li>
                    <li>Right to withdraw consent at any time</li>
                    <li>Right to lodge a complaint with a supervisory authority</li>
                  </ul>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">5.3 CCPA Rights (California Users)</h3>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Right to know what personal information is collected</li>
                    <li>Right to know whether personal information is sold or disclosed</li>
                    <li>Right to say no to the sale of personal information</li>
                    <li>Right to non-discrimination for exercising your rights</li>
                  </ul>
                </div>

                <div className="mt-4 p-4 bg-purple-500/10 border border-purple-400/30 rounded-lg">
                  <p className="text-purple-200">
                    <strong>To Exercise Your Rights:</strong> Contact us at{' '}
                    <a href="mailto:privacy@poissonai.com" className="text-purple-300 hover:text-purple-100 underline">
                      privacy@poissonai.com
                    </a>
                    {' '}or use our <Link href="/contact" className="text-purple-300 hover:text-purple-100 underline">Contact Form</Link>.
                  </p>
                </div>
              </div>
            </motion.div>

            {/* Section 6 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 }}
              className="backdrop-blur-xl bg-white/10 rounded-2xl p-8 border border-white/20 shadow-xl"
            >
              <div className="flex items-center gap-3 mb-4">
                <Database className="w-6 h-6 text-cyan-400" />
                <h2 className="text-2xl font-bold text-white">6. Cookies and Tracking Technologies</h2>
              </div>
              
              <div className="space-y-3 text-gray-200">
                <p>We use cookies and similar technologies to:</p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li><strong>Essential Cookies:</strong> Required for basic platform functionality</li>
                  <li><strong>Performance Cookies:</strong> Help us understand how users interact with the platform</li>
                  <li><strong>Functional Cookies:</strong> Remember your preferences and settings</li>
                  <li><strong>Analytics Cookies:</strong> Collect information about platform usage and performance</li>
                </ul>
                
                <p className="mt-4">
                  You can control cookies through your browser settings. Note that disabling certain cookies may 
                  affect platform functionality.
                </p>
              </div>
            </motion.div>

            {/* Section 7 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 }}
              className="backdrop-blur-xl bg-white/10 rounded-2xl p-8 border border-white/20 shadow-xl"
            >
              <div className="flex items-center gap-3 mb-4">
                <FileText className="w-6 h-6 text-orange-400" />
                <h2 className="text-2xl font-bold text-white">7. Data Retention</h2>
              </div>
              
              <div className="space-y-3 text-gray-200">
                <p>We retain your personal information for as long as necessary to:</p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Provide our services to you</li>
                  <li>Comply with legal obligations</li>
                  <li>Resolve disputes and enforce agreements</li>
                  <li>Maintain business records</li>
                </ul>
                
                <p className="mt-4">
                  When you delete your account, we will delete or anonymize your personal information within 
                  30 days, except where we must retain it for legal or compliance purposes.
                </p>
              </div>
            </motion.div>

            {/* Section 8 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.9 }}
              className="backdrop-blur-xl bg-white/10 rounded-2xl p-8 border border-white/20 shadow-xl"
            >
              <div className="flex items-center gap-3 mb-4">
                <Shield className="w-6 h-6 text-pink-400" />
                <h2 className="text-2xl font-bold text-white">8. Children's Privacy</h2>
              </div>
              
              <div className="space-y-3 text-gray-200">
                <p>
                  Our platform is not intended for children under 13 years of age. We do not knowingly collect 
                  personal information from children under 13. If you are a parent or guardian and believe your 
                  child has provided us with personal information, please contact us immediately.
                </p>
              </div>
            </motion.div>

            {/* Section 9 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.0 }}
              className="backdrop-blur-xl bg-white/10 rounded-2xl p-8 border border-white/20 shadow-xl"
            >
              <div className="flex items-center gap-3 mb-4">
                <AlertCircle className="w-6 h-6 text-red-400" />
                <h2 className="text-2xl font-bold text-white">9. Changes to This Privacy Policy</h2>
              </div>
              
              <div className="space-y-3 text-gray-200">
                <p>
                  We may update this Privacy Policy from time to time to reflect changes in our practices or 
                  for legal, operational, or regulatory reasons. We will notify you of any material changes by:
                </p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Posting the updated policy on this page</li>
                  <li>Updating the "Last Updated" date at the top of this policy</li>
                  <li>Sending you an email notification (for significant changes)</li>
                </ul>
                
                <p className="mt-4">
                  Your continued use of the platform after changes become effective constitutes acceptance of 
                  the updated Privacy Policy.
                </p>
              </div>
            </motion.div>

            {/* Contact Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.1 }}
              className="backdrop-blur-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-2xl p-8 border border-white/20 shadow-xl"
            >
              <div className="flex items-center gap-3 mb-4">
                <Mail className="w-6 h-6 text-white" />
                <h2 className="text-2xl font-bold text-white">10. Contact Us</h2>
              </div>
              
              <div className="space-y-3 text-gray-200">
                <p>
                  If you have any questions, concerns, or requests regarding this Privacy Policy or our data practices, 
                  please contact us:
                </p>
                
                <div className="bg-white/10 rounded-lg p-6 mt-4 space-y-3">
                  <p><strong className="text-white">POISSON AI®, LLC</strong></p>
                  <p className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-blue-400" />
                    <span>Email: <a href="mailto:privacy@poissonai.com" className="text-blue-300 hover:text-blue-100 underline">privacy@poissonai.com</a></span>
                  </p>
                  <p className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-blue-400" />
                    <span>Support: <a href="mailto:support@poissonai.com" className="text-blue-300 hover:text-blue-100 underline">support@poissonai.com</a></span>
                  </p>
                  <p className="mt-4">
                    <Link href="/contact" className="inline-flex items-center gap-2 text-blue-300 hover:text-blue-100 underline">
                      Or use our Contact Form →
                    </Link>
                  </p>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Footer Note */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2 }}
            className="mt-8 text-center"
          >
            <p className="text-gray-400 text-sm">
              © 2024-2026 POISSON AI®, LLC. All Rights Reserved.
            </p>
            <div className="flex items-center justify-center gap-4 mt-4">
              <Link href="/terms" className="text-gray-300 hover:text-white transition-colors text-sm underline">
                Terms of Service
              </Link>
              <span className="text-gray-600">•</span>
              <Link href="/contact" className="text-gray-300 hover:text-white transition-colors text-sm underline">
                Contact
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
