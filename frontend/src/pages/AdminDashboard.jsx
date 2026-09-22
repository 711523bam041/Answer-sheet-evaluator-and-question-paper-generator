import { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { Users, FileText, CheckCircle, AlertTriangle, ShieldCheck, Activity } from 'lucide-react';
import { Link } from 'react-router-dom';

const AdminDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRecords();
  }, []);

  const fetchRecords = async () => {
    try {
      const res = await axios.get('/api/admin/records');
      setData(res.data);
    } catch (error) {
      toast.error('Failed to load system records');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-purple-600 border-t-transparent"></div>
        <p className="mt-3 text-sm text-gray-500">Loading System Metrics...</p>
      </div>
    );
  }

  const stats = data?.stats || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <ShieldCheck className="h-7 w-7 text-purple-600 mr-2" /> Administrator Dashboard
          </h1>
          <p className="text-sm text-gray-500">
            System overview, user management, and security audit logs.
          </p>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase">Registered Users</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{stats.total_users || 0}</p>
          </div>
          <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
            <Users className="h-6 w-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase">Question Papers</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{stats.total_papers || 0}</p>
          </div>
          <div className="p-3 bg-purple-50 text-purple-600 rounded-xl">
            <FileText className="h-6 w-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase">Total Evaluations</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{stats.total_evaluations || 0}</p>
          </div>
          <div className="p-3 bg-green-50 text-green-600 rounded-xl">
            <CheckCircle className="h-6 w-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase">Flagged Submissions</p>
            <p className="text-2xl font-bold text-red-600 mt-1">{stats.total_flagged || 0}</p>
          </div>
          <div className="p-3 bg-red-50 text-red-600 rounded-xl">
            <AlertTriangle className="h-6 w-6" />
          </div>
        </div>
      </div>

      {/* Quick Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link to="/admin/users" className="bg-white p-5 rounded-xl border border-gray-200 hover:border-purple-300 transition-colors shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-purple-100 text-purple-700 rounded-xl">
            <Users className="h-6 w-6" />
          </div>
          <div>
            <h3 className="font-bold text-gray-900">User Management</h3>
            <p className="text-xs text-gray-500">View faculty & enable/disable accounts</p>
          </div>
        </Link>

        <Link to="/admin/activity" className="bg-white p-5 rounded-xl border border-gray-200 hover:border-purple-300 transition-colors shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-blue-100 text-blue-700 rounded-xl">
            <Activity className="h-6 w-6" />
          </div>
          <div>
            <h3 className="font-bold text-gray-900">Audit Activity Logs</h3>
            <p className="text-xs text-gray-500">Inspect system actions & login history</p>
          </div>
        </Link>

        <Link to="/admin/records" className="bg-white p-5 rounded-xl border border-gray-200 hover:border-purple-300 transition-colors shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-green-100 text-green-700 rounded-xl">
            <FileText className="h-6 w-6" />
          </div>
          <div>
            <h3 className="font-bold text-gray-900">System Records</h3>
            <p className="text-xs text-gray-500">Inspect papers & evaluation records</p>
          </div>
        </Link>
      </div>
    </div>
  );
};

export default AdminDashboard;
