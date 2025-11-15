import React from 'react';

function Header({ title }) {
  return (
    <header className="bg-blue-900 text-white shadow">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <h1 className="text-3xl font-bold">{title}</h1>
      </div>
    </header>
  );
}

export default Header;
