'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { FileText, Scale, AlertTriangle, UserCheck, Shield, Ban, Lock, Mail, ArrowLeft } from 'lucide-react';

export default function TermsOfService() {
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
              <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg">
                <Scale className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-4xl font-bold text-white mb-2">Terms of Service</h1>
                <p className="text-gray-300">Last Updated: {lastUpdated}</p>
              </div>
            </div>
            
            <div className="bg-yellow-500/10 border border-yellow-400/30 rounded-lg p-4">
              <p className="text-yellow-200 flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Important:</strong> Please read these Terms of Service carefully before using the POISSON AI® 
                  Vetting Intelligence Search Hub platform. By accessing or using our services, you agree to be bound by 
                  these terms. If you do not agree, do not use our platform.
                </span>
              </p>
            </div>
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
                <FileText className="w-6 h-6 text-blue-400" />
                <h2 className="text-2xl font-bold text-white">1. Acceptance of Terms</h2>
              </div>
              
              <div className="space-y-3 text-gray-200">
                <p>
                  These Terms of Service ("Terms") constitute a legally binding agreement between you ("User," "you," or "your") 
                  and POISSON AI®, LLC ("Company," "we," "us," or "our") regarding your use of the Vetting Intelligence Search Hub 
                  platform (the "Platform" or "Service").
                </p>
                <p>
                  By accessing, browsing, or using the Platform, you acknowledge that you have read, understood, and agree to be 
                  bound by these Terms and our <Link href="/privacy" className="text-blue-300 hover:text-blue-100 underline">Privacy Policy</Link>.
                </p>
                <p>
                  We reserve the right to modify these Terms at any time. Your continued use of the Platform after such changes 
                  constitutes acceptance of the modified Terms.
                </p>
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
                <UserCheck className="w-6 h-6 text-green-400" />
                <h2 className="text-2xl font-bold text-white">2. Eligibility and Account Registration</h2>
              </div>
              
              <div className="space-y-4 text-gray-200">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">2.1 Eligibility</h3>
                  <p>You must meet the following requirements to use our Platform:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4 mt-2">
                    <li>Be at least 18 years of age or the age of majority in your jurisdiction</li>
                    <li>Have the legal capacity to enter into binding contracts</li>
                    <li>Not be prohibited from using the Service under applicable laws</li>
                    <li>Use the Platform for lawful business or professional purposes only</li>
                  </ul>
                </div>
                
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">2.2 Account Security</h3>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>You are responsible for maintaining the confidentiality of your account credentials</li>
                    <li>You must notify us immediately of any unauthorized access to your account</li>
                    <li>You are responsible for all activities that occur under your account</li>
                    <li>We reserve the right to suspend or terminate accounts that violate these Terms</li>
                  </ul>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">2.3 Account Information</h3>
                  <p>You agree to:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4 mt-2">
                    <li>Provide accurate, current, and complete information during registration</li>
                    <li>Maintain and promptly update your account information</li>
                    <li>Not impersonate any person or entity</li>
                    <li>Not create multiple accounts to circumvent restrictions or limits</li>
                  </ul>
                </div>
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
                <Shield className="w-6 h-6 text-purple-400" />
                <h2 className="text-2xl font-bold text-white">3. Permitted Use and Restrictions</h2>
              </div>
              
              <div className="space-y-4 text-gray-200">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">3.1 Permitted Use</h3>
                  <p>You may use the Platform for the following purposes:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4 mt-2">
                    <li>Due diligence and compliance research</li>
                    <li>Legitimate business intelligence gathering</li>
                    <li>Investigative journalism and public accountability research</li>
                    <li>Academic research and analysis</li>
                    <li>Legal research and litigation support</li>
                  </ul>
                </div>
                
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">3.2 Prohibited Activities</h3>
                  <p>You agree NOT to:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4 mt-2">
                    <li><strong>Violate Laws:</strong> Use the Platform for any illegal purpose or in violation of any laws</li>
                    <li><strong>Harassment:</strong> Use the Platform to harass, stalk, or threaten any individual</li>
                    <li><strong>Discrimination:</strong> Use data for unlawful discrimination in employment, housing, credit, or insurance</li>
                    <li><strong>Scraping:</strong> Use automated tools to scrape, crawl, or harvest data from the Platform</li>
                    <li><strong>Reverse Engineering:</strong> Decompile, reverse engineer, or attempt to extract source code</li>
                    <li><strong>System Interference:</strong> Disrupt, interfere with, or overload the Platform's infrastructure</li>
                    <li><strong>Security Breaches:</strong> Attempt to gain unauthorized access to any systems or data</li>
                    <li><strong>Resale:</strong> Resell or redistribute Platform access or data without authorization</li>
                    <li><strong>Misrepresentation:</strong> Misrepresent your identity or affiliation</li>
                    <li><strong>Malware:</strong> Upload viruses, malware, or any harmful code</li>
                  </ul>
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
                <FileText className="w-6 h-6 text-cyan-400" />
                <h2 className="text-2xl font-bold text-white">4. Data Sources and Accuracy</h2>
              </div>
              
              <div className="space-y-3 text-gray-200">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">4.1 Third-Party Data</h3>
                  <p>
                    Our Platform aggregates publicly available data from government sources including but not limited to 
                    the Federal Election Commission, NYC Open Data, U.S. Senate, U.S. House of Representatives, New York 
                    State Ethics Commission, and NYC Lobbying Bureau.
                  </p>
                  <p className="mt-2">
                    This data is provided by third parties and is subject to their respective terms of service and data policies.
                  </p>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">4.2 No Warranty of Accuracy</h3>
                  <p>
                    While we strive to provide accurate and up-to-date information, we make no representations or warranties 
                    regarding the accuracy, completeness, reliability, or timeliness of any data displayed on the Platform.
                  </p>
                  <ul className="list-disc list-inside space-y-2 ml-4 mt-2">
                    <li>Data may contain errors, omissions, or outdated information</li>
                    <li>We are not responsible for the accuracy of third-party government data</li>
                    <li>You should verify critical information through original government sources</li>
                    <li>Data is provided "as is" without warranty of any kind</li>
                  </ul>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">4.3 Not Legal Advice</h3>
                  <div className="bg-red-500/10 border border-red-400/30 rounded-lg p-4 mt-2">
                    <p className="text-red-200">
                      <strong>Disclaimer:</strong> The Platform does not provide legal, financial, investment, or professional 
                      advice. Information provided should not be relied upon as a substitute for consultation with professional 
                      advisors. Consult qualified professionals for specific advice tailored to your situation.
                    </p>
                  </div>
                </div>
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
                <Lock className="w-6 h-6 text-yellow-400" />
                <h2 className="text-2xl font-bold text-white">5. Intellectual Property Rights</h2>
              </div>
              
              <div className="space-y-4 text-gray-200">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">5.1 Company Ownership</h3>
                  <p>
                    The Platform, including its software, design, graphics, text, algorithms, and all intellectual property 
                    rights therein, is owned by POISSON AI®, LLC and is protected by copyright, trademark, patent, trade secret, 
                    and other intellectual property laws.
                  </p>
                  <p className="mt-2">
                    POISSON AI® and the POISSON AI logo are registered trademarks of POISSON AI®, LLC. You may not use these 
                    trademarks without our prior written permission.
                  </p>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">5.2 Limited License</h3>
                  <p>
                    We grant you a limited, non-exclusive, non-transferable, revocable license to access and use the Platform 
                    for your internal business purposes in accordance with these Terms.
                  </p>
                  <p className="mt-2">This license does not include the right to:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4 mt-2">
                    <li>Modify, copy, distribute, transmit, display, reproduce, or create derivative works</li>
                    <li>Reverse engineer or access the Platform to build a competitive product</li>
                    <li>Frame, mirror, or deep-link to the Platform without authorization</li>
                    <li>Remove or alter any copyright, trademark, or proprietary notices</li>
                  </ul>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">5.3 Government Data</h3>
                  <p>
                    While our Platform technology is proprietary, the underlying government data is public information. 
                    Users are free to access original government data sources directly. Our value lies in aggregation, 
                    analysis, correlation, and presentation of that data.
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
                <AlertTriangle className="w-6 h-6 text-red-400" />
                <h2 className="text-2xl font-bold text-white">6. Disclaimer of Warranties</h2>
              </div>
              
              <div className="space-y-3 text-gray-200">
                <div className="bg-orange-500/10 border border-orange-400/30 rounded-lg p-4">
                  <p className="text-orange-200 uppercase font-semibold mb-2">IMPORTANT LEGAL NOTICE</p>
                  <p className="text-orange-200">
                    THE PLATFORM IS PROVIDED ON AN "AS IS" AND "AS AVAILABLE" BASIS WITHOUT WARRANTIES OF ANY KIND, 
                    EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO:
                  </p>
                </div>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Warranties of merchantability, fitness for a particular purpose, or non-infringement</li>
                  <li>Warranties regarding accuracy, reliability, or completeness of data</li>
                  <li>Warranties that the Platform will be uninterrupted, timely, secure, or error-free</li>
                  <li>Warranties regarding the results obtained from using the Platform</li>
                  <li>Warranties that defects will be corrected</li>
                </ul>
                <p className="mt-4">
                  We do not warrant that the Platform will meet your requirements or expectations. Your use of the Platform 
                  is at your sole risk.
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
                <Ban className="w-6 h-6 text-red-400" />
                <h2 className="text-2xl font-bold text-white">7. Limitation of Liability</h2>
              </div>
              
              <div className="space-y-3 text-gray-200">
                <div className="bg-red-500/10 border border-red-400/30 rounded-lg p-4">
                  <p className="text-red-200 uppercase font-semibold mb-2">LIMITATION OF LIABILITY</p>
                  <p className="text-red-200">
                    TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT SHALL POISSON AI®, LLC, ITS OFFICERS, 
                    DIRECTORS, EMPLOYEES, AGENTS, OR AFFILIATES BE LIABLE FOR:
                  </p>
                </div>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li><strong>Indirect, incidental, special, consequential, or punitive damages</strong></li>
                  <li><strong>Loss of profits, revenue, data, or business opportunities</strong></li>
                  <li><strong>Business interruption or loss of goodwill</strong></li>
                  <li><strong>Personal injury or property damage</strong></li>
                  <li><strong>Damages resulting from unauthorized access to your account</strong></li>
                  <li><strong>Reliance on any information obtained through the Platform</strong></li>
                  <li><strong>Errors, mistakes, or inaccuracies in data</strong></li>
                </ul>
                <p className="mt-4">
                  WHETHER BASED ON WARRANTY, CONTRACT, TORT (INCLUDING NEGLIGENCE), PRODUCT LIABILITY, OR ANY OTHER LEGAL THEORY, 
                  EVEN IF WE HAVE BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
                </p>
                <p className="mt-4">
                  IN JURISDICTIONS THAT DO NOT ALLOW THE EXCLUSION OR LIMITATION OF LIABILITY FOR CONSEQUENTIAL OR INCIDENTAL 
                  DAMAGES, OUR LIABILITY IS LIMITED TO THE GREATEST EXTENT PERMITTED BY LAW.
                </p>
                <p className="mt-4 font-semibold text-white">
                  Our total liability to you for any claims arising from your use of the Platform shall not exceed the greater of 
                  (a) the amount you paid us in the twelve (12) months preceding the claim, or (b) $100 USD.
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
                <Shield className="w-6 h-6 text-blue-400" />
                <h2 className="text-2xl font-bold text-white">8. Indemnification</h2>
              </div>
              
              <div className="space-y-3 text-gray-200">
                <p>
                  You agree to indemnify, defend, and hold harmless POISSON AI®, LLC, its officers, directors, employees, 
                  agents, affiliates, and licensors from and against any and all claims, liabilities, damages, losses, costs, 
                  expenses, or fees (including reasonable attorneys' fees) arising from:
                </p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Your use or misuse of the Platform</li>
                  <li>Your violation of these Terms</li>
                  <li>Your violation of any rights of another party</li>
                  <li>Your violation of any applicable laws or regulations</li>
                  <li>Any content you submit or transmit through the Platform</li>
                  <li>Your breach of any representations or warranties</li>
                </ul>
                <p className="mt-4">
                  We reserve the right to assume the exclusive defense and control of any matter subject to indemnification 
                  by you, and you agree to cooperate with our defense of such claims.
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
                <Ban className="w-6 h-6 text-orange-400" />
                <h2 className="text-2xl font-bold text-white">9. Termination</h2>
              </div>
              
              <div className="space-y-4 text-gray-200">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">9.1 Termination by You</h3>
                  <p>
                    You may terminate your account at any time by contacting us or using the account deletion feature. 
                    Upon termination, your right to access the Platform will cease immediately.
                  </p>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">9.2 Termination by Us</h3>
                  <p>We reserve the right to suspend or terminate your account and access to the Platform:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4 mt-2">
                    <li>For violation of these Terms</li>
                    <li>For fraudulent, abusive, or illegal activity</li>
                    <li>For extended periods of inactivity</li>
                    <li>For non-payment of fees (if applicable)</li>
                    <li>At our discretion, with or without notice</li>
                  </ul>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">9.3 Effect of Termination</h3>
                  <p>Upon termination:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4 mt-2">
                    <li>Your license to use the Platform will immediately terminate</li>
                    <li>You must cease all use of the Platform</li>
                    <li>We may delete your account and data per our data retention policies</li>
                    <li>Provisions that by their nature should survive termination will remain in effect</li>
                  </ul>
                </div>
              </div>
            </motion.div>

            {/* Section 10 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.1 }}
              className="backdrop-blur-xl bg-white/10 rounded-2xl p-8 border border-white/20 shadow-xl"
            >
              <div className="flex items-center gap-3 mb-4">
                <Scale className="w-6 h-6 text-purple-400" />
                <h2 className="text-2xl font-bold text-white">10. Governing Law and Dispute Resolution</h2>
              </div>
              
              <div className="space-y-4 text-gray-200">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">10.1 Governing Law</h3>
                  <p>
                    These Terms shall be governed by and construed in accordance with the laws of the State of Delaware, 
                    United States, without regard to its conflict of law provisions.
                  </p>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">10.2 Dispute Resolution</h3>
                  <p>
                    Any dispute, controversy, or claim arising out of or relating to these Terms or your use of the Platform 
                    shall be resolved through binding arbitration in accordance with the Commercial Arbitration Rules of the 
                    American Arbitration Association.
                  </p>
                  <ul className="list-disc list-inside space-y-2 ml-4 mt-2">
                    <li>Arbitration shall be conducted in Delaware, United States</li>
                    <li>The arbitrator's decision shall be final and binding</li>
                    <li>Each party shall bear its own costs and fees</li>
                    <li>Class action waiver: You agree to arbitrate disputes on an individual basis only</li>
                  </ul>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">10.3 Exceptions</h3>
                  <p>
                    Either party may seek equitable relief in court for intellectual property infringement or unauthorized 
                    access to the Platform.
                  </p>
                </div>
              </div>
            </motion.div>

            {/* Section 11 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.2 }}
              className="backdrop-blur-xl bg-white/10 rounded-2xl p-8 border border-white/20 shadow-xl"
            >
              <div className="flex items-center gap-3 mb-4">
                <FileText className="w-6 h-6 text-cyan-400" />
                <h2 className="text-2xl font-bold text-white">11. Miscellaneous</h2>
              </div>
              
              <div className="space-y-4 text-gray-200">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">11.1 Entire Agreement</h3>
                  <p>
                    These Terms, together with our Privacy Policy, constitute the entire agreement between you and POISSON AI® 
                    regarding the Platform and supersede all prior agreements and understandings.
                  </p>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">11.2 Severability</h3>
                  <p>
                    If any provision of these Terms is found to be invalid or unenforceable, the remaining provisions shall 
                    remain in full force and effect.
                  </p>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">11.3 Waiver</h3>
                  <p>
                    No waiver of any term shall be deemed a further or continuing waiver of such term or any other term.
                  </p>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">11.4 Assignment</h3>
                  <p>
                    You may not assign or transfer these Terms without our prior written consent. We may assign these Terms 
                    without restriction.
                  </p>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">11.5 Force Majeure</h3>
                  <p>
                    We shall not be liable for any failure or delay in performance due to circumstances beyond our reasonable 
                    control, including acts of God, natural disasters, war, terrorism, labor disputes, or government actions.
                  </p>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">11.6 Export Control</h3>
                  <p>
                    You agree to comply with all applicable export and import laws and regulations. You represent that you 
                    are not located in a country subject to U.S. government embargo or designated as a "terrorist supporting" 
                    country.
                  </p>
                </div>
              </div>
            </motion.div>

            {/* Contact Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.3 }}
              className="backdrop-blur-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-2xl p-8 border border-white/20 shadow-xl"
            >
              <div className="flex items-center gap-3 mb-4">
                <Mail className="w-6 h-6 text-white" />
                <h2 className="text-2xl font-bold text-white">12. Contact Information</h2>
              </div>
              
              <div className="space-y-3 text-gray-200">
                <p>
                  If you have any questions about these Terms of Service, please contact us:
                </p>
                
                <div className="bg-white/10 rounded-lg p-6 mt-4 space-y-3">
                  <p><strong className="text-white">POISSON AI®, LLC</strong></p>
                  <p className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-blue-400" />
                    <span>Legal: <a href="mailto:legal@poissonai.com" className="text-blue-300 hover:text-blue-100 underline">legal@poissonai.com</a></span>
                  </p>
                  <p className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-blue-400" />
                    <span>Support: <a href="mailto:support@poissonai.com" className="text-blue-300 hover:text-blue-100 underline">support@poissonai.com</a></span>
                  </p>
                  <p className="mt-4">
                    <Link href="/contact" className="inline-flex items-center gap-2 text-blue-300 hover:text-blue-100 underline">
                      Use our Contact Form →
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
            transition={{ delay: 1.4 }}
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
