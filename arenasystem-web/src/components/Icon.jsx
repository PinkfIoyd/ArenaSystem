const paths = {
  overview: (
    <>
      <path d="M4 13h6V4H4v9Z" />
      <path d="M14 20h6V4h-6v16Z" />
      <path d="M4 20h6v-3H4v3Z" />
    </>
  ),
  inbox: (
    <>
      <path d="M4 4h16v11h-4l-2 3h-4l-2-3H4V4Z" />
      <path d="M8 9h8" />
      <path d="M8 12h5" />
    </>
  ),
  queue: (
    <>
      <circle cx="12" cy="12" r="8" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  users: (
    <>
      <path d="M16 19c0-2.2-1.8-4-4-4s-4 1.8-4 4" />
      <circle cx="12" cy="9" r="3" />
      <path d="M20 18c0-1.7-1.1-3.1-2.7-3.7" />
      <path d="M6.7 14.3C5.1 14.9 4 16.3 4 18" />
    </>
  ),
  money: (
    <>
      <rect x="3" y="6" width="18" height="12" rx="2" />
      <circle cx="12" cy="12" r="3" />
      <path d="M6 9v.01" />
      <path d="M18 15v.01" />
    </>
  ),
  calendar: (
    <>
      <rect x="4" y="5" width="16" height="15" rx="2" />
      <path d="M8 3v4" />
      <path d="M16 3v4" />
      <path d="M4 10h16" />
      <path d="M8 14h.01" />
      <path d="M12 14h.01" />
      <path d="M16 14h.01" />
    </>
  ),
  stock: (
    <>
      <path d="M4 7h16" />
      <path d="M6 7l1 13h10l1-13" />
      <path d="M9 7V5a3 3 0 0 1 6 0v2" />
    </>
  ),
  court: (
    <>
      <rect x="4" y="4" width="16" height="16" rx="2" />
      <path d="M12 4v16" />
      <path d="M4 12h16" />
    </>
  ),
  home: (
    <>
      <path d="M3 11 12 4l9 7" />
      <path d="M5 10v10h14V10" />
      <path d="M9 20v-6h6v6" />
    </>
  ),
  cart: (
    <>
      <path d="M4 5h2l2 10h10l2-7H7" />
      <circle cx="10" cy="19" r="1.5" />
      <circle cx="17" cy="19" r="1.5" />
    </>
  ),
  box: (
    <>
      <path d="M12 3 4 7l8 4 8-4-8-4Z" />
      <path d="M4 7v10l8 4 8-4V7" />
      <path d="M12 11v10" />
    </>
  ),
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M19 12a7 7 0 0 0-.1-1l2-1.5-2-3.4-2.4 1a8 8 0 0 0-1.7-1L14.5 3h-5l-.3 3.1a8 8 0 0 0-1.7 1l-2.4-1-2 3.4L5.1 11a7 7 0 0 0 0 2l-2 1.5 2 3.4 2.4-1a8 8 0 0 0 1.7 1l.3 3.1h5l.3-3.1a8 8 0 0 0 1.7-1l2.4 1 2-3.4-2-1.5a7 7 0 0 0 .1-1Z" />
    </>
  ),
  shield: (
    <>
      <path d="M12 3 19 6v5c0 4.5-2.8 8.4-7 10-4.2-1.6-7-5.5-7-10V6l7-3Z" />
      <path d="m9 12 2 2 4-4" />
    </>
  ),
  refresh: (
    <>
      <path d="M20 11a8 8 0 0 0-14.9-4" />
      <path d="M5 3v4h4" />
      <path d="M4 13a8 8 0 0 0 14.9 4" />
      <path d="M19 21v-4h-4" />
    </>
  ),
  alert: (
    <>
      <path d="M12 3 2.8 20h18.4L12 3Z" />
      <path d="M12 9v5" />
      <path d="M12 17v.01" />
    </>
  ),
  check: (
    <path d="m5 12 4 4L19 6" />
  ),
  trophy: (
    <>
      <path d="M8 4h8v4a4 4 0 0 1-8 0V4Z" />
      <path d="M8 6H5a3 3 0 0 0 3 3" />
      <path d="M16 6h3a3 3 0 0 1-3 3" />
      <path d="M12 12v5" />
      <path d="M9 20h6" />
    </>
  ),
  trend: (
    <>
      <path d="M4 18h16" />
      <path d="m5 14 5-5 4 4 5-7" />
      <path d="M16 6h3v3" />
    </>
  ),
  pin: (
    <>
      <path d="M12 21s7-5.3 7-11a7 7 0 1 0-14 0c0 5.7 7 11 7 11Z" />
      <circle cx="12" cy="10" r="2.5" />
    </>
  ),
  logIn: (
    <>
      <path d="M10 17H5V7h5" />
      <path d="m14 8 4 4-4 4" />
      <path d="M8 12h10" />
    </>
  ),
  panelLeft: (
    <>
      <rect x="4" y="4" width="16" height="16" rx="2" />
      <path d="M9 4v16" />
    </>
  ),
  chevronLeft: (
    <path d="m15 18-6-6 6-6" />
  ),
  chevronRight: (
    <path d="m9 18 6-6-6-6" />
  ),
};

function Icon({ name, className = 'h-5 w-5', strokeWidth = 1.8 }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {paths[name] || paths.overview}
    </svg>
  );
}

export default Icon;
