import { Link, useLocation } from 'react-router-dom';

/**
 * Breadcrumbs Component - Premium Light theme
 */
const Breadcrumbs = ({ items = [], className = '' }) => {
  const location = useLocation();

  const defaultItems = () => {
    const pathSegments = location.pathname.split('/').filter(Boolean);
    const breadcrumbs = [{ label: 'Dashboard', path: '/' }];
    
    const pathMap = {
      'all-stocks': { label: 'Inventory', path: '/all-stocks' },
      'strategies': { label: 'Models', path: '/strategies' },
      'results': { label: 'Analysis', path: null },
      'backtest': { label: 'Simulation', path: null },
      'config': { label: 'Engine Config', path: null }
    };

    pathSegments.forEach((segment, index) => {
      if (pathMap[segment]) {
        breadcrumbs.push(pathMap[segment]);
      } else if (index === pathSegments.length - 1 && !pathMap[segment]) {
        breadcrumbs.push({ label: segment.toUpperCase(), path: null });
      }
    });

    return breadcrumbs;
  };

  const breadcrumbItems = items.length > 0 ? items : defaultItems();

  return (
    <nav className={`mb-6 ${className}`} aria-label="Breadcrumb">
      <div className="bg-white/40 backdrop-blur-md rounded-xl border border-white/50 px-5 py-2.5 shadow-sm inline-block">
        <ol className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-widest">
          <li className="flex items-center">
            <Link to="/" className="text-slate-400 hover:text-primary-600 transition-colors">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
              </svg>
            </Link>
          </li>

          {breadcrumbItems.map((item, index) => {
            const isLast = index === breadcrumbItems.length - 1;
            return (
              <li key={index} className="flex items-center">
                <svg className="w-4 h-4 text-slate-300" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>

                {isLast || !item.path ? (
                  <span className={`ml-1.5 ${isLast ? 'text-primary-600' : 'text-slate-400'}`}>
                    {item.label}
                  </span>
                ) : (
                  <Link to={item.path} className="ml-1.5 text-slate-400 hover:text-primary-600 transition-colors">
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
