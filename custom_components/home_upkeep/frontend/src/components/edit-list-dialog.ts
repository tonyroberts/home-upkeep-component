import { LitElement, css, html, type PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import type { TaskList } from "../ha-api";
import { buttonStyles, dialogStyles, formStyles, inputStyles } from "../styles";

@customElement("home-upkeep-edit-list-dialog")
export class HomeUpkeepEditListDialog extends LitElement {
  @property({ attribute: false }) list: TaskList | null = null;

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

  willUpdate(changed: PropertyValues) {
    if (changed.has("list") && this.list) {
      this._name = this.list.name;
    }
  }

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
  }

  render() {
    if (!this.list) {
      return null;
    }
    return html`
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="edit-list-title"
        class="dialog"
        @click=${(e: Event) => {
          if (e.target === e.currentTarget) this._close();
        }}
      >
        <div class="dialog-body">
          <div class="dialog-content">
            <h2 id="edit-list-title" class="dialog-title">Rename List</h2>
            <div class="form-section">
              <label>
                <span class="dialog-label">Name</span>
                <input
                  class="input-field"
                  autofocus
                  .value=${this._name}
                  @input=${(e: InputEvent) => {
                    this._name = (e.target as HTMLInputElement).value;
                  }}
                />
              </label>
            </div>
            <div class="dialog-actions">
              <button class="btn-secondary" @click=${() => this._close()}>
                Cancel
              </button>
              <button class="btn-primary" @click=${() => this._save()}>
                Save Changes
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
    "home-upkeep-edit-list-dialog": HomeUpkeepEditListDialog;
  }
}
