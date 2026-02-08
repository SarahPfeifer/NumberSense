import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import VisualModel, { FractionBar, InteractiveFractionBar, FractionBarComparison } from './VisualModels';

describe('FractionBar', () => {
  test('renders correct number of SVG rects for denominator', () => {
    const { container } = render(
      <FractionBar numerator={3} denominator={4} />
    );
    // 4 segment rects + outer border rect = look for rects
    const rects = container.querySelectorAll('rect');
    // 4 segments + 1 border = 5
    expect(rects.length).toBe(5);
  });

  test('displays fraction label', () => {
    const { container } = render(
      <FractionBar numerator={2} denominator={5} />
    );
    expect(container.textContent).toContain('2/5');
  });

  test('handles legacy value/parts props', () => {
    const { container } = render(
      <FractionBar value={0.5} parts={6} />
    );
    // Should compute 3 filled out of 6
    expect(container.textContent).toContain('3/6');
  });
});

describe('InteractiveFractionBar', () => {
  test('renders with initial empty state', () => {
    const { container } = render(
      <InteractiveFractionBar denominator={4} />
    );
    expect(container.textContent).toContain('Tap parts to shade');
  });

  test('calls onShadedChange when segment clicked', () => {
    const mockFn = jest.fn();
    const { container } = render(
      <InteractiveFractionBar denominator={4} onShadedChange={mockFn} />
    );
    // Click the first segment rect (index 0)
    const rects = container.querySelectorAll('svg rect');
    fireEvent.click(rects[0]);
    expect(mockFn).toHaveBeenCalledWith(1);
  });
});

describe('FractionBarComparison', () => {
  test('renders two bars in static mode', () => {
    const { container } = render(
      <FractionBarComparison
        left={{ numerator: 1, denominator: 3, value: 0.333 }}
        right={{ numerator: 2, denominator: 5, value: 0.4 }}
      />
    );
    expect(container.textContent).toContain('1/3');
    expect(container.textContent).toContain('2/5');
  });
});

describe('VisualModel dispatcher', () => {
  test('renders fraction bars for fraction_bars type', () => {
    const hint = {
      type: 'fraction_bars',
      left_numerator: 1, left_denominator: 2, left_value: 0.5,
      right_numerator: 2, right_denominator: 4, right_value: 0.5,
    };
    const { container } = render(
      <VisualModel hint={hint} problemData={{}} interactive={false} visualLevel={5} />
    );
    expect(container.textContent).toContain('1/2');
    expect(container.textContent).toContain('2/4');
  });

  test('renders number line for number_line type', () => {
    const hint = {
      type: 'number_line',
      start: 3, move: 5, result: 8,
      line_min: -5, line_max: 15,
    };
    const { container } = render(
      <VisualModel hint={hint} problemData={{}} interactive={false} visualLevel={5} />
    );
    // SVG should be present
    expect(container.querySelector('svg')).toBeTruthy();
  });

  test('renders null for unknown type', () => {
    const { container } = render(
      <VisualModel hint={{ type: 'unknown' }} problemData={{}} />
    );
    expect(container.innerHTML).toBe('');
  });

  test('renders null when hint is null', () => {
    const { container } = render(
      <VisualModel hint={null} problemData={{}} />
    );
    expect(container.innerHTML).toBe('');
  });
});
