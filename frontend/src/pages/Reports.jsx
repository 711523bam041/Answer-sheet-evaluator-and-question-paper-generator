import { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { 
  FileText, 
  Download, 
  Users, 
  TrendingUp, 
  AlertTriangle, 
  Award, 
  Layers, 
  Search, 
  ShieldAlert,
  FileSpreadsheet,
  Calendar,
  Grid
} from 'lucide-react';

const Reports = () => {
  const [batches, setBatches] = useState([]);
  const [selectedBatch, setSelectedBatch] = useState('all');
  const [results, setResults] = useState([]);
  const [selectedStudentId, setSelectedStudentId] = useState('');
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    average: 0,
    passed: 0,
    passRate: 0,
    flagged: 0,
    highest: 0,
    lowest: 0
  });

  useEffect(() => {
    fetchBatches();
  }, []);

  useEffect(() => {
    fetchResults();
  }, [selectedBatch]);

  useEffect(() => {
    calculateStats();
    if (results.length > 0) {
      setSelectedStudentId(results[0].id.toString());
    } else {
      setSelectedStudentId('');
    }
  }, [results]);

  const fetchBatches = async () => {
    try {
      const response = await axios.get('/api/reports/batches');
      setBatches(response.data);
    } catch (error) {
      console.error(error);
      toast.error('Failed to fetch evaluation batches');
    }
  };

  const fetchResults = async () => {
    setLoading(true);
    try {
      const url = selectedBatch === 'all' ? '/api/results' : `/api/results?batch_id=${selectedBatch}`;
      const response = await axios.get(url);
      setResults(response.data);
    } catch (error) {
      console.error(error);
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
        passed: 0,
        passRate: 0,
        flagged: 0,
        highest: 0,
        lowest: 0
      });
      return;
    }

    const total = results.length;
    const average = (results.reduce((sum, r) => sum + r.marks, 0) / total).toFixed(1);
    const passed = results.filter(r => r.marks >= 60).length;
    const passRate = ((passed / total) * 100).toFixed(1);
    const flagged = results.filter(r => r.flagged).length;
    const highest = Math.max(...results.map(r => r.marks)).toFixed(1);
    const lowest = Math.min(...results.map(r => r.marks)).toFixed(1);

    setStats({
      total,
      average,
      passed,
      passRate,
      flagged,
      highest,
      lowest
    });
  };

  const triggerDownload = async (endpoint, filename) => {
    try {
      toast.loading('Generating report...', { id: 'download' });
      const response = await axios.get(endpoint, { responseType: 'blob' });
      
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Report downloaded successfully!', { id: 'download' });
    } catch (error) {
      console.error(error);
      toast.error('Failed to generate report', { id: 'download' });
    }
  };

  const handleStudentReportDownload = (format) => {
    if (!selectedStudentId) {
      toast.error('Please select a student');
      return;
    }
    const student = results.find(r => r.id.toString() === selectedStudentId);
    const nameSlug = student ? student.student_name.replace(/\s+/g, '_') : selectedStudentId;
    const ext = format === 'excel' ? 'xlsx' : 'pdf';
    triggerDownload(
      `/api/reports/student/${selectedStudentId}?format=${format}`,
      `student_report_${nameSlug}.${ext}`
    );
  };

  const handleBatchReportDownload = (reportType, format) => {
    const ext = format === 'excel' ? 'xlsx' : 'pdf';
    const batchSlug = selectedBatch === 'all' ? 'all_batches' : selectedBatch.substring(0, 8);
    triggerDownload(
      `/api/reports/${reportType}?format=${format}&batch_id=${selectedBatch}`,
      `${reportType}_report_${batchSlug}.${ext}`
    );
  };

  const formatDate = (isoString) => {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    return date.toLocaleDateString(undefined, { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header section */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between pb-6 border-b border-gray-200">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">Administrative Reports Panel</h1>
          <p className="mt-2 text-sm text-gray-500">
            Generate and export student performance audits, similarity matrices, flag dashboards, and class analytics.
          </p>
        </div>
        
        {/* Batch selection dropdown */}
        <div className="mt-4 md:mt-0 flex items-center space-x-3">
          <label htmlFor="batch-select" className="text-sm font-semibold text-gray-700 flex items-center space-x-1">
            <Layers className="h-4 w-4 text-gray-500" />
            <span>Select Evaluation Batch:</span>
          </label>
          <select
            id="batch-select"
            value={selectedBatch}
            onChange={(e) => setSelectedBatch(e.target.value)}
            className="block w-64 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md shadow-sm bg-white"
          >
            <option value="all">All Batches (Overall Summary)</option>
            {batches.map((b) => (
              <option key={b.batch_id} value={b.batch_id}>
                {formatDate(b.created_at)} ({b.student_count} students)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Visual statistics preview cards */}
      {loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-6 gap-4 animate-pulse">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-200 rounded-lg"></div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 flex flex-col justify-between">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Total Evaluated</span>
            <div className="flex items-baseline space-x-2 mt-2">
              <span className="text-2xl font-bold text-gray-900">{stats.total}</span>
              <span className="text-xs text-gray-500">sheets</span>
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 flex flex-col justify-between">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Class Average</span>
            <div className="flex items-baseline space-x-2 mt-2">
              <span className="text-2xl font-bold text-blue-600">{stats.average}%</span>
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 flex flex-col justify-between">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Pass Rate (≥60%)</span>
            <div className="flex items-baseline space-x-2 mt-2">
              <span className="text-2xl font-bold text-green-600">{stats.passRate}%</span>
              <span className="text-xs text-gray-500">({stats.passed} pass)</span>
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 flex flex-col justify-between">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Flagged Incidents</span>
            <div className="flex items-baseline space-x-2 mt-2">
              <span className={`text-2xl font-bold ${stats.flagged > 0 ? 'text-red-600' : 'text-gray-900'}`}>{stats.flagged}</span>
              <span className="text-xs text-gray-500">flagged</span>
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 flex flex-col justify-between">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Highest Score</span>
            <div className="flex items-baseline space-x-2 mt-2">
              <span className="text-2xl font-bold text-gray-900">{stats.highest}%</span>
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 flex flex-col justify-between">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Lowest Score</span>
            <div className="flex items-baseline space-x-2 mt-2">
              <span className="text-2xl font-bold text-gray-900">{stats.lowest}%</span>
            </div>
          </div>
        </div>
      )}

      {/* Reports Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
        
        {/* 1. STUDENT REPORT CARD */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden flex flex-col justify-between p-6 hover:shadow-md transition-shadow">
          <div>
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
                <FileText className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">Student Performance Report</h3>
                <p className="text-xs text-gray-400">Individual student breakdown</p>
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-6">
              Generates a comprehensive grading report for a specific student, detailing question-by-question scoring breakdown, OCR extracted response text, explainable feedback remarks, and plagiarism flag alerts.
            </p>

            {/* Student selector */}
            <div className="mb-6">
              <label htmlFor="student-select" className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                Select Student:
              </label>
              <select
                id="student-select"
                value={selectedStudentId}
                onChange={(e) => setSelectedStudentId(e.target.value)}
                disabled={results.length === 0}
                className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md shadow-sm bg-white"
              >
                {results.length === 0 ? (
                  <option value="">No students in selected batch</option>
                ) : (
                  results.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.student_name} {r.roll_number ? `(${r.roll_number})` : ''} - Score: {r.marks}%
                    </option>
                  ))
                )}
              </select>
            </div>
          </div>

          <div className="flex space-x-3 border-t border-gray-100 pt-4">
            <button
              onClick={() => handleStudentReportDownload('pdf')}
              disabled={!selectedStudentId}
              className="flex-1 inline-flex justify-center items-center px-4 py-2.5 border border-transparent text-sm font-semibold rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors"
            >
              <Download className="h-4 w-4 mr-2" />
              Export PDF
            </button>
            <button
              onClick={() => handleStudentReportDownload('excel')}
              disabled={!selectedStudentId}
              className="flex-1 inline-flex justify-center items-center px-4 py-2.5 border border-gray-300 text-sm font-semibold rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors"
            >
              <FileSpreadsheet className="h-4 w-4 mr-2 text-green-600" />
              Export Excel
            </button>
          </div>
        </div>

        {/* 2. FACULTY REPORT CARD */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden flex flex-col justify-between p-6 hover:shadow-md transition-shadow">
          <div>
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-3 bg-purple-50 text-purple-600 rounded-xl">
                <Users className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">Faculty Audit Report</h3>
                <p className="text-xs text-gray-400">Class overview & status metrics</p>
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-6">
              Exports an administrative audit log summarizing the class parameters, overall average scores, student pass rate statistics, and the comprehensive list of submissions showing grades, similarity scores, and reviewercomments.
            </p>
          </div>

          <div className="flex space-x-3 border-t border-gray-100 pt-4">
            <button
              onClick={() => handleBatchReportDownload('faculty', 'pdf')}
              disabled={results.length === 0}
              className="flex-1 inline-flex justify-center items-center px-4 py-2.5 border border-transparent text-sm font-semibold rounded-lg text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 transition-colors"
            >
              <Download className="h-4 w-4 mr-2" />
              Export PDF
            </button>
            <button
              onClick={() => handleBatchReportDownload('faculty', 'excel')}
              disabled={results.length === 0}
              className="flex-1 inline-flex justify-center items-center px-4 py-2.5 border border-gray-300 text-sm font-semibold rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 transition-colors"
            >
              <FileSpreadsheet className="h-4 w-4 mr-2 text-green-600" />
              Export Excel
            </button>
          </div>
        </div>

        {/* 3. CLASS PERFORMANCE REPORT CARD */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden flex flex-col justify-between p-6 hover:shadow-md transition-shadow">
          <div>
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
                <TrendingUp className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">Class Performance Report</h3>
                <p className="text-xs text-gray-400">Class analytics, rankings & grades</p>
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-6">
              Compiles in-depth academic analytics: top performer rankings, pass/fail rates, letter grade distribution tables, and multi-dimensional grading metrics (semantic correctness, keyword matching, concept coverage, and completeness).
            </p>
          </div>

          <div className="flex space-x-3 border-t border-gray-100 pt-4">
            <button
              onClick={() => handleBatchReportDownload('class', 'pdf')}
              disabled={results.length === 0}
              className="flex-1 inline-flex justify-center items-center px-4 py-2.5 border border-transparent text-sm font-semibold rounded-lg text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-50 transition-colors"
            >
              <Download className="h-4 w-4 mr-2" />
              Export PDF
            </button>
            <button
              onClick={() => handleBatchReportDownload('class', 'excel')}
              disabled={results.length === 0}
              className="flex-1 inline-flex justify-center items-center px-4 py-2.5 border border-gray-300 text-sm font-semibold rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-50 transition-colors"
            >
              <FileSpreadsheet className="h-4 w-4 mr-2 text-green-600" />
              Export Excel
            </button>
          </div>
        </div>

        {/* 4. SIMILARITY REPORT CARD */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden flex flex-col justify-between p-6 hover:shadow-md transition-shadow">
          <div>
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-3 bg-amber-50 text-amber-600 rounded-xl">
                <Layers className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">Plagiarism & Similarity Report</h3>
                <p className="text-xs text-gray-400">Match pairings list & matrices</p>
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-6">
              Maps and lists all duplicate answer sheets and semantic overlaps exceeding the 80% threshold. Isolates student-to-student copying and matches copied from the reference model answer key.
            </p>
          </div>

          <div className="flex space-x-3 border-t border-gray-100 pt-4">
            <button
              onClick={() => handleBatchReportDownload('similarity', 'pdf')}
              disabled={results.length === 0}
              className="flex-1 inline-flex justify-center items-center px-4 py-2.5 border border-transparent text-sm font-semibold rounded-lg text-white bg-amber-600 hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 disabled:opacity-50 transition-colors"
            >
              <Download className="h-4 w-4 mr-2" />
              Export PDF
            </button>
            <button
              onClick={() => handleBatchReportDownload('similarity', 'excel')}
              disabled={results.length === 0}
              className="flex-1 inline-flex justify-center items-center px-4 py-2.5 border border-gray-300 text-sm font-semibold rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 disabled:opacity-50 transition-colors"
            >
              <FileSpreadsheet className="h-4 w-4 mr-2 text-green-600" />
              Export Excel
            </button>
          </div>
        </div>

        {/* 5. FLAGGED SUBMISSION REPORT CARD */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden flex flex-col justify-between p-6 hover:shadow-md transition-shadow md:col-span-2 md:max-w-xl md:mx-auto w-full">
          <div>
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-3 bg-red-50 text-red-600 rounded-xl">
                <ShieldAlert className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">Flagged Submissions Audit Report</h3>
                <p className="text-xs text-gray-400">Suspicious cases & AI content details</p>
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-6">
              A specialized report on all flagged student sheets. Displays the roll number, specific reasons for flagging (AI content detectors, self-duplicates, low-score high-overlap), AI confidence levels, and the educator review remarks.
            </p>
          </div>

          <div className="flex space-x-3 border-t border-gray-100 pt-4">
            <button
              onClick={() => handleBatchReportDownload('flagged', 'pdf')}
              disabled={results.length === 0}
              className="flex-1 inline-flex justify-center items-center px-4 py-2.5 border border-transparent text-sm font-semibold rounded-lg text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 transition-colors"
            >
              <Download className="h-4 w-4 mr-2" />
              Export PDF
            </button>
            <button
              onClick={() => handleBatchReportDownload('flagged', 'excel')}
              disabled={results.length === 0}
              className="flex-1 inline-flex justify-center items-center px-4 py-2.5 border border-gray-300 text-sm font-semibold rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 transition-colors"
            >
              <FileSpreadsheet className="h-4 w-4 mr-2 text-green-600" />
              Export Excel
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Reports;
