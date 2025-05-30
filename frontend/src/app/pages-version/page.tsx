'use client';

import { useEffect } from 'react';

export default function PagesVersionRedirect() {
  useEffect(() => {
    // Redirect to the Pages Router version
    window.location.href = '/';
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <p className="text-lg">Redirecting to current version...</p>
      </div>
    </div>
  );
} 