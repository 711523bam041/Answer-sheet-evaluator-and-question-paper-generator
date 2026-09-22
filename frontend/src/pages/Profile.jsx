import { useState } from 'react';
import { User, Shield, Mail, Calendar } from 'lucide-react';

const Profile = () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm space-y-6">
        <div className="flex items-center space-x-4 border-b pb-6">
          <div className="w-16 h-16 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-2xl font-bold">
            {user.username ? user.username.charAt(0).toUpperCase() : 'U'}
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{user.username}</h1>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 uppercase mt-1">
              <Shield className="w-3 h-3 mr-1" /> {user.role || 'Faculty'}
            </span>
          </div>
        </div>

        <div className="space-y-4 text-sm">
          <div className="flex items-center space-x-3 text-gray-700">
            <User className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-xs text-gray-500 font-semibold uppercase">Username</p>
              <p className="font-semibold">{user.username || 'N/A'}</p>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-gray-700">
            <Mail className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-xs text-gray-500 font-semibold uppercase">Email Address</p>
              <p className="font-semibold">{user.email || 'Not provided'}</p>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-gray-700">
            <Calendar className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-xs text-gray-500 font-semibold uppercase">Account Created</p>
              <p className="font-semibold">{user.created_at ? new Date(user.created_at).toLocaleString() : 'Active'}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
