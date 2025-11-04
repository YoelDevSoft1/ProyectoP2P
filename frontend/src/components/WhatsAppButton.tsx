'use client'

import { MessageCircle } from 'lucide-react'
import { useState } from 'react'

interface WhatsAppButtonProps {
  phoneNumber: string
  message: string
}

export function WhatsAppButton({ phoneNumber, message }: WhatsAppButtonProps) {
  const [isHovered, setIsHovered] = useState(false)

  const handleClick = () => {
    const url = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  return (
    <>
      {/* Floating WhatsApp Button */}
      <button
        onClick={handleClick}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className="fixed bottom-6 right-6 z-50 group"
        aria-label="Contactar por WhatsApp"
      >
        {/* Pulse animation ring */}
        <div className="absolute inset-0 bg-green-500 rounded-full animate-ping opacity-75 group-hover:opacity-0 transition-opacity"></div>

        {/* Main button */}
        <div className="relative flex items-center gap-3 bg-green-600 hover:bg-green-700 text-white rounded-full shadow-2xl transition-all duration-300 hover:scale-110 hover:shadow-green-600/50">
          {/* Icon container */}
          <div className="p-4">
            <MessageCircle
              className={`h-7 w-7 transition-transform duration-300 ${
                isHovered ? 'scale-110 rotate-12' : ''
              }`}
            />
          </div>

          {/* Text tooltip (appears on hover on desktop) */}
          <div
            className={`
              hidden md:flex items-center pr-4 overflow-hidden transition-all duration-300
              ${isHovered ? 'max-w-xs opacity-100' : 'max-w-0 opacity-0'}
            `}
          >
            <span className="font-semibold text-sm whitespace-nowrap">
              ¡Chatea con nosotros!
            </span>
          </div>
        </div>

        {/* Badge notification (optional - shows number of unread messages) */}
        {/* Uncomment if you want to add a notification badge
        <div className="absolute -top-1 -right-1 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-xs font-bold text-white border-2 border-gray-900">
          1
        </div>
        */}
      </button>

      {/* Mobile-specific styling adjustments */}
      <style jsx>{`
        @media (max-width: 768px) {
          button {
            bottom: 1.25rem;
            right: 1.25rem;
          }
        }
      `}</style>
    </>
  )
}
