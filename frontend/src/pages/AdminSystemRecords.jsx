import { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { FileText, CheckCircle, RefreshCw } from 'lucide-react';

const AdminSystemRecords = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRecords();
  }, []);

  const fetchRecords = async () => {
    setLoading(true);
    try {
      const res = await axios.get('/api/admin/records');
      setData(res.data);
    } catch (error) {
      toast.error('Failed to fetch system records');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <FileText className="h-7 w-7 text-green-600 mr-2" /> System-Wide Records & History
          </h1>
          <p className="text-sm text-gray-500">
            View all generated question papers and student evaluation records across all faculty members.
          </p>
        </div>
        <button
          onClick={fetchRecords}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50"
        >
          <RefreshCw className="h-4 w-4 mr-2" /> Refresh
        </button>
      </div>

      {loading ? (
        <div className="bg-white p-12 rounded-xl border border-gray-200 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-green-600 border-t-transparent"></div>
          <p className="mt-3 text-sm text-gray-500">Loading Records...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Question Papers Section */}
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm space-y-4">
            <h2 className="text-lg font-bold text-gray-900 flex items-center">
              <FileText className="h-5 w-5 text-purple-600 mr-2" /> Recent Question Papers ({data?.recent_papers?.length || 0})
            </h2>
            <div className="divide-y divide-gray-100 text-sm">
              {data?.recent_papers?.map((paper) => (
                <div key={paper.id} className="py-3 flex items-center justify-between">
                  <div>
                    <p className="font-bold text-gray-900">{paper.subject_name}</p>
                    <p className="text-xs text-gray-500">Topics: {paper.topics} | {paper.total_marks} Marks</p>
                  </div>
                  <span className="text-xs text-gray-400">
                    {paper.created_at ? new Date(paper.created_at).toLocaleDateString() : 'N/A'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Evaluations Section */}
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm space-y-4">
            <h2 className="text-lg font-bold text-gray-900 flex items-center">
              <CheckCircle className="h-5 w-5 text-green-600 mr-2" /> Recent Evaluations ({data?.recent_evaluations?.length || 0})
            </h2>
            <div className="divide-y divide-gray-100 text-sm">
              {data?.recent_evaluations?.map((res) => (
                <div key={res.id} className="py-3 flex items-center justify-between">
                  <div>
                    <p className="font-bold text-gray-900">{res.student_name} (Roll: {res.roll_number || 'N/A'})</p>
                    <p className="text-xs text-gray-500">Score: {res.marks}/100 | Grade: {res.grade || 'N/A'}</p>
                  </div>
                  <div className="text-right">
                    <span className={`inline-block px-2 py-0.5 text-xs font-semibold rounded ${
                      res.flagged ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                    }`}>
                      {res.flagged ? 'FLAGGED' : 'CLEARED'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminSystemRecords;
