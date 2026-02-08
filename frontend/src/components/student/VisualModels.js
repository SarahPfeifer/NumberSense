import React, { useState, useRef, useCallback, useEffect } from 'react';

/**
 * Visual model components for math problem scaffolding.
 * NumberLine supports both static display and interactive drag-to-answer.
 */

// ─── Fraction Bars (SVG) ────────────────────────────────
//
// Scaffolding tiers (driven by visualLevel 1-5):
//   Level 5-4: Static bars — equal parts clearly divided + shading + labels
//   Level 3-2: Interactive bars — parts shown but empty; student clicks to shade
//   Level 1:   No visual (handled upstream)

const FB_W = 360, FB_H = 36;

export function FractionBar({ numerator, denominator, value, parts, label, showLabel = true }) {
  const denom = denominator || parts || 8;
  const numer = numerator !== undefined ? numerator : Math.round((value || 0) * denom);
  const displayLabel = label || (showLabel && denom ? `${numer}/${denom}` : null);
  const segW = FB_W / denom;

  return (
    <div style={{ textAlign: 'center', marginBottom: 8 }}>
      {displayLabel && (
        <div style={{ fontSize: 13, color: '#4F46E5', fontWeight: 700, marginBottom: 4, fontFamily: 'Inter, sans-serif' }}>
          {displayLabel}
        </div>
      )}
      <svg viewBox={`0 0 ${FB_W} ${FB_H}`}
        style={{ width: '100%', maxWidth: FB_W, display: 'block', margin: '0 auto' }}>
        {/* Segment fills */}
        {Array.from({ length: denom }, (_, i) => (
          <rect key={`s-${i}`}
            x={i * segW} y={0} width={segW} height={FB_H}
            fill={i < numer ? '#6366F1' : '#E5E7EB'}
          />
        ))}
        {/* Division lines between segments */}
        {Array.from({ length: denom - 1 }, (_, i) => (
          <line key={`d-${i}`}
            x1={(i + 1) * segW} y1={0} x2={(i + 1) * segW} y2={FB_H}
            stroke="#374151" strokeWidth="2"
          />
        ))}
        {/* Outer border */}
        <rect x={1} y={1} width={FB_W - 2} height={FB_H - 2} rx={3}
          fill="none" stroke="#374151" strokeWidth="2" />
      </svg>
    </div>
  );
}

// Interactive fraction bar — student clicks segments to shade from left
export function InteractiveFractionBar({ denominator, label, onShadedChange, initialShaded = 0 }) {
  const [shadedCount, setShadedCount] = useState(initialShaded);
  const [hoverIdx, setHoverIdx] = useState(null);
  const denom = denominator || 8;
  const segW = FB_W / denom;

  const handleClick = (i) => {
    // Click fills from left through segment i. Clicking the last filled segment un-shades it.
    const newCount = (i + 1 === shadedCount) ? i : i + 1;
    setShadedCount(newCount);
    if (onShadedChange) onShadedChange(newCount);
  };

  // Compute preview fill for each segment on hover
  const previewCount = hoverIdx !== null
    ? (hoverIdx + 1 === shadedCount ? hoverIdx : hoverIdx + 1)
    : null;

  const getFill = (i) => {
    if (previewCount !== null) {
      if (i < Math.min(shadedCount, previewCount)) return '#6366F1';      // stays filled
      if (i < previewCount && i >= shadedCount)     return '#A5B4FC';      // would be filled (preview)
      if (i < shadedCount && i >= previewCount)     return '#C7D2FE';      // would be un-filled (preview)
      return '#E5E7EB';                                                     // empty
    }
    return i < shadedCount ? '#6366F1' : '#E5E7EB';
  };

  return (
    <div style={{ textAlign: 'center', marginBottom: 8 }}>
      {label && (
        <div style={{ fontSize: 13, color: '#6B7280', fontWeight: 600, marginBottom: 4, fontFamily: 'Inter, sans-serif' }}>
          {label}
        </div>
      )}
      <svg viewBox={`0 0 ${FB_W} ${FB_H + 4}`}
        style={{ width: '100%', maxWidth: FB_W, display: 'block', margin: '0 auto', cursor: 'pointer' }}>
        {Array.from({ length: denom }, (_, i) => (
          <rect key={`s-${i}`}
            x={i * segW} y={0} width={segW} height={FB_H}
            fill={getFill(i)}
            onClick={() => handleClick(i)}
            onMouseEnter={() => setHoverIdx(i)}
            onMouseLeave={() => setHoverIdx(null)}
            style={{ cursor: 'pointer' }}
          />
        ))}
        {Array.from({ length: denom - 1 }, (_, i) => (
          <line key={`d-${i}`}
            x1={(i + 1) * segW} y1={0} x2={(i + 1) * segW} y2={FB_H}
            stroke="#374151" strokeWidth="2" style={{ pointerEvents: 'none' }}
          />
        ))}
        <rect x={1} y={1} width={FB_W - 2} height={FB_H - 2} rx={3}
          fill="none" stroke="#374151" strokeWidth="2" style={{ pointerEvents: 'none' }} />
      </svg>
      <div style={{
        fontSize: 12, fontWeight: 600, marginTop: 3, fontFamily: 'Inter, sans-serif',
        color: shadedCount > 0 ? '#4F46E5' : '#9CA3AF',
      }}>
        {shadedCount > 0 ? `${shadedCount}/${denom}` : 'Tap parts to shade'}
      </div>
    </div>
  );
}

// Comparison layout for two fraction bars (static or interactive based on visualLevel)
export function FractionBarComparison({ left, right, interactive, onLeftShaded, onRightShaded }) {
  if (interactive) {
    return (
      <div className="visual-model">
        <InteractiveFractionBar
          denominator={left.denominator}
          label={`Shade ${left.numerator}/${left.denominator}`}
          onShadedChange={onLeftShaded}
        />
        <div style={{ textAlign: 'center', fontSize: 14, fontWeight: 700, color: '#6B7280', margin: '2px 0' }}>vs</div>
        <InteractiveFractionBar
          denominator={right.denominator}
          label={`Shade ${right.numerator}/${right.denominator}`}
          onShadedChange={onRightShaded}
        />
      </div>
    );
  }
  return (
    <div className="visual-model">
      <FractionBar numerator={left.numerator} denominator={left.denominator}
        value={left.value} parts={left.denominator}
        label={`${left.numerator}/${left.denominator}`} />
      <FractionBar numerator={right.numerator} denominator={right.denominator}
        value={right.value} parts={right.denominator}
        label={right.label || `${right.numerator}/${right.denominator}`} />
    </div>
  );
}

// Equivalent fractions layout: static left bar + interactive (or static) right bar
export function EquivalentFractionBars({ hint, interactive, onShadedChange }) {
  const leftNum = hint.left_numerator;
  const leftDen = hint.left_denominator || hint.left_parts;
  const rightDen = hint.right_denominator || hint.right_parts;
  const rightNum = hint.right_numerator; // may be undefined during practice

  if (interactive) {
    return (
      <div className="visual-model">
        <FractionBar numerator={leftNum} denominator={leftDen}
          label={`${leftNum}/${leftDen}`} />
        <div style={{ textAlign: 'center', fontSize: 16, fontWeight: 700, color: '#6B7280', margin: '2px 0' }}>=</div>
        <InteractiveFractionBar
          denominator={rightDen}
          label={`Shade to match — how many out of ${rightDen}?`}
          onShadedChange={onShadedChange}
        />
      </div>
    );
  }

  // Static mode (full support or feedback) — show both bars fully shaded
  const computedRightNum = rightNum !== undefined ? rightNum : Math.round((hint.left_value || 0) * rightDen);
  return (
    <div className="visual-model">
      <FractionBar numerator={leftNum} denominator={leftDen}
        label={`${leftNum}/${leftDen}`} />
      <div style={{ textAlign: 'center', fontSize: 16, fontWeight: 700, color: '#6B7280', margin: '2px 0' }}>=</div>
      <FractionBar numerator={computedRightNum} denominator={rightDen}
        label={`${computedRightNum}/${rightDen}`} />
    </div>
  );
}

// ─── Number Line Helpers ────────────────────────────────

/** Pick a clean step size that produces integer tick marks. */
function pickStep(range) {
  if (range <= 0) return 1;
  const nice = [1, 2, 5, 10, 20, 25, 50, 100];
  // We want roughly 5-10 labeled ticks
  const raw = range / 8;
  for (const n of nice) {
    if (n >= raw) return n;
  }
  return Math.ceil(raw / 100) * 100;
}

/** Generate clean tick values between min and max. */
function generateTicks(min, max, options = {}) {
  const { forceStep, fractionDenom, everyInteger } = options;
  const range = max - min;

  // Fraction number lines: tick every 1/denom
  if (fractionDenom) {
    const ticks = [];
    for (let i = 0; i <= fractionDenom; i++) {
      ticks.push({ value: min + (i / fractionDenom) * range, label: i === 0 ? '0' : i === fractionDenom ? '1' : `${i}/${fractionDenom}` });
    }
    return ticks;
  }

  // Integer add/sub number lines: tick every whole number
  if (everyInteger) {
    const ticks = [];
    const intMin = Math.ceil(min);
    const intMax = Math.floor(max);
    // Determine label frequency: label every tick if ≤25, else label key values
    const count = intMax - intMin + 1;
    const labelEvery = count <= 25 ? 1 : count <= 50 ? 2 : 5;
    for (let v = intMin; v <= intMax; v++) {
      const showLabel = v === intMin || v === intMax || v === 0 || v % labelEvery === 0;
      ticks.push({ value: v, label: showLabel ? String(v) : '' });
    }
    return ticks;
  }

  // Generic integer number lines: spaced labels
  const step = forceStep || pickStep(range);
  const start = Math.ceil(min / step) * step;
  const ticks = [];
  for (let v = start; v <= max; v += step) {
    ticks.push({ value: v, label: String(Math.round(v)) });
  }
  // Ensure min and max are included
  if (ticks.length === 0 || ticks[0].value > min) {
    ticks.unshift({ value: min, label: String(Math.round(min)) });
  }
  if (ticks[ticks.length - 1].value < max) {
    ticks.push({ value: max, label: String(Math.round(max)) });
  }
  return ticks;
}

// ─── Static Number Line ─────────────────────────────────

export function NumberLine({ min, max, points, marker, fractionDenom, startVal, moveVal, everyInteger }) {
  const range = max - min;
  const getPos = (val) => Math.max(0, Math.min(100, ((val - min) / range) * 100));
  const ticks = generateTicks(min, max, { fractionDenom, everyInteger });

  // For integer addition/subtraction: show the "hop" arc
  const showHop = startVal !== undefined && moveVal !== undefined && moveVal !== 0;
  const hopEnd = showHop ? startVal + moveVal : null;

  return (
    <div className="visual-model">
      <svg
        viewBox="0 0 500 90"
        style={{ width: '100%', maxWidth: 500, display: 'block', margin: '0 auto', overflow: 'visible' }}
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Track */}
        <line x1="20" y1="50" x2="480" y2="50" stroke="#D1D5DB" strokeWidth="2" />

        {/* Ticks + labels */}
        {ticks.map((t, i) => {
          const x = 20 + (getPos(t.value) / 100) * 460;
          // Only label every other tick if there are many
          const showLabel = ticks.length <= 12 || i % 2 === 0 || t.value === min || t.value === max || t.value === 0;
          return (
            <g key={i}>
              <line x1={x} y1="44" x2={x} y2="56" stroke="#9CA3AF" strokeWidth="1.5" />
              {showLabel && (
                <text x={x} y="72" textAnchor="middle" fontSize="11" fill="#6B7280" fontFamily="Inter, sans-serif">
                  {t.label}
                </text>
              )}
            </g>
          );
        })}

        {/* Zero marker (if in range and integer) */}
        {min < 0 && max > 0 && (
          <line x1={20 + (getPos(0) / 100) * 460} y1="42" x2={20 + (getPos(0) / 100) * 460} y2="58"
            stroke="#374151" strokeWidth="2" />
        )}

        {/* Hop arc for addition/subtraction */}
        {showHop && (() => {
          const sx = 20 + (getPos(startVal) / 100) * 460;
          const ex = 20 + (getPos(hopEnd) / 100) * 460;
          const dx = ex - sx;
          const arcHeight = Math.min(35, Math.abs(dx) * 0.4);
          const color = moveVal > 0 ? '#22C55E' : '#EF4444';
          return (
            <g>
              {/* Start dot */}
              <circle cx={sx} cy={50} r="5" fill="#4F46E5" />
              <text x={sx} y="32" textAnchor="middle" fontSize="11" fontWeight="600" fill="#4F46E5">
                {Math.round(startVal)}
              </text>
              {/* Arc */}
              <path
                d={`M ${sx} 50 Q ${sx + dx / 2} ${50 - arcHeight} ${ex} 50`}
                fill="none" stroke={color} strokeWidth="2" strokeDasharray="4 3"
              />
              {/* Arrow at end */}
              <circle cx={ex} cy={50} r="5" fill={color} />
              {/* Move label */}
              <text x={sx + dx / 2} y={50 - arcHeight - 4} textAnchor="middle" fontSize="10" fontWeight="600" fill={color}>
                {moveVal > 0 ? `+${moveVal}` : moveVal}
              </text>
              {/* Result label */}
              <text x={ex} y="32" textAnchor="middle" fontSize="11" fontWeight="600" fill={color}>
                {Math.round(hopEnd)}
              </text>
            </g>
          );
        })()}

        {/* Static points */}
        {points && points.map((p, i) => {
          const x = 20 + (getPos(p) / 100) * 460;
          return (
            <g key={`p-${i}`}>
              <circle cx={x} cy={50} r={i === 0 ? 6 : 4}
                fill={i === 0 ? '#4F46E5' : '#9CA3AF'} />
              <text x={x} y="32" textAnchor="middle" fontSize="10" fontWeight="600"
                fill={i === 0 ? '#4F46E5' : '#9CA3AF'}>
                {typeof p === 'number' && Number.isInteger(p) ? p : ''}
              </text>
            </g>
          );
        })}

        {/* Main marker (e.g. fraction position) */}
        {marker !== undefined && !showHop && (
          <g>
            <circle cx={20 + (getPos(marker) / 100) * 460} cy={50} r="7" fill="#4F46E5" />
            <line x1={20 + (getPos(marker) / 100) * 460} y1={43} x2={20 + (getPos(marker) / 100) * 460} y2={32}
              stroke="#4F46E5" strokeWidth="2" />
            <polygon
              points={`${20 + (getPos(marker) / 100) * 460 - 4},35 ${20 + (getPos(marker) / 100) * 460 + 4},35 ${20 + (getPos(marker) / 100) * 460},28`}
              fill="#4F46E5"
            />
          </g>
        )}
      </svg>
    </div>
  );
}

// ─── Interactive Draggable Number Line ──────────────────
//
// Scaffolding tiers (driven by visualLevel 1–5):
//   Level 5–4: Starting point is shown; student drags to the answer.
//   Level 3–2: Student must first tap to place the starting point,
//              THEN drag from it to the answer.
//   Level 1:   No visual shown at all (handled upstream).

export function InteractiveNumberLine({ min, max, startVal, onDragEnd, fractionDenom, visualLevel = 5, everyInteger }) {
  const svgRef = useRef(null);
  const showStartGiven = visualLevel >= 4;
  // Phases: place_start → (if wrong) retry_start → drag
  const [phase, setPhase] = useState(showStartGiven ? 'drag' : 'place_start');
  const [placedStart, setPlacedStart] = useState(showStartGiven ? startVal : null);
  const [dragging, setDragging] = useState(false);
  const [dragVal, setDragVal] = useState(null);
  const [wrongAttempt, setWrongAttempt] = useState(null); // tracks the incorrect placement

  const range = max - min;
  const getPos = (val) => Math.max(0, Math.min(100, ((val - min) / range) * 100));
  const ticks = generateTicks(min, max, { fractionDenom, everyInteger });

  const snap = useCallback((val) => {
    if (fractionDenom) {
      const step = 1 / fractionDenom;
      return Math.round(val / step) * step;
    }
    return Math.round(val);
  }, [fractionDenom]);

  const getValFromX = useCallback((clientX) => {
    if (!svgRef.current) return min;
    const rect = svgRef.current.getBoundingClientRect();
    const trackLeft = rect.left + (20 / 500) * rect.width;
    const trackWidth = (460 / 500) * rect.width;
    const pct = Math.max(0, Math.min(1, (clientX - trackLeft) / trackWidth));
    return snap(min + pct * range);
  }, [min, range, snap]);

  const handlePointerDown = useCallback((e) => {
    e.preventDefault();
    const val = getValFromX(e.clientX);

    if (phase === 'place_start' || phase === 'retry_start') {
      if (val === startVal) {
        // Correct placement — advance to drag
        setPlacedStart(val);
        setWrongAttempt(null);
        setPhase('drag');
      } else {
        // Wrong placement — show the incorrect point and prompt retry
        setWrongAttempt(val);
        setPlacedStart(null);
        setPhase('retry_start');
      }
      return;
    }
    // drag phase
    setDragging(true);
    setDragVal(val);
    svgRef.current?.setPointerCapture?.(e.pointerId);
  }, [getValFromX, phase, startVal]);

  const handlePointerMove = useCallback((e) => {
    if (!dragging) return;
    setDragVal(getValFromX(e.clientX));
  }, [dragging, getValFromX]);

  const handlePointerUp = useCallback((e) => {
    if (!dragging) return;
    setDragging(false);
    const val = getValFromX(e.clientX);
    setDragVal(val);
    if (onDragEnd) onDragEnd(val);
  }, [dragging, getValFromX, onDragEnd]);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const prevent = (e) => { if (dragging) e.preventDefault(); };
    svg.addEventListener('touchmove', prevent, { passive: false });
    return () => svg.removeEventListener('touchmove', prevent);
  }, [dragging]);

  // Only show the placed start in drag phase (after correct placement)
  const activeStart = phase === 'drag' ? (placedStart !== null ? placedStart : startVal) : null;
  const moveVal = dragVal !== null && activeStart !== null ? dragVal - activeStart : 0;
  const hopEnd = dragVal;
  const showArc = dragVal !== null && activeStart !== null && dragVal !== activeStart;

  const isPlacing = phase === 'place_start' || phase === 'retry_start';

  return (
    <div className="visual-model">
      {/* First attempt — generic instruction */}
      {phase === 'place_start' && (
        <div style={{
          background: '#EEF2FF', border: '2px solid #6366F1', borderRadius: 8,
          padding: '8px 16px', textAlign: 'center', marginBottom: 8,
          fontSize: 14, fontWeight: 700, color: '#4338CA',
          fontFamily: 'Inter, sans-serif',
        }}>
          Step 1: Find the starting number on the number line and tap to place your point
        </div>
      )}
      {/* Retry — tell them it was wrong, let them try again */}
      {phase === 'retry_start' && (
        <div style={{
          background: '#FEF2F2', border: '2px solid #EF4444', borderRadius: 8,
          padding: '8px 16px', textAlign: 'center', marginBottom: 8,
          fontSize: 14, fontWeight: 700, color: '#DC2626',
          fontFamily: 'Inter, sans-serif',
        }}>
          Not quite — that's {wrongAttempt}. Look carefully and tap again to place the starting point.
        </div>
      )}
      {phase === 'drag' && dragVal === null && (
        <div style={{
          background: '#F0FDF4', border: '2px solid #22C55E', borderRadius: 8,
          padding: '8px 16px', textAlign: 'center', marginBottom: 8,
          fontSize: 14, fontWeight: 700, color: '#166534',
          fontFamily: 'Inter, sans-serif',
        }}>
          {!showStartGiven && (
            <span style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 2 }}>
              ✓ Starting point placed correctly!
            </span>
          )}
          Step 2: Drag on the line to show your answer
        </div>
      )}
      <svg
        ref={svgRef}
        viewBox="0 0 500 90"
        style={{
          width: '100%', maxWidth: 500, display: 'block', margin: '0 auto',
          overflow: 'visible',
          cursor: isPlacing ? 'crosshair' : dragging ? 'grabbing' : 'pointer',
          touchAction: 'none',
        }}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
      >
        {/* Track */}
        <line x1="20" y1="45" x2="480" y2="45" stroke="#D1D5DB" strokeWidth="2.5" />

        {/* Ticks + labels */}
        {ticks.map((t, i) => {
          const x = 20 + (getPos(t.value) / 100) * 460;
          const showLabel = ticks.length <= 12 || i % 2 === 0 || t.value === min || t.value === max || t.value === 0;
          return (
            <g key={i}>
              <line x1={x} y1="38" x2={x} y2="52" stroke="#9CA3AF" strokeWidth="1.5" />
              {showLabel && (
                <text x={x} y="68" textAnchor="middle" fontSize="11" fill="#6B7280" fontFamily="Inter, sans-serif">
                  {t.label}
                </text>
              )}
            </g>
          );
        })}

        {/* Wrong attempt marker (faded, with X) — shown during retry */}
        {phase === 'retry_start' && wrongAttempt !== null && (
          <g opacity="0.5">
            <circle cx={20 + (getPos(wrongAttempt) / 100) * 460} cy={45} r="7" fill="#EF4444" />
            <line x1={20 + (getPos(wrongAttempt) / 100) * 460 - 4} y1={41}
              x2={20 + (getPos(wrongAttempt) / 100) * 460 + 4} y2={49}
              stroke="white" strokeWidth="2" />
            <line x1={20 + (getPos(wrongAttempt) / 100) * 460 + 4} y1={41}
              x2={20 + (getPos(wrongAttempt) / 100) * 460 - 4} y2={49}
              stroke="white" strokeWidth="2" />
          </g>
        )}

        {/* Start position (shown only after correct placement or when given) */}
        {activeStart !== null && (
          <g>
            <circle cx={20 + (getPos(activeStart) / 100) * 460} cy={45} r="7" fill="#4F46E5" />
            <text x={20 + (getPos(activeStart) / 100) * 460} y="28" textAnchor="middle"
              fontSize="12" fontWeight="700" fill="#4F46E5" fontFamily="Inter, sans-serif">
              {Number.isInteger(activeStart) ? activeStart : activeStart.toFixed(1)}
            </text>
          </g>
        )}

        {/* Drag arc */}
        {showArc && (() => {
          const sx = 20 + (getPos(activeStart) / 100) * 460;
          const ex = 20 + (getPos(hopEnd) / 100) * 460;
          const dx = ex - sx;
          const arcH = Math.min(30, Math.abs(dx) * 0.35 + 8);
          const color = moveVal > 0 ? '#22C55E' : '#EF4444';
          return (
            <g>
              <path d={`M ${sx} 45 Q ${sx + dx / 2} ${45 - arcH} ${ex} 45`}
                fill="none" stroke={color} strokeWidth="2.5" opacity="0.7" />
              <circle cx={ex} cy={45} r="9" fill={color} stroke="white" strokeWidth="2" />
              <text x={ex} y="28" textAnchor="middle" fontSize="12" fontWeight="700" fill={color}
                fontFamily="Inter, sans-serif">
                {Number.isInteger(hopEnd) ? hopEnd : hopEnd.toFixed(1)}
              </text>
              <text x={sx + dx / 2} y={45 - arcH - 6} textAnchor="middle" fontSize="10" fontWeight="600" fill={color}>
                {moveVal > 0 ? `+${Math.round(moveVal)}` : Math.round(moveVal)}
              </text>
            </g>
          );
        })()}
      </svg>
    </div>
  );
}

// ─── Array Model ────────────────────────────────────────

export function ArrayModel({ rows, cols, maxDisplay = 12, showDimensions = false, highlight }) {
  const displayRows = Math.min(rows, maxDisplay);
  const displayCols = Math.min(cols, maxDisplay);

  // highlight = { type: 'double', baseRows: N } or { type: 'half', keepRows: N }
  // 'double': first baseRows rows in primary color, remaining in accent color
  // 'half':   first keepRows rows solid, remaining rows faded out
  const getDotStyle = (dotIndex) => {
    if (!highlight) return {};
    const row = Math.floor(dotIndex / displayCols);

    if (highlight.type === 'double') {
      const base = highlight.baseRows || Math.floor(displayRows / 2);
      if (row >= base) {
        return { background: '#F59E0B' }; // amber for the "extra" doubled rows
      }
      return {}; // primary color (from CSS)
    }

    if (highlight.type === 'half') {
      const keep = highlight.keepRows || Math.ceil(displayRows / 2);
      if (row >= keep) {
        return { opacity: 0.2 }; // faded for the "removed" half
      }
      return {};
    }

    return {};
  };

  // Label for the highlight sections
  const highlightLabel = (() => {
    if (!highlight) return null;
    if (highlight.type === 'double') {
      const base = highlight.baseRows || Math.floor(displayRows / 2);
      const extra = displayRows - base;
      return (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 16, marginTop: 6, fontSize: 11, fontWeight: 600, fontFamily: 'Inter, sans-serif' }}>
          <span style={{ color: '#4F46E5' }}>● {base} rows</span>
          <span style={{ color: '#D97706' }}>● +{extra} rows (double)</span>
        </div>
      );
    }
    if (highlight.type === 'half') {
      const keep = highlight.keepRows || Math.ceil(displayRows / 2);
      return (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 16, marginTop: 6, fontSize: 11, fontWeight: 600, fontFamily: 'Inter, sans-serif' }}>
          <span style={{ color: '#4F46E5' }}>● {keep} rows (half)</span>
          <span style={{ color: '#D1D5DB' }}>○ {displayRows - keep} rows</span>
        </div>
      );
    }
    return null;
  })();

  return (
    <div className="visual-model text-center">
      <div className="array-model" style={{
        gridTemplateColumns: `repeat(${displayCols}, 20px)`,
        display: 'inline-grid',
      }}>
        {Array.from({ length: displayRows * displayCols }, (_, i) => (
          <div key={i} className="array-dot" style={getDotStyle(i)} />
        ))}
      </div>
      {highlightLabel}
      {showDimensions && (
        <div className="text-sm text-muted" style={{ marginTop: '.5rem' }}>
          {rows} rows &times; {cols} columns
        </div>
      )}
    </div>
  );
}

// ─── Scaling Bar ────────────────────────────────────────

export function ScalingBar({ base, multiplier, showAnswer = false }) {
  const maxWidth = 280;
  const baseWidth = Math.min(maxWidth, base * 20);
  const resultWidth = Math.min(maxWidth, base * multiplier * 20);

  return (
    <div className="visual-model">
      <div style={{ marginBottom: '.5rem' }}>
        <div className="text-sm text-muted">Original: {base}</div>
        <div style={{ height: 24, width: baseWidth || 4, background: 'var(--ns-indigo-500)', borderRadius: 4, minWidth: 4 }} />
      </div>
      <div>
        <div className="text-sm text-muted">
          {showAnswer
            ? `Result: ${base} × ${multiplier} = ${base * multiplier}`
            : `${base} × ${multiplier}`}
        </div>
        <div style={{ height: 24, width: resultWidth || 4, background: 'var(--ns-green-500)', borderRadius: 4, minWidth: 4 }} />
      </div>
    </div>
  );
}

// ─── Yellow / Red Counter Models ────────────────────────
//
// Yellow = positive (+1), Red = negative (−1).
// A yellow + red pair = zero pair (cancel out).
// Scaffolding:
//   Static (level 5-4): shows the full solution step-by-step
//   Interactive (level 3-2): student adds/removes singles & zero pairs
//   Level 1: no visual (handled upstream)

const CTR_R = 14; // counter circle radius
const CTR_GAP = 6;

function CounterCircle({ color, x, y, crossed, opacity = 1 }) {
  const fill = color === 'yellow' ? '#FBBF24' : '#EF4444';
  const stroke = color === 'yellow' ? '#D97706' : '#B91C1C';
  return (
    <g opacity={opacity}>
      <circle cx={x} cy={y} r={CTR_R} fill={fill} stroke={stroke} strokeWidth="2" />
      <text x={x} y={y + 1} textAnchor="middle" dominantBaseline="middle"
        fontSize="13" fontWeight="700" fill={color === 'yellow' ? '#78350F' : '#FFF'}
        fontFamily="Inter, sans-serif">
        {color === 'yellow' ? '+' : '−'}
      </text>
      {crossed && (
        <>
          <line x1={x - CTR_R + 3} y1={y - CTR_R + 3} x2={x + CTR_R - 3} y2={y + CTR_R - 3}
            stroke="#374151" strokeWidth="2.5" />
          <line x1={x + CTR_R - 3} y1={y - CTR_R + 3} x2={x - CTR_R + 3} y2={y + CTR_R - 3}
            stroke="#374151" strokeWidth="2.5" />
        </>
      )}
    </g>
  );
}

/** Lay out counters in a row, wrapping after maxPerRow. Returns [{x, y}] */
function layoutCounters(count, startX, startY, maxPerRow = 10) {
  const positions = [];
  const cellW = CTR_R * 2 + CTR_GAP;
  const cellH = CTR_R * 2 + CTR_GAP;
  for (let i = 0; i < count; i++) {
    const col = i % maxPerRow;
    const row = Math.floor(i / maxPerRow);
    positions.push({ x: startX + col * cellW + CTR_R, y: startY + row * cellH + CTR_R });
  }
  return positions;
}

/** Static counter model — shows the full solution with zero pairs crossed out. */
export function CounterModel({ data }) {
  if (!data) return null;
  const { start_yellow, start_red, result_yellow, result_red, a, b, operation } = data;

  // Show starting counters + any added counters, then cross out zero pairs
  const totalYellow = result_yellow;
  const totalRed = result_red;
  const zeroPairs = operation === '+'
    ? Math.min(Math.max(a, 0) + Math.max(b, 0) - result_yellow, Math.abs(Math.min(a, 0)) + Math.abs(Math.min(b, 0)) - result_red)
    : data.zero_pairs_needed || 0;
  const showYellow = totalYellow + Math.max(zeroPairs, 0);
  const showRed = totalRed + Math.max(zeroPairs, 0);

  const maxPerRow = 10;
  const cellW = CTR_R * 2 + CTR_GAP;
  const cellH = CTR_R * 2 + CTR_GAP;
  const yellowRows = Math.ceil(showYellow / maxPerRow) || 0;
  const redRows = Math.ceil(showRed / maxPerRow) || 0;
  const yPadding = 30; // space for labels
  const sectionGap = 12;
  const totalH = yPadding + yellowRows * cellH + sectionGap + redRows * cellH + 10;
  const totalW = Math.min(showYellow, maxPerRow, showRed || 1) * cellW + 20;
  const svgW = Math.max(totalW, 200);

  const yellowPos = layoutCounters(showYellow, 10, yPadding, maxPerRow);
  const redPos = layoutCounters(showRed, 10, yPadding + yellowRows * cellH + sectionGap, maxPerRow);

  return (
    <div style={{ textAlign: 'center', marginTop: 8, marginBottom: 4 }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: '#6B7280', marginBottom: 4, fontFamily: 'Inter, sans-serif' }}>
        Counter Model
      </div>
      <svg viewBox={`0 0 ${svgW} ${Math.max(totalH, 60)}`}
        style={{ width: '100%', maxWidth: svgW, display: 'block', margin: '0 auto', overflow: 'visible' }}>
        {/* Yellow label */}
        {showYellow > 0 && (
          <text x={10} y={yPadding - 6} fontSize="11" fontWeight="600" fill="#D97706" fontFamily="Inter, sans-serif">
            Positive (+)
          </text>
        )}
        {yellowPos.map((p, i) => (
          <CounterCircle key={`y-${i}`} color="yellow" x={p.x} y={p.y}
            crossed={i >= totalYellow} />
        ))}
        {/* Red label */}
        {showRed > 0 && (
          <text x={10} y={yPadding + yellowRows * cellH + sectionGap - 6}
            fontSize="11" fontWeight="600" fill="#B91C1C" fontFamily="Inter, sans-serif">
            Negative (−)
          </text>
        )}
        {redPos.map((p, i) => (
          <CounterCircle key={`r-${i}`} color="red" x={p.x} y={p.y}
            crossed={i >= totalRed} />
        ))}
      </svg>
      {zeroPairs > 0 && (
        <div style={{ fontSize: 11, color: '#6B7280', marginTop: 2, fontFamily: 'Inter, sans-serif' }}>
          {zeroPairs} zero pair{zeroPairs > 1 ? 's' : ''} cancel out (✕)
        </div>
      )}
      <div style={{ fontSize: 13, fontWeight: 700, color: '#374151', marginTop: 4, fontFamily: 'Inter, sans-serif' }}>
        Result: {result_yellow > 0 ? `${result_yellow} yellow` : ''}{result_yellow > 0 && result_red > 0 ? ', ' : ''}{result_red > 0 ? `${result_red} red` : ''}{result_yellow === 0 && result_red === 0 ? '0' : ''} = {data.result}
      </div>
    </div>
  );
}

/** Interactive counter model — student adds/removes yellow, red, and zero pairs. */
export function InteractiveCounterModel({ data }) {
  const initial = data || {};
  const [yellows, setYellows] = useState(initial.start_yellow || 0);
  const [reds, setReds] = useState(initial.start_red || 0);

  const value = yellows - reds;

  const maxPerRow = 10;
  const cellW = CTR_R * 2 + CTR_GAP;
  const cellH = CTR_R * 2 + CTR_GAP;
  const yRows = Math.ceil(Math.max(yellows, 1) / maxPerRow);
  const rRows = Math.ceil(Math.max(reds, 1) / maxPerRow);
  const yPadding = 28;
  const sectionGap = 12;
  const totalH = yPadding + yRows * cellH + sectionGap + rRows * cellH + 10;
  const svgW = Math.max(maxPerRow * cellW + 20, 200);

  const yellowPos = layoutCounters(yellows, 10, yPadding, maxPerRow);
  const redPos = layoutCounters(reds, 10, yPadding + yRows * cellH + sectionGap, maxPerRow);

  return (
    <div style={{ textAlign: 'center', marginTop: 8, marginBottom: 4 }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: '#6B7280', marginBottom: 6, fontFamily: 'Inter, sans-serif' }}>
        Use counters to model the problem
      </div>

      {/* Control buttons */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>
        <button onClick={() => setYellows(y => y + 1)}
          style={{ padding: '4px 10px', borderRadius: 6, border: '2px solid #D97706', background: '#FEF3C7', cursor: 'pointer', fontSize: 12, fontWeight: 700, color: '#92400E' }}>
          + Yellow
        </button>
        <button onClick={() => setYellows(y => Math.max(0, y - 1))}
          style={{ padding: '4px 10px', borderRadius: 6, border: '2px solid #D97706', background: '#FFF7ED', cursor: 'pointer', fontSize: 12, fontWeight: 700, color: '#92400E' }}>
          − Yellow
        </button>
        <button onClick={() => setReds(r => r + 1)}
          style={{ padding: '4px 10px', borderRadius: 6, border: '2px solid #B91C1C', background: '#FEE2E2', cursor: 'pointer', fontSize: 12, fontWeight: 700, color: '#7F1D1D' }}>
          + Red
        </button>
        <button onClick={() => setReds(r => Math.max(0, r - 1))}
          style={{ padding: '4px 10px', borderRadius: 6, border: '2px solid #B91C1C', background: '#FFF1F2', cursor: 'pointer', fontSize: 12, fontWeight: 700, color: '#7F1D1D' }}>
          − Red
        </button>
        <button onClick={() => { setYellows(y => y + 1); setReds(r => r + 1); }}
          style={{ padding: '4px 10px', borderRadius: 6, border: '2px solid #6366F1', background: '#EEF2FF', cursor: 'pointer', fontSize: 12, fontWeight: 700, color: '#4338CA' }}>
          + Zero Pair
        </button>
        <button onClick={() => {
          if (yellows > 0 && reds > 0) { setYellows(y => y - 1); setReds(r => r - 1); }
        }}
          style={{ padding: '4px 10px', borderRadius: 6, border: '2px solid #6366F1', background: '#F5F3FF', cursor: 'pointer', fontSize: 12, fontWeight: 700, color: '#4338CA' }}>
          − Zero Pair
        </button>
      </div>

      {/* Counter display */}
      <svg viewBox={`0 0 ${svgW} ${Math.max(totalH, 50)}`}
        style={{ width: '100%', maxWidth: svgW, display: 'block', margin: '0 auto', overflow: 'visible' }}>
        {yellows > 0 && (
          <text x={10} y={yPadding - 6} fontSize="11" fontWeight="600" fill="#D97706" fontFamily="Inter, sans-serif">
            Positive: {yellows}
          </text>
        )}
        {yellowPos.map((p, i) => (
          <CounterCircle key={`y-${i}`} color="yellow" x={p.x} y={p.y} />
        ))}
        {reds > 0 && (
          <text x={10} y={yPadding + yRows * cellH + sectionGap - 6}
            fontSize="11" fontWeight="600" fill="#B91C1C" fontFamily="Inter, sans-serif">
            Negative: {reds}
          </text>
        )}
        {redPos.map((p, i) => (
          <CounterCircle key={`r-${i}`} color="red" x={p.x} y={p.y} />
        ))}
      </svg>

      {/* Running total */}
      <div style={{
        fontSize: 15, fontWeight: 700, marginTop: 4, fontFamily: 'Inter, sans-serif',
        color: value > 0 ? '#D97706' : value < 0 ? '#DC2626' : '#6B7280',
      }}>
        Value: {yellows} − {reds} = {value}
      </div>
    </div>
  );
}

// ─── Visual Model Dispatcher ────────────────────────────

export default function VisualModel({ hint, problemData, interactive, onInteractiveAnswer, visualLevel }) {
  if (!hint) return null;
  const vl = visualLevel || 5;

  switch (hint.type) {
    case 'fraction_bars': {
      // ── Equivalent fractions mode ──
      if (hint.equiv_mode) {
        const isInteractive = interactive && vl <= 3 && vl >= 2;
        return (
          <EquivalentFractionBars
            hint={hint}
            interactive={isInteractive}
            onShadedChange={onInteractiveAnswer}
          />
        );
      }

      // ── Fraction comparison mode (two bars) ──
      if (hint.left_numerator !== undefined && hint.right_numerator !== undefined) {
        const isInteractive = interactive && vl <= 3 && vl >= 2;
        const left = {
          numerator: hint.left_numerator,
          denominator: hint.left_denominator,
          value: hint.left_value,
        };
        const right = {
          numerator: hint.right_numerator,
          denominator: hint.right_denominator,
          value: hint.right_value,
          label: hint.right_label, // e.g. "1/2" for benchmarks
        };
        return (
          <FractionBarComparison
            left={left}
            right={right}
            interactive={isInteractive}
          />
        );
      }

      // ── Fallback: single fraction bar (legacy data) ──
      if (problemData?.left && problemData?.right) {
        return (
          <FractionBarComparison
            left={{ ...problemData.left, value: hint.left_value }}
            right={{ ...problemData.right, value: hint.right_value }}
          />
        );
      }
      return <FractionBar value={hint.left_value} parts={hint.right_parts || hint.left_parts || 8} />;
    }

    case 'number_line': {
      const nlMin = hint.line_min !== undefined ? hint.line_min : -20;
      const nlMax = hint.line_max !== undefined ? hint.line_max : 20;
      const isIntOp = hint.start !== undefined; // integer add/sub has start
      const counterData = hint.counter_data;
      // Only show counters when numbers are small enough to be useful (≤20 total)
      const showCounters = counterData && (Math.abs(counterData.a) + Math.abs(counterData.b) <= 20);

      // Interactive mode for addition/subtraction
      if (interactive && isIntOp) {
        return (
          <div>
            <InteractiveNumberLine
              min={nlMin}
              max={nlMax}
              startVal={hint.start}
              onDragEnd={onInteractiveAnswer}
              visualLevel={vl}
              everyInteger
            />
            {showCounters && (
              <InteractiveCounterModel data={counterData} />
            )}
          </div>
        );
      }

      // Static display with hop arc (for feedback)
      if (hint.start !== undefined && hint.move !== undefined) {
        return (
          <div>
            <NumberLine
              min={nlMin}
              max={nlMax}
              startVal={hint.start}
              moveVal={hint.move}
              everyInteger
            />
            {showCounters && (
              <CounterModel data={counterData} />
            )}
          </div>
        );
      }

      // Fraction number line
      if (hint.denominator) {
        return (
          <NumberLine
            min={0}
            max={1}
            marker={hint.marked_position !== undefined ? hint.marked_position : hint.fraction_value}
            fractionDenom={hint.denominator}
          />
        );
      }

      // Generic number line (magnitude, integer placement)
      return (
        <NumberLine
          min={hint.line_min !== undefined ? hint.line_min : 0}
          max={hint.line_max !== undefined ? hint.line_max : 1}
          marker={hint.marked_position !== undefined ? hint.marked_position : hint.fraction_value}
          points={hint.points}
        />
      );
    }

    case 'array_model':
      return <ArrayModel rows={hint.rows} cols={hint.cols} highlight={hint.highlight} />;

    case 'scaling_bar':
      return <ScalingBar base={hint.base_value} multiplier={hint.multiplier} />;

    case 'double_array':
      return (
        <div style={{ display: 'flex', gap: '2rem', justifyContent: 'center', flexWrap: 'wrap' }}>
          <ArrayModel rows={hint.left.rows} cols={hint.left.cols} />
          <ArrayModel rows={hint.right.rows} cols={hint.right.cols} />
        </div>
      );

    default:
      return null;
  }
}
