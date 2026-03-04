import React, { useState } from 'react';
import { RefreshCw, X } from 'lucide-react';
import Button from './Button';
import Spinner from './Spinner';

interface RegenerateDialogProps {
  onRegenerate: (instructions: string) => Promise<void>;
  onClose: () => void;
  isRegenerating: boolean;
  initialInstructions?: string;
}

const RegenerateDialog: React.FC<RegenerateDialogProps> = ({ onRegenerate, onClose, isRegenerating, initialInstructions = '' }) => {
  const [instructions, setInstructions] = useState(initialInstructions);

  const handleSubmit = async () => {
    if (!instructions.trim()) return;
    await onRegenerate(instructions);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-2xl max-w-lg w-full p-6 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-blue-500" />
            <h3 className="text-lg font-semibold text-white">
              Regenerate SEO Content
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
            disabled={isRegenerating}
          >
            <X size={20} />
          </button>
        </div>

        {/* Instructions */}
        <div className="space-y-2">
          <label className="text-sm text-gray-300 font-medium">
            What would you like to improve or change?
          </label>
          <textarea
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="e.g., Make it more professional, add luxury keywords, focus on eco-friendly aspects, use simpler language..."
            className="w-full h-32 px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none resize-none text-sm"
            disabled={isRegenerating}
          />
          <p className="text-xs text-gray-400">
            Be specific about what you want to see in the regenerated content
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 pt-2">
          <Button
            variant="secondary"
            size="md"
            onClick={onClose}
            disabled={isRegenerating}
            className="flex-1"
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={handleSubmit}
            disabled={!instructions.trim() || isRegenerating}
            className="flex-1"
          >
            {isRegenerating ? (
              <>
                <Spinner size="sm" className="mr-2" />
                Regenerating...
              </>
            ) : (
              <>
                <RefreshCw size={16} className="mr-2" />
                Regenerate
              </>
            )}
          </Button>
        </div>

        {/* Helper Text */}
        <div className="pt-2 border-t border-gray-700">
          <p className="text-xs text-gray-400 leading-relaxed">
            💡 <span className="font-medium">Tip:</span> The AI will use your original product images and current analysis as context while incorporating your feedback.
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegenerateDialog;
