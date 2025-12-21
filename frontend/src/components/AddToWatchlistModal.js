import React, { useCallback, useEffect, useState } from 'react';
import { addStocksToCollection, createWatchlistCollection, getWatchlistCollections } from '../api/api';

function AddToWatchlistModal({ stocks, onClose, onSuccess }) {
  const [collections, setCollections] = useState([]);
  const [selectedCollection, setSelectedCollection] = useState(null); // null = Default
  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Load collections on mount
  useEffect(() => {
    loadCollections();
  }, []);

  const loadCollections = async () => {
    try {
      setLoading(true);
      const data = await getWatchlistCollections();
      setCollections(data);
      setError(null);
    } catch (err) {
      console.error('Failed to load collections:', err);
      setError('Failed to load watchlists');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCollection = useCallback(async () => {
    if (!newCollectionName.trim()) {
      setError('Please enter a name for the new watchlist');
      return;
    }

    try {
      setSubmitting(true);
      const result = await createWatchlistCollection(newCollectionName.trim());
      // Add to local state and select it
      const newCollection = {
        id: result.id,
        name: result.name,
        description: result.description,
        stock_count: 0
      };
      setCollections(prev => [...prev, newCollection]);
      setSelectedCollection(result.id);
      setIsCreatingNew(false);
      setNewCollectionName('');
      setError(null);
    } catch (err) {
      console.error('Failed to create collection:', err);
      if (err.response?.data?.error_code === 'COLLECTION_DUPLICATE') {
        setError('A watchlist with this name already exists');
      } else {
        setError('Failed to create watchlist');
      }
    } finally {
      setSubmitting(false);
    }
  }, [newCollectionName]);

  const handleSubmit = useCallback(async () => {
    try {
      setSubmitting(true);
      // Call API directly with stock objects {symbol, name}
      await addStocksToCollection(stocks, selectedCollection);
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      console.error('Failed to add stocks:', err);
      setError('Failed to add stocks to watchlist');
      setSubmitting(false);
    }
  }, [stocks, selectedCollection, onSuccess, onClose]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">
              Add to Watchlist
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {stocks.length} stock{stocks.length !== 1 ? 's' : ''} selected
          </p>
        </div>

        {/* Content */}
        <div className="px-6 py-4 overflow-y-auto max-h-[60vh]">
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <>
              {/* Error message */}
              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {error}
                </div>
              )}

              {/* Collection selection */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Watchlist
                </label>
                
                {collections.map((collection) => (
                  <label
                    key={collection.id ?? 'default'}
                    className={`flex items-center p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedCollection === collection.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <input
                      type="radio"
                      name="collection"
                      checked={selectedCollection === collection.id}
                      onChange={() => {
                        setSelectedCollection(collection.id);
                        setIsCreatingNew(false);
                      }}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                    />
                    <div className="ml-3 flex-1">
                      <div className="font-medium text-gray-900">{collection.name}</div>
                      <div className="text-xs text-gray-500">
                        {collection.stock_count} stock{collection.stock_count !== 1 ? 's' : ''}
                      </div>
                    </div>
                  </label>
                ))}

                {/* Create new option */}
                <label
                  className={`flex items-center p-3 rounded-lg border cursor-pointer transition-colors ${
                    isCreatingNew
                      ? 'border-green-500 bg-green-50'
                      : 'border-dashed border-gray-300 hover:border-gray-400 hover:bg-gray-50'
                  }`}
                >
                  <input
                    type="radio"
                    name="collection"
                    checked={isCreatingNew}
                    onChange={() => {
                      setIsCreatingNew(true);
                      setSelectedCollection(null);
                    }}
                    className="h-4 w-4 text-green-600 focus:ring-green-500"
                  />
                  <div className="ml-3 flex-1">
                    <div className="font-medium text-green-700">+ Create New Watchlist</div>
                  </div>
                </label>

                {/* New collection name input */}
                {isCreatingNew && (
                  <div className="mt-3 pl-7">
                    <input
                      type="text"
                      value={newCollectionName}
                      onChange={(e) => setNewCollectionName(e.target.value)}
                      placeholder="Enter watchlist name..."
                      maxLength={50}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm"
                      autoFocus
                    />
                    <button
                      onClick={handleCreateCollection}
                      disabled={!newCollectionName.trim() || submitting}
                      className="mt-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 text-sm font-medium transition-colors"
                    >
                      {submitting ? 'Creating...' : 'Create Watchlist'}
                    </button>
                  </div>
                )}
              </div>

              {/* Selected stocks preview */}
              <div className="mt-6">
                <h3 className="text-sm font-medium text-gray-700 mb-2">
                  Stocks to Add
                </h3>
                <div className="max-h-32 overflow-y-auto bg-gray-50 rounded-lg p-3">
                  <div className="flex flex-wrap gap-2">
                    {stocks.slice(0, 20).map((stock) => (
                      <span
                        key={stock.symbol || stock}
                        className="px-2 py-1 bg-white border border-gray-200 rounded text-xs font-mono text-gray-700"
                      >
                        {stock.symbol || stock}
                      </span>
                    ))}
                    {stocks.length > 20 && (
                      <span className="px-2 py-1 text-xs text-gray-500">
                        +{stocks.length - 20} more
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={submitting || loading || (isCreatingNew && !selectedCollection)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium transition-colors"
            >
              {submitting ? 'Adding...' : `Add ${stocks.length} Stock${stocks.length !== 1 ? 's' : ''}`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AddToWatchlistModal;
