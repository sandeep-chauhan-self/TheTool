import { useState } from 'react';
import { verifyBulkPassword } from '../api/api';

/**
 * Password modal that gates multi-stock analysis.
 * Explains why password is required and provides contact info.
 *
 * Props:
 *   onClose   - called when the user dismisses the modal
 *   onSuccess - called when the password is verified successfully
 */
function PasswordModal({ onClose, onSuccess }) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!password.trim()) {
      setError('Please enter a password');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const result = await verifyBulkPassword(password);
      if (result.authorized) {
        // Cache in sessionStorage so the user only enters once per tab
        sessionStorage.setItem('bulkAnalysisVerified', 'true');
        onSuccess();
      } else {
        setError(result.message || 'Incorrect password');
      }
    } catch (err) {
      if (err.response?.status === 403) {
        setError('Incorrect password. Please try again.');
      } else {
        setError('Verification failed. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-amber-500 to-orange-500 px-6 py-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              🔒 Password Required
            </h2>
            <button
              onClick={onClose}
              className="text-white hover:text-amber-100 transition-colors text-xl leading-none"
            >
              ×
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4">
          {/* Explanation */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-900 space-y-2">
            <p>
              <strong>⚠️ Multiple stock analysis</strong> causes heavy load on the server and
              consumes API tokens. To prevent abuse, this feature is password-protected.
            </p>
            <p>
              Please ask the owner of the website for the password:
            </p>
            <ul className="list-disc list-inside space-y-1 ml-1">
              <li>
                Email:{' '}
                <a href="mailto:Sandeepchauhan10401@gmail.com" className="text-blue-600 hover:underline font-medium">
                  Sandeepchauhan10401@gmail.com
                </a>
              </li>
              <li>
                LinkedIn:{' '}
                <a
                  href="https://www.linkedin.com/in/sandeep-chauhan-243012181/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline font-medium"
                >
                  Sandeep Chauhan
                </a>
              </li>
            </ul>
          </div>

          {/* Single stock suggestion */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
            <strong>💡 Tip:</strong> Single stock analysis is freely available — try analyzing
            one stock at a time instead!
          </div>

          {/* Password form */}
          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <label htmlFor="bulk-password" className="block text-sm font-medium text-gray-700 mb-1">
                Enter Password
              </label>
              <input
                id="bulk-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter the bulk analysis password"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 text-sm"
                autoFocus
                disabled={loading}
              />
            </div>

            {error && (
              <p className="text-red-600 text-sm font-medium">
                ❌ {error}
              </p>
            )}

            <div className="flex gap-3 pt-1">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:bg-gray-400 font-medium text-sm transition-colors"
              >
                {loading ? 'Verifying...' : 'Verify & Proceed'}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default PasswordModal;
