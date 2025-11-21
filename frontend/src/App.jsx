import { useState } from 'react'

// Route definitions matching the backend
const STORY_ROUTES = {
  "1": { name: "Chronological Steward", description: "Share your story in order from beginning to present" },
  "2": { name: "Thematic Explorer", description: "Organize by life themes (love, career, growth)" },
  "3": { name: "Anecdotal Spark", description: "Share vivid, standalone moments and memories" },
  "4": { name: "Interviewer's Chair", description: "Answer structured, thought-provoking questions" },
  "5": { name: "Reflective Journaler", description: "Explore challenges and personal growth introspectively" },
  "6": { name: "Legacy Weaver", description: "Focus on what you want to leave behind for future generations" },
  "7": { name: "Personal Route", description: "Describe your own approach" },
}

function App() {
  // Estado para armazenar as mensagens do chat
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Welcome to the Life Story Game! I\'ll guide you through telling your life story to create a personalized board game. Are you ready to begin?' }
  ])

  // Estado para o texto do input
  const [input, setInput] = useState('')

  // Estado para loading
  const [isLoading, setIsLoading] = useState(false)

  // Estado para erros
  const [error, setError] = useState(null)

  // Phase tracking (client-side state for stateless backend)
  const [currentPhase, setCurrentPhase] = useState('GREETING')
  const [selectedRoute, setSelectedRoute] = useState(null)
  const [customRouteDescription, setCustomRouteDescription] = useState(null)
  const [showRouteSelection, setShowRouteSelection] = useState(false)

  // Handle route selection
  const handleRouteSelect = async (routeNumber) => {
    setSelectedRoute(routeNumber)
    setShowRouteSelection(false)

    // If route 7, show custom input prompt
    if (routeNumber === "7") {
      const customMessage = { role: 'assistant', content: 'Please describe your preferred approach to telling your story:' }
      setMessages([...messages,
      { role: 'user', content: routeNumber },
        customMessage
      ])
      // Don't advance phase yet - need description first
    } else {
      // Send route selection to backend and advance phase
      setCurrentPhase('QUESTION_1')  // Move to first question
      await sendMessage(routeNumber)
    }
  }

  // Função que é chamada quando o formulário é enviado
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return
    await sendMessage(input.trim())
  }

  // Send message to backend
  const sendMessage = async (userMessage) => {
    // Adiciona a mensagem do usuário ao array de mensagens
    const newUserMessage = { role: 'user', content: userMessage }
    const updatedMessages = [...messages, newUserMessage]
    setMessages(updatedMessages)

    // Limpa o input e erros anteriores
    setInput('')
    setError(null)
    setIsLoading(true)

    try {
      // Send full state to stateless backend
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: updatedMessages,
          phase: currentPhase,
          selected_route: selectedRoute,
          custom_route_description: customRouteDescription
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        throw new Error(errorData.error || `Error ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()

      // Handle phase advancement logic (client-side)
      const lastMessage = userMessage.toLowerCase()

      // Advance from GREETING to ROUTE_SELECTION on affirmative
      if (currentPhase === 'GREETING' && (lastMessage.includes('yes') || lastMessage.includes('sim') || lastMessage.includes('ready') || lastMessage.includes('ok'))) {
        setCurrentPhase('ROUTE_SELECTION')
        setShowRouteSelection(true)
      }

      // Advance from ROUTE_SELECTION when route selected (handled in handleRouteSelect)

      // Advance from QUESTION phases on any response
      if (currentPhase.startsWith('QUESTION_') && userMessage.trim().length > 0) {
        const questionNum = parseInt(currentPhase.split('_')[1])
        if (questionNum < 6) {
          setCurrentPhase(`QUESTION_${questionNum + 1}`)
        } else {
          setCurrentPhase('SYNTHESIS')
        }
      }

      // Handle route 7 custom description
      if (selectedRoute === '7' && !customRouteDescription && userMessage.trim().length > 10) {
        setCustomRouteDescription(userMessage.trim())
        setCurrentPhase('QUESTION_1')
      }

      // Adiciona a resposta do assistente
      setMessages([...updatedMessages, { role: 'assistant', content: data.response }])

    } catch (err) {
      console.error('Error calling API:', err)
      setError(err.message || 'Error connecting to server. Check if backend is running.')

      // Adiciona mensagem de erro ao chat
      setMessages([
        ...updatedMessages,
        { role: 'assistant', content: `Sorry, an error occurred: ${err.message || 'Unknown error'}` }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col">
      <div className="p-4 border-b border-gray-700">
        <h1 className="text-2xl font-bold">Life Story Game</h1>
        {currentPhase !== 'GREETING' && (
          <div className="text-sm text-gray-400 mt-1">
            Phase: {currentPhase}
            {selectedRoute && selectedRoute !== "7" && ` | Route: ${STORY_ROUTES[selectedRoute]?.name}`}
            {selectedRoute === "7" && ` | Route: Personal Route`}
          </div>
        )}
      </div>

      {/* Route Selection UI */}
      {showRouteSelection && (
        <div className="p-4 bg-gray-800 border-b border-gray-700">
          <h2 className="text-xl font-semibold mb-4">Choose Your Storytelling Approach:</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(STORY_ROUTES).map(([num, route]) => (
              <button
                key={num}
                onClick={() => handleRouteSelect(num)}
                className="text-left p-4 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors border border-gray-600"
              >
                <div className="font-semibold text-blue-400">{num}. {route.name}</div>
                <div className="text-sm text-gray-300 mt-1">{route.description}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Área de mensagens - ocupa o espaço disponível */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${msg.role === 'user'
                ? 'bg-blue-600'
                : 'bg-gray-700'
                }`}
            >
              <div className="whitespace-pre-wrap break-words">
                {msg.content}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-700 px-4 py-2 rounded-lg">
              <span className="animate-pulse">Digitando...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="flex justify-center">
            <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-2 rounded-lg text-sm">
              {error}
            </div>
          </div>
        )}
      </div>

      {/* Formulário de input - fica fixo na parte inferior */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-700">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Digite sua mensagem..."
            className="flex-1 p-3 rounded-lg bg-gray-800 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-400 disabled:opacity-50"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-6 py-3 bg-blue-600 rounded-lg font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-600 disabled:cursor-not-allowed"
          >
            Enviar
          </button>
        </div>
      </form>
    </div>
  )
}

export default App
