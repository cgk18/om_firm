import { APP_NAME } from "@/lib/brand";

/** Otomeda wordmark with a small "listening" waveform soundmark. Placeholder
 *  until the real logo lands — swap this component + the globals.css tokens. */
export function BrandMark() {
  return (
    <div className="flex items-center gap-2.5">
      <svg
        width="26"
        height="26"
        viewBox="0 0 26 26"
        aria-hidden
        className="text-primary"
      >
        <circle cx="13" cy="13" r="12" className="fill-primary-soft" />
        {/* waveform bars — the product listens */}
        {[
          [8, 9, 8],
          [11, 5, 16],
          [14, 3, 20],
          [17, 7, 12],
        ].map(([x, y, h]) => (
          <rect
            key={x}
            x={x}
            y={y}
            width="2.2"
            height={h}
            rx="1.1"
            className="fill-primary"
          />
        ))}
      </svg>
      <span className="text-[17px] font-semibold tracking-tight text-foreground">
        {APP_NAME}
      </span>
    </div>
  );
}
