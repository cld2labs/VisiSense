import React from 'react';
import { ValidationWarning } from '../../types/catalog';

interface ConfirmationDialogProps {
  warning: ValidationWarning;
  onConfirm: () => void;
  onCancel: () => void;
}

const ConfirmationDialog: React.FC<ConfirmationDialogProps> = ({ warning, onConfirm, onCancel }) => {
  const getImageTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'infographic': 'infographic or diagram',
      'scenic_photo': 'scenic photo or landscape',
      'text_content': 'text-heavy content',
      'artwork': 'artwork or illustration',
      'other': 'non-standard content'
    };
    return labels[type] || type;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl max-w-md w-full p-6 space-y-4 animate-fade-in">
        {/* Warning Icon */}
        <div className="flex items-center space-x-3">
          <div className="flex-shrink-0 w-12 h-12 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
            <svg
              className="w-6 h-6 text-amber-600 dark:text-amber-500"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Product Type Confirmation
            </h3>
            <p className="text-sm text-amber-600 dark:text-amber-500">
              Image appears to be {getImageTypeLabel(warning.image_type)}
            </p>
          </div>
        </div>

        {/* Warning Message */}
        <div className="space-y-2">
          <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
            {warning.reason}
          </p>

          <div className="bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 p-3 rounded">
            <p className="text-sm text-blue-800 dark:text-blue-300">
              <span className="font-medium">Note:</span> {warning.suggestion}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-3 pt-2">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-gray-400"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2.5 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg font-medium hover:from-blue-600 hover:to-purple-700 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-400 shadow-lg"
          >
            Continue Analysis
          </button>
        </div>

        {/* Helper Text */}
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center pt-2 border-t border-gray-200 dark:border-gray-700">
          You can analyze any product meant for retail sale
        </p>
      </div>
    </div>
  );
};

export default ConfirmationDialog;
