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
            expect(screen.getByText(/Welcome to the Life Story Game!/i)).toBeTruthy()
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
                    phase: 'ROUTE_SELECTION',
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

    describe('Route Selection', () => {
        it('should advance to route selection after GREETING', async () => {
            const user = userEvent.setup()
            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    message: 'Here are your storytelling options...',
                    phase: 'ROUTE_SELECTION',
                }),
            })

            render(<App />)
            const input = screen.getByPlaceholderText(/Digite sua mensagem/i)
            const button = screen.getByRole('button', { name: /Enviar/i })

            await user.type(input, 'yes')
            await user.click(button)

            await waitFor(() => {
                expect(screen.getByText(/Choose Your Storytelling Approach/i)).toBeTruthy()
            })
        })
    })

    describe('Input Behavior', () => {
        it('should clear input after sending message', async () => {
            const user = userEvent.setup()
            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    message: 'Response',
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
})
