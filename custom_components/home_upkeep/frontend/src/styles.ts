import { css } from "lit";

/**
 * Palette custom properties, ported verbatim from the add-on's
 * `index.css` `@theme` block (primary/gray) plus the standard Tailwind
 * default shades it relied on for red/green/yellow/orange/blue. These are
 * fixed hex values — a given shade means the same thing in light and dark
 * mode; what changes between modes is *which* shade a given rule uses; see
 * each component's own `@media (prefers-color-scheme: dark)` block for that.
 *
 * Only the root panel (`entrypoint.ts`) includes this; CSS custom properties
 * inherit through shadow DOM boundaries, so every descendant component's
 * shadow root can reference `var(--hu-*)` without redefining it.
 */
export const designTokens = css`
  :host {
    --hu-primary-50: #e6f6ff;
    --hu-primary-100: #b3e5fc;
    --hu-primary-400: #29b6f6;
    --hu-primary-500: #03a9f4;
    --hu-primary-600: #039be5;
    --hu-primary-700: #0288d1;
    --hu-primary-800: #0277bd;
    --hu-primary-900: #01579b;

    --hu-gray-50: #fafafa;
    --hu-gray-100: #f5f5f5;
    --hu-gray-200: #eeeeee;
    --hu-gray-300: #e0e0e0;
    --hu-gray-400: #bdbdbd;
    --hu-gray-500: #9e9e9e;
    --hu-gray-600: #757575;
    --hu-gray-700: #616161;
    --hu-gray-800: #424242;
    --hu-gray-900: #1c1c1c;

    --hu-red-50: #fef2f2;
    --hu-red-100: #fee2e2;
    --hu-red-200: #fecaca;
    --hu-red-300: #fca5a5;
    --hu-red-400: #f87171;
    --hu-red-600: #dc2626;
    --hu-red-700: #b91c1c;
    --hu-red-800: #991b1b;
    --hu-red-900: #7f1d1d;

    --hu-green-100: #dcfce7;
    --hu-green-200: #bbf7d0;
    --hu-green-800: #166534;
    --hu-green-900: #14532d;

    --hu-yellow-100: #fef9c3;
    --hu-yellow-200: #fef08a;
    --hu-yellow-800: #854d0e;
    --hu-yellow-900: #713f12;

    --hu-orange-100: #ffedd5;
    --hu-orange-200: #fed7aa;
    --hu-orange-800: #9a3412;
    --hu-orange-900: #7c2d12;

    --hu-blue-100: #dbeafe;
    --hu-blue-200: #bfdbfe;
    --hu-blue-400: #60a5fa;
    --hu-blue-600: #2563eb;
    --hu-blue-800: #1e40af;
    --hu-blue-900: #1e3a8a;

    font-family: Roboto, Noto, sans-serif;
  }
`;

/** `.btn-primary` / `.btn-secondary` / `.btn-danger` */
export const buttonStyles = css`
  .btn-primary,
  .btn-secondary,
  .btn-danger {
    font-weight: 500;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    transition: background-color 0.2s;
    border: none;
    cursor: pointer;
    font-size: 0.875rem;
  }
  .btn-primary:disabled,
  .btn-secondary:disabled,
  .btn-danger:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }
  .btn-primary {
    background: var(--hu-primary-600);
    color: white;
  }
  .btn-primary:hover:not(:disabled) {
    background: var(--hu-primary-700);
  }
  .btn-secondary {
    background: var(--hu-gray-200);
    color: var(--hu-gray-700);
  }
  .btn-secondary:hover:not(:disabled) {
    background: var(--hu-gray-300);
  }
  .btn-danger {
    background: var(--hu-red-600);
    color: white;
  }
  .btn-danger:hover:not(:disabled) {
    background: var(--hu-red-700);
  }
  @media (prefers-color-scheme: dark) {
    .btn-secondary {
      background: var(--hu-gray-700);
      color: var(--hu-gray-200);
    }
    .btn-secondary:hover:not(:disabled) {
      background: var(--hu-gray-600);
    }
  }
`;

/** `.input-field` */
export const inputStyles = css`
  .input-field {
    width: 100%;
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--hu-gray-300);
    border-radius: 0.5rem;
    background: white;
    color: var(--hu-gray-900);
    font-size: 0.875rem;
    font-family: inherit;
    box-sizing: border-box;
  }
  .input-field:focus {
    outline: none;
    box-shadow: 0 0 0 2px var(--hu-primary-500);
    border-color: transparent;
  }
  @media (prefers-color-scheme: dark) {
    .input-field {
      background: var(--hu-gray-800);
      border-color: var(--hu-gray-600);
      color: var(--hu-gray-100);
    }
    .input-field:focus {
      box-shadow: 0 0 0 2px var(--hu-primary-400);
    }
  }
`;

/** `.checkbox` */
export const checkboxStyles = css`
  .checkbox {
    height: 1rem;
    width: 1rem;
    accent-color: var(--hu-primary-600);
    border: 1px solid var(--hu-gray-300);
    border-radius: 0.25rem;
  }
  @media (prefers-color-scheme: dark) {
    .checkbox {
      border-color: var(--hu-gray-600);
    }
  }
`;

/** `.icon-button` / `.icon-button-danger` */
export const iconButtonStyles = css`
  .icon-button,
  .icon-button-danger {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 0.25rem;
    display: inline-flex;
    color: var(--hu-gray-400);
  }
  .icon-button:hover {
    color: var(--hu-gray-600);
  }
  .icon-button-danger:hover {
    color: var(--hu-red-600);
  }
  @media (prefers-color-scheme: dark) {
    .icon-button,
    .icon-button-danger {
      color: var(--hu-gray-500);
    }
    .icon-button:hover {
      color: var(--hu-gray-300);
    }
    .icon-button-danger:hover {
      color: var(--hu-red-400);
    }
  }
`;

/** `.card` */
export const cardStyles = css`
  .card {
    background: white;
    border-radius: 0.5rem;
    box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    border: 1px solid var(--hu-gray-200);
  }
  @media (prefers-color-scheme: dark) {
    .card {
      background: var(--hu-gray-900);
      border-color: var(--hu-gray-800);
    }
  }
`;

/**
 * `.dialog` / `.dialog-body` / `.dialog-body-large` / `.dialog-content` /
 * `.dialog-title` / `.dialog-title-large` / `.dialog-label` /
 * `.dialog-label-inline` / `.dialog-help-text` / `.dialog-actions` /
 * `.dialog-actions-no-margin`
 */
export const dialogStyles = css`
  .dialog {
    position: fixed;
    inset: 0;
    background: rgb(0 0 0 / 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    z-index: 50;
  }
  .dialog-body {
    background: white;
    border-radius: 0.5rem;
    box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1);
    width: 100%;
    max-width: 28rem;
  }
  .dialog-body-large {
    background: white;
    border-radius: 0.5rem;
    box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1);
    width: 100%;
    max-width: 42rem;
    max-height: 90vh;
    overflow-y: auto;
  }
  .dialog-content {
    padding: 1.5rem;
  }
  .dialog-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--hu-gray-900);
    margin: 0 0 1rem;
  }
  .dialog-title-large {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--hu-gray-900);
    margin: 0 0 1.5rem;
  }
  .dialog-label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--hu-gray-700);
    margin-bottom: 0.25rem;
    display: block;
  }
  .dialog-label-inline {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--hu-gray-700);
  }
  .dialog-help-text {
    font-size: 0.75rem;
    color: var(--hu-gray-500);
    margin-top: 0.25rem;
  }
  .dialog-actions {
    display: flex;
    gap: 0.75rem;
    justify-content: flex-end;
    margin-top: 1.5rem;
  }
  .dialog-actions-no-margin {
    display: flex;
    gap: 0.75rem;
    justify-content: flex-end;
  }
  @media (prefers-color-scheme: dark) {
    .dialog-body,
    .dialog-body-large {
      background: var(--hu-gray-900);
    }
    .dialog-title,
    .dialog-title-large {
      color: var(--hu-gray-100);
    }
    .dialog-label,
    .dialog-label-inline {
      color: var(--hu-gray-300);
    }
    .dialog-help-text {
      color: var(--hu-gray-400);
    }
  }
`;

/**
 * `.badge-warning` / `.badge-info` / `.badge-orange` / `.badge-green`
 */
export const badgeStyles = css`
  .badge-warning,
  .badge-info {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 500;
    border-radius: 0.25rem;
  }
  .badge-warning {
    background: var(--hu-yellow-100);
    color: var(--hu-yellow-800);
  }
  .badge-info {
    background: var(--hu-blue-100);
    color: var(--hu-blue-800);
  }
  .badge-info button {
    margin-left: 0.25rem;
    background: none;
    border: none;
    cursor: pointer;
    color: var(--hu-blue-600);
    font-size: inherit;
  }
  .badge-info button:hover {
    color: var(--hu-blue-800);
  }
  .badge-orange,
  .badge-green {
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
  }
  .badge-orange {
    background: var(--hu-orange-100);
    color: var(--hu-orange-800);
  }
  .badge-green {
    background: var(--hu-green-100);
    color: var(--hu-green-800);
  }
  @media (prefers-color-scheme: dark) {
    .badge-warning {
      background: rgb(113 63 18 / 0.3);
      color: var(--hu-yellow-200);
    }
    .badge-info {
      background: rgb(30 58 138 / 0.3);
      color: var(--hu-blue-200);
    }
    .badge-info button {
      color: var(--hu-blue-400);
    }
    .badge-info button:hover {
      color: var(--hu-blue-200);
    }
    .badge-orange {
      background: rgb(124 45 18 / 0.3);
      color: var(--hu-orange-200);
    }
    .badge-green {
      background: rgb(20 83 45 / 0.3);
      color: var(--hu-green-200);
    }
  }
`;

/** `.task-item` / `.task-list` */
export const taskItemStyles = css`
  .task-item {
    background: white;
    border-radius: 0.5rem;
    border: 1px solid var(--hu-gray-200);
    padding: 1rem;
    transition: box-shadow 0.2s;
  }
  .task-item:hover {
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  }
  .task-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  @media (prefers-color-scheme: dark) {
    .task-item {
      background: var(--hu-gray-800);
      border-color: var(--hu-gray-700);
    }
    .task-item:hover {
      box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.3);
    }
  }
`;

/** `.list-item` / `.list-item-selected` */
export const listItemStyles = css`
  .list-item {
    background: white;
    border-radius: 0.5rem;
    border: 1px solid var(--hu-gray-200);
    padding: 0.75rem;
    transition:
      box-shadow 0.2s,
      background-color 0.2s,
      border-color 0.2s;
  }
  .list-item:hover {
    box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  }
  .list-item-selected {
    background: var(--hu-primary-50);
    border-color: var(--hu-primary-100);
    box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  }
  @media (prefers-color-scheme: dark) {
    .list-item {
      background: var(--hu-gray-800);
      border-color: var(--hu-gray-700);
    }
    .list-item:hover {
      background: var(--hu-gray-700);
    }
    .list-item-selected {
      background: rgb(1 87 155 / 0.2);
      border-color: var(--hu-primary-800);
    }
    .list-item-selected:hover {
      background: rgb(1 87 155 / 0.2);
    }
  }
`;

/**
 * `.section-title` / `.section-header` / `.count-due` / `.count-upcoming` /
 * `.count-completed` / `.empty-state` / `.empty-state-icon` /
 * `.empty-state-text`
 */
export const sectionStyles = css`
  .section-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--hu-gray-900);
    margin: 0;
  }
  .section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }
  .count-due,
  .count-upcoming,
  .count-completed {
    font-size: 0.75rem;
    font-weight: 500;
    padding: 0.125rem 0.625rem;
    border-radius: 9999px;
  }
  .count-due {
    background: var(--hu-orange-100);
    color: var(--hu-orange-800);
  }
  .count-upcoming {
    background: var(--hu-blue-100);
    color: var(--hu-blue-800);
  }
  .count-completed {
    background: var(--hu-green-100);
    color: var(--hu-green-800);
  }
  .empty-state {
    text-align: center;
    padding: 2rem 0;
    color: var(--hu-gray-500);
  }
  .empty-state-icon {
    margin: 0 auto;
    height: 3rem;
    width: 3rem;
    color: var(--hu-gray-400);
  }
  .empty-state-text {
    margin-top: 0.5rem;
  }
  @media (prefers-color-scheme: dark) {
    .section-title {
      color: var(--hu-gray-100);
    }
    .count-due {
      background: rgb(124 45 18 / 0.3);
      color: var(--hu-orange-200);
    }
    .count-upcoming {
      background: rgb(30 58 138 / 0.3);
      color: var(--hu-blue-200);
    }
    .count-completed {
      background: rgb(20 83 45 / 0.3);
      color: var(--hu-green-200);
    }
    .empty-state {
      color: var(--hu-gray-400);
    }
    .empty-state-icon {
      color: var(--hu-gray-500);
    }
  }
`;

/** `.form-grid` / `.form-section` */
export const formStyles = css`
  .form-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  @media (min-width: 768px) {
    .form-grid {
      grid-template-columns: 1fr 1fr;
    }
  }
  .form-section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
`;

