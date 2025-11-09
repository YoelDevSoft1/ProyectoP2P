'use client'

import { Shield, Award, CheckCircle, Users, Clock, Zap, Lock, TrendingUp } from 'lucide-react'

export function TrustSection() {
  const features = [
    {
      icon: Shield,
      title: '100% Seguro',
      description: 'Todas las operaciones están respaldadas por Binance P2P, la plataforma más segura del mundo.',
      color: 'text-blue-400',
      bgColor: 'bg-blue-600/20',
    },
    {
      icon: Zap,
      title: 'Transacciones Rápidas',
      description: 'Operaciones completadas en menos de 10 minutos. Sin esperas, sin complicaciones.',
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-600/20',
    },
    {
      icon: TrendingUp,
      title: 'Mejor Precio Garantizado',
      description: 'Tasas competitivas basadas en el mercado en tiempo real. Siempre la mejor opción.',
      color: 'text-green-400',
      bgColor: 'bg-green-600/20',
    },
    {
      icon: Lock,
      title: 'Datos Protegidos',
      description: 'Tus datos personales y financieros están completamente seguros y encriptados.',
      color: 'text-purple-400',
      bgColor: 'bg-purple-600/20',
    },
    {
      icon: Clock,
      title: 'Soporte 24/7',
      description: 'Equipo de soporte disponible en todo momento para ayudarte con tus operaciones.',
      color: 'text-orange-400',
      bgColor: 'bg-orange-600/20',
    },
    {
      icon: Award,
      title: 'Verificado y Confiable',
      description: 'Miles de operaciones exitosas. Confianza construida con transparencia y honestidad.',
      color: 'text-red-400',
      bgColor: 'bg-red-600/20',
    },
  ]

  const stats = [
    { value: '10,000+', label: 'Usuarios Satisfechos', icon: Users },
    { value: '50,000+', label: 'Operaciones Exitosas', icon: CheckCircle },
    { value: '99.8%', label: 'Tasa de Éxito', icon: Award },
    { value: '<10 min', label: 'Tiempo Promedio', icon: Clock },
  ]

  const testimonials = [
    {
      name: 'Carlos M.',
      location: 'Bogotá, Colombia',
      text: 'La mejor casa de cambio que he usado. Precios transparentes y operaciones súper rápidas. ¡100% recomendado!',
      rating: 5,
    },
    {
      name: 'María G.',
      location: 'Caracas, Venezuela',
      text: 'Increíble servicio. Cambié mis bolívares a USDT en minutos y con la mejor tasa del mercado.',
      rating: 5,
    },
    {
      name: 'Juan P.',
      location: 'Medellín, Colombia',
      text: 'Muy profesional y confiable. Llevo meses usando este servicio y nunca he tenido problemas.',
      rating: 5,
    },
  ]

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-900">
      <div className="max-w-7xl mx-auto">
        {/* Estadísticas */}
        <div className="mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white text-center mb-4">
            Confianza Respaldada por Números
          </h2>
          <p className="text-xl text-gray-400 text-center mb-12 max-w-2xl mx-auto">
            Miles de usuarios confían en nosotros para sus operaciones de cambio
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((stat, index) => {
              const Icon = stat.icon
              return (
                <div
                  key={index}
                  className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6 text-center hover:border-primary-500 transition-colors"
                >
                  <Icon className="h-8 w-8 text-primary-500 mx-auto mb-4" />
                  <p className="text-3xl md:text-4xl font-bold text-white mb-2">{stat.value}</p>
                  <p className="text-sm text-gray-400">{stat.label}</p>
                </div>
              )
            })}
          </div>
        </div>

        {/* Características */}
        <div className="mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-white text-center mb-12">
            ¿Por Qué Elegirnos?
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => {
              const Icon = feature.icon
              return (
                <div
                  key={index}
                  className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6 hover:border-primary-500 transition-all hover:shadow-xl"
                >
                  <div className={`${feature.bgColor} w-12 h-12 rounded-lg flex items-center justify-center mb-4`}>
                    <Icon className={`h-6 w-6 ${feature.color}`} />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">{feature.title}</h3>
                  <p className="text-gray-400">{feature.description}</p>
                </div>
              )
            })}
          </div>
        </div>

        {/* Testimonios */}
        <div>
          <h2 className="text-3xl md:text-4xl font-bold text-white text-center mb-12">
            Lo Que Dicen Nuestros Usuarios
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {testimonials.map((testimonial, index) => (
              <div
                key={index}
                className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6"
              >
                <div className="flex items-center gap-1 mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <svg
                      key={i}
                      className="w-5 h-5 text-yellow-400 fill-current"
                      viewBox="0 0 20 20"
                    >
                      <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z" />
                    </svg>
                  ))}
                </div>
                <p className="text-gray-300 mb-4 italic">"{testimonial.text}"</p>
                <div>
                  <p className="text-white font-semibold">{testimonial.name}</p>
                  <p className="text-sm text-gray-400">{testimonial.location}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Garantías */}
        <div className="mt-16 bg-gradient-to-r from-primary-900/30 to-primary-800/20 border border-primary-700/50 rounded-2xl p-8">
          <div className="text-center">
            <Shield className="h-16 w-16 text-primary-400 mx-auto mb-4" />
            <h3 className="text-2xl md:text-3xl font-bold text-white mb-4">
              Garantía de Mejor Precio
            </h3>
            <p className="text-lg text-gray-300 max-w-2xl mx-auto mb-6">
              Si encuentras un precio mejor en otra casa de cambio verificada, te igualamos el precio y te damos un 5% de descuento adicional.
            </p>
            <div className="flex flex-wrap justify-center gap-4 text-sm text-gray-400">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-primary-400" />
                <span>Sin costos ocultos</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-primary-400" />
                <span>Transparencia total</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-primary-400" />
                <span>Protección de datos</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-primary-400" />
                <span>Soporte prioritario</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

