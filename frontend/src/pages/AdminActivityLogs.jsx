import { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { Activity, RefreshCw, Filter, Clock } from 'lucide-react';

const AdminActivityLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('all');

  useEffect(() => {
    fetchLogs();
  }, [actionFilter]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`/api/admin/activity-logs?action=${actionFilter}`);
      setLogs(res.data);
    } catch (error) {
      toast.error('Failed to fetch activity audit logs');
    } finally {
      setLoading(false);
    }
  };

  const actionsList = [
    'all',
    'LOGIN',
    'LOGOUT',
    'QUESTION_PAPER_GENERATED',
    'ANSWER_KEY_GENERATED',
    'ANSWER_SHEET_UPLOADED',
    'EVALUATION_COMPLETED',
    'SIMILARITY_CHECK_COMPLETED',
    'ANSWER_FLAGGED',
    'FLAG_REVIEWED'
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <Activity className="h-7 w-7 text-blue-600 mr-2" /> Security & Audit Activity Logs
          </h1>
          <p className="text-sm text-gray-500">
            Real-time audit log of user logins, question paper generations, and evaluations.
          </p>
        </div>
        <button
          onClick={fetchLogs}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50"
        >
          <RefreshCw className="h-4 w-4 mr-2" /> Refresh
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex items-center space-x-3 overflow-x-auto">
        <div className="flex items-center space-x-2 text-sm text-gray-600 font-medium whitespace-nowrap">
          <Filter className="h-4 w-4 text-gray-400" />
          <span>Filter Action:</span>
        </div>
        <div className="flex space-x-2">
          {actionsList.map((act) => (
            <button
              key={act}
              onClick={() => setActionFilter(act)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                actionFilter === act
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {act === 'all' ? 'All Actions' : act}
            </button>
          ))}
        </div>
      </div>

      {/* Log Table */}
      {loading ? (
        <div className="bg-white p-12 rounded-xl border border-gray-200 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
          <p className="mt-3 text-sm text-gray-500">Loading Audit Logs...</p>
        </div>
      ) : logs.length === 0 ? (
        <div className="bg-white p-12 rounded-xl border border-gray-200 text-center text-gray-500">
          No audit logs recorded for this action.
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Timestamp</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">User</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Role</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Action</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 font-mono text-xs">
                {logs.map((logItem) => (
                  <tr key={logItem.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                      {logItem.created_at ? new Date(logItem.created_at).toLocaleString() : 'N/A'}
                    </td>
                    <td className="px-4 py-3 font-semibold text-gray-900">{logItem.username}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 text-gray-700 uppercase">
                        {logItem.user_role}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">
                        {logItem.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {logItem.details ? JSON.stringify(logItem.details) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminActivityLogs;
