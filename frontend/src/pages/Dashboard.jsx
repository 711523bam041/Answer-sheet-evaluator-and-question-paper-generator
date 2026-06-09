import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import { Upload, FileText, Users, AlertTriangle, TrendingUp, X, Check } from 'lucide-react';

const Dashboard = () => {
  const [files, setFiles] = useState({ answerKey: null, answers: [] });
  const [studentNames, setStudentNames] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stats, setStats] = useState(null);

  // Question Paper integration states
  const [papers, setPapers] = useState([]);
  const [useGeneratedPaper, setUseGeneratedPaper] = useState(false);
  const [selectedPaperId, setSelectedPaperId] = useState('');

  const navigate = useNavigate();

  useEffect(() => {
    fetchStats();
    fetchPapers();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/results');
      const results = response.data;

      if (results.length > 0) {
        const totalStudents = results.length;
        const avgScore = results.reduce((sum, r) => sum + r.marks, 0) / totalStudents;
        const flaggedCases = results.filter(r => r.flagged).length;

        setStats({
          totalStudents,
          avgScore: avgScore.toFixed(1),
          flaggedCases
        });
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchPapers = async () => {
    try {
      const response = await axios.get('/api/question_papers');
      setPapers(response.data);
    } catch (error) {
      console.error('Error fetching question papers:', error);
    }
  };

  const handleFileChange = (e) => {
    const { name, files: fileList } = e.target;
    if (name === 'answers') {
      const filesArray = Array.from(fileList);
      setFiles(prev => ({ ...prev, answers: filesArray }));
      setStudentNames(filesArray.map((file, idx) => ({
        name: file.name.split('.')[0].replace(/_/g, ' '),
        rollNumber: `R-${1000 + idx + 1}`,
        originalName: file.name
      })));
    } else {
      setFiles(prev => ({ ...prev, [name]: fileList[0] }));
    }
  };

  const handleStudentNameChange = (index, name) => {
    setStudentNames(prev => {
      const updated = [...prev];
      updated[index].name = name;
      return updated;
    });
  };

  const handleStudentRollNumberChange = (index, rollNumber) => {
    setStudentNames(prev => {
      const updated = [...prev];
      updated[index].rollNumber = rollNumber;
      return updated;
    });
  };

  const handleRemoveStudentFile = (index) => {
    setFiles(prev => ({
      ...prev,
      answers: prev.answers.filter((_, i) => i !== index)
    }));
    setStudentNames(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (useGeneratedPaper && !selectedPaperId) {
      toast.error('Please select a Question Paper to use as evaluation key');
      return;
    }

    if (!useGeneratedPaper && !files.answerKey) {
      toast.error('Please upload an Answer Key file');
      return;
    }

    if (files.answers.length === 0) {
      toast.error('Please select at least one student answer sheet');
      return;
    }

    for (let i = 0; i < studentNames.length; i++) {
      if (!studentNames[i].name.trim()) {
        toast.error(`Please enter a name for student ${i + 1}`);
        return;
      }
    }

    setUploading(true);
    setProgress(0);

    const formData = new FormData();
    if (useGeneratedPaper) {
      formData.append('paperId', selectedPaperId);
    } else {
      formData.append('answerkey', files.answerKey);
    }
    
    files.answers.forEach((file, idx) => {
      formData.append('answers', file);
      formData.append(`studentNames[${idx}]`, studentNames[idx].name.trim());
      formData.append(`studentRollNumbers[${idx}]`, (studentNames[idx].rollNumber || '').trim());
    });

    try {
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 300);

      const response = await axios.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      clearInterval(progressInterval);
      setProgress(100);

      toast.success(`Evaluation complete! ${response.data.results_count} students evaluated`);
      
      setFiles({ answerKey: null, answers: [] });
      setStudentNames([]);
      setProgress(0);
      setSelectedPaperId('');

      fetchStats();
      
      setTimeout(() => navigate('/results'), 1000);
    } catch (error) {
      console.error(error);
      toast.error(error.response?.data?.message || 'Upload and evaluation failed');
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const selectedPaperSubject = papers.find(p => p.id === parseInt(selectedPaperId))?.subject_name;

  return (
    <div className="space-y-8">
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Dashboard</h1>
        <p className="text-gray-600">Upload handwritten or digital answer sheets for automatic evaluation</p>
      </div>

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 hover:shadow-md transition-shadow">
            <div className="flex items-center">
              <Users className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Students</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalStudents}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 hover:shadow-md transition-shadow">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Average Score</p>
                <p className="text-2xl font-bold text-gray-900">{stats.avgScore}%</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 hover:shadow-md transition-shadow">
            <div className="flex items-center">
              <AlertTriangle className="h-8 w-8 text-red-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Flagged Cases</p>
                <p className="text-2xl font-bold text-gray-900">{stats.flaggedCases}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Upload Files</h2>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Key Selection Control Header */}
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h4 className="text-sm font-bold text-blue-900">Grading Key Reference</h4>
                <p className="text-xs text-blue-700 mt-0.5">
                  Evaluate using a previously generated AI Question Paper or upload a custom answer key file.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => { setUseGeneratedPaper(false); setSelectedPaperId(''); }}
                  className={`px-4 py-2 text-xs font-semibold rounded-lg border transition-all ${
                    !useGeneratedPaper
                      ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  Upload File
                </button>
                <button
                  type="button"
                  disabled={papers.length === 0}
                  onClick={() => { setUseGeneratedPaper(true); setFiles(prev => ({ ...prev, answerKey: null })); }}
                  className={`px-4 py-2 text-xs font-semibold rounded-lg border transition-all ${
                    useGeneratedPaper
                      ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  } ${papers.length === 0 ? 'opacity-50 cursor-not-allowed' : ''}`}
                  title={papers.length === 0 ? "Generate a question paper first" : ""}
                >
                  Select AI Paper ({papers.length})
                </button>
              </div>
            </div>

            {useGeneratedPaper && (
              <div className="mt-4 pt-3 border-t border-blue-200">
                <label className="block text-xs font-bold text-blue-800 uppercase tracking-wider mb-1">Select Question Paper</label>
                <select
                  value={selectedPaperId}
                  onChange={(e) => setSelectedPaperId(e.target.value)}
                  className="w-full px-3 py-2 border border-blue-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">-- Choose from your generated papers list --</option>
                  {papers.map((paper) => (
                    <option key={paper.id} value={paper.id}>
                      {paper.subject_name} ({paper.total_marks} Marks) - Created {new Date(paper.created_at).toLocaleDateString()}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Answer Key File / Selected Banner */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Answer Key *
              </label>
              {useGeneratedPaper ? (
                <div className="flex flex-col items-center justify-center w-full h-32 border-2 border-green-300 bg-green-50 rounded-lg p-4 text-center">
                  <Check className="h-8 w-8 text-green-600 mb-1" />
                  <p className="text-sm text-green-800 font-bold">Paper Connected</p>
                  <p className="text-xs text-green-600 mt-0.5 truncate max-w-full">
                    {selectedPaperSubject ? selectedPaperSubject : 'None Selected'}
                  </p>
                </div>
              ) : (
                <div className="relative">
                  <input
                    type="file"
                    name="answerKey"
                    accept=".pdf,.png,.jpg,.jpeg,.txt"
                    onChange={handleFileChange}
                    className="hidden"
                    id="answerKey"
                    disabled={uploading}
                  />
                  <label
                    htmlFor="answerKey"
                    className="flex items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-blue-400 transition-colors bg-gray-50 hover:bg-blue-50"
                  >
                    <div className="text-center">
                      <FileText className="mx-auto h-8 w-8 text-gray-400" />
                      <p className="mt-2 text-sm text-gray-600 font-medium font-sans">
                        {files.answerKey ? files.answerKey.name : 'Click to upload answer key'}
                      </p>
                      {!files.answerKey && <p className="text-xs text-gray-500 mt-1">PDF, Image or Text</p>}
                    </div>
                  </label>
                </div>
              )}
            </div>

            {/* Student Answers Upload */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Student Answers *
              </label>
              <div className="relative">
                <input
                  type="file"
                  name="answers"
                  accept=".pdf,.png,.jpg,.jpeg,.txt"
                  multiple
                  onChange={handleFileChange}
                  className="hidden"
                  id="answers"
                  disabled={uploading}
                />
                <label
                  htmlFor="answers"
                  className="flex items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-blue-400 transition-colors bg-gray-50 hover:bg-blue-50"
                >
                  <div className="text-center font-sans">
                    <Upload className="mx-auto h-8 w-8 text-gray-400" />
                    <p className="mt-2 text-sm text-gray-600 font-medium">
                      {files.answers.length > 0
                        ? `${files.answers.length} file(s) selected`
                        : 'Click to upload student answers'
                      }
                    </p>
                    {files.answers.length === 0 && <p className="text-xs text-gray-500 mt-1">Multiple files supported</p>}
                  </div>
                </label>
              </div>
            </div>
          </div>

          {/* Student Details List */}
          {files.answers.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-gray-700">Student Details (Name & Roll Number) *</h3>
              <div className="space-y-2 max-h-48 overflow-y-auto border border-gray-200 rounded-lg p-4 bg-gray-50">
                {files.answers.map((file, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <input
                      type="text"
                      value={studentNames[idx]?.name || ''}
                      onChange={(e) => handleStudentNameChange(idx, e.target.value)}
                      placeholder={`Student ${idx + 1} Name`}
                      disabled={uploading}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 font-sans"
                    />
                    <input
                      type="text"
                      value={studentNames[idx]?.rollNumber || ''}
                      onChange={(e) => handleStudentRollNumberChange(idx, e.target.value)}
                      placeholder="Roll Number"
                      disabled={uploading}
                      className="w-40 px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 font-sans"
                    />
                    <span className="text-xs text-gray-500 truncate max-w-xs" title={file.name}>
                      {file.name}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRemoveStudentFile(idx)}
                      disabled={uploading}
                      className="p-1 text-gray-400 hover:text-red-600 disabled:opacity-50"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Progress Bar */}
          {uploading && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-700">Processing...</span>
                <span className="text-gray-600">{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => {
                setFiles({ answerKey: null, answers: [] });
                setStudentNames([]);
                setSelectedPaperId('');
              }}
              disabled={uploading}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Clear
            </button>
            <button
              type="submit"
              disabled={
                uploading || 
                (!useGeneratedPaper && !files.answerKey) || 
                (useGeneratedPaper && !selectedPaperId) || 
                files.answers.length === 0
              }
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {uploading ? `Processing (${progress}%)...` : 'Start Evaluation'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Dashboard;