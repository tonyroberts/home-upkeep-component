import { LitElement, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { buttonStyles, dialogStyles, formStyles, inputStyles } from "../styles";

@customElement("home-upkeep-create-list-dialog")
export class HomeUpkeepCreateListDialog extends LitElement {
  @property({ type: Boolean }) open = false;

  @state() private _name = "";

  static styles = [
    dialogStyles,
    buttonStyles,
    inputStyles,
    formStyles,
    css`
      label {
        display: block;
      }
    `,
  ];

  private _close() {
    this.dispatchEvent(
      new CustomEvent("dialog-close", { bubbles: true, composed: true }),
    );
  }

  private _save() {
    const name = this._name.trim();
    if (!name) {
      return;
    }
    this.dispatchEvent(
      new CustomEvent("dialog-save", {
        detail: { name },
        bubbles: true,
        composed: true,
      }),
    );
    this._name = "";
  }

  render() {
    if (!this.open) {
      return null;
    }
    return html`
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="new-list-title"
        class="dialog"
        @click=${(e: Event) => {
          if (e.target === e.currentTarget) this._close();
        }}
      >
        <div class="dialog-body">
          <div class="dialog-content">
            <h2 id="new-list-title" class="dialog-title">Create New List</h2>
            <div class="form-section">
              <label>
                <span class="dialog-label">Name</span>
                <input
                  class="input-field"
                  placeholder="List name"
                  autofocus
                  .value=${this._name}
                  @input=${(e: InputEvent) => {
                    this._name = (e.target as HTMLInputElement).value;
                  }}
                  @keydown=${(e: KeyboardEvent) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      this._save();
                    }
                  }}
                />
              </label>
            </div>
            <div class="dialog-actions">
              <button class="btn-secondary" @click=${() => this._close()}>
                Cancel
              </button>
              <button class="btn-primary" @click=${() => this._save()}>
                Create
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "home-upkeep-create-list-dialog": HomeUpkeepCreateListDialog;
  }
}
