import api from './api'

export const getCurrentModel = () => api.get('/model/current')

export const getModelVersions = () => api.get('/model/versions')

export const getModelAccuracy = () => api.get('/model/accuracy')
