import { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { Download, Search, Filter, AlertTriangle, RefreshCw, TrendingUp, Users, CheckCircle, AlertCircle, X } from 'lucide-react';

const Results = () => {
  const [results, setResults] = useState([]);
  const [filteredResults, setFilteredResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('student_name');
  const [sortOrder, setSortOrder] = useState('asc');
  const [showFlagged, setShowFlagged] = useState(false);
  const [activeTab, setActiveTab] = useState('grading'); // 'grading' or 'flags'
  
  // Review form states
  const [reviewStatus, setReviewStatus] = useState('Pending Review');
  const [reviewComments, setReviewComments] = useState('');
  const [reviewMarks, setReviewMarks] = useState('');
  
  // Side-by-side comparison state
  const [compareData, setCompareData] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [hoveredSentenceIdx, setHoveredSentenceIdx] = useState(null);
  const [hoveredSource, setHoveredSource] = useState(null);
  
  // Interactive Scorecard details state
  const [selectedResult, setSelectedResult] = useState(null);

  const [stats, setStats] = useState({
    total: 0,
    average: 0,
    flagged: 0,
    passRate: 0,
    avgSimilarity: 0,
    highestScore: 0,
    lowestScore: 0
  });

  useEffect(() => {
    fetchResults();
  }, []);

  useEffect(() => {
    filterAndSortResults();
    calculateStats();
  }, [results, searchTerm, sortBy, sortOrder, showFlagged, activeTab]);

  useEffect(() => {
    if (selectedResult) {
      setReviewStatus(selectedResult.review_status || 'Pending Review');
      setReviewComments(selectedResult.reviewer_comments || '');
      setReviewMarks(selectedResult.marks !== undefined ? selectedResult.marks.toString() : '');
      setCompareData(null); // Clear comparison when result shifts
    }
  }, [selectedResult]);

  const handleReviewSubmit = async (resultId, status, comments, marks = null) => {
    try {
      const payload = { status, comments };
      if (marks !== null && marks !== '') {
        payload.marks = parseFloat(marks);
      }
      const response = await axios.post(`/api/results/${resultId}/review`, payload);
      toast.success(`Review decision submitted: ${status}`);
      // Update local state
      setResults(prev => prev.map(r => r.id === resultId ? response.data : r));
      setSelectedResult(response.data);
      setCompareData(null); // Return to scorecard on success
      fetchResults();
    } catch (error) {
      console.error(error);
      toast.error(error.response?.data?.message || 'Failed to submit review');
    }
  };

  const handleStartComparison = async (params) => {
    setCompareLoading(true);
    setCompareData(null);
    try {
      const queryParams = new URLSearchParams(params).toString();
      const response = await axios.get(`/api/results/${selectedResult.id}/compare?${queryParams}`);
      setCompareData(response.data);
    } catch (error) {
      console.error(error);
      toast.error('Failed to load comparison data');
    } finally {
      setCompareLoading(false);
    }
  };

  const handleSentenceHover = (index, source) => {
    if (index === null) {
      setHoveredSentenceIdx(null);
      setHoveredSource(null);
      return;
    }
    setHoveredSentenceIdx(index);
    setHoveredSource(source);
  };

  const getSentenceMatch = (index, source) => {
    if (!compareData || !compareData.matches) return null;
    if (source === 'a') {
      return compareData.matches.find(m => m.a_idx === index);
    } else {
      return compareData.matches.find(m => m.b_idx === index);
    }
  };

  const fetchResults = async () => {
    try {
      const response = await axios.get('/api/results');
      setResults(response.data);
    } catch (error) {
      toast.error('Failed to fetch results');
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = () => {
    if (results.length === 0) {
      setStats({
        total: 0,
        average: 0,
        flagged: 0,
        passRate: 0,
        avgSimilarity: 0,
        highestScore: 0,
        lowestScore: 0
      });
      return;
    }

    const total = results.length;
    const average = (results.reduce((sum, r) => sum + r.marks, 0) / total).toFixed(1);
    const flagged = results.filter(r => r.flagged).length;
    const passed = results.filter(r => r.marks >= 60).length;
    const passRate = ((passed / total) * 100).toFixed(1);
    const avgSimilarity = (results.reduce((sum, r) => sum + r.similarity, 0) / total).toFixed(1);
    const highestScore = Math.max(...results.map(r => r.marks));
    const lowestScore = Math.min(...results.map(r => r.marks));

    setStats({
      total,
      average,
      flagged,
      passRate,
      avgSimilarity,
      highestScore,
      lowestScore
    });
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchResults();
    setRefreshing(false);
    toast.success('Results refreshed');
  };

  const filterAndSortResults = () => {
    let filtered = results.filter(result => {
      const matchesSearch = 
        (result.student_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (result.filename || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (result.feedback || '').toLowerCase().includes(searchTerm.toLowerCase());
      const matchesTab = activeTab === 'flags' ? result.flagged : true;
      const matchesFlag = !showFlagged || result.flagged;
      return matchesSearch && matchesTab && matchesFlag;
    });

    filtered.sort((a, b) => {
      let aVal = sortBy === 'student_name' ? (a.student_name || '').toLowerCase() : a[sortBy];
      let bVal = sortBy === 'student_name' ? (b.student_name || '').toLowerCase() : b[sortBy];

      if (sortBy === 'marks' || sortBy === 'similarity') {
        aVal = parseFloat(aVal) || 0;
        bVal = parseFloat(bVal) || 0;
      }

      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
      } else {
        return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
      }
    });

    setFilteredResults(filtered);
  };

  const handleDownload = async (format) => {
    try {
      const response = await axios.get(`/api/download_${format}`, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `evaluation_results.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success(`Downloaded ${format.toUpperCase()}`);
    } catch (error) {
      toast.error(`Failed to download ${format.toUpperCase()}`);
    }
  };

  const getScoreBadgeColor = (score) => {
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getProgressColor = (score) => {
    if (score >= 80) return 'bg-green-600';
    if (score >= 60) return 'bg-yellow-600';
    return 'bg-red-600';
  };

  const getGradeBadgeColor = (grade) => {
    if (!grade) return 'bg-gray-100 text-gray-800';
    const g = grade.toUpperCase();
    if (g.startsWith('A')) return 'bg-green-100 text-green-800';
    if (g.startsWith('B')) return 'bg-purple-100 text-purple-800';
    if (g.startsWith('C')) return 'bg-blue-100 text-blue-800';
    if (g.startsWith('D')) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const StatCard = ({ icon: Icon, label, value, subtitle, color }) => (
    <div className="bg-white rounded-lg shadow-sm p-6 border-l-4 border-gray-200" style={{ borderColor: color }}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className="p-3 rounded-lg" style={{ backgroundColor: `${color}20` }}>
          <Icon className="h-6 w-6" style={{ color }} />
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 font-sans">Loading results...</p>
        </div>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-12 text-center border border-gray-200">
        <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Results Yet</h3>
        <p className="text-gray-600">
          Upload and evaluate answer sheets from the Dashboard to see results here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">Evaluation Results</h1>
          <p className="text-sm text-gray-600 mt-1">{results.length} total evaluations</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => handleDownload('csv')}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
          >
            <Download className="h-4 w-4 mr-2" />
            CSV
          </button>
          <button
            onClick={() => handleDownload('pdf')}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
          >
            <Download className="h-4 w-4 mr-2" />
            PDF
          </button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={Users}
          label="Total Evaluations"
          value={stats.total}
          color="#3B82F6"
        />
        <StatCard
          icon={TrendingUp}
          label="Average Score"
          value={`${stats.average}/100`}
          subtitle={`Range: ${stats.lowestScore}-${stats.highestScore}`}
          color="#10B981"
        />
        <StatCard
          icon={CheckCircle}
          label="Pass Rate"
          value={`${stats.passRate}%`}
          subtitle={`Marks ≥ 60`}
          color="#8B5CF6"
        />
        <StatCard
          icon={AlertCircle}
          label="Flagged"
          value={stats.flagged}
          subtitle={`${((stats.flagged / stats.total) * 100).toFixed(1)}% of total`}
          color="#EF4444"
        />
      </div>

      {/* Advanced Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Score Distribution</h3>
          <div className="space-y-3">
            {[
              { label: 'Excellent (80+)', range: [80, 100], color: 'bg-green-600' },
              { label: 'Good (60-79)', range: [60, 79], color: 'bg-yellow-600' },
              { label: 'Poor (<60)', range: [0, 59], color: 'bg-red-600' }
            ].map(({ label, range, color }) => {
              const count = results.filter(r => r.marks >= range[0] && r.marks <= range[1]).length;
              const percentage = ((count / results.length) * 100).toFixed(1);
              return (
                <div key={label}>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">{label}</span>
                    <span className="text-sm font-semibold text-gray-900">{count} ({percentage}%)</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className={`${color} h-2 rounded-full`} style={{ width: `${percentage}%` }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Plagiarism Statistics</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Average Similarity</span>
                <span className="text-sm font-semibold text-gray-900">{stats.avgSimilarity}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${stats.avgSimilarity}%` }}
                ></div>
              </div>
            </div>
            <div className="border-t pt-4 border-gray-100">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Flagged for Plagiarism</span>
                <span className="text-2xl font-bold text-red-600">{stats.flagged}</span>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {stats.flagged === 0 ? 'No plagiarism detected' : `${((stats.flagged / stats.total) * 100).toFixed(1)}% of submissions`}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters Section */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Filter className="h-5 w-5 mr-2 text-gray-600" />
          Filters & Search
        </h3>
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by name, filename, or feedback..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500 focus:outline-none bg-white"
              >
                <option value="student_name">Sort by Student Name</option>
                <option value="marks">Sort by Score</option>
                <option value="similarity">Sort by Similarity</option>
                <option value="created_at">Sort by Date</option>
              </select>

              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 text-sm"
                title={sortOrder === 'asc' ? 'Ascending' : 'Descending'}
              >
                {sortOrder === 'asc' ? '↑' : '↓'}
              </button>

              <label className="flex items-center text-sm cursor-pointer whitespace-nowrap">
                <input
                  type="checkbox"
                  checked={showFlagged}
                  onChange={(e) => setShowFlagged(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-gray-700">Flagged only</span>
              </label>
            </div>
          </div>

          {filteredResults.length !== results.length && (
            <p className="text-sm text-gray-600">
              Showing {filteredResults.length} of {results.length} results
            </p>
          )}
        </div>
      </div>

      {/* Tab controls */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => { setActiveTab('grading'); setShowFlagged(false); }}
          className={`py-3 px-6 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'grading'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          Grading Results
        </button>
        <button
          onClick={() => { setActiveTab('flags'); }}
          className={`py-3 px-6 text-sm font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === 'flags'
              ? 'border-red-600 text-red-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          <AlertTriangle className="h-4 w-4" />
          Flag Dashboard
          {results.filter(r => r.flagged).length > 0 && (
            <span className="ml-1 bg-red-100 text-red-800 text-xs font-bold px-2 py-0.5 rounded-full">
              {results.filter(r => r.flagged).length}
            </span>
          )}
        </button>
      </div>

      {/* Results Table */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden border border-gray-200">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              {activeTab === 'flags' ? (
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Student Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Roll Number
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Similarity %
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Flag Reason(s)
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Review Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              ) : (
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Student Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    File
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Grade
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Similarity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Feedback
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              )}
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredResults.map((result) => {
                if (activeTab === 'flags') {
                  const reasons = result.flag_details?.reasons || [];
                  return (
                    <tr 
                      key={result.id} 
                      onClick={() => setSelectedResult(result)}
                      className="cursor-pointer hover:bg-gray-50 transition-colors"
                      title="Click to audit/review flagged sheet"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <AlertTriangle className="h-4 w-4 text-red-500 mr-2 flex-shrink-0" />
                          <span className="text-sm font-semibold text-gray-900">
                            {result.student_name || 'Unknown'}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {result.roll_number || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                        {result.similarity}%
                      </td>
                      <td className="px-6 py-4 text-xs text-gray-700 max-w-md truncate" title={reasons.join(' | ')}>
                        {reasons.length > 0 ? reasons.join(' | ') : 'High similarity match'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2.5 py-1 text-xs font-bold rounded-full ${
                          result.review_status === 'Approved' ? 'bg-green-100 text-green-800' :
                          result.review_status === 'Rejected' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {result.review_status || 'Pending Review'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600 font-semibold hover:underline">
                        Review
                      </td>
                    </tr>
                  );
                } else {
                  return (
                    <tr 
                      key={result.id} 
                      onClick={() => setSelectedResult(result)}
                      className={`cursor-pointer transition-colors ${result.flagged ? 'bg-red-50 hover:bg-red-100' : 'hover:bg-gray-50'}`}
                      title="Click to view detailed grading scorecard and raw OCR text"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {result.flagged && (
                            <AlertTriangle className="h-4 w-4 text-red-500 mr-2 flex-shrink-0" />
                          )}
                          <span className="text-sm font-medium text-gray-900">
                            {result.student_name || 'Unknown'}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 truncate max-w-xs" title={result.filename}>
                        {result.filename}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 min-w-[100px] bg-gray-200 rounded-full h-2">
                            <div
                              className={`${getProgressColor(result.marks)} h-2 rounded-full transition-all`}
                              style={{ width: `${result.marks}%` }}
                            ></div>
                          </div>
                          <span className={`text-sm font-bold px-2 py-1 rounded ${getScoreBadgeColor(result.marks)}`}>
                            {result.marks}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2.5 py-1 text-xs font-bold rounded-full ${getGradeBadgeColor(result.grade)}`}>
                          {result.grade || 'N/A'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-gray-900">
                            {result.similarity}%
                          </span>
                          <div className="w-12 h-2 bg-gray-200 rounded-full">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${Math.min(result.similarity, 100)}%` }}
                            ></div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate" title={result.feedback}>
                        {result.feedback}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {result.flagged ? (
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            ⚠ Flagged
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            ✓ Clear
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                }
              })}
            </tbody>
          </table>
        </div>

        {filteredResults.length === 0 && (
          <div className="text-center py-12">
            <AlertTriangle className="h-8 w-8 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-600">No results match your filters</p>
          </div>
        )}
      </div>

      {/* Detailed Scorecard Modal Overlay */}
      {selectedResult && (
        <div className="fixed inset-0 z-50 overflow-y-auto flex items-center justify-center p-4 bg-black bg-opacity-50 font-sans">
          <div className="bg-white rounded-xl shadow-2xl border border-gray-200 max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            
            {/* Modal Header */}
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
              <div>
                <h3 className="text-lg font-bold text-gray-900">{selectedResult.student_name}</h3>
                <p className="text-xs text-gray-500 mt-0.5">Filename: {selectedResult.filename}</p>
              </div>
              <button
                onClick={() => setSelectedResult(null)}
                className="p-1 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-150 transition-colors"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 p-6 overflow-y-auto space-y-6">
              {compareLoading ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
                  <p className="text-xs text-gray-500 font-medium font-sans">Running sentence-level semantic alignment...</p>
                </div>
              ) : compareData ? (
                <div className="space-y-6 animate-in fade-in zoom-in-95 duration-200">
                  {/* Compare Header Controls */}
                  <div className="flex justify-between items-center bg-gray-50 border border-gray-200 rounded-lg p-3">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Comparing Student Sheet</span>
                      <h4 className="text-sm font-extrabold text-gray-900">{selectedResult.student_name}</h4>
                    </div>
                    <button
                      type="button"
                      onClick={() => setCompareData(null)}
                      className="px-3 py-1.5 bg-white border border-gray-300 rounded-lg text-xs font-bold hover:bg-gray-50 transition-colors shadow-sm"
                    >
                      ← Back to Scorecard
                    </button>
                  </div>

                  {/* Side-by-side splits */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Panel A (Left) */}
                    <div className="space-y-2">
                      <div className="flex justify-between items-center px-1">
                        <span className="text-xs font-bold text-gray-700 uppercase tracking-wide">
                          Student Sheet Text ({compareData.sentences_a.length} sentences)
                        </span>
                        <span className="text-[10px] text-gray-400 font-medium">Hover matched text to trace peer source</span>
                      </div>
                      <div className="h-[40vh] overflow-y-auto border border-gray-250 rounded-xl p-4 bg-white shadow-inner space-y-2 leading-relaxed text-xs">
                        {compareData.sentences_a.map((sent, idx) => {
                          const match = getSentenceMatch(idx, 'a');
                          const isMatched = !!match;
                          const isActive = (hoveredSource === 'a' && hoveredSentenceIdx === idx) || 
                                           (hoveredSource === 'b' && getSentenceMatch(hoveredSentenceIdx, 'b')?.a_idx === idx);
                          
                          let bgClass = "text-gray-800 transition-all duration-150 py-0.5 px-1 rounded ";
                          if (isActive) {
                            bgClass += "bg-red-200 text-red-950 font-bold border-l-2 border-red-600 scale-[1.01] shadow-sm";
                          } else if (isMatched) {
                            bgClass += "bg-red-50 hover:bg-red-100 text-gray-950 cursor-pointer border-b border-dashed border-red-300";
                          }
                          
                          return (
                            <span 
                              key={idx}
                              className={`inline-block mr-1.5 ${bgClass}`}
                              onMouseEnter={() => handleSentenceHover(idx, 'a')}
                              onMouseLeave={() => handleSentenceHover(null, null)}
                              title={isMatched ? `Match: ${match.similarity}% Similarity` : ""}
                            >
                              {sent}
                            </span>
                          );
                        })}
                      </div>
                    </div>

                    {/* Panel B (Right) */}
                    <div className="space-y-2">
                      <div className="flex justify-between items-center px-1">
                        <span className="text-xs font-bold text-gray-700 uppercase tracking-wide">
                          Matched Reference: {compareData.target_name} ({compareData.sentences_b.length} sentences)
                        </span>
                      </div>
                      <div className="h-[40vh] overflow-y-auto border border-gray-250 rounded-xl p-4 bg-white shadow-inner space-y-2 leading-relaxed text-xs">
                        {compareData.sentences_b.map((sent, idx) => {
                          const match = getSentenceMatch(idx, 'b');
                          const isMatched = !!match;
                          const isActive = (hoveredSource === 'b' && hoveredSentenceIdx === idx) || 
                                           (hoveredSource === 'a' && getSentenceMatch(hoveredSentenceIdx, 'a')?.b_idx === idx);
                          
                          let bgClass = "text-gray-800 transition-all duration-150 py-0.5 px-1 rounded ";
                          if (isActive) {
                            bgClass += "bg-red-200 text-red-950 font-bold border-l-2 border-red-600 scale-[1.01] shadow-sm";
                          } else if (isMatched) {
                            bgClass += "bg-red-50 hover:bg-red-100 text-gray-950 cursor-pointer border-b border-dashed border-red-300";
                          }
                          
                          return (
                            <span 
                              key={idx}
                              className={`inline-block mr-1.5 ${bgClass}`}
                              onMouseEnter={() => handleSentenceHover(idx, 'b')}
                              onMouseLeave={() => handleSentenceHover(null, null)}
                              title={isMatched ? `Match: ${match.similarity}% Similarity` : ""}
                            >
                              {sent}
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  </div>

                  {/* Override Form */}
                  <div className="p-4 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 shadow-sm space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs uppercase tracking-wider text-gray-700">✍️ Faculty Audit & Override Decisions</span>
                      <span className={`px-2.5 py-0.5 text-[10px] font-bold rounded-full uppercase tracking-wide ${
                        reviewStatus === 'Approved' ? 'bg-green-100 text-green-800 border border-green-200' :
                        reviewStatus === 'Rejected' ? 'bg-red-100 text-red-800 border border-red-200' :
                        'bg-yellow-100 text-yellow-800 border border-yellow-200'
                      }`}>
                        {reviewStatus}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-sans">
                      <div>
                        <label className="block font-bold text-gray-600 uppercase tracking-[0.05em] text-[10px] mb-1.5">Override Marks (0-100):</label>
                        <input
                          type="number"
                          value={reviewMarks}
                          onChange={(e) => setReviewMarks(e.target.value)}
                          placeholder="Assign custom marks..."
                          min="0"
                          max="100"
                          className="w-full px-3 py-1.5 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 font-sans text-xs font-bold"
                        />
                      </div>

                      <div>
                        <label className="block font-bold text-gray-600 uppercase tracking-[0.05em] text-[10px] mb-1.5">Update Status:</label>
                        <div className="flex gap-1.5">
                          {['Pending Review', 'Approved', 'Rejected'].map((statusOption) => (
                            <button
                              key={statusOption}
                              type="button"
                              onClick={() => setReviewStatus(statusOption)}
                              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all border ${
                                reviewStatus === statusOption
                                  ? statusOption === 'Approved' ? 'bg-green-600 text-white border-green-600 shadow-sm' :
                                    statusOption === 'Rejected' ? 'bg-red-600 text-white border-red-600 shadow-sm' :
                                    'bg-yellow-500 text-white border-yellow-500 shadow-sm'
                                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'
                              }`}
                            >
                              {statusOption === 'Pending Review' ? 'Hold' : statusOption}
                            </button>
                          ))}
                        </div>
                      </div>
                      
                      <div>
                        <label className="block font-bold text-gray-600 uppercase tracking-[0.05em] text-[10px] mb-1.5">Reviewer Comments:</label>
                        <textarea
                          value={reviewComments}
                          onChange={(e) => setReviewComments(e.target.value)}
                          placeholder="Type auditor notes or comments..."
                          rows={2}
                          className="w-full px-3 py-1.5 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 font-sans text-xs"
                        />
                      </div>
                    </div>
                    
                    <div className="flex justify-end pt-2 border-t border-gray-200">
                      <button
                        type="button"
                        onClick={() => handleReviewSubmit(selectedResult.id, reviewStatus, reviewComments, reviewMarks)}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg text-xs transition-all shadow-sm"
                      >
                        Submit Override Decision
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <>
                  {/* Score summary panel */}
                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 bg-blue-50 border border-blue-100 rounded-xl p-4">
                    <div className="text-center p-2">
                      <span className="text-xs font-semibold text-blue-700 uppercase tracking-wider">Evaluation Score</span>
                      <div className="text-3xl font-extrabold text-blue-900 mt-1">{selectedResult.marks}/100</div>
                    </div>
                    <div className="text-center p-2 border-y sm:border-y-0 sm:border-x border-blue-200">
                      <span className="text-xs font-semibold text-blue-700 uppercase tracking-wider">Grade</span>
                      <div className="text-3xl font-extrabold text-blue-900 mt-1">{selectedResult.grade || 'N/A'}</div>
                    </div>
                    <div className="text-center p-2 border-b sm:border-b-0 sm:border-r border-blue-200">
                      <span className="text-xs font-semibold text-blue-700 uppercase tracking-wider">Mean Similarity</span>
                      <div className="text-3xl font-extrabold text-blue-900 mt-1">{selectedResult.similarity}%</div>
                    </div>
                    <div className="text-center p-2">
                      <span className="text-xs font-semibold text-blue-700 uppercase tracking-wider">AI Confidence</span>
                      <div className="text-3xl font-extrabold text-blue-900 mt-1">{(selectedResult.confidence * 100).toFixed(0)}%</div>
                    </div>
                  </div>

                  {/* Flagging & Similarity Warning Block */}
                  {selectedResult.flag_details && (
                    <div className="space-y-4">
                      {/* Status Banner */}
                      <div className={`p-4 rounded-xl border ${
                        selectedResult.flagged 
                          ? 'bg-red-50 border-red-200 text-red-900' 
                          : 'bg-green-50 border-green-200 text-green-900'
                      }`}>
                        <div className="flex items-center gap-2 mb-2">
                          {selectedResult.flagged ? (
                            <AlertTriangle className="h-5 w-5 text-red-600 animate-pulse" />
                          ) : (
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          )}
                          <span className="font-bold text-sm uppercase tracking-wider">
                            {selectedResult.flagged ? '🚩 Flagged for Review' : '✓ Cleared / No Flags'}
                          </span>
                        </div>
                        
                        {selectedResult.flagged ? (
                          <div className="space-y-3">
                            <p className="text-xs font-semibold text-red-800">
                              Automatic screening has flagged this answer sheet for the following reasons:
                            </p>
                            <ul className="list-disc list-inside space-y-1 text-xs text-red-950 font-medium">
                              {selectedResult.flag_details.reasons.map((reason, rIdx) => (
                                <li key={rIdx}>{reason}</li>
                              ))}
                            </ul>
                            {selectedResult.plagiarism_details && selectedResult.plagiarism_details.matches?.length > 0 && (
                              <div className="space-y-1.5 pt-2 border-t border-red-200">
                                <span className="text-[10px] font-bold uppercase tracking-wider text-red-700 block">Detailed Similarity Matches:</span>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                  {selectedResult.plagiarism_details.matches.map((match, mIdx) => (
                                    <div key={mIdx} className="bg-white border border-red-100 rounded-lg p-2.5 text-[11px] text-gray-800 shadow-sm">
                                      <div className="flex justify-between font-bold">
                                        <span>{selectedResult.student_name} ↔ {match.matched_to}</span>
                                        <span className="text-red-600">{match.similarity}%</span>
                                      </div>
                                      <p className="text-[10px] text-gray-500 mt-0.5">{match.reason}</p>
                                      <div className="flex justify-end mt-2">
                                        <button
                                          type="button"
                                          onClick={() => handleStartComparison({
                                            type: match.type === 'model_answer' ? 'model' : 'student',
                                            target_filename: match.type === 'model_answer' ? null : match.matched_to
                                          })}
                                          className="text-[10px] bg-red-50 hover:bg-red-100 text-red-700 font-bold px-2 py-1 rounded border border-red-200 transition-colors"
                                        >
                                          Compare Side-by-Side
                                        </button>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            {selectedResult.flag_details?.pattern_details?.self_duplicates?.length > 0 && (
                              <div className="space-y-1.5 pt-2 border-t border-red-200">
                                <span className="text-[10px] font-bold uppercase tracking-wider text-red-700 block">Self-Duplicate Violations:</span>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                  {selectedResult.flag_details.pattern_details.self_duplicates.map((dup, dIdx) => (
                                    <div key={dIdx} className="bg-white border border-red-100 rounded-lg p-2.5 text-[11px] text-gray-800 shadow-sm">
                                      <div className="flex justify-between font-bold">
                                        <span>Question {dup.q1} ↔ Question {dup.q2}</span>
                                        <span className="text-red-600">{dup.similarity}%</span>
                                      </div>
                                      <div className="flex justify-end mt-2">
                                        <button
                                          type="button"
                                          onClick={() => handleStartComparison({
                                            type: 'self',
                                            q1: dup.q1,
                                            q2: dup.q2
                                          })}
                                          className="text-[10px] bg-red-50 hover:bg-red-100 text-red-700 font-bold px-2 py-1 rounded border border-red-200 transition-colors"
                                        >
                                          Compare Answers
                                        </button>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="text-xs font-medium">
                            No similarity matches, AI content indicators, or duplicate patterns were detected. The sheet is clear.
                          </p>
                        )}
                      </div>

                      {/* Educator Audit Board */}
                      {selectedResult.flagged && (
                        <div className="p-4 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 shadow-sm space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-xs uppercase tracking-wider text-gray-700">✍️ Educator Review Board</span>
                            <span className={`px-2.5 py-0.5 text-[10px] font-bold rounded-full uppercase tracking-wide ${
                              reviewStatus === 'Approved' ? 'bg-green-100 text-green-800 border border-green-200' :
                              reviewStatus === 'Rejected' ? 'bg-red-100 text-red-800 border border-red-200' :
                              'bg-yellow-100 text-yellow-800 border border-yellow-200'
                            }`}>
                              {reviewStatus}
                            </span>
                          </div>
                          
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-sans">
                            <div>
                              <label className="block font-bold text-gray-600 uppercase tracking-[0.05em] text-[10px] mb-1.5">Override Marks (0-100):</label>
                              <input
                                type="number"
                                value={reviewMarks}
                                onChange={(e) => setReviewMarks(e.target.value)}
                                placeholder="Assign custom marks..."
                                min="0"
                                max="100"
                                className="w-full px-3 py-1.5 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 font-sans text-xs font-bold"
                              />
                            </div>
                            <div>
                              <label className="block font-bold text-gray-600 uppercase tracking-[0.05em] text-[10px] mb-1.5">Update Status:</label>
                              <div className="flex gap-1.5">
                                {['Pending Review', 'Approved', 'Rejected'].map((statusOption) => (
                                  <button
                                    key={statusOption}
                                    type="button"
                                    onClick={() => setReviewStatus(statusOption)}
                                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all border ${
                                      reviewStatus === statusOption
                                        ? statusOption === 'Approved' ? 'bg-green-600 text-white border-green-600 shadow-sm' :
                                          statusOption === 'Rejected' ? 'bg-red-600 text-white border-red-600 shadow-sm' :
                                          'bg-yellow-500 text-white border-yellow-500 shadow-sm'
                                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'
                                    }`}
                                  >
                                    {statusOption === 'Pending Review' ? 'Hold' : statusOption}
                                  </button>
                                ))}
                              </div>
                            </div>
                            
                            <div>
                              <label className="block font-bold text-gray-600 uppercase tracking-[0.05em] text-[10px] mb-1.5">Reviewer Comments:</label>
                              <textarea
                                value={reviewComments}
                                onChange={(e) => setReviewComments(e.target.value)}
                                placeholder="Type auditor notes or comments..."
                                rows={2}
                                className="w-full px-3 py-1.5 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 font-sans text-xs"
                              />
                            </div>
                          </div>
                          
                          <div className="flex justify-end pt-2 border-t border-gray-200">
                            <button
                              type="button"
                              onClick={() => handleReviewSubmit(selectedResult.id, reviewStatus, reviewComments, reviewMarks)}
                              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg text-xs transition-all shadow-sm"
                            >
                              Submit Review Decision
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Collapsible details list */}
                  <div className="space-y-4">
                    {/* Question evaluations scorecard */}
                    <div>
                      <h4 className="text-sm font-bold text-gray-900 mb-3 border-b border-gray-100 pb-1.5">Detailed Grading Scorecard</h4>
                      
                      {!selectedResult.question_evaluations || selectedResult.question_evaluations.length === 0 ? (
                        <div className="p-4 bg-gray-50 rounded-xl text-center text-xs text-gray-500 border border-dashed border-gray-200">
                          No question-by-question breakdown available for this evaluation. (Overall document similarity was used)
                        </div>
                      ) : (
                        <div className="space-y-4">
                          {selectedResult.question_evaluations.map((q, idx) => {
                            const matchedKeywords = (q.keywords_details || []).filter(kw => kw.matched);
                            const missingKeywords = (q.keywords_details || []).filter(kw => !kw.matched);
                            
                            const matchedConcepts = (q.concepts_details || []).filter(c => c.covered);
                            const missingConcepts = (q.concepts_details || []).filter(c => !c.covered);
                            
                            const hasDeductions = q.earned_marks < q.max_marks;
                            
                            return (
                              <div key={idx} className="border border-gray-200 rounded-xl overflow-hidden shadow-sm bg-white">
                                <div className="bg-gray-50 px-4 py-2 border-b border-gray-200 flex justify-between items-center text-xs">
                                  <span className="font-bold text-gray-700">Question {q.question_num}</span>
                                  <span className="font-bold px-2 py-0.5 bg-blue-50 text-blue-700 border border-blue-200 rounded">
                                    Score: {q.earned_marks} / {q.max_marks} Marks
                                  </span>
                                </div>
                                
                                <div className="p-4 space-y-3">
                                  {/* Question text */}
                                  <div className="text-xs">
                                    <span className="font-bold text-gray-400 uppercase tracking-wider">Question Description:</span>
                                    <p className="font-semibold text-gray-900 mt-0.5 leading-relaxed">{q.question}</p>
                                  </div>

                                  {/* Student vs Model Answer */}
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                                      <span className="font-bold text-gray-400 uppercase tracking-wider">Student's Answer:</span>
                                      <p className="mt-1.5 text-gray-800 leading-relaxed font-sans whitespace-pre-wrap">
                                        {q.student_answer || "(No Answer Extracted)"}
                                      </p>
                                    </div>
                                    <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                                      <span className="font-bold text-green-700 uppercase tracking-wider">Model Grading Answer Key:</span>
                                      <p className="mt-1.5 text-green-800 leading-relaxed font-sans whitespace-pre-wrap">
                                        {q.model_answer}
                                      </p>
                                    </div>
                                  </div>

                                  {/* Rubrics Grading Breakdowns */}
                                  <div className="border-t border-gray-150 pt-3 mt-1.5">
                                    <span className="font-bold text-gray-400 text-[10px] uppercase tracking-wider block mb-2">Grading Components Breakdown:</span>
                                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs mb-2">
                                      <div className="bg-gray-50 p-2 rounded border border-gray-200 shadow-sm">
                                        <div className="text-gray-500 font-semibold text-[10px] uppercase tracking-wide">Correctness (40%)</div>
                                        <div className="font-bold text-gray-800 mt-0.5">{q.correctness_score ?? 'N/A'} / {(q.max_marks * 0.4).toFixed(1)}</div>
                                      </div>
                                      <div className="bg-gray-50 p-2 rounded border border-gray-200 shadow-sm">
                                        <div className="text-gray-500 font-semibold text-[10px] uppercase tracking-wide">Concepts (30%)</div>
                                        <div className="font-bold text-gray-800 mt-0.5">{q.concept_score ?? 'N/A'} / {(q.max_marks * 0.3).toFixed(1)}</div>
                                      </div>
                                      <div className="bg-gray-50 p-2 rounded border border-gray-200 shadow-sm">
                                        <div className="text-gray-500 font-semibold text-[10px] uppercase tracking-wide">Keywords (20%)</div>
                                        <div className="font-bold text-gray-800 mt-0.5">{q.keyword_score ?? 'N/A'} / {(q.max_marks * 0.2).toFixed(1)}</div>
                                      </div>
                                      <div className="bg-gray-50 p-2 rounded border border-gray-200 shadow-sm">
                                        <div className="text-gray-500 font-semibold text-[10px] uppercase tracking-wide">Completeness (10%)</div>
                                        <div className="font-bold text-gray-800 mt-0.5">{q.completeness_score ?? 'N/A'} / {(q.max_marks * 0.1).toFixed(1)}</div>
                                      </div>
                                    </div>
                                  </div>
                                  
                                  {/* Matched Rubrics Checklist */}
                                  {(matchedKeywords.length > 0 || matchedConcepts.length > 0) && (
                                    <div className="text-xs border-t border-gray-100 pt-3">
                                      <span className="font-bold text-green-700 text-[10px] uppercase tracking-wider block mb-1.5">Matched Elements (✔):</span>
                                      <div className="space-y-2 bg-green-50/50 p-3 rounded-lg border border-green-100">
                                        {matchedKeywords.length > 0 && (
                                          <div className="flex flex-wrap gap-1.5">
                                            {matchedKeywords.map((kw, kwIdx) => (
                                              <span key={kwIdx} className="px-2 py-0.5 rounded-full font-semibold bg-green-100 text-green-800 border border-green-200 text-[11px]">
                                                ✔ {kw.keyword}
                                              </span>
                                            ))}
                                          </div>
                                        )}
                                        
                                        {matchedConcepts.length > 0 && (
                                          <ul className="space-y-1">
                                            {matchedConcepts.map((c, cIdx) => (
                                              <li key={cIdx} className="text-[11px] text-green-950 flex items-start gap-1.5">
                                                <span className="font-bold text-green-600 flex-shrink-0 mt-0.5">✔</span>
                                                <div>
                                                  <span className="font-semibold text-green-900">{c.concept}</span>
                                                  {c.matched_text && (
                                                    <p className="text-[10px] text-green-700 italic mt-0.5 pl-1.5 border-l-2 border-green-300">
                                                      Matched: "{c.matched_text}" ({c.similarity}%)
                                                    </p>
                                                  )}
                                                </div>
                                              </li>
                                            ))}
                                          </ul>
                                        )}
                                      </div>
                                    </div>
                                  )}

                                  {/* Missing Rubrics Checklist */}
                                  {(missingKeywords.length > 0 || missingConcepts.length > 0) && (
                                    <div className="text-xs border-t border-gray-100 pt-3">
                                      <span className="font-bold text-red-700 text-[10px] uppercase tracking-wider block mb-1.5">Missing Elements (✘):</span>
                                      <div className="space-y-2 bg-red-50/50 p-3 rounded-lg border border-red-100">
                                        {missingKeywords.length > 0 && (
                                          <div className="flex flex-wrap gap-1.5">
                                            {missingKeywords.map((kw, kwIdx) => (
                                              <span key={kwIdx} className="px-2 py-0.5 rounded-full font-semibold bg-red-100 text-red-800 border border-red-200 text-[11px] line-through opacity-75">
                                                ✘ {kw.keyword}
                                              </span>
                                            ))}
                                          </div>
                                        )}
                                        
                                        {missingConcepts.length > 0 && (
                                          <ul className="space-y-1">
                                            {missingConcepts.map((c, cIdx) => (
                                              <li key={cIdx} className="text-[11px] text-red-950 flex items-start gap-1.5">
                                                <span className="font-bold text-red-600 flex-shrink-0 mt-0.5">✘</span>
                                                <span className="font-semibold text-red-900 line-through opacity-75">{c.concept}</span>
                                              </li>
                                            ))}
                                          </ul>
                                        )}
                                      </div>
                                    </div>
                                  )}

                                  {/* Reason for Deduction warning block */}
                                  {hasDeductions && q.deduction_reason && (
                                    <div className="text-xs bg-amber-50 border border-amber-200 rounded-lg p-3 text-amber-900">
                                      <span className="font-bold text-amber-800 block uppercase tracking-wider text-[10px] mb-1">Reason for Deduction:</span>
                                      <p className="leading-relaxed font-semibold">{q.deduction_reason}</p>
                                    </div>
                                  )}

                                  {/* Similarity and feedback */}
                                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-t border-gray-100 pt-2 gap-2 text-xs">
                                    <div className="flex items-center gap-2">
                                      <span className="font-bold text-gray-400">Match score:</span>
                                      <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full font-bold">{q.similarity}%</span>
                                    </div>
                                    <div className="text-gray-700">
                                      <span className="font-bold text-gray-400">Grading Remark:</span> {q.feedback}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>

                    {/* Raw Extracted Text */}
                    <div>
                      <h4 className="text-sm font-bold text-gray-900 mb-3 border-b border-gray-100 pb-1.5">Raw Extracted OCR Text</h4>
                      <div className="relative">
                        <pre className="p-4 bg-gray-900 text-gray-100 rounded-lg text-xs leading-relaxed font-mono overflow-auto max-h-48 whitespace-pre-wrap select-text">
                          {selectedResult.extracted_text || "(No extracted text stored)"}
                        </pre>
                        <button
                          type="button"
                          onClick={() => {
                            navigator.clipboard.writeText(selectedResult.extracted_text || '');
                            toast.success("Extracted text copied to clipboard");
                          }}
                          className="absolute right-3 top-3 px-2 py-1 bg-gray-800 hover:bg-gray-700 text-[10px] text-gray-300 border border-gray-700 rounded transition-all"
                        >
                          Copy Text
                        </button>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedResult(null)}
                className="px-4 py-2 bg-gray-900 hover:bg-gray-800 text-white rounded-lg text-sm font-semibold transition-all shadow-sm"
              >
                Close Scorecard
              </button>
            </div>

          </div>
        </div>
      )}
    </div>
  );
};

export default Results;