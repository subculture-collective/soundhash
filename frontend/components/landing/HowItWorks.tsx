'use client'

import { motion } from 'framer-motion'
import { Upload, Cpu, CheckCircle } from 'lucide-react'

const steps = [
  {
    icon: Upload,
    title: 'Upload Audio',
    description: 'Upload an audio file or video clip that you want to identify.',
  },
  {
    icon: Cpu,
    title: 'AI Processing',
    description: 'Our AI analyzes the audio fingerprint using spectral analysis.',
  },
  {
    icon: CheckCircle,
    title: 'Get Matches',
    description: 'Receive a list of matching videos with timestamps and confidence scores.',
  },
]

export function HowItWorks() {
  return (
    <section className="py-24 bg-gray-50 dark:bg-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            How It Works
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Three simple steps to find the origin of any audio clip
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-12">
          {steps.map((step, index) => {
            const Icon = step.icon
            return (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.2, duration: 0.5 }}
                viewport={{ once: true }}
                className="text-center"
              >
                <div className="relative inline-block mb-6">
                  <div className="w-20 h-20 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full flex items-center justify-center">
                    <Icon className="w-10 h-10 text-white" />
                  </div>
                  {index < steps.length - 1 && (
                    <div className="hidden md:block absolute top-10 left-full w-32 h-0.5 bg-gradient-to-r from-blue-600 to-indigo-600" />
                  )}
                  <div className="absolute -top-2 -right-2 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                    {index + 1}
                  </div>
                </div>
                <h3 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
                  {step.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-300">
                  {step.description}
                </p>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
