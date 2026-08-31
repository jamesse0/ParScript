import { api } from '../lib/api'

export const getProblems = (difficulty) =>
  api(`/problems${difficulty ? `?difficulty=${difficulty}` : ''}`)

export const getProblem = (problemId) => api(`/problems/${problemId}`)
