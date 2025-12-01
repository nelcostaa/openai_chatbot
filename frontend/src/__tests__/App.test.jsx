import { render, screen, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { describe, it, expect, beforeEach } from 'vitest'
import userEvent from '@testing-library/user-event'
import App from '../App'

// Mock fetch globally
global.fetch = vi.fn()

describe('App Component', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    describe('Initial Render', () => {
        it('should render the main heading', () => {
            render(<App />)
            expect(screen.getByText('Life Story Game')).toBeTruthy()
        })

        it('should display initial greeting message', () => {
            render(<App />)
            // Updated to match actual greeting in App.jsx
            expect(screen.getByText(/Welcome! I'm here to help you tell your life story/i)).toBeTruthy()
        })

        it('should show input field and send button', () => {
            render(<App />)
            expect(screen.getByPlaceholderText(/Digite sua mensagem/i)).toBeTruthy()
            expect(screen.getByRole('button', { name: /Enviar/i })).toBeTruthy()
        })
    })

    describe('Message Sending', () => {
        it('should send message when button clicked', async () => {
            const user = userEvent.setup()
            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    response: 'Great! Let me help you tell your story.',
                    model: 'gemini-2.0-flash',
                    attempts: 1,
                    phase: 'AGE_SELECTION',
                }),
            })

            render(<App />)
            const input = screen.getByPlaceholderText(/Digite sua mensagem/i)
            const button = screen.getByRole('button', { name: /Enviar/i })

            await user.type(input, 'yes')
            await user.click(button)

            await waitFor(() => {
                expect(screen.getByText(/Great! Let me help you tell your story./i)).toBeTruthy()
            })
        })
    })

    describe('Error Handling', () => {
        it('should handle network errors gracefully', async () => {
            const user = userEvent.setup()
            global.fetch.mockRejectedValueOnce(new Error('Network error'))

            render(<App />)
            const input = screen.getByPlaceholderText(/Digite sua mensagem/i)
            const button = screen.getByRole('button', { name: /Enviar/i })

            await user.type(input, 'test')
            await user.click(button)

            await waitFor(() => {
                expect(screen.getByText(/Sorry, an error occurred/i)).toBeTruthy()
            })
        })

        it('should handle API error responses', async () => {
            const user = userEvent.setup()
            global.fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                json: async () => ({ error: 'Server error' }),
            })

            render(<App />)
            const input = screen.getByPlaceholderText(/Digite sua mensagem/i)
            const button = screen.getByRole('button', { name: /Enviar/i })

            await user.type(input, 'test')
            await user.click(button)

            await waitFor(() => {
                expect(screen.getByText(/Sorry, an error occurred/i)).toBeTruthy()
            })
        })
    })

    describe('Age Selection Flow', () => {
        it('should show age selection UI after saying yes to greeting', async () => {
            const user = userEvent.setup()
            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    response: '',
                    phase: 'AGE_SELECTION',
                }),
            })

            render(<App />)
            const input = screen.getByPlaceholderText(/Digite sua mensagem/i)
            const button = screen.getByRole('button', { name: /Enviar/i })

            await user.type(input, 'yes')
            await user.click(button)

            // App shows age selection UI after GREETING -> AGE_SELECTION transition
            await waitFor(() => {
                expect(screen.getByText(/Select Your Age Range/i)).toBeTruthy()
            })
        })
    })

    describe('Input Behavior', () => {
        it('should clear input after sending message', async () => {
            const user = userEvent.setup()
            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    response: 'Response',
                    phase: 'GREETING',
                }),
            })

            render(<App />)
            const input = screen.getByPlaceholderText(/Digite sua mensagem/i)
            const button = screen.getByRole('button', { name: /Enviar/i })

            await user.type(input, 'yes')
            await user.click(button)

            await waitFor(() => {
                expect(input.value).toBe('')
            })
        })
    })

    // ============================================================
    // TDD TESTS: Per-Chapter History Tracker Feature
    // These tests define the expected behavior BEFORE implementation
    // ============================================================
    describe('Per-Chapter Summary Feature', () => {
        // Helper function to open the chapter dropdown
        const openChapterDropdown = async (user) => {
            const toggleBtn = screen.getByTestId('chapter-dropdown-toggle')
            await user.click(toggleBtn)
        }

        describe('Chapter Selection UI', () => {
            it('should display chapter selection dropdown in summary sidebar', () => {
                render(<App />)
                // Expect a dropdown/multi-select for chapter selection
                expect(screen.getByTestId('chapter-select-dropdown')).toBeTruthy()
            })

            it('should show all available interview phases as selectable options', async () => {
                const user = userEvent.setup()
                render(<App />)

                // Open dropdown first
                await openChapterDropdown(user)

                // Should show interview phases (not GREETING, AGE_SELECTION, or SYNTHESIS)
                const expectedPhases = ['FAMILY_HISTORY', 'CHILDHOOD', 'ADOLESCENCE', 'EARLY_ADULTHOOD', 'MIDLIFE', 'PRESENT']
                expectedPhases.forEach(phase => {
                    expect(screen.getByTestId(`chapter-option-${phase}`)).toBeTruthy()
                })
            })

            it('should allow selecting multiple chapters via checkboxes', async () => {
                const user = userEvent.setup()
                render(<App />)

                // Open dropdown first
                await openChapterDropdown(user)

                // Select multiple chapters
                const childhoodCheckbox = screen.getByTestId('chapter-checkbox-CHILDHOOD')
                const adolescenceCheckbox = screen.getByTestId('chapter-checkbox-ADOLESCENCE')

                await user.click(childhoodCheckbox)
                await user.click(adolescenceCheckbox)

                expect(childhoodCheckbox).toBeChecked()
                expect(adolescenceCheckbox).toBeChecked()
            })

            it('should allow deselecting chapters', async () => {
                const user = userEvent.setup()
                render(<App />)

                // Open dropdown first
                await openChapterDropdown(user)

                const childhoodCheckbox = screen.getByTestId('chapter-checkbox-CHILDHOOD')

                // Select then deselect
                await user.click(childhoodCheckbox)
                expect(childhoodCheckbox).toBeChecked()

                await user.click(childhoodCheckbox)
                expect(childhoodCheckbox).not.toBeChecked()
            })

            it('should display human-readable chapter names', async () => {
                const user = userEvent.setup()
                render(<App />)

                // Open dropdown first
                await openChapterDropdown(user)

                // Should show friendly names, not raw phase identifiers
                expect(screen.getByText(/Family History/i)).toBeTruthy()
                expect(screen.getByText(/Childhood/i)).toBeTruthy()
                expect(screen.getByText(/Adolescence/i)).toBeTruthy()
            })
        })

        describe('Generate Summary Button', () => {
            it('should not display generate summary button when no chapters selected', () => {
                render(<App />)
                expect(screen.queryByTestId('generate-chapter-summary-btn')).toBeNull()
            })

            it('should display generate button when at least one chapter is selected', async () => {
                const user = userEvent.setup()
                render(<App />)

                // Open dropdown first
                await openChapterDropdown(user)

                const childhoodCheckbox = screen.getByTestId('chapter-checkbox-CHILDHOOD')
                await user.click(childhoodCheckbox)

                const generateBtn = screen.getByTestId('generate-chapter-summary-btn')
                expect(generateBtn).toBeTruthy()
            })

            it('should show selected chapter count on button', async () => {
                const user = userEvent.setup()
                render(<App />)

                // Open dropdown first
                await openChapterDropdown(user)

                const childhoodCheckbox = screen.getByTestId('chapter-checkbox-CHILDHOOD')
                const adolescenceCheckbox = screen.getByTestId('chapter-checkbox-ADOLESCENCE')

                await user.click(childhoodCheckbox)
                await user.click(adolescenceCheckbox)

                const generateBtn = screen.getByTestId('generate-chapter-summary-btn')
                expect(generateBtn.textContent).toMatch(/2 chapters/i)
            })
        })

        describe('Summary Generation API Call', () => {
            it('should call /api/summary with selected phases when generate clicked', async () => {
                const user = userEvent.setup()
                global.fetch.mockResolvedValueOnce({
                    ok: true,
                    json: async () => ({ summary: 'Chapter-specific summary' }),
                })

                render(<App />)

                // Open dropdown first
                await openChapterDropdown(user)

                // Select chapters
                const childhoodCheckbox = screen.getByTestId('chapter-checkbox-CHILDHOOD')
                const adolescenceCheckbox = screen.getByTestId('chapter-checkbox-ADOLESCENCE')
                await user.click(childhoodCheckbox)
                await user.click(adolescenceCheckbox)

                // Wait for button to be enabled (state updated)
                const generateBtn = screen.getByTestId('generate-chapter-summary-btn')
                await waitFor(() => {
                    expect(generateBtn).not.toBeDisabled()
                })

                // Click generate
                await user.click(generateBtn)

                // Verify API was called with phases parameter
                await waitFor(() => {
                    expect(global.fetch).toHaveBeenCalledWith('/api/summary', expect.objectContaining({
                        method: 'POST',
                        body: expect.stringContaining('"phases"'),
                    }))
                })

                // Verify phases array was sent
                const fetchCall = global.fetch.mock.calls.find(call => call[0] === '/api/summary')
                const requestBody = JSON.parse(fetchCall[1].body)
                expect(requestBody.phases).toEqual(['CHILDHOOD', 'ADOLESCENCE'])
            })

            it('should display loading state while generating', async () => {
                const user = userEvent.setup()
                let resolvePromise
                global.fetch.mockReturnValueOnce(new Promise(resolve => {
                    resolvePromise = resolve
                }))

                render(<App />)

                // Open dropdown first
                await openChapterDropdown(user)

                const childhoodCheckbox = screen.getByTestId('chapter-checkbox-CHILDHOOD')
                await user.click(childhoodCheckbox)

                const generateBtn = screen.getByTestId('generate-chapter-summary-btn')
                await user.click(generateBtn)

                // Should show loading indicator (wait for state update)
                await waitFor(() => {
                    expect(screen.getByText(/Generating summary/i)).toBeTruthy()
                })

                // Resolve the promise to clean up
                resolvePromise({
                    ok: true,
                    json: async () => ({ summary: 'Test summary' }),
                })
            })

            it('should display generated summary after successful API call', async () => {
                const user = userEvent.setup()
                global.fetch.mockResolvedValueOnce({
                    ok: true,
                    json: async () => ({ summary: 'During childhood, the user experienced...' }),
                })

                render(<App />)

                // Open dropdown first
                await openChapterDropdown(user)

                const childhoodCheckbox = screen.getByTestId('chapter-checkbox-CHILDHOOD')
                await user.click(childhoodCheckbox)

                const generateBtn = screen.getByTestId('generate-chapter-summary-btn')
                await user.click(generateBtn)

                await waitFor(() => {
                    expect(screen.getByText(/During childhood, the user experienced/i)).toBeTruthy()
                })
            })

            it('should handle API errors gracefully', async () => {
                const user = userEvent.setup()
                global.fetch.mockResolvedValueOnce({
                    ok: false,
                    status: 500,
                    json: async () => ({ error: 'Summary generation failed' }),
                })

                render(<App />)

                // Open dropdown first
                await openChapterDropdown(user)

                const childhoodCheckbox = screen.getByTestId('chapter-checkbox-CHILDHOOD')
                await user.click(childhoodCheckbox)

                const generateBtn = screen.getByTestId('generate-chapter-summary-btn')
                await user.click(generateBtn)

                await waitFor(() => {
                    expect(screen.getByText(/Failed to generate summary/i)).toBeTruthy()
                })
            })
        })

        describe('Select All / Clear All Controls', () => {
            it('should have a Select All button', async () => {
                const user = userEvent.setup()
                render(<App />)

                // Open dropdown first
                await openChapterDropdown(user)

                expect(screen.getByTestId('select-all-chapters-btn')).toBeTruthy()
            })

            it('should have a Clear All button', async () => {
                const user = userEvent.setup()
                render(<App />)

                // Open dropdown first
                await openChapterDropdown(user)

                expect(screen.getByTestId('clear-all-chapters-btn')).toBeTruthy()
            })

            it('should select all chapters when Select All is clicked', async () => {
                const user = userEvent.setup()
                render(<App />)

                // Open dropdown first
                await openChapterDropdown(user)

                const selectAllBtn = screen.getByTestId('select-all-chapters-btn')
                await user.click(selectAllBtn)

                // All interview phases should be selected
                const expectedPhases = ['FAMILY_HISTORY', 'CHILDHOOD', 'ADOLESCENCE', 'EARLY_ADULTHOOD', 'MIDLIFE', 'PRESENT']
                expectedPhases.forEach(phase => {
                    const checkbox = screen.getByTestId(`chapter-checkbox-${phase}`)
                    expect(checkbox).toBeChecked()
                })
            })

            it('should deselect all chapters when Clear All is clicked', async () => {
                const user = userEvent.setup()
                render(<App />)

                // Open dropdown first
                await openChapterDropdown(user)

                // First select some
                const childhoodCheckbox = screen.getByTestId('chapter-checkbox-CHILDHOOD')
                await user.click(childhoodCheckbox)

                // Then clear all
                const clearAllBtn = screen.getByTestId('clear-all-chapters-btn')
                await user.click(clearAllBtn)

                expect(childhoodCheckbox).not.toBeChecked()
            })
        })

        describe('Integration with Phase Order', () => {
            it('should only show chapters that exist in current phaseOrder', async () => {
                const user = userEvent.setup()
                // Simulate age-based phase filtering (under_18 doesn't have MIDLIFE)
                global.fetch.mockResolvedValueOnce({
                    ok: true,
                    json: async () => ({
                        response: '',
                        phase: 'FAMILY_HISTORY',
                        phase_order: ['GREETING', 'AGE_SELECTION', 'FAMILY_HISTORY', 'CHILDHOOD', 'ADOLESCENCE', 'PRESENT', 'SYNTHESIS'],
                    }),
                })

                render(<App />)

                // Trigger phase update
                const input = screen.getByPlaceholderText(/Digite sua mensagem/i)
                const button = screen.getByRole('button', { name: /Enviar/i })
                await user.type(input, 'test')
                await user.click(button)

                // Open dropdown to access chapter options
                await openChapterDropdown(user)

                await waitFor(() => {
                    // MIDLIFE should NOT be visible (not in phase_order for under_18)
                    expect(screen.queryByTestId('chapter-option-MIDLIFE')).toBeNull()
                    // But CHILDHOOD should be
                    expect(screen.getByTestId('chapter-option-CHILDHOOD')).toBeTruthy()
                })
            })
        })
    })
})
