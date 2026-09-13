function Svg({ size = 18, strokeWidth = 1.8, children, ...rest }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...rest}
    >
      {children}
    </svg>
  );
}

export const InfoIcon = (props) => (
  <Svg {...props}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 11v5.5" />
    <circle cx="12" cy="7.6" r="0.5" fill="currentColor" />
  </Svg>
);

export const PinIcon = (props) => (
  <Svg {...props}>
    <path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z" />
    <circle cx="12" cy="10" r="2.3" />
  </Svg>
);

export const CrosshairIcon = (props) => (
  <Svg {...props}>
    <circle cx="12" cy="12" r="7" />
    <path d="M12 2.5v4M12 17.5v4M2.5 12h4M17.5 12h4" />
    <circle cx="12" cy="12" r="1" fill="currentColor" />
  </Svg>
);

export const BellIcon = (props) => (
  <Svg {...props}>
    <path d="M6 16v-5a6 6 0 1 1 12 0v5l1.5 2h-15z" />
    <path d="M10 20.5a2 2 0 0 0 4 0" />
  </Svg>
);

export const ChatIcon = (props) => (
  <Svg {...props}>
    <path d="M4 5.5h16v10H10l-5 4v-4H4z" />
  </Svg>
);

export const CheckIcon = (props) => (
  <Svg {...props}>
    <path d="M5 12.5l4.2 4.2L19 7" />
  </Svg>
);

export const CheckCircleIcon = (props) => (
  <Svg {...props}>
    <circle cx="12" cy="12" r="9" />
    <path d="M8 12.3l2.7 2.7L16.2 9.5" />
  </Svg>
);

export const FlagIcon = (props) => (
  <Svg {...props}>
    <path d="M5 21V4" />
    <path d="M5 4h12l-2.5 4.5L17 13H5" />
  </Svg>
);

export const ArrowLeftIcon = (props) => (
  <Svg {...props}>
    <path d="M19 12H5" />
    <path d="M11 18l-6-6 6-6" />
  </Svg>
);

export const DownloadIcon = (props) => (
  <Svg {...props}>
    <path d="M12 4v11" />
    <path d="M7 10.5l5 5 5-5" />
    <path d="M5 20h14" />
  </Svg>
);

export const ExternalIcon = (props) => (
  <Svg {...props}>
    <path d="M14 5h5v5" />
    <path d="M19 5l-8 8" />
    <path d="M17 14v5H5V7h5" />
  </Svg>
);

export const CloseIcon = (props) => (
  <Svg {...props}>
    <path d="M6 6l12 12" />
    <path d="M18 6L6 18" />
  </Svg>
);

export const AlertIcon = (props) => (
  <Svg {...props}>
    <path d="M12 4l9 16H3z" />
    <path d="M12 10v4" />
    <circle cx="12" cy="17" r="0.5" fill="currentColor" />
  </Svg>
);

export const ChevronDownIcon = (props) => (
  <Svg {...props}>
    <path d="M6 9l6 6 6-6" />
  </Svg>
);

export const LeafIcon = (props) => (
  <Svg {...props}>
    <path d="M5 19c0-8 6-14 14-14 0 8-6 14-14 14z" />
    <path d="M5 19l8-8" />
  </Svg>
);

export const StarIcon = ({ filled = false, ...props }) => (
  <Svg {...props}>
    <path
      d="M12 3.5l2.6 5.5 5.9.6-4.5 4 1.3 5.9L12 16.5l-5.3 3 1.3-5.9-4.5-4 5.9-.6z"
      fill={filled ? "currentColor" : "none"}
    />
  </Svg>
);
