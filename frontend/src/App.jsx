import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ComplaintsPage from './pages/ComplaintsPage';
import ComplaintDetailPage from './pages/ComplaintDetailPage';
import MyAssignedPage from './pages/MyAssignedPage';
import DepartmentsPage from './pages/DepartmentsPage';
import TeamsPage from './pages/TeamsPage';
import AgentsPage from './pages/AgentsPage';
import AnalyticsPage from './pages/AnalyticsPage';
import AIAssistantPage from './pages/AIAssistantPage';
import KnowledgeBasePage from './pages/KnowledgeBasePage';
import AIPlaygroundPage from './pages/AIPlaygroundPage';
import GmailSyncPage from './pages/GmailSyncPage';
import NotificationsPage from './pages/NotificationsPage';
import AuditLogsPage from './pages/AuditLogsPage';
import SettingsPage from './pages/SettingsPage';

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          {/* Main 14 Pages */}
          <Route index element={<DashboardPage />} />
          <Route path="complaints" element={<ComplaintsPage />} />
          <Route path="complaints/:id" element={<ComplaintDetailPage />} />
          <Route path="my-assigned" element={<MyAssignedPage />} />
          <Route path="departments" element={<DepartmentsPage />} />
          <Route path="teams" element={<TeamsPage />} />
          <Route path="agents" element={<AgentsPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="ai-assistant" element={<AIAssistantPage />} />
          <Route path="knowledge-base" element={<KnowledgeBasePage />} />
          <Route path="notifications" element={<NotificationsPage />} />
          <Route path="audit-logs" element={<AuditLogsPage />} />
          <Route path="settings" element={<SettingsPage />} />

          {/* Interactive Lab & Ingestion */}
          <Route path="ai-playground" element={<AIPlaygroundPage />} />
          <Route path="gmail" element={<GmailSyncPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
