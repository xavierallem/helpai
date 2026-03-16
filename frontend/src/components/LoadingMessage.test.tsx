import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { LoadingMessage } from './LoadingMessage';

describe('LoadingMessage', () => {
  it('renders thinking text', () => {
    render(<LoadingMessage />);
    expect(screen.getByText('Thinking...')).toBeInTheDocument();
  });

  it('renders three typing dots', () => {
    const { container } = render(<LoadingMessage />);
    const dots = container.querySelectorAll('.typing-dot');
    expect(dots).toHaveLength(3);
  });

  it('renders the loading container', () => {
    const { container } = render(<LoadingMessage />);
    expect(container.querySelector('.loading-content')).toBeInTheDocument();
  });
});
