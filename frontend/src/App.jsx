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

// Available tags for story themes (matching backend)
const AVAILABLE_TAGS = [
  "adventure", "family", "career", "love", "challenge",
  "growth", "travel", "friendship", "legacy", "identity",
  "father_figure", "mother_figure", "mentor", "loss",
  "success", "failure", "humor", "courage", "resilience",
]

function App() {
  // Estado para armazenar as mensagens do chat
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Welcome! I\'m here to help you tell your life story chronologically. Your story will be organized into chapters that follow your life timeline, capturing each era of your journey. Are you ready to begin?' }
  ])

  // Estado para o texto do input
  const [input, setInput] = useState('')

  // Estado para loading
  const [isLoading, setIsLoading] = useState(false)

  // Estado para erros
  const [error, setError] = useState(null)

  // Phase tracking (client-side state for stateless backend)
  const [currentPhase, setCurrentPhase] = useState('GREETING')
  const [selectedRoute, setSelectedRoute] = useState('1')  // Default to Chronological Steward
  const [customRouteDescription, setCustomRouteDescription] = useState(null)
  const [showRouteSelection, setShowRouteSelection] = useState(false)
  const [ageRange, setAgeRange] = useState(null)
  const [showAgeSelection, setShowAgeSelection] = useState(false)

  // Tag selection state
  const [selectedTags, setSelectedTags] = useState([])

  // Estado para o resumo da história
  const [storySummary, setStorySummary] = useState("No story details shared yet.")
  const [isSummarizing, setIsSummarizing] = useState(false)

  // Phase timeline state
  const [phaseOrder, setPhaseOrder] = useState([])
  const [phaseIndex, setPhaseIndex] = useState(-1)

  // Define interview phases that allow multi-question conversations
  const INTERVIEW_PHASES = ['BEFORE_BORN', 'CHILDHOOD', 'ADOLESCENCE', 'EARLY_ADULTHOOD', 'MIDLIFE', 'PRESENT']

  // Check if current phase is an interview phase (shows "Next Phase" button)
  const isInterviewPhase = INTERVIEW_PHASES.includes(currentPhase)

  // Handle tag selection/deselection
  const handleTagToggle = (tag) => {
    setSelectedTags(prev =>
      prev.includes(tag)
        ? prev.filter(t => t !== tag)  // Remove if already selected
        : [...prev, tag]                // Add if not selected
    )
  }

  // Handle age range selection
  const handleAgeSelect = async (ageNumber) => {
    const ageMap = {
      "1": "under_18",
      "2": "18_30",
      "3": "31_45",
      "4": "46_60",
      "5": "61_plus",
    }
    setAgeRange(ageMap[ageNumber])
    setShowAgeSelection(false)

    // Send age selection to backend WITHOUT adding to visible chat
    // This prevents AI from seeing the control code "5" and misinterpreting it
    await sendAgeSelection(ageNumber)
  }

  // Função que é chamada quando o formulário é enviado
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return
    await sendMessage(input.trim(), false) // false = not advancing phase
  }

  // Handle explicit phase advancement (Next Phase button clicked)
  const handleNextPhase = async () => {
    if (isLoading) return
    await sendMessage('__ADVANCE_PHASE__', true) // true = advancing phase
  }

  // Handle clicking on a phase in the timeline to jump to it
  const handlePhaseClick = async (targetPhase) => {
    // Don't allow jumping to current phase
    if (targetPhase === currentPhase) return

    // Don't allow jumping to GREETING or AGE_SELECTION (setup phases)
    if (targetPhase === 'GREETING' || targetPhase === 'AGE_SELECTION') return

    // Don't allow jumping if age not selected yet
    if (!ageRange) return

    // Don't allow jumping while loading
    if (isLoading) return

    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: messages,
          route: selectedRoute,
          phase: currentPhase,
          age_range: ageRange,
          jump_to_phase: targetPhase,
          selected_tags: selectedTags
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        throw new Error(errorData.error || `Error ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()

      // Update phase state
      if (data.phase) {
        setCurrentPhase(data.phase)
        console.log(`[PHASE] Jumped to: ${data.phase}`)
      }
      if (data.phase_order) {
        setPhaseOrder(data.phase_order)
      }
      if (data.phase_index !== undefined) {
        setPhaseIndex(data.phase_index)
      }

      // Add AI response to messages
      if (data.response && data.response.trim()) {
        const newMsgs = [...messages, { role: 'assistant', content: data.response }]
        setMessages(newMsgs)
        fetchSummary(newMsgs)
      }
    } catch (err) {
      console.error('Phase jump failed:', err)
      setError(err.message || 'Failed to jump to phase')
    } finally {
      setIsLoading(false)
    }
  }

  // Fetch story summary from backend
  const fetchSummary = async (currentMessages) => {
    // Don't summarize if only greeting
    if (currentMessages.length <= 2) return

    setIsSummarizing(true)
    try {
      const response = await fetch('/api/summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: currentMessages }),
      })

      if (response.ok) {
        const data = await response.json()
        if (data.summary) {
          setStorySummary(data.summary)
        }
      }
    } catch (err) {
      console.error("Failed to fetch summary:", err)
    } finally {
      setIsSummarizing(false)
    }
  }

  // Send age selection without adding to visible conversation
  const sendAgeSelection = async (ageNumber) => {
    setIsLoading(true)
    setError(null)

    try {
      // Send to backend with age validation, but don't add to chat history
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: messages,  // Existing messages WITHOUT the age selection number
          route: selectedRoute,
          phase: currentPhase,
          age_range: ageRange,
          age_selection_input: ageNumber  // Send as metadata, not message content
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        throw new Error(errorData.error || `Error ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()

      // Update phase from backend
      const newPhase = data.phase
      const newAgeRange = data.age_range

      if (data.phase_order) setPhaseOrder(data.phase_order)
      if (data.phase_index !== undefined) setPhaseIndex(data.phase_index)

      if (newPhase && newPhase !== currentPhase) {
        setCurrentPhase(newPhase)
        console.log(`[PHASE] Advanced to: ${newPhase}`)
      }

      // After successful age selection, get opening prompt for new phase
      // Backend returns empty response for age selection, so we need a second call
      if (newPhase && newPhase !== 'AGE_SELECTION' && (!data.response || !data.response.trim())) {
        // Build messages with transition marker so AI knows age was selected via button
        // This prevents AI from asking for age again
        const messagesWithMarker = [
          ...messages,
          {
            role: 'user',
            content: `[Age selected via button: ${newAgeRange}. Moving to phase: ${newPhase}]`
          }
        ]

        // Make second API call to get opening prompt for new phase
        const promptResponse = await fetch('/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            messages: messagesWithMarker,  // Messages WITH transition marker
            route: selectedRoute,
            phase: newPhase,  // Use new phase (BEFORE_BORN)
            age_range: newAgeRange,  // Use newly selected age range
            selected_tags: selectedTags
          }),
        })

        if (promptResponse.ok) {
          const promptData = await promptResponse.json()
          if (promptData.response && promptData.response.trim()) {
            const newMsgs = [...messages, { role: 'assistant', content: promptData.response }]
            setMessages(newMsgs)
            fetchSummary(newMsgs)
          }
        }
      } else if (data.response && data.response.trim()) {
        // Add AI response if there is content (shouldn't happen for age selection)
        const newMsgs = [...messages, { role: 'assistant', content: data.response }]
        setMessages(newMsgs)
        fetchSummary(newMsgs)
      }

    } catch (err) {
      console.error('Error calling API:', err)
      setError(err.message || 'Error connecting to server.')
      setMessages([
        ...messages,
        { role: 'assistant', content: `Sorry, an error occurred: ${err.message || 'Unknown error'}` }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  // Send message to backend
  const sendMessage = async (userMessage, advancePhase = false) => {
    // For phase advancement, don't add user message to chat
    let updatedMessages
    if (advancePhase) {
      updatedMessages = [...messages]
    } else {
      // Adiciona a mensagem do usuário ao array de mensagens
      const newUserMessage = { role: 'user', content: userMessage }
      updatedMessages = [...messages, newUserMessage]
      setMessages(updatedMessages)
    }

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
          route: selectedRoute,
          phase: currentPhase,
          age_range: ageRange,
          advance_phase: advancePhase,  // Signal explicit phase transition
          selected_tags: selectedTags    // User's chosen focus areas
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        throw new Error(errorData.error || `Error ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()

      // Update phase from backend response (backend handles advancement)
      if (data.phase_order) setPhaseOrder(data.phase_order)
      if (data.phase_index !== undefined) setPhaseIndex(data.phase_index)

      if (data.phase && data.phase !== currentPhase) {
        setCurrentPhase(data.phase)
        console.log(`[PHASE] Advanced to: ${data.phase}`)
      }

      // Handle special phase transitions that need UI updates
      const lastMessage = userMessage.toLowerCase()

      // Advance from GREETING to AGE_SELECTION on affirmative
      if (currentPhase === 'GREETING' && (lastMessage.includes('yes') || lastMessage.includes('sim') || lastMessage.includes('ready') || lastMessage.includes('ok'))) {
        setCurrentPhase('AGE_SELECTION')
        setShowAgeSelection(true)
      }

      // Note: Age selection now handled by sendAgeSelection function
      // This code path is for manual text input (if user types "5" instead of clicking)

      // Adiciona a resposta do assistente
      const newMessages = [...updatedMessages, { role: 'assistant', content: data.response }]
      setMessages(newMessages)

      // Update summary after AI response
      fetchSummary(newMessages)

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
      {/* Sticky Navbar - stays visible when scrolling */}
      <nav className="sticky top-0 z-50 bg-gray-900 border-b border-gray-700 shadow-lg">
        <div className="p-4">
          <div className="flex justify-between items-center mb-2">
            <h1 className="text-2xl font-bold">Life Story Game</h1>
            {currentPhase !== 'GREETING' && (
              <div className="text-sm text-gray-400">
                {ageRange && `Age: ${ageRange.replace('_', ' ')}`}
              </div>
            )}
          </div>

          {/* Phase Timeline - Clickable phases for navigation */}
          {phaseOrder.length > 0 && (
            <div className="flex items-center gap-1 overflow-x-auto pb-2 scrollbar-thin">
              {phaseOrder.map((phase, idx) => {
                // Determine status: completed, current, or future
                let status = 'future'
                if (idx < phaseIndex) status = 'completed'
                if (idx === phaseIndex) status = 'current'

                // Check if phase is clickable (not GREETING, AGE_SELECTION, and age is selected)
                const isClickable = phase !== 'GREETING' && phase !== 'AGE_SELECTION' && ageRange && phase !== currentPhase

                return (
                  <div key={phase} className="flex items-center shrink-0">
                    {isClickable ? (
                      <button
                        onClick={() => handlePhaseClick(phase)}
                        disabled={isLoading}
                        aria-label={`Jump to ${phase.replace('_', ' ')} phase`}
                        className={`
                          px-3 py-1 rounded-full text-xs font-medium transition-all
                          focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900
                          ${status === 'completed'
                            ? 'bg-green-700 text-green-100 border border-green-600 hover:bg-green-600 focus:ring-green-500 cursor-pointer'
                            : ''}
                          ${status === 'current'
                            ? 'bg-blue-600 text-white border border-blue-500 shadow-lg shadow-blue-900/50'
                            : ''}
                          ${status === 'future'
                            ? 'bg-gray-700 text-gray-300 border border-gray-600 hover:bg-gray-600 focus:ring-gray-500 cursor-pointer'
                            : ''}
                          ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
                        `}
                      >
                        <span className="flex items-center gap-1">
                          {status === 'completed' && <span>✓</span>}
                          {phase.replace('_', ' ')}
                        </span>
                      </button>
                    ) : (
                      <div className={`
                        px-3 py-1 rounded-full text-xs font-medium transition-colors
                        ${status === 'completed' ? 'bg-green-900 text-green-300 border border-green-700' : ''}
                        ${status === 'current' ? 'bg-blue-600 text-white border border-blue-500 shadow-lg shadow-blue-900/50' : ''}
                        ${status === 'future' ? 'bg-gray-800 text-gray-500 border border-gray-700' : ''}
                        ${phase === 'GREETING' || phase === 'AGE_SELECTION' ? 'opacity-50' : ''}
                      `}>
                        <span className="flex items-center gap-1">
                          {status === 'completed' && <span>✓</span>}
                          {status === 'current' && <span className="inline-block w-2 h-2 bg-white rounded-full animate-pulse mr-1"></span>}
                          {phase.replace('_', ' ')}
                        </span>
                      </div>
                    )}
                    {idx < phaseOrder.length - 1 && (
                      <div className={`w-4 h-0.5 mx-1 ${idx < phaseIndex ? 'bg-green-600' : 'bg-gray-700'}`} />
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </nav>

      {/* Age Selection UI */}
      {showAgeSelection && (
        <div className="p-4 bg-gray-800 border-b border-gray-700">
          <h2 className="text-xl font-semibold mb-4">Select Your Age Range:</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[
              { num: "1", label: "Under 18", desc: "Your story is just beginning" },
              { num: "2", label: "18-30", desc: "Early adulthood and discovery" },
              { num: "3", label: "31-45", desc: "Building and growing" },
              { num: "4", label: "46-60", desc: "Wisdom and experience" },
              { num: "5", label: "61 and above", desc: "A lifetime of stories" },
            ].map((age) => (
              <button
                key={age.num}
                onClick={() => handleAgeSelect(age.num)}
                className="text-left p-4 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors border border-gray-600"
              >
                <div className="font-semibold text-blue-400">{age.num}. {age.label}</div>
                <div className="text-sm text-gray-300 mt-1">{age.desc}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main content area - flex container for tags sidebar and messages */}
      <div className="flex-1 overflow-hidden flex">

        {/* Tag Selection Sidebar */}
        <div className="w-64 bg-gray-800 border-r border-gray-700 overflow-y-auto p-4 flex flex-col gap-4">
          {/* Selected Tags Section */}
          <div>
            <h3 className="text-sm font-semibold text-gray-300 mb-2">Selected Themes ({selectedTags.length})</h3>
            <div className="flex flex-wrap gap-2 min-h-[60px] p-2 bg-gray-900 rounded border border-gray-600">
              {selectedTags.length === 0 ? (
                <div className="text-xs text-gray-500 italic">Click tags below to add focus areas</div>
              ) : (
                selectedTags.map(tag => (
                  <button
                    key={tag}
                    onClick={() => handleTagToggle(tag)}
                    className="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors"
                  >
                    {tag} ×
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Available Tags Section */}
          <div>
            <h3 className="text-sm font-semibold text-gray-300 mb-2">Available Themes</h3>
            <div className="flex flex-wrap gap-2">
              {AVAILABLE_TAGS.filter(tag => !selectedTags.includes(tag)).map(tag => (
                <button
                  key={tag}
                  onClick={() => handleTagToggle(tag)}
                  className="px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 text-xs rounded transition-colors"
                >
                  + {tag}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Messages Area */}
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

        {/* Right Sidebar - User Story Summary */}
        <div className="w-80 bg-gray-800 border-l border-gray-700 overflow-y-auto p-4 flex flex-col gap-4 hidden lg:flex">
          <div>
            <h3 className="text-sm font-semibold text-gray-300 mb-2">Story Summary</h3>
            <p className="text-xs text-gray-500 mb-4">Live narrative of your journey so far</p>

            <div className="p-4 rounded bg-gray-900 border border-gray-700 min-h-[200px]">
              {isSummarizing ? (
                <div className="flex items-center justify-center h-full text-gray-500 text-xs animate-pulse">
                  Updating story...
                </div>
              ) : (
                <div className="text-sm text-gray-300 font-serif leading-relaxed whitespace-pre-wrap">
                  {storySummary}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Next Phase Button - shown during interview phases */}
      {isInterviewPhase && !isLoading && (
        <div className="px-4 py-2 border-t border-gray-700">
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs text-gray-400 flex-1">
              Continue sharing about this period, or move forward when ready
            </p>
            <button
              onClick={handleNextPhase}
              className="py-2 px-4 bg-gray-700 hover:bg-gray-600 rounded text-sm text-gray-300 hover:text-white transition-colors focus:outline-none focus:ring-1 focus:ring-gray-500 flex items-center gap-2 whitespace-nowrap"
            >
              <span>Next chapter</span>
              <span>→</span>
            </button>
          </div>
        </div>
      )}

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
