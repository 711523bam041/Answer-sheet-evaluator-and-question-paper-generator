import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  FileText, Upload, BarChart3, LogOut, Menu, X, BookOpen,
  ShieldCheck, Users, Activity, History, UserCheck, AlertTriangle, User
} from 'lucide-react';
import toast from 'react-hot-toast';
import axios from 'axios';

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const isAdmin = user.role === 'admin';

  const handleLogout = async () => {
    try {
      await axios.post('/api/logout');
    } catch (e) {
      // Ignore error on logout call
    }
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    toast.success('Logged out successfully');
    navigate('/login');
  };

  const facultyNavItems = [
    { path: '/', icon: Upload, label: 'Dashboard & Upload' },
    { path: '/generate', icon: BookOpen, label: 'Generate Paper' },
    { path: '/results', icon: BarChart3, label: 'Evaluation Results' },
    { path: '/similarity-review', icon: AlertTriangle, label: 'Similarity Review' },
    { path: '/history', icon: History, label: 'History Archive' },
    { path: '/profile', icon: User, label: 'Profile' },
  ];

  const adminNavItems = [
    { path: '/admin', icon: ShieldCheck, label: 'Admin Overview' },
    { path: '/admin/users', icon: Users, label: 'User Management' },
    { path: '/admin/activity', icon: Activity, label: 'Activity Audit Logs' },
    { path: '/admin/records', icon: FileText, label: 'System Records' },
    { path: '/profile', icon: User, label: 'Profile' },
  ];

  const navItems = isAdmin ? adminNavItems : facultyNavItems;

  return (
    <div className="flex h-screen bg-gray-50 font-sans">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-600 text-white rounded-lg">
              <FileText className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900 leading-tight">AI Evaluator</h1>
              <span className="text-xs text-gray-500">Exam & Grading System</span>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1 rounded-md text-gray-400 hover:text-gray-500"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* User Info Card */}
        <div className="p-4 mx-3 my-3 bg-gray-50 rounded-xl border border-gray-100 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-sm">
              {user.username ? user.username.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="overflow-hidden">
              <p className="text-sm font-semibold text-gray-900 truncate">{user.username || 'User'}</p>
              <p className="text-xs text-gray-500 capitalize">{user.role || 'Faculty'}</p>
            </div>
          </div>
          <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${
            isAdmin ? 'bg-purple-100 text-purple-700' : 'bg-green-100 text-green-700'
          }`}>
            {isAdmin ? 'ADMIN' : 'FACULTY'}
          </span>
        </div>

        {/* Navigation items */}
        <nav className="mt-2 px-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors duration-200 text-sm font-medium ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 border-r-4 border-blue-700 font-semibold'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
                onClick={() => setSidebarOpen(false)}
              >
                <Icon className={`h-5 w-5 ${isActive ? 'text-blue-700' : 'text-gray-400'}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Bottom Logout Button */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t bg-white">
          <button
            onClick={handleLogout}
            className="flex items-center space-x-3 w-full px-3 py-2.5 text-red-600 hover:bg-red-50 rounded-lg transition-colors duration-200 text-sm font-medium"
          >
            <LogOut className="h-5 w-5 text-red-500" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile header */}
        <div className="lg:hidden bg-white shadow-sm border-b px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FileText className="h-6 w-6 text-blue-600" />
            <span className="font-bold text-gray-900">AI Evaluator</span>
          </div>
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
          >
            <Menu className="h-6 w-6" />
          </button>
        </div>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;