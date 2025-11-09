'use client'

import { Calculator, MessageCircle, CheckCircle, CreditCard, Zap, ArrowRight } from 'lucide-react'

export function ProcessSteps({ whatsappLink }: { whatsappLink?: string | null }) {
  const steps = [
    {
      number: 1,
      icon: Calculator,
      title: 'Calcula tu Cambio',
      description: 'Usa nuestra calculadora para ver exactamente cuánto recibirás. Sin sorpresas, sin costos ocultos.',
      color: 'text-blue-400',
      bgColor: 'bg-blue-600/20',
    },
    {
      number: 2,
      icon: MessageCircle,
      title: 'Contacta por WhatsApp',
      description: 'Envía un mensaje con el monto que deseas cambiar. Nuestro equipo te responderá en menos de 2 minutos.',
      color: 'text-green-400',
      bgColor: 'bg-green-600/20',
    },
    {
      number: 3,
      icon: CheckCircle,
      title: 'Confirma los Detalles',
      description: 'Revisa los detalles de la operación y confirma. Te enviaremos todas las instrucciones claras y detalladas.',
      color: 'text-purple-400',
      bgColor: 'bg-purple-600/20',
    },
    {
      number: 4,
      icon: CreditCard,
      title: 'Realiza el Pago',
      description: 'Realiza la transferencia según las instrucciones. Puedes usar transferencia bancaria, Nequi, Daviplata, o cualquier método acordado.',
      color: 'text-orange-400',
      bgColor: 'bg-orange-600/20',
    },
    {
      number: 5,
      icon: Zap,
      title: 'Recibe tu USDT',
      description: 'Una vez confirmado el pago, recibirás tu USDT en menos de 10 minutos. ¡Así de rápido y sencillo!',
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-600/20',
    },
  ]

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Cómo Funciona
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Proceso simple y rápido en solo 5 pasos. Sin complicaciones, sin esperas.
          </p>
        </div>

        <div className="relative">
          {/* Línea conectora para desktop */}
          <div className="hidden lg:block absolute top-24 left-0 right-0 h-0.5 bg-gradient-to-r from-primary-600 via-primary-500 to-primary-600" />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
            {steps.map((step, index) => {
              const Icon = step.icon
              const isLast = index === steps.length - 1

              return (
                <div key={step.number} className="relative">
                  {/* Conector móvil */}
                  {!isLast && (
                    <div className="lg:hidden absolute top-12 left-1/2 transform -translate-x-1/2 w-0.5 h-8 bg-gradient-to-b from-primary-600 to-primary-500" />
                  )}

                  <div className="relative bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-2xl p-6 hover:border-primary-500 transition-all hover:shadow-xl hover:scale-105">
                    {/* Número */}
                    <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center border-4 border-gray-900">
                      <span className="text-white font-bold text-sm">{step.number}</span>
                    </div>

                    {/* Icono */}
                    <div className={`${step.bgColor} w-16 h-16 rounded-xl flex items-center justify-center mx-auto mb-4 mt-4`}>
                      <Icon className={`h-8 w-8 ${step.color}`} />
                    </div>

                    {/* Contenido */}
                    <h3 className="text-xl font-bold text-white text-center mb-2">
                      {step.title}
                    </h3>
                    <p className="text-gray-400 text-center text-sm">
                      {step.description}
                    </p>

                    {/* Flecha para desktop */}
                    {!isLast && (
                      <div className="hidden lg:block absolute top-24 -right-4 z-10">
                        <ArrowRight className="h-6 w-6 text-primary-500" />
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* CTA */}
        {whatsappLink && (
          <div className="mt-12 text-center">
            <a
              href={whatsappLink}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-3 px-8 py-4 bg-green-600 hover:bg-green-700 text-white rounded-xl font-bold text-lg transition-all hover:scale-105 shadow-lg hover:shadow-green-600/50"
            >
              <MessageCircle className="h-6 w-6" />
              Comenzar Ahora
              <ArrowRight className="h-5 w-5" />
            </a>
            <p className="mt-4 text-gray-400 text-sm">
              Respuesta garantizada en menos de 2 minutos
            </p>
          </div>
        )}

        {/* Tiempo estimado */}
        <div className="mt-12 bg-gradient-to-r from-primary-900/30 to-primary-800/20 border border-primary-700/50 rounded-xl p-6 max-w-2xl mx-auto">
          <div className="flex items-center justify-center gap-4">
            <Zap className="h-8 w-8 text-primary-400" />
            <div className="text-center">
              <p className="text-2xl font-bold text-white mb-1">
                Tiempo Total: Menos de 10 minutos
              </p>
              <p className="text-gray-400">
                Desde el primer contacto hasta recibir tu USDT
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

