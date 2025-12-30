import { Link, useLocation } from 'react-router-dom';

/**
 * Breadcrumbs Component - Light theme with clean UI
 * 
 * Props:
 *   - items: Array of { label: string, path?: string }
 *            Last item is current page (no link)
 *   - className: Additional CSS classes
 */
const Breadcrumbs = ({ items = [], className = '' }) => {
  const location = useLocation();

  // Default breadcrumbs based on current path if no items provided
  const defaultItems = () => {
    const pathSegments = location.pathname.split('/').filter(Boolean);
    const breadcrumbs = [{ label: 'Dashboard', path: '/' }];
    
    const pathMap = {
      'all-stocks': { label: 'All Stocks', path: '/all-stocks' },
      'strategies': { label: 'Strategies', path: '/strategies' },
      'results': { label: 'Results', path: null },
      'backtest': { label: 'Backtest', path: null },
      'config': { label: 'Config', path: null }
    };

    pathSegments.forEach((segment, index) => {
      if (pathMap[segment]) {
        breadcrumbs.push(pathMap[segment]);
      } else if (index === pathSegments.length - 1 && !pathMap[segment]) {
        // Last segment that's not in pathMap (likely a dynamic param)
        breadcrumbs.push({ label: segment, path: null });
      }
    });

    return breadcrumbs;
  };

  const breadcrumbItems = items.length > 0 ? items : defaultItems();

  return (
    <nav className={`mb-6 ${className}`} aria-label="Breadcrumb">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 px-4 py-3">
        <ol className="flex items-center flex-wrap gap-1 text-sm">
          {/* Home Icon */}
          <li className="flex items-center">
            <Link 
              to="/" 
              className="text-gray-400 hover:text-blue-600 transition-colors"
              aria-label="Home"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
              </svg>
            </Link>
          </li>

          {breadcrumbItems.map((item, index) => {
            const isLast = index === breadcrumbItems.length - 1;
            const isFirst = index === 0;

            return (
              <li key={index} className="flex items-center">
                {/* Separator */}
                <svg 
                  className="w-4 h-4 text-gray-300 mx-2" 
                  fill="currentColor" 
                  viewBox="0 0 20 20"
                >
                  <path 
                    fillRule="evenodd" 
                    d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" 
                    clipRule="evenodd" 
                  />
                </svg>

                {/* Breadcrumb Item */}
                {isLast || !item.path ? (
                  <span className={`font-medium ${isLast ? 'text-blue-600' : 'text-gray-500'}`}>
                    {item.label}
                  </span>
                ) : (
                  <Link
                    to={item.path}
                    className="text-gray-500 hover:text-blue-600 transition-colors hover:underline"
                  >
                    {item.label}
                  </Link>
                )}
              </li>
            );
          })}
        </ol>
      </div>
    </nav>
  );
};

export default Breadcrumbs;
