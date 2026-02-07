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
  const { forceStep, fractionDenom } = options;
  const range = max - min;

  // Fraction number lines: tick every 1/denom
  if (fractionDenom) {
    const ticks = [];
    for (let i = 0; i <= fractionDenom; i++) {
      ticks.push({ value: min + (i / fractionDenom) * range, label: i === 0 ? '0' : i === fractionDenom ? '1' : `${i}/${fractionDenom}` });
    }
    return ticks;
  }

  // Integer number lines: always integer labels
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

export function NumberLine({ min, max, points, marker, fractionDenom, startVal, moveVal }) {
  const range = max - min;
  const getPos = (val) => Math.max(0, Math.min(100, ((val - min) / range) * 100));
  const ticks = generateTicks(min, max, { fractionDenom });

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

export function InteractiveNumberLine({ min, max, startVal, onDragEnd, fractionDenom, visualLevel = 5 }) {
  const svgRef = useRef(null);
  const showStartGiven = visualLevel >= 4;
  const [phase, setPhase] = useState(showStartGiven ? 'drag' : 'place_start');
  const [placedStart, setPlacedStart] = useState(showStartGiven ? startVal : null);
  const [dragging, setDragging] = useState(false);
  const [dragVal, setDragVal] = useState(null);

  const range = max - min;
  const getPos = (val) => Math.max(0, Math.min(100, ((val - min) / range) * 100));
  const ticks = generateTicks(min, max, { fractionDenom });

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

    if (phase === 'place_start') {
      setPlacedStart(val);
      setPhase('drag');
      return;
    }
    // drag phase
    setDragging(true);
    setDragVal(val);
    svgRef.current?.setPointerCapture?.(e.pointerId);
  }, [getValFromX, phase]);

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

  const activeStart = placedStart !== null ? placedStart : startVal;
  const moveVal = dragVal !== null && activeStart !== null ? dragVal - activeStart : 0;
  const hopEnd = dragVal;
  const showArc = dragVal !== null && activeStart !== null && dragVal !== activeStart;

  // Did the student place the start incorrectly?
  const startPlacedWrong = phase === 'drag' && !showStartGiven && placedStart !== null && placedStart !== startVal;

  return (
    <div className="visual-model">
      {/* Prominent instruction banner for place-start phase */}
      {phase === 'place_start' && (
        <div style={{
          background: '#EEF2FF', border: '2px solid #6366F1', borderRadius: 8,
          padding: '8px 16px', textAlign: 'center', marginBottom: 8,
          fontSize: 14, fontWeight: 700, color: '#4338CA',
          fontFamily: 'Inter, sans-serif',
        }}>
          Step 1: Tap the number line to place <span style={{ fontSize: 18 }}>{startVal}</span>
        </div>
      )}
      {phase === 'drag' && dragVal === null && (
        <div style={{
          background: '#F0FDF4', border: '2px solid #22C55E', borderRadius: 8,
          padding: '8px 16px', textAlign: 'center', marginBottom: 8,
          fontSize: 14, fontWeight: 700, color: '#166534',
          fontFamily: 'Inter, sans-serif',
        }}>
          Step 2: Drag on the line to show your answer
        </div>
      )}
      {startPlacedWrong && (
        <div style={{
          background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 8,
          padding: '6px 12px', textAlign: 'center', marginBottom: 6,
          fontSize: 12, color: '#DC2626', fontFamily: 'Inter, sans-serif',
        }}>
          The starting number is {startVal} — try to place it more carefully next time!
        </div>
      )}
      <svg
        ref={svgRef}
        viewBox="0 0 500 90"
        style={{
          width: '100%', maxWidth: 500, display: 'block', margin: '0 auto',
          overflow: 'visible',
          cursor: phase === 'place_start' ? 'crosshair' : dragging ? 'grabbing' : 'pointer',
          touchAction: 'none',
        }}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
      >
        {/* Track */}
        <line x1="20" y1="45" x2="480" y2="45" stroke="#D1D5DB" strokeWidth="2.5" />

        {/* Pulsing guide for place-start phase */}
        {phase === 'place_start' && (
          <circle cx="250" cy="45" r="12" fill="none" stroke="#6366F1" strokeWidth="2" opacity="0.4">
            <animate attributeName="r" values="8;16;8" dur="1.5s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.5;0.15;0.5" dur="1.5s" repeatCount="indefinite" />
          </circle>
        )}

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

        {/* Start position (shown or student-placed) */}
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

export function ArrayModel({ rows, cols, maxDisplay = 12 }) {
  const displayRows = Math.min(rows, maxDisplay);
  const displayCols = Math.min(cols, maxDisplay);

  return (
    <div className="visual-model text-center">
      <div className="array-model" style={{
        gridTemplateColumns: `repeat(${displayCols}, 20px)`,
        display: 'inline-grid',
      }}>
        {Array.from({ length: displayRows * displayCols }, (_, i) => (
          <div key={i} className="array-dot" />
        ))}
      </div>
      <div className="text-sm text-muted" style={{ marginTop: '.5rem' }}>
        {rows} rows &times; {cols} columns = {rows * cols}
      </div>
    </div>
  );
}

// ─── Scaling Bar ────────────────────────────────────────

export function ScalingBar({ base, multiplier }) {
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
        <div className="text-sm text-muted">Result: {base} &times; {multiplier} = {base * multiplier}</div>
        <div style={{ height: 24, width: resultWidth || 4, background: 'var(--ns-green-500)', borderRadius: 4, minWidth: 4 }} />
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
      // Interactive mode for addition/subtraction
      if (interactive && hint.start !== undefined) {
        return (
          <InteractiveNumberLine
            min={hint.line_min !== undefined ? hint.line_min : -20}
            max={hint.line_max !== undefined ? hint.line_max : 20}
            startVal={hint.start}
            onDragEnd={onInteractiveAnswer}
            visualLevel={vl}
          />
        );
      }

      // Static display with hop arc (for feedback)
      if (hint.start !== undefined && hint.move !== undefined) {
        return (
          <NumberLine
            min={hint.line_min !== undefined ? hint.line_min : -20}
            max={hint.line_max !== undefined ? hint.line_max : 20}
            startVal={hint.start}
            moveVal={hint.move}
          />
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
      return <ArrayModel rows={hint.rows} cols={hint.cols} />;

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
