import { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { AlertTriangle, CheckCircle, XCircle, Clock, Eye, Filter, RefreshCw } from 'lucide-react';

const SimilarityReview = () => {
  const [flags, setFlags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedFlag, setSelectedFlag] = useState(null);
  const [reviewComments, setReviewComments] = useState('');
  const [reviewStatus, setReviewStatus] = useState('Cleared');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchFlags();
  }, [filterStatus]);

  const fetchFlags = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`/api/similarity-flags?status=${filterStatus}`);
      setFlags(res.data);
    } catch (error) {
      toast.error('Failed to load similarity flags');
    } finally {
      setLoading(false);
    }
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFlag) return;

    setSubmitting(true);
    try {
      await axios.post(`/api/similarity-flags/${selectedFlag.id}/review`, {
        status: reviewStatus,
        comments: reviewComments
      });
      toast.success(`Flag updated to ${reviewStatus}`);
      setSelectedFlag(null);
      setReviewComments('');
      fetchFlags();
    } catch (error) {
      toast.error('Failed to update flag review status');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Cleared':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800"><CheckCircle className="w-3 h-3 mr-1" /> Cleared</span>;
      case 'Confirmed':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800"><XCircle className="w-3 h-3 mr-1" /> Plagiarism Confirmed</span>;
      case 'Reviewed':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800"><CheckCircle className="w-3 h-3 mr-1" /> Reviewed</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800"><Clock className="w-3 h-3 mr-1" /> Pending Review</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Student Similarity & Plagiarism Review</h1>
          <p className="text-sm text-gray-500">
            Review pairwise student answer similarities and make official faculty determinations.
          </p>
        </div>
        <button
          onClick={fetchFlags}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50"
        >
          <RefreshCw className="h-4 w-4 mr-2" /> Refresh List
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex items-center space-x-4">
        <div className="flex items-center space-x-2 text-sm text-gray-600 font-medium">
          <Filter className="h-4 w-4 text-gray-400" />
          <span>Filter by Review Status:</span>
        </div>
        <div className="flex space-x-2">
          {['all', 'Pending Review', 'Cleared', 'Confirmed'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                filterStatus === st
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {st === 'all' ? 'All Flags' : st}
            </button>
          ))}
        </div>
      </div>

      {/* Flags Table */}
      {loading ? (
        <div className="bg-white p-12 rounded-xl border border-gray-200 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
          <p className="mt-3 text-sm text-gray-500">Loading similarity flags...</p>
        </div>
      ) : flags.length === 0 ? (
        <div className="bg-white p-12 rounded-xl border border-gray-200 text-center">
          <AlertTriangle className="mx-auto h-12 w-12 text-gray-300" />
          <h3 className="mt-2 text-base font-semibold text-gray-900">No similarity flags found</h3>
          <p className="mt-1 text-sm text-gray-500">No student answer sheets have exceeded similarity thresholds under this filter.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Student 1</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Student 2 / Reference</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Similarity</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Flag Reason & Snippet</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Status</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-600">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {flags.map((flag) => (
                  <tr key={flag.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-semibold text-gray-900">{flag.student1_name}</td>
                    <td className="px-4 py-3 font-medium text-gray-700">{flag.student2_name}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${
                        flag.similarity_percentage >= 80 ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {flag.similarity_percentage}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600 max-w-xs truncate" title={flag.flag_reason}>
                      {flag.flag_reason}
                    </td>
                    <td className="px-4 py-3">{getStatusBadge(flag.review_status)}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => {
                          setSelectedFlag(flag);
                          setReviewStatus(flag.review_status === 'Pending Review' ? 'Cleared' : flag.review_status);
                          setReviewComments(flag.reviewer_comments || '');
                        }}
                        className="inline-flex items-center px-2.5 py-1.5 border border-blue-600 text-blue-600 hover:bg-blue-50 text-xs font-semibold rounded-md"
                      >
                        <Eye className="w-3.5 h-3.5 mr-1" /> Review Flag
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Review Modal */}
      {selectedFlag && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="bg-white max-w-lg w-full rounded-2xl p-6 shadow-2xl space-y-4">
            <h2 className="text-xl font-bold text-gray-900 flex items-center">
              <AlertTriangle className="text-yellow-500 mr-2 h-6 w-6" /> Review Similarity Flag
            </h2>

            <div className="bg-gray-50 p-4 rounded-xl border text-sm space-y-2">
              <div><span className="font-semibold">Student 1:</span> {selectedFlag.student1_name}</div>
              <div><span className="font-semibold">Compared With:</span> {selectedFlag.student2_name}</div>
              <div><span className="font-semibold">Similarity Percentage:</span> <span className="font-bold text-red-600">{selectedFlag.similarity_percentage}%</span></div>
              <div><span className="font-semibold">System Flag Reason:</span> {selectedFlag.flag_reason}</div>
            </div>

            <form onSubmit={handleReviewSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Faculty Determination
                </label>
                <select
                  value={reviewStatus}
                  onChange={(e) => setReviewStatus(e.target.value)}
                  className="w-full py-2 px-3 border border-gray-300 rounded-lg text-sm bg-white font-medium"
                >
                  <option value="Cleared">Cleared (Coincidental / Acceptable)</option>
                  <option value="Confirmed">Confirmed Plagiarism (Flagged)</option>
                  <option value="Reviewed">Reviewed (General Note)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Faculty Review Comments
                </label>
                <textarea
                  rows="3"
                  value={reviewComments}
                  onChange={(e) => setReviewComments(e.target.value)}
                  placeholder="Enter specific notes or explanation for your determination..."
                  className="w-full p-2.5 border border-gray-300 rounded-lg text-sm"
                ></textarea>
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedFlag(null)}
                  className="px-4 py-2 border text-sm font-medium rounded-lg text-gray-600 hover:bg-gray-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {submitting ? 'Saving...' : 'Save Review Determination'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SimilarityReview;
