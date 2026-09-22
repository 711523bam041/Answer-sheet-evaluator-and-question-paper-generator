import { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { Users, UserCheck, UserX, Shield, RefreshCw } from 'lucide-react';

const AdminUsers = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await axios.get('/api/admin/users');
      setUsers(res.data);
    } catch (error) {
      toast.error('Failed to fetch user list');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleStatus = async (userId, currentUsername) => {
    try {
      const res = await axios.post(`/api/admin/users/${userId}/toggle-status`);
      toast.success(res.data.message);
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Failed to update user status');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <Users className="h-7 w-7 text-purple-600 mr-2" /> User Account Management
          </h1>
          <p className="text-sm text-gray-500">
            View registered faculty members and manage active/inactive status.
          </p>
        </div>
        <button
          onClick={fetchUsers}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50"
        >
          <RefreshCw className="h-4 w-4 mr-2" /> Refresh
        </button>
      </div>

      {loading ? (
        <div className="bg-white p-12 rounded-xl border border-gray-200 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-purple-600 border-t-transparent"></div>
          <p className="mt-3 text-sm text-gray-500">Loading User Accounts...</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">ID</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Username</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Email</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Role</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Status</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Created At</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-600">Account Control</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-gray-500">#{u.id}</td>
                    <td className="px-4 py-3 font-semibold text-gray-900">{u.username}</td>
                    <td className="px-4 py-3 text-gray-600">{u.email || 'N/A'}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        u.role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'
                      }`}>
                        {u.role === 'admin' && <Shield className="w-3 h-3 mr-1" />}
                        {u.role.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {u.is_active ? 'Active' : 'Disabled'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {u.created_at ? new Date(u.created_at).toLocaleString() : 'N/A'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {u.role !== 'admin' && (
                        <button
                          onClick={() => handleToggleStatus(u.id, u.username)}
                          className={`inline-flex items-center px-2.5 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                            u.is_active
                              ? 'bg-red-50 text-red-700 hover:bg-red-100 border border-red-200'
                              : 'bg-green-50 text-green-700 hover:bg-green-100 border border-green-200'
                          }`}
                        >
                          {u.is_active ? (
                            <>
                              <UserX className="w-3.5 h-3.5 mr-1" /> Disable Account
                            </>
                          ) : (
                            <>
                              <UserCheck className="w-3.5 h-3.5 mr-1" /> Enable Account
                            </>
                          )}
                        </button>
                      )}
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

export default AdminUsers;
