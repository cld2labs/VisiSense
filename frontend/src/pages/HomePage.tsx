import { useState } from 'react';
import { Sparkles, FileText, Tags, AlertCircle, CheckCircle2, Send, Upload, Info, Package, RefreshCw, Download, TrendingUp } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import GlowCard from '../components/ui/GlowCard';
import Spinner from '../components/ui/Spinner';
import ConfirmationDialog from '../components/ui/ConfirmationDialog';
import RegenerateDialog from '../components/ui/RegenerateDialog';
import { analyzeProductStream, sendChatMessage, ValidationWarningError, regenerateSection, enhanceSEO } from '../services/api';
import { AnalyzeResponse, ProcessingStatus, ValidationWarning } from '../types/catalog';

// Helper function to get confidence badge variant and description
const getConfidenceInfo = (confidence: number, isCritical: boolean = false) => {
  if (confidence >= 0.8) {
    return {
      variant: 'success' as const,
      label: 'High',
      description: 'Highly reliable - Ready to use',
      icon: '✓'
    };
  } else if (confidence >= 0.7) {
    return {
      variant: 'cyan' as const,
      label: 'Good',
      description: 'Reliable - Minor review recommended',
      icon: '○'
    };
  } else if (confidence >= 0.5) {
    return {
      variant: 'warning' as const,
      label: 'Medium',
      description: isCritical ? 'Requires review before publishing' : 'Review recommended',
      icon: '⚠'
    };
  } else {
    return {
      variant: 'error' as const,
      label: 'Low',
      description: isCritical ? 'CRITICAL: Must verify before use' : 'Verification needed',
      icon: '⚠'
    };
  }
};

// Critical attributes that must be accurate
const CRITICAL_ATTRIBUTES = ['color', 'material'];

export default function HomePage() {
  const [images, setImages] = useState<File[]>([]);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [status, setStatus] = useState('');
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showConfidenceGuide, setShowConfidenceGuide] = useState(false);
  const [validationWarning, setValidationWarning] = useState<ValidationWarning | null>(null);
  const [showRegenerateDialog, setShowRegenerateDialog] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [showAllIssues, setShowAllIssues] = useState(false);
  const [showAllRecommendations, setShowAllRecommendations] = useState(false);
  const [quickFixInstruction, setQuickFixInstruction] = useState<string>('');
  const [fixingIssueIndex, setFixingIssueIndex] = useState<number | null>(null);

  // Chat state
  const [chatMessages, setChatMessages] = useState<Array<{role: 'user' | 'assistant', content: string}>>([]);
  const [chatInput, setChatInput] = useState('');
  const [isSendingChat, setIsSendingChat] = useState(false);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/webp': ['.webp']
    },
    maxSize: 10 * 1024 * 1024,
    maxFiles: 5,
    multiple: true,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setImages(acceptedFiles);

        // Create preview URL for first image
        const reader = new FileReader();
        reader.onloadend = () => {
          setImagePreview(reader.result as string);
        };
        reader.readAsDataURL(acceptedFiles[0]);

        // Reset previous results
        setResult(null);
        setError(null);
        setChatMessages([]);
      }
    }
  });

  const handleAnalyze = async (overrideValidation: boolean = false) => {
    if (images.length === 0) return;

    setIsAnalyzing(true);
    setStatus('Preparing analysis...');
    setError(null);
    setResult(null);
    setValidationWarning(null);

    try {
      for await (const event of analyzeProductStream(images, undefined, overrideValidation)) {
        if ('step' in event) {
          const statusEvent = event as ProcessingStatus;
          setStatus(statusEvent.message || 'Processing...');
        } else {
          const responseEvent = event as AnalyzeResponse;
          setResult(responseEvent);
          setStatus('Analysis complete!');
        }
      }
    } catch (err) {
      console.error('Analysis failed:', err);

      // Handle validation warning (soft warning with user confirmation)
      if (err instanceof ValidationWarningError) {
        setValidationWarning(err.warning);
        setStatus('');
      } else {
        // Handle hard errors (content policy, parsing errors, etc.)
        setError(err instanceof Error ? err.message : 'Analysis failed. Please try again.');
        setStatus('');
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleConfirmAnalysis = () => {
    setValidationWarning(null);
    handleAnalyze(true); // Retry with override
  };

  const handleCancelAnalysis = () => {
    setValidationWarning(null);
  };

  const handleRegenerate = async (instructions: string) => {
    if (!result) return;

    setIsRegenerating(true);
    try {
      const response = await regenerateSection(result.session_id, 'seo_content', instructions);

      // Update result with new content AND new SEO score
      setResult({
        ...result,
        content_package: {
          ...result.content_package,
          titles_descriptions: response.updated_content
        },
        seo_score: response.seo_score  // Update score
      });

      setShowRegenerateDialog(false);

      // Show improvement message if available
      if (response.improvement && response.improvement !== 0) {
        console.log(`SEO Score ${response.improvement > 0 ? 'improved' : 'changed'} by ${response.improvement > 0 ? '+' : ''}${response.improvement}%`);
      }
    } catch (err) {
      console.error('Regeneration failed:', err);
      setError(err instanceof Error ? err.message : 'Regeneration failed. Please try again.');
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleQuickFix = async (issue: string, issueIndex: number) => {
    if (!result) return;

    setFixingIssueIndex(issueIndex);
    try {
      const response = await regenerateSection(result.session_id, 'seo_content', `Fix this issue: ${issue}`);

      // Update result with new content AND new SEO score
      setResult({
        ...result,
        content_package: {
          ...result.content_package,
          titles_descriptions: response.updated_content
        },
        seo_score: response.seo_score  // Update score
      });

      // Show improvement message
      if (response.improvement && response.improvement !== 0) {
        console.log(`✅ Issue fixed! SEO Score ${response.improvement > 0 ? 'improved' : 'changed'} by ${response.improvement > 0 ? '+' : ''}${response.improvement}%`);
      }
    } catch (err) {
      console.error('Quick fix failed:', err);
      setError(err instanceof Error ? err.message : 'Quick fix failed. Please try again.');
    } finally {
      setFixingIssueIndex(null);
    }
  };

  const handleEnhanceSEO = async () => {
    if (!result) return;

    setIsEnhancing(true);
    try {
      const response = await enhanceSEO(result.session_id);

      // Update result with enhanced content and new SEO score
      setResult({
        ...result,
        content_package: {
          ...result.content_package,
          titles_descriptions: response.updated_content
        },
        seo_score: response.seo_score
      });

      // Show success message
      console.log(`SEO Score improved by +${response.improvement} points!`);
    } catch (err) {
      console.error('Enhancement failed:', err);
      setError(err instanceof Error ? err.message : 'Enhancement failed. Please try again.');
    } finally {
      setIsEnhancing(false);
    }
  };

  const handleExport = () => {
    if (!result) return;

    const { content_package } = result;

    // Create export object with only business-relevant data
    const exportData = {
      product_identity: {
        category: content_package.product_identity.category,
        subcategory: content_package.product_identity.subcategory,
        price_positioning: content_package.product_identity.price_positioning,
        marketing_tagline: content_package.product_identity.marketing_tagline
      },
      titles_descriptions: content_package.titles_descriptions,
      attributes: {
        material: content_package.attributes.material.value,
        color: content_package.attributes.color.value,
        style: content_package.attributes.style.value,
        finish: content_package.attributes.finish.value,
        target_demographic: content_package.attributes.target_demographic.value,
        occasion: content_package.attributes.occasion.value
      },
      feature_highlights: content_package.feature_highlights,
      seo_keywords: content_package.seo_keywords,
      sku_intelligence: content_package.sku_intelligence
    };

    // Create and download JSON file
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `product-analysis-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleSendChat = async () => {
    if (!chatInput.trim() || !result || isSendingChat) return;

    const userMessage = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsSendingChat(true);

    try {
      const response = await sendChatMessage({
        session_id: result.session_id,
        message: userMessage,
        history: chatMessages
      });

      setChatMessages(prev => [...prev, { role: 'assistant', content: response.message.content }]);
    } catch (err) {
      console.error('Chat failed:', err);
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your message.'
      }]);
    } finally {
      setIsSendingChat(false);
    }
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Validation Warning Dialog */}
      {validationWarning && (
        <ConfirmationDialog
          warning={validationWarning}
          onConfirm={handleConfirmAnalysis}
          onCancel={handleCancelAnalysis}
        />
      )}

      {/* Regenerate Dialog */}
      {showRegenerateDialog && (
        <RegenerateDialog
          onRegenerate={handleRegenerate}
          onClose={() => {
            setShowRegenerateDialog(false);
            setQuickFixInstruction('');
          }}
          isRegenerating={isRegenerating}
          initialInstructions={quickFixInstruction}
        />
      )}

      {/* Compact Header */}
      <div className="px-6 py-3 border-b border-border-subtle flex-shrink-0">
        <h1 className="text-2xl font-bold gradient-text">Visual Product Intelligence</h1>
      </div>

      {/* Main Content - Full Height */}
      <div className="flex-1 grid grid-cols-12 gap-4 p-4 overflow-hidden min-h-0">
        {/* Left Column - Scrollable (6 cols = 50%) */}
        <div className="col-span-6 flex flex-col space-y-3 overflow-hidden">
          {/* Upload Section - Fixed */}
          <GlowCard className="p-4 flex-shrink-0">
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-3 text-center cursor-pointer transition-all ${
                isDragActive
                  ? 'border-accent-cyan bg-accent-cyan bg-opacity-5'
                  : 'border-border-accent hover:border-accent-cyan'
              }`}
            >
              <input {...getInputProps()} />
              <Upload className="w-6 h-6 mx-auto text-accent-cyan" />
            </div>
            <div className="text-xs text-text-muted text-center mt-2 space-y-1">
              <p>JPG, PNG, WEBP • Max 10MB per image</p>
              <p className="text-text-secondary">• Upload 1-5 product images</p>
              <p className="text-text-secondary">• Best results with clear, well-lit photos</p>
            </div>
            {images.length > 0 && (
              <Button
                variant="primary"
                size="sm"
                fullWidth
                disabled={isAnalyzing}
                onClick={() => handleAnalyze()}
                className="mt-3"
              >
                {isAnalyzing ? (
                  <>
                    <Spinner size="sm" className="mr-2" />
                    {status}
                  </>
                ) : (
                  'Analyze Product'
                )}
              </Button>
            )}
          </GlowCard>

          {/* Error Display */}
          {error && (
            <GlowCard className="p-3 border-2 border-red-500 flex-shrink-0">
              <div className="flex items-start gap-2">
                <AlertCircle className="text-red-500 flex-shrink-0" size={16} />
                <div>
                  <p className="text-red-400 font-medium text-xs">Analysis Failed</p>
                  <p className="text-text-secondary text-xs mt-1">{error}</p>
                </div>
              </div>
            </GlowCard>
          )}

          {/* Scrollable Content Area */}
          <div className="flex-1 overflow-y-auto space-y-3 pr-2">
            {/* Image Preview */}
            {imagePreview && (
              <GlowCard className="p-3">
                <h3 className="text-xs font-semibold text-text-muted mb-2">
                  Product Image{images.length > 1 ? `s (${images.length})` : ''}
                </h3>
                <img
                  src={imagePreview}
                  alt="Product preview"
                  className="w-full rounded-lg"
                />
                {images.length > 1 && (
                  <p className="text-xs text-text-secondary mt-2 text-center">
                    Showing first image • {images.length - 1} more uploaded
                  </p>
                )}
              </GlowCard>
            )}

            {/* SEO Content & Attributes */}
            {result && (
              <>
                {/* Export Button */}
                <Button
                  variant="secondary"
                  size="sm"
                  fullWidth
                  onClick={handleExport}
                  className="flex items-center justify-center gap-2"
                >
                  <Download size={14} />
                  Export to JSON
                </Button>

                {/* Product Identity */}
                <GlowCard className="p-3">
                  <h3 className="text-xs font-semibold text-text-muted mb-2 flex items-center gap-2">
                    <Tags size={14} />
                    Product Identity
                  </h3>
                  <div className="space-y-1.5">
                    <div>
                      <span className="text-xs text-text-secondary">Category:</span>
                      <span className="text-xs text-text-primary font-medium ml-2">
                        {result.content_package.product_identity.category}
                      </span>
                    </div>
                    {result.content_package.product_identity.subcategory && (
                      <div>
                        <span className="text-xs text-text-secondary">Subcategory:</span>
                        <span className="text-xs text-text-primary font-medium ml-2">
                          {result.content_package.product_identity.subcategory}
                        </span>
                      </div>
                    )}
                    <div>
                      <span className="text-xs text-text-secondary">Positioning:</span>
                      <Badge variant="cyan" size="sm" className="ml-2">
                        {result.content_package.product_identity.price_positioning}
                      </Badge>
                    </div>
                  </div>
                </GlowCard>

                {/* Titles & Descriptions (SEO Content) */}
                <GlowCard className="p-3">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xs font-semibold text-text-muted flex items-center gap-2">
                      <FileText size={14} />
                      SEO Content
                    </h3>
                    <button
                      onClick={() => {
                        setQuickFixInstruction('');
                        setShowRegenerateDialog(true);
                      }}
                      className="flex items-center gap-1 text-xs text-accent-cyan hover:text-accent-cyan-bright transition-colors"
                      title="Regenerate SEO content with custom instructions"
                    >
                      <RefreshCw size={12} />
                      Regenerate
                    </button>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <p className="text-xs text-text-secondary mb-1">SEO Title:</p>
                      <p className="text-xs text-text-primary font-medium">
                        {result.content_package.titles_descriptions.seo_title}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-text-secondary mb-1">Short Description:</p>
                      <p className="text-xs text-text-primary">
                        {result.content_package.titles_descriptions.short_description}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-text-secondary mb-1">Long Description:</p>
                      <p className="text-xs text-text-primary leading-relaxed">
                        {result.content_package.titles_descriptions.long_description}
                      </p>
                    </div>
                  </div>
                </GlowCard>

                {/* SEO Quality Score - Moved below SEO Content */}
                <GlowCard className={`p-3 border-2 ${
                  result.seo_score.overall_score >= 80 ? 'border-green-500/50' :
                  result.seo_score.overall_score >= 70 ? 'border-cyan-500/50' :
                  result.seo_score.overall_score >= 60 ? 'border-yellow-500/50' :
                  'border-red-500/50'
                }`}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xs font-semibold text-text-muted flex items-center gap-2">
                      <TrendingUp size={14} />
                      SEO Quality Score
                    </h3>
                    <div className="flex items-center gap-2">
                      <span className={`text-2xl font-bold ${
                        result.seo_score.overall_score >= 80 ? 'text-green-400' :
                        result.seo_score.overall_score >= 70 ? 'text-cyan-400' :
                        result.seo_score.overall_score >= 60 ? 'text-yellow-400' :
                        'text-red-400'
                      }`}>
                        {result.seo_score.overall_score}%
                      </span>
                      <Badge variant={
                        result.seo_score.overall_score >= 80 ? 'success' :
                        result.seo_score.overall_score >= 70 ? 'cyan' :
                        result.seo_score.overall_score >= 60 ? 'warning' :
                        'error'
                      } size="sm">
                        {result.seo_score.grade}
                      </Badge>
                    </div>
                  </div>

                  <p className="text-xs text-text-secondary mb-3">{result.seo_score.grade_label}</p>

                  {/* Category Scores */}
                  <div className="space-y-1.5 mb-3">
                    {Object.entries(result.seo_score.category_scores).map(([category, points]) => {
                      const maxPoints = result.seo_score.category_max_points || 20;
                      const percentage = result.seo_score.category_percentages?.[category] || ((points / maxPoints) * 100);
                      const isPerfect = points === maxPoints;

                      return (
                        <div key={category} className="flex items-center gap-2">
                          <span className="text-xs text-text-secondary capitalize flex-1">
                            {category.replace('_', ' ')}
                          </span>
                          <div className="flex-1 bg-bg-secondary rounded-full h-1.5">
                            <div
                              className={`h-full rounded-full transition-all ${
                                percentage >= 90 ? 'bg-green-500' :
                                percentage >= 75 ? 'bg-cyan-500' :
                                percentage >= 60 ? 'bg-yellow-500' :
                                'bg-red-500'
                              }`}
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                          <span className={`text-xs font-medium w-24 text-right flex items-center justify-end gap-1 ${
                            isPerfect ? 'text-green-400' : 'text-text-primary'
                          }`}>
                            {Math.round(points)}/{maxPoints}
                            <span className="text-text-muted">({Math.round(percentage)}%)</span>
                            {isPerfect && <span className="text-green-400">✓</span>}
                          </span>
                        </div>
                      );
                    })}
                  </div>

                  {/* Total Points Display */}
                  <div className="text-xs text-text-muted text-center mb-3 pb-3 border-b border-border-subtle">
                    Total: {Math.round(Object.values(result.seo_score.category_scores).reduce((a, b) => a + b, 0))} / {result.seo_score.total_possible_points || 120} points
                  </div>

                  {/* Issues (if any) */}
                  {result.seo_score.issues.length > 0 && (
                    <div className="mb-2">
                      <p className="text-xs font-semibold text-red-400 mb-1">Issues ({result.seo_score.issues.length}):</p>
                      <ul className="space-y-1.5">
                        {(showAllIssues ? result.seo_score.issues : result.seo_score.issues.slice(0, 3)).map((issue, idx) => {
                          const isFixing = fixingIssueIndex === idx;
                          return (
                            <li key={idx} className="text-xs text-text-secondary flex items-start justify-between gap-2 group">
                              <div className="flex items-start gap-1.5 flex-1">
                                <span className="text-red-400 mt-0.5">•</span>
                                <span className="flex-1">{issue}</span>
                              </div>
                              <button
                                onClick={() => handleQuickFix(issue, idx)}
                                disabled={isFixing || fixingIssueIndex !== null}
                                className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs transition-all ${
                                  isFixing
                                    ? 'bg-accent-cyan/20 text-accent-cyan opacity-100'
                                    : 'bg-accent-cyan/10 text-accent-cyan hover:bg-accent-cyan/20 opacity-0 group-hover:opacity-100'
                                } ${fixingIssueIndex !== null && !isFixing ? 'opacity-50 cursor-not-allowed' : ''}`}
                                title={isFixing ? "Fixing..." : "Quick fix this issue"}
                              >
                                {isFixing ? (
                                  <>
                                    <Spinner size="sm" />
                                    <span>Fixing...</span>
                                  </>
                                ) : (
                                  <>
                                    <span>⚡</span>
                                    <span>Fix</span>
                                  </>
                                )}
                              </button>
                            </li>
                          );
                        })}
                        {result.seo_score.issues.length > 3 && (
                          <li>
                            <button
                              onClick={() => setShowAllIssues(!showAllIssues)}
                              className="text-xs text-accent-cyan hover:text-accent-cyan-bright transition-colors underline"
                            >
                              {showAllIssues ? 'Show less' : `+${result.seo_score.issues.length - 3} more issues`}
                            </button>
                          </li>
                        )}
                      </ul>
                    </div>
                  )}

                  {/* Recommendations */}
                  {result.seo_score.recommendations.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-cyan-400 mb-1">Recommendations ({result.seo_score.recommendations.length}):</p>
                      <ul className="space-y-0.5">
                        {(showAllRecommendations ? result.seo_score.recommendations : result.seo_score.recommendations.slice(0, 2)).map((rec, idx) => (
                          <li key={idx} className="text-xs text-text-secondary flex items-start gap-1.5">
                            <span className="text-cyan-400 mt-0.5">→</span>
                            <span>{rec}</span>
                          </li>
                        ))}
                        {result.seo_score.recommendations.length > 2 && (
                          <li>
                            <button
                              onClick={() => setShowAllRecommendations(!showAllRecommendations)}
                              className="text-xs text-accent-cyan hover:text-accent-cyan-bright transition-colors underline"
                            >
                              {showAllRecommendations ? 'Show less' : `+${result.seo_score.recommendations.length - 2} more recommendations`}
                            </button>
                          </li>
                        )}
                      </ul>
                    </div>
                  )}

                  {/* Enhance Button (if score < 85) */}
                  {result.seo_score.overall_score < 85 && (
                    <Button
                      variant="primary"
                      size="sm"
                      fullWidth
                      disabled={isEnhancing}
                      onClick={handleEnhanceSEO}
                      className="mt-3"
                    >
                      {isEnhancing ? (
                        <>
                          <Spinner size="sm" className="mr-2" />
                          Enhancing...
                        </>
                      ) : (
                        <>
                          <TrendingUp size={14} className="mr-2" />
                          Auto-Enhance SEO
                        </>
                      )}
                    </Button>
                  )}
                </GlowCard>

                {/* SEO Keywords */}
                <GlowCard className="p-3">
                  <h3 className="text-xs font-semibold text-text-muted mb-2">SEO Keywords</h3>
                  <div className="space-y-2">
                    <div>
                      <p className="text-xs text-text-secondary mb-1">Primary:</p>
                      <div className="flex flex-wrap gap-1">
                        {result.content_package.seo_keywords.primary.map((keyword, idx) => (
                          <Badge key={idx} variant="success" size="sm">
                            {keyword}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-text-secondary mb-1">Long-tail:</p>
                      <div className="flex flex-wrap gap-1">
                        {result.content_package.seo_keywords.long_tail.map((keyword, idx) => (
                          <Badge key={idx} variant="violet" size="sm">
                            {keyword}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </GlowCard>

                {/* Attributes */}
                <GlowCard className="p-3">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xs font-semibold text-text-muted">Product Attributes</h3>
                    <button
                      onClick={() => setShowConfidenceGuide(!showConfidenceGuide)}
                      className="text-accent-cyan hover:text-accent-cyan-bright transition-colors"
                      title="Show confidence guide"
                    >
                      <Info size={14} />
                    </button>
                  </div>

                  {/* Confidence Guide */}
                  {showConfidenceGuide && (
                    <div className="mb-3 p-2 bg-bg-secondary rounded-lg border border-border-accent">
                      <p className="text-xs font-semibold text-text-primary mb-2">Confidence Score Guide:</p>
                      <div className="space-y-1.5">
                        <div className="flex items-start gap-2">
                          <Badge variant="success" size="sm">≥80%</Badge>
                          <span className="text-xs text-text-secondary">High - Highly reliable, ready to use</span>
                        </div>
                        <div className="flex items-start gap-2">
                          <Badge variant="cyan" size="sm">70-79%</Badge>
                          <span className="text-xs text-text-secondary">Good - Reliable, minor review recommended</span>
                        </div>
                        <div className="flex items-start gap-2">
                          <Badge variant="warning" size="sm">50-69%</Badge>
                          <span className="text-xs text-text-secondary">Medium - Review recommended before publishing</span>
                        </div>
                        <div className="flex items-start gap-2">
                          <Badge variant="error" size="sm">&lt;50%</Badge>
                          <span className="text-xs text-text-secondary">Low - Verification required, do not publish</span>
                        </div>
                      </div>
                      <p className="text-xs text-yellow-400 mt-2 flex items-start gap-1">
                        <AlertCircle size={12} className="mt-0.5 flex-shrink-0" />
                        <span><strong>Color</strong> and <strong>Material</strong> are critical attributes that must be accurate</span>
                      </p>
                    </div>
                  )}

                  <div className="space-y-1.5">
                    {Object.entries(result.content_package.attributes).map(([key, attr]) => {
                      const isCritical = CRITICAL_ATTRIBUTES.includes(key);
                      const confInfo = getConfidenceInfo(attr.confidence, isCritical);

                      return (
                        <div key={key} className="flex justify-between items-center">
                          <div className="flex items-center gap-1.5">
                            <span className="text-xs text-text-secondary capitalize">
                              {key.replace('_', ' ')}
                            </span>
                            {isCritical && (
                              <span className="text-xs text-yellow-400" title="Critical attribute">★</span>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`text-xs font-medium ${
                              attr.confidence < 0.5 ? 'text-red-400' :
                              attr.confidence < 0.7 ? 'text-yellow-400' :
                              'text-text-primary'
                            }`}>
                              {attr.value || 'N/A'}
                            </span>
                            <Badge
                              variant={confInfo.variant}
                              size="sm"
                            >
                              {confInfo.icon} {Math.round(attr.confidence * 100)}%
                            </Badge>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </GlowCard>

                {/* Feature Highlights */}
                <GlowCard className="p-3">
                  <h3 className="text-xs font-semibold text-text-muted mb-2">Feature Highlights</h3>
                  <ul className="space-y-1">
                    {result.content_package.feature_highlights.map((feature, idx) => (
                      <li key={idx} className="text-xs text-text-primary flex items-start gap-2">
                        <CheckCircle2 size={12} className="text-accent-cyan mt-0.5 flex-shrink-0" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                </GlowCard>

                {/* SKU Intelligence */}
                <GlowCard className="p-3">
                  <h3 className="text-xs font-semibold text-text-muted mb-2 flex items-center gap-2">
                    <Package size={14} />
                    SKU Intelligence
                  </h3>
                  <div className="space-y-2">
                    <div>
                      <p className="text-xs text-text-secondary mb-1">Suggested SKU:</p>
                      <p className="text-xs text-text-primary font-mono font-medium bg-bg-secondary px-2 py-1 rounded">
                        {result.content_package.sku_intelligence.naming_suggestion}
                      </p>
                      <p className="text-xs text-text-muted mt-1">
                        Note: Verify uniqueness before use
                      </p>
                    </div>

                    {result.content_package.sku_intelligence.variant_signals.length > 0 && (
                      <div>
                        <p className="text-xs text-text-secondary mb-1">Variant Signals:</p>
                        <div className="flex flex-wrap gap-1">
                          {result.content_package.sku_intelligence.variant_signals.map((signal, idx) => (
                            <Badge key={idx} variant="violet" size="sm">
                              {signal}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {result.content_package.sku_intelligence.bundle_pairings.length > 0 && (
                      <div>
                        <p className="text-xs text-text-secondary mb-1">Suggested Pairings:</p>
                        <ul className="space-y-0.5">
                          {result.content_package.sku_intelligence.bundle_pairings.map((pairing, idx) => (
                            <li key={idx} className="text-xs text-text-primary flex items-start gap-1.5">
                              <span className="text-accent-cyan">•</span>
                              <span>{pairing}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </GlowCard>

                {/* AI Disclaimer */}
                <div className="p-3 bg-amber-900/20 border border-amber-500/30 rounded-lg">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="text-amber-500 flex-shrink-0 mt-0.5" size={14} />
                    <p className="text-xs text-amber-200/90 leading-relaxed">
                      <span className="font-semibold">Disclaimer:</span> This content was generated by AI and should be reviewed and verified before use. While our system strives for accuracy, AI-generated content may contain errors or require human validation.
                    </p>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Right Column - Chat Interface (6 cols = 50%) */}
        <div className="col-span-6 flex flex-col overflow-hidden">
          <GlowCard className="h-full flex flex-col p-4">
            <h3 className="text-lg font-bold mb-3 gradient-text">Product Q&A Chat</h3>

            {!result ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <Sparkles className="w-12 h-12 mx-auto mb-3 text-accent-cyan opacity-50" />
                  <p className="text-text-muted">Upload and analyze an image to start chatting</p>
                </div>
              </div>
            ) : (
              <>
                {/* Suggested Questions */}
                {chatMessages.length === 0 && result.suggested_questions && (
                  <div className="mb-3">
                    <p className="text-xs text-text-muted mb-2">Suggested questions:</p>
                    <div className="flex flex-wrap gap-2">
                      {result.suggested_questions.slice(0, 3).map((q, idx) => (
                        <button
                          key={idx}
                          onClick={() => {
                            setChatInput(q);
                            setTimeout(() => handleSendChat(), 100);
                          }}
                          className="text-xs px-3 py-1.5 rounded-full border border-accent-cyan text-accent-cyan hover:bg-accent-cyan hover:bg-opacity-10 transition-all"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Chat Messages */}
                <div className="flex-1 overflow-y-auto space-y-3 mb-3">
                  {chatMessages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg px-4 py-2 ${
                          msg.role === 'user'
                            ? 'bg-accent-cyan bg-opacity-20 text-text-primary'
                            : 'bg-bg-secondary text-text-secondary'
                        }`}
                      >
                        <p className="text-sm">{msg.content}</p>
                      </div>
                    </div>
                  ))}
                  {isSendingChat && (
                    <div className="flex justify-start">
                      <div className="bg-bg-secondary rounded-lg px-4 py-2">
                        <Spinner size="sm" />
                      </div>
                    </div>
                  )}
                </div>

                {/* Chat Input */}
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendChat()}
                    placeholder="Ask about this product..."
                    className="flex-1 px-4 py-2 rounded-lg bg-bg-secondary border border-border-subtle focus:border-accent-cyan focus:outline-none text-text-primary text-sm"
                    disabled={isSendingChat}
                  />
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handleSendChat}
                    disabled={!chatInput.trim() || isSendingChat}
                  >
                    <Send size={18} />
                  </Button>
                </div>
              </>
            )}
          </GlowCard>
        </div>
      </div>
    </div>
  );
}
