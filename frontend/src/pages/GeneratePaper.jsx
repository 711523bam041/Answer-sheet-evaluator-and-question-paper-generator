import { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { 
  FileText, Download, Printer, Trash2, Eye, 
  HelpCircle, AlertTriangle, CheckCircle, RefreshCw, 
  BookOpen, Plus, Minus, Info
} from 'lucide-react';

const GeneratePaper = () => {
  // Paper Details Form State
  const [subjectName, setSubjectName] = useState('');
  const [topics, setTopics] = useState('');
  const [syllabus, setSyllabus] = useState('');
  const [difficulty, setDifficulty] = useState('Medium');
  const [duration, setDuration] = useState('3 Hours');
  const [totalMarks, setTotalMarks] = useState(50);
  
  // Custom Marks Distribution State
  const [distribution, setDistribution] = useState({
    '1': 10,
    '2': 5,
    '5': 2,
    '10': 2,
    '13': 0
  });

  // UI States
  const [generating, setGenerating] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [activePaper, setActivePaper] = useState(null);
  const [history, setHistory] = useState([]);
  const [showAnswers, setShowAnswers] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Micro-animation loading messages
  const loadingSteps = [
    "Analyzing subject and topic details...",
    "Parsing complete syllabus requirements...",
    "Selecting questions mapped to Bloom's Taxonomy...",
    "Formulating custom marks distribution...",
    "Structuring options and generating answer keys...",
    "Finalizing premium examination paper layout..."
  ];

  useEffect(() => {
    fetchHistory();
  }, []);

  // Set up step change interval during generation
  useEffect(() => {
    let interval;
    if (generating) {
      interval = setInterval(() => {
        setLoadingStep(prev => (prev + 1) % loadingSteps.length);
      }, 2500);
    } else {
      setLoadingStep(0);
    }
    return () => clearInterval(interval);
  }, [generating]);

  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const response = await axios.get('/api/question_papers');
      setHistory(response.data);
      // Automatically load the latest generated paper as active preview if none selected
      if (response.data.length > 0 && !activePaper) {
        setActivePaper(response.data[0]);
      }
    } catch (error) {
      console.error('Error fetching paper history:', error);
      toast.error('Failed to load past generated papers');
    } finally {
      setLoadingHistory(false);
    }
  };

  // Calculate current sum of distribution
  const calculateCurrentSum = () => {
    return Object.entries(distribution).reduce((sum, [mark, count]) => {
      return sum + (parseInt(mark) * parseInt(count || 0));
    }, 0);
  };

  const distSum = calculateCurrentSum();
  const isDistributionValid = distSum === parseInt(totalMarks);

  const handleDistChange = (markVal, change) => {
    setDistribution(prev => {
      const currentVal = parseInt(prev[markVal] || 0);
      const newVal = Math.max(0, currentVal + change);
      return {
        ...prev,
        [markVal]: newVal
      };
    });
  };

  const handleDirectDistInput = (markVal, val) => {
    const parsed = parseInt(val);
    setDistribution(prev => ({
      ...prev,
      [markVal]: isNaN(parsed) ? 0 : Math.max(0, parsed)
    }));
  };

  const handleGenerate = async (e) => {
    e.preventDefault();

    if (!subjectName.trim()) {
      toast.error('Please enter a subject name');
      return;
    }
    if (!topics.trim()) {
      toast.error('Please specify the topics');
      return;
    }
    if (!isDistributionValid) {
      toast.error(`Marks distribution sum (${distSum}) must match total marks (${totalMarks})`);
      return;
    }

    setGenerating(true);
    try {
      const response = await axios.post('/api/question_papers/generate', {
        subject_name: subjectName.trim(),
        topics: topics.trim(),
        syllabus: syllabus.trim(),
        difficulty,
        duration,
        total_marks: totalMarks,
        distribution
      });

      toast.success('Question Paper generated successfully!');
      setActivePaper(response.data);
      fetchHistory();
      
      // Clear generation details (except subject to make iterations easy)
      setTopics('');
      setSyllabus('');
    } catch (error) {
      console.error('Generation failed:', error);
      const errorMsg = error.response?.data?.message || 'Error occurred during generation';
      toast.error(errorMsg);
    } finally {
      setGenerating(false);
    }
  };

  const handleDeletePaper = async (id, e) => {
    e.stopPropagation(); // Avoid selecting the card
    if (!window.confirm('Are you sure you want to delete this question paper?')) return;

    try {
      await axios.delete(`/api/question_papers/${id}`);
      toast.success('Question paper deleted');
      if (activePaper?.id === id) {
        setActivePaper(null);
      }
      fetchHistory();
    } catch (error) {
      console.error('Failed to delete paper:', error);
      toast.error('Failed to delete question paper');
    }
  };

  const handleDownloadPDF = async (paper, withAnswers = false) => {
    try {
      toast.loading('Generating PDF download...', { id: 'pdf_download' });
      const response = await axios.get(`/api/question_papers/${paper.id}/download_pdf?answers=${withAnswers}`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      const suffix = withAnswers ? '_answers' : '';
      link.download = `question_paper_${paper.subject_name.replace(/\s+/g, '_')}${suffix}.pdf`;
      link.click();
      
      toast.dismiss('pdf_download');
      toast.success('PDF downloaded successfully');
    } catch (error) {
      console.error('PDF download error:', error);
      toast.dismiss('pdf_download');
      toast.error('Failed to download PDF');
    }
  };

  const handlePrint = () => {
    window.print();
  };

  // Helper colors for Bloom's Taxonomy levels
  const getBloomBadgeColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'remembering': return 'bg-gray-100 text-gray-800 border-gray-300';
      case 'understanding': return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'applying': return 'bg-green-50 text-green-700 border-green-200';
      case 'analyzing': return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      case 'evaluating': return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'creating': return 'bg-purple-50 text-purple-700 border-purple-200';
      default: return 'bg-gray-50 text-gray-600 border-gray-200';
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Printable Paper Wrapper - Visible ONLY in print mode */}
      {activePaper && (
        <div className="hidden print:block p-8 bg-white text-black font-serif text-sm leading-relaxed">
          <div className="text-center font-bold text-lg mb-2">INSTITUTION SEMESTER EXAMINATION</div>
          <div className="text-center font-bold text-base mb-4">SUBJECT: {activePaper.subject_name.toUpperCase()}</div>
          
          <div className="flex justify-between border-b pb-2 mb-4">
            <div><strong>Duration:</strong> {activePaper.duration}</div>
            <div><strong>Difficulty:</strong> {activePaper.difficulty}</div>
            <div><strong>Max Marks:</strong> {activePaper.total_marks}</div>
          </div>

          <div className="mb-6">
            <strong className="text-xs tracking-wider">GENERAL INSTRUCTIONS:</strong>
            <ol className="list-decimal pl-4 mt-1 text-xs space-y-1">
              <li>Read all questions carefully before answering.</li>
              <li>Underline/highlight keywords and draw neat diagrams where appropriate.</li>
              <li>Answer all parts of a question sequentially.</li>
            </ol>
          </div>

          {/* Render questions sorted by mark values */}
          {Object.entries(
            activePaper.paper_content.questions.reduce((groups, q) => {
              const m = q.marks;
              if (!groups[m]) groups[m] = [];
              groups[m].push(q);
              return groups;
            }, {})
          )
          .sort(([a], [b]) => parseInt(a) - parseInt(b))
          .map(([marks, qList], sectionIdx) => {
            const partLabels = ["PART A", "PART B", "PART C", "PART D", "PART E", "PART F"];
            const partLabel = partLabels[sectionIdx] || `PART ${sectionIdx + 1}`;
            return (
              <div key={marks} className="mb-6 break-inside-avoid">
                <div className="font-bold border-b pb-1 mb-3 bg-gray-100 px-2 py-1 flex justify-between">
                  <span>{partLabel} - ({marks} Mark Questions)</span>
                  <span className="text-xs">Answer all questions</span>
                </div>
                <div className="space-y-4">
                  {qList.map((q, idx) => (
                    <div key={idx} className="pl-2">
                      <div className="flex justify-between items-start">
                        <span className="font-bold mr-2">Q{idx + 1}.</span>
                        <div className="flex-1">
                          <p className="font-medium inline">{q.question}</p>
                          {q.options && q.options.length > 0 && (
                            <div className="grid grid-cols-2 gap-2 mt-2 pl-4">
                              {q.options.map((opt, optIdx) => {
                                const letters = ["A", "B", "C", "D"];
                                return (
                                  <div key={optIdx}>
                                    ({letters[optIdx]}) {opt}
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                        <span className="font-bold ml-4 text-right">[{marks} Mark]</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Main UI Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between border-b pb-4 gap-4 print:hidden">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">Question Paper Generator</h1>
          <p className="mt-1 text-sm text-gray-500">
            Generate customized academic exam sheets mapping syllabus topics to Bloom's Taxonomy.
          </p>
        </div>
        
        {activePaper && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleDownloadPDF(activePaper, false)}
              className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 shadow-sm transition-all"
              title="Download clean question sheet"
            >
              <Download className="h-4 w-4" />
              Download PDF
            </button>
            <button
              onClick={() => handleDownloadPDF(activePaper, true)}
              className="inline-flex items-center gap-2 px-4 py-2 border border-green-300 text-green-700 bg-green-50 hover:bg-green-100 rounded-lg text-sm font-medium shadow-sm transition-all"
              title="Download PDF containing answers & scoring rubrics"
            >
              <Download className="h-4 w-4" />
              Answer Key PDF
            </button>
            <button
              onClick={handlePrint}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium shadow-sm transition-all"
            >
              <Printer className="h-4 w-4" />
              Print Paper
            </button>
          </div>
        )}
      </div>

      {/* Page content */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 print:hidden">
        
        {/* Left Side: Parameters Form */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2 border-b pb-2">
              <BookOpen className="h-5 w-5 text-blue-600" />
              Exam Parameters
            </h2>

            <form onSubmit={handleGenerate} className="space-y-4">
              {/* Subject & Difficulty */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Subject Name</label>
                  <input
                    type="text"
                    required
                    value={subjectName}
                    onChange={(e) => setSubjectName(e.target.value)}
                    placeholder="e.g. Machine Learning"
                    className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Difficulty Level</label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="Easy">Easy</option>
                    <option value="Medium">Medium</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>
              </div>

              {/* Duration & Total Marks */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Exam Duration</label>
                  <input
                    type="text"
                    required
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                    placeholder="e.g. 3 Hours"
                    className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Total Marks</label>
                  <input
                    type="number"
                    required
                    min="1"
                    max="100"
                    value={totalMarks}
                    onChange={(e) => setTotalMarks(e.target.value ? parseInt(e.target.value) : '')}
                    className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Specific Topics */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Topics (Comma separated)</label>
                <input
                  type="text"
                  required
                  value={topics}
                  onChange={(e) => setTopics(e.target.value)}
                  placeholder="Neural Networks, Regularization, SVM"
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Syllabus details */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Syllabus Details (Optional)</label>
                <textarea
                  value={syllabus}
                  onChange={(e) => setSyllabus(e.target.value)}
                  placeholder="Paste complete syllabus text here to optimize question generation..."
                  rows="3"
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-sans"
                />
              </div>

              {/* Interactive Question Mark Distribution Grid */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500">Questions Count Distribution</label>
                  <span className={`text-xs px-2 py-0.5 rounded font-bold border ${
                    isDistributionValid 
                      ? 'bg-green-50 text-green-700 border-green-200' 
                      : 'bg-red-50 text-red-700 border-red-200'
                  }`}>
                    Sum: {distSum} / {totalMarks} Marks
                  </span>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 space-y-3">
                  {[1, 2, 5, 10, 13].map((mark) => (
                    <div key={mark} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-16 text-sm font-semibold text-gray-700">{mark} {mark === 1 ? 'Mark' : 'Marks'}:</span>
                        <span className="text-xs text-gray-400">({mark * (distribution[mark] || 0)} Total)</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => handleDistChange(mark.toString(), -1)}
                          className="p-1 border bg-white rounded hover:bg-gray-100 text-gray-500"
                        >
                          <Minus className="h-3.5 w-3.5" />
                        </button>
                        <input
                          type="number"
                          min="0"
                          value={distribution[mark.toString()] || 0}
                          onChange={(e) => handleDirectDistInput(mark.toString(), e.target.value)}
                          className="w-12 text-center py-1 border rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white"
                        />
                        <button
                          type="button"
                          onClick={() => handleDistChange(mark.toString(), 1)}
                          className="p-1 border bg-white rounded hover:bg-gray-100 text-gray-500"
                        >
                          <Plus className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Button */}
              <button
                type="submit"
                disabled={generating || !isDistributionValid}
                className={`w-full py-2.5 rounded-lg text-sm font-semibold text-white shadow-sm flex items-center justify-center gap-2 transition-all ${
                  generating 
                    ? 'bg-blue-400 cursor-not-allowed' 
                    : !isDistributionValid 
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {generating ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Generating Paper...
                  </>
                ) : (
                  <>
                    <FileText className="h-4 w-4" />
                    Generate Question Paper
                  </>
                )}
              </button>
            </form>
          </div>

          {/* micro animation banner for generation progress */}
          {generating && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start gap-3 animate-pulse">
              <RefreshCw className="h-5 w-5 text-blue-600 animate-spin mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="text-sm font-bold text-blue-900">AI Generator in Progress</h4>
                <p className="text-xs text-blue-700 mt-1">{loadingSteps[loadingStep]}</p>
              </div>
            </div>
          )}

          {/* Paper Generation History */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2 border-b pb-2">
              <Info className="h-5 w-5 text-gray-600" />
              Generated Papers History
            </h2>

            {loadingHistory ? (
              <div className="text-center py-6">
                <RefreshCw className="h-6 w-6 animate-spin text-gray-400 mx-auto" />
              </div>
            ) : history.length === 0 ? (
              <div className="text-center py-6 text-sm text-gray-500">
                No question papers generated yet.
              </div>
            ) : (
              <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
                {history.map((paper) => (
                  <div
                    key={paper.id}
                    onClick={() => setActivePaper(paper)}
                    className={`p-3 rounded-lg border text-left cursor-pointer transition-all flex justify-between items-center gap-2 ${
                      activePaper?.id === paper.id
                        ? 'border-blue-500 bg-blue-50 shadow-sm'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <div className="min-w-0 flex-1">
                      <h4 className="text-sm font-bold text-gray-900 truncate">{paper.subject_name}</h4>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {paper.difficulty} • {paper.total_marks} Marks • {paper.duration}
                      </p>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDownloadPDF(paper); }}
                        className="p-1.5 text-gray-500 hover:text-blue-600 rounded hover:bg-white"
                        title="Download PDF"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                      <button
                        onClick={(e) => handleDeletePaper(paper.id, e)}
                        className="p-1.5 text-gray-400 hover:text-red-600 rounded hover:bg-white"
                        title="Delete Paper"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Paper Live Preview Sheet */}
        <div className="lg:col-span-7">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col h-full min-h-[600px]">
            
            {/* Header Tabs */}
            <div className="bg-gray-50 px-6 py-3 border-b flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-gray-900">Live Examination Preview</span>
                {activePaper && (
                  <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 border rounded">
                    ID: #{activePaper.id}
                  </span>
                )}
              </div>
              
              {activePaper && (
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => setShowAnswers(false)}
                    className={`px-3 py-1 text-xs font-semibold rounded-lg border transition-all ${
                      !showAnswers
                        ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Question Paper
                  </button>
                  <button
                    onClick={() => setShowAnswers(true)}
                    className={`px-3 py-1 text-xs font-semibold rounded-lg border transition-all ${
                      showAnswers
                        ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Answer Key
                  </button>
                </div>
              )}
            </div>

            {/* Preview Sheet Container */}
            <div className="flex-1 p-6 sm:p-8 bg-gray-100 overflow-y-auto">
              {!activePaper ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 bg-white rounded-lg border-2 border-dashed border-gray-300 shadow-inner">
                  <FileText className="h-12 w-12 text-gray-400 animate-pulse mb-3" />
                  <h3 className="text-base font-bold text-gray-900">No active paper generated</h3>
                  <p className="text-xs text-gray-500 mt-1 max-w-xs">
                    Adjust the parameters on the left and click "Generate Question Paper" to view the live preview layout here.
                  </p>
                </div>
              ) : (
                <div className="bg-white p-6 sm:p-8 rounded-lg shadow-lg border border-gray-300 font-serif text-gray-900 min-h-full max-w-[800px] mx-auto text-sm select-text">
                  
                  {/* Institutional Header */}
                  <div className="text-center font-bold text-base tracking-wide uppercase border-b-2 border-double border-gray-900 pb-2 mb-4">
                    INSTITUTION SEMESTER EXAMINATION
                    <div className="text-sm font-semibold mt-1">Subject: {activePaper.subject_name.toUpperCase()}</div>
                  </div>

                  {/* Metadata Row */}
                  <div className="grid grid-cols-3 gap-2 border-b border-gray-300 pb-2 mb-4 text-xs font-sans text-gray-700">
                    <div><strong>Duration:</strong> {activePaper.duration}</div>
                    <div className="text-center"><strong>Difficulty:</strong> {activePaper.difficulty}</div>
                    <div className="text-right"><strong>Max Marks:</strong> {activePaper.total_marks} Marks</div>
                  </div>

                  {/* Instructions Block */}
                  <div className="mb-6 font-sans">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-gray-800">General Instructions:</h4>
                    <ul className="list-disc pl-4 mt-1 text-xs text-gray-600 space-y-0.5">
                      <li>Read all questions carefully before attempting solutions.</li>
                      <li>Highlight crucial labels, variables, and formulas.</li>
                      <li>Answer keys/explanations can be verified by toggle above.</li>
                    </ul>
                  </div>

                  {/* Question Groups sorted by Mark value */}
                  {Object.entries(
                    activePaper.paper_content.questions.reduce((groups, q) => {
                      const m = q.marks;
                      if (!groups[m]) groups[m] = [];
                      groups[m].push(q);
                      return groups;
                    }, {})
                  )
                  .sort(([a], [b]) => parseInt(a) - parseInt(b))
                  .map(([marks, qList], sectionIdx) => {
                    const partLabels = ["PART A", "PART B", "PART C", "PART D", "PART E", "PART F"];
                    const partLabel = partLabels[sectionIdx] || `PART ${sectionIdx + 1}`;
                    return (
                      <div key={marks} className="mb-6 border-b border-gray-100 pb-4 last:border-b-0 last:pb-0">
                        
                        {/* Section Part Header */}
                        <div className="font-sans font-bold text-sm bg-gray-100 px-3 py-1.5 border border-gray-200 rounded flex justify-between items-center mb-4">
                          <span>{partLabel} - ({marks} {parseInt(marks) === 1 ? 'Mark' : 'Marks'} Questions)</span>
                          <span className="text-xs font-normal text-gray-500">Answer all questions</span>
                        </div>

                        {/* List Questions */}
                        <div className="space-y-5">
                          {qList.map((q, idx) => (
                            <div key={idx} className="space-y-2">
                              
                              {/* Question Line */}
                              <div className="flex justify-between items-start gap-4">
                                <div className="flex items-start gap-2 flex-1">
                                  <span className="font-bold font-sans">Q{idx + 1}.</span>
                                  <div>
                                    {/* Bloom taxonomy and Question Type indicators */}
                                    <div className="flex items-center gap-1.5 mb-1.5 font-sans print:hidden">
                                      <span className={`text-[10px] px-1.5 py-0.5 font-bold border rounded-full ${getBloomBadgeColor(q.bloom_taxonomy)}`}>
                                        {q.bloom_taxonomy}
                                      </span>
                                      <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-500 border border-gray-200 rounded-full font-bold">
                                        {q.type}
                                      </span>
                                    </div>
                                    <p className="font-medium text-gray-900 font-serif leading-relaxed inline">{q.question}</p>
                                  </div>
                                </div>
                                <span className="font-bold text-gray-900 font-sans flex-shrink-0 text-right">[{marks} Mark]</span>
                              </div>

                              {/* MCQ options if available */}
                              {q.options && q.options.length > 0 && (
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pl-6 pt-1 font-sans">
                                  {q.options.map((opt, optIdx) => {
                                    const letters = ["A", "B", "C", "D"];
                                    const isCorrect = q.answer === opt;
                                    return (
                                      <div 
                                        key={optIdx} 
                                        className={`px-3 py-1.5 rounded-lg border text-xs flex items-center gap-2 ${
                                          showAnswers && isCorrect
                                            ? 'bg-green-50 border-green-300 text-green-800 font-bold'
                                            : 'border-gray-200 bg-gray-50 text-gray-700'
                                        }`}
                                      >
                                        <span className="font-semibold text-gray-400">({letters[optIdx]})</span>
                                        <span className="truncate">{opt}</span>
                                        {showAnswers && isCorrect && (
                                          <CheckCircle className="h-3.5 w-3.5 text-green-600 ml-auto flex-shrink-0" />
                                        )}
                                      </div>
                                    );
                                  })}
                                </div>
                              )}

                              {/* Answer / Evaluation Rubric Row */}
                              {showAnswers && (
                                <div className="mt-3 pl-6 pr-4 py-3.5 bg-green-50 border border-green-200 rounded-xl font-sans space-y-3">
                                  <div className="flex items-center gap-1.5 text-green-800 font-bold text-xs border-b border-green-200 pb-1.5">
                                    <CheckCircle className="h-3.5 w-3.5 text-green-600" />
                                    Evaluation Rubric & Grading Guidelines
                                  </div>

                                  {/* Ideal Answer Length */}
                                  <div className="flex items-center gap-2 text-xs">
                                    <span className="font-bold text-green-800">Expected Answer Length:</span>
                                    <span className="px-2 py-0.5 bg-white text-green-700 rounded-md font-semibold border border-green-200">
                                      {q.answer_key_details?.ideal_length || "N/A"}
                                    </span>
                                  </div>

                                  {/* Keywords */}
                                  {q.answer_key_details?.keywords && q.answer_key_details.keywords.length > 0 && (
                                    <div className="space-y-1">
                                      <div className="text-xs font-bold text-green-800">Essential Keywords:</div>
                                      <div className="flex flex-wrap gap-1.5 pt-0.5">
                                        {q.answer_key_details.keywords.map((kw, kwIdx) => (
                                          <span key={kwIdx} className="px-2 py-0.5 text-[10px] bg-white text-green-700 font-semibold border border-green-200 rounded-full">
                                            {kw}
                                          </span>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  {/* Expected Concepts */}
                                  {q.answer_key_details?.expected_concepts && q.answer_key_details.expected_concepts.length > 0 && (
                                    <div className="space-y-1">
                                      <div className="text-xs font-bold text-green-800">Expected Conceptual Coverage:</div>
                                      <ul className="list-disc pl-4 text-xs text-green-700 space-y-0.5">
                                        {q.answer_key_details.expected_concepts.map((concept, cIdx) => (
                                          <li key={cIdx}>{concept}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}

                                  {/* Marking Scheme Breakdown */}
                                  {q.answer_key_details?.marking_scheme && q.answer_key_details.marking_scheme.length > 0 && (
                                    <div className="space-y-1.5">
                                      <div className="text-xs font-bold text-green-800">Marking Scheme Breakdown:</div>
                                      <div className="bg-white border border-green-200 rounded-lg p-2.5 space-y-1.5 shadow-sm">
                                        {q.answer_key_details.marking_scheme.map((step, sIdx) => (
                                          <div key={sIdx} className="flex justify-between items-center text-xs text-green-800">
                                            <span>• {step.criteria}</span>
                                            <span className="font-bold border-l border-green-200 pl-2 ml-2 flex-shrink-0">
                                              {step.marks} Mark{step.marks > 1 ? 's' : ''}
                                            </span>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  {/* Model Answer */}
                                  {q.type !== "MCQ" && (
                                    <div className="space-y-1">
                                      <div className="text-xs font-bold text-green-800">Model Answer / Explanation:</div>
                                      <p className="text-xs text-green-700 leading-relaxed bg-white/70 p-2.5 rounded-lg border border-green-200">
                                        {q.answer_key_details?.model_answer || q.answer}
                                      </p>
                                    </div>
                                  )}

                                </div>
                              )}

                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                  
                </div>
              )}
            </div>

          </div>
        </div>

      </div>
    </div>
  );
};

export default GeneratePaper;
