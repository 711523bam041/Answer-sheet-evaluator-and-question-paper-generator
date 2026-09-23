import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import axios from 'axios';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Results from './pages/Results';
import GeneratePaper from './pages/GeneratePaper';
import Reports from './pages/Reports';
import SimilarityReview from './pages/SimilarityReview';
import Profile from './pages/Profile';

import AdminDashboard from './pages/AdminDashboard';
import AdminUsers from './pages/AdminUsers';
import AdminActivityLogs from './pages/AdminActivityLogs';
import AdminSystemRecords from './pages/AdminSystemRecords';

import Layout from './components/Layout';
import { ProtectedRoute, AdminRoute } from './components/ProtectedRoute';

// Only set baseURL when explicitly configured (e.g., local dev with separate backend).
// In production (Render), frontend and backend share the same domain, so relative /api/* paths work.
const API_URL = import.meta.env.VITE_API_URL;
const REQUEST_TIMEOUT = parseInt(import.meta.env.VITE_REQUEST_TIMEOUT || '300000');

if (API_URL && !API_URL.includes('localhost')) {
  axios.defaults.baseURL = API_URL;
}
axios.defaults.timeout = REQUEST_TIMEOUT;

axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      error.message = 'Request timeout. Please try again.';
    }
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50 font-sans">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Faculty Protected Routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/results" element={
            <ProtectedRoute>
              <Layout>
                <Results />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/generate" element={
            <ProtectedRoute>
              <Layout>
                <GeneratePaper />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/similarity-review" element={
            <ProtectedRoute>
              <Layout>
                <SimilarityReview />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/reports" element={
            <ProtectedRoute>
              <Layout>
                <Reports />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/history" element={
            <ProtectedRoute>
              <Layout>
                <Reports />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/profile" element={
            <ProtectedRoute>
              <Layout>
                <Profile />
              </Layout>
            </ProtectedRoute>
          } />

          {/* Admin Protected Routes */}
          <Route path="/admin" element={
            <AdminRoute>
              <Layout>
                <AdminDashboard />
              </Layout>
            </AdminRoute>
          } />
          <Route path="/admin/users" element={
            <AdminRoute>
              <Layout>
                <AdminUsers />
              </Layout>
            </AdminRoute>
          } />
          <Route path="/admin/activity" element={
            <AdminRoute>
              <Layout>
                <AdminActivityLogs />
              </Layout>
            </AdminRoute>
          } />
          <Route path="/admin/records" element={
            <AdminRoute>
              <Layout>
                <AdminSystemRecords />
              </Layout>
            </AdminRoute>
          } />
        </Routes>
        <Toaster position="top-right" />
      </div>
    </Router>
  );
}

export default App;