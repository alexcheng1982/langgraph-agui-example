"use client";

import { useAgent } from "@copilotkit/react-core/v2";
import { useEffect, useRef, useState } from "react";

type AgentState = {
  available_ingredients?: string[];
  selected_ingredients?: string[];
};

export function IngredientsPanel() {
  const { agent } = useAgent();
  const [ingredients, setIngredients] = useState<string[]>([]);
  const [availableIngredients, setAvailableIngredients] = useState<string[]>([]);
  const [newItem, setNewItem] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const syncState = (state: AgentState) => {
      setAvailableIngredients(state.available_ingredients ?? []);
      setIngredients(state.selected_ingredients ?? []);
    };

    syncState(agent.state as AgentState);

    const subscriber = agent.subscribe({
      onStateSnapshotEvent: ({ state }) => syncState(state as AgentState),
      onRunFinalized: ({ state }) => syncState(state as AgentState),
    });
    return () => subscriber.unsubscribe();
  }, [agent]);

  const updateIngredients = (next: string[]) => {
    setIngredients(next);
    agent.setState({ ...(agent.state as object), selected_ingredients: next });
  };

  const removeIngredient = (index: number) => {
    updateIngredients(ingredients.filter((_, i) => i !== index));
  };

  const addIngredient = () => {
    const trimmed = newItem.trim();
    if (!trimmed) return;
    updateIngredients([...ingredients, trimmed]);
    setNewItem("");
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") addIngredient();
  };

  const isEmpty = ingredients.length === 0;

  return (
    <aside className="ingredients-panel">
      <header className="panel-header">
        <span className="panel-eyebrow">Pantry</span>
        <h2 className="panel-title">Ingredients</h2>
      </header>

      <div className="panel-body">
        {isEmpty ? (
          <div className="empty-state">
            <svg
              className="empty-icon"
              viewBox="0 0 48 48"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
            >
              <path
                d="M24 8C15.163 8 8 15.163 8 24s7.163 16 16 16 16-7.163 16-16S32.837 8 24 8z"
                stroke="currentColor"
                strokeWidth="2"
                fill="none"
              />
              <path
                d="M18 20c0-1.1.9-2 2-2s2 .9 2 2-.9 2-2 2-2-.9-2-2zM26 20c0-1.1.9-2 2-2s2 .9 2 2-.9 2-2 2-2-.9-2-2z"
                fill="currentColor"
              />
              <path
                d="M17 31c1.8-2.4 4.2-4 7-4s5.2 1.6 7 4"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
            <p className="empty-text">
              Tell me what's in your kitchen and I'll track it here.
            </p>
          </div>
        ) : (
          <ul className="ingredient-list" role="list">
            {ingredients.map((item, i) => (
              <li key={i} className="ingredient-chip">
                <span
                  className={`chip-dot ${availableIngredients.some(
                    (available) => available.trim().toLowerCase() === item.trim().toLowerCase(),
                  ) ? "chip-dot-available" : "chip-dot-unavailable"}`}
                  aria-hidden="true"
                />
                <span className="chip-label">{item}</span>
                <button
                  className="chip-remove"
                  onClick={() => removeIngredient(i)}
                  aria-label={`Remove ${item}`}
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="panel-add">
        <input
          ref={inputRef}
          className="add-input"
          type="text"
          placeholder="Add ingredient…"
          value={newItem}
          onChange={(e) => setNewItem(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button className="add-btn" onClick={addIngredient} aria-label="Add">
          +
        </button>
      </div>

      <div className="panel-count">
        {!isEmpty && (
          <span>
            <strong>{ingredients.length}</strong>{" "}
            {ingredients.length === 1 ? "item" : "items"}
          </span>
        )}
      </div>

      <style>{`
        .ingredients-panel {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: var(--panel-bg);
          border-left: 1px solid var(--panel-border);
          overflow: hidden;
        }

        .panel-header {
          padding: 1.5rem 1.5rem 1rem;
          border-bottom: 1px solid var(--panel-border);
          flex-shrink: 0;
        }

        .panel-eyebrow {
          display: block;
          font-size: 0.6875rem;
          font-weight: 600;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          color: var(--herb);
          margin-bottom: 0.25rem;
        }

        .panel-title {
          font-size: 1.125rem;
          font-weight: 700;
          color: var(--text-primary);
          margin: 0;
          line-height: 1.2;
          text-wrap: balance;
        }

        .panel-body {
          flex: 1;
          overflow-y: auto;
          padding: 1rem 1.25rem;
          scrollbar-width: thin;
          scrollbar-color: var(--panel-border) transparent;
        }

        .ingredient-list {
          list-style: none;
          margin: 0;
          padding: 0;
          display: flex;
          flex-direction: column;
          gap: 0.375rem;
        }

        .ingredient-chip {
          display: flex;
          align-items: center;
          gap: 0.625rem;
          padding: 0.5rem 0.75rem;
          background: var(--chip-bg);
          border: 1px solid var(--chip-border);
          border-radius: 0.5rem;
          transition: background 0.15s, border-color 0.15s;
        }

        .ingredient-chip:hover {
          background: var(--chip-bg-hover);
          border-color: var(--chip-border-hover);
        }

        .chip-remove {
          margin-left: auto;
          background: none;
          border: none;
          cursor: pointer;
          color: var(--text-muted);
          font-size: 1rem;
          line-height: 1;
          padding: 0 0.125rem;
          opacity: 0;
          transition: opacity 0.15s, color 0.15s;
          flex-shrink: 0;
        }

        .ingredient-chip:hover .chip-remove {
          opacity: 1;
        }

        .chip-remove:hover {
          color: #c0392b;
        }

        .panel-add {
          flex-shrink: 0;
          padding: 0.5rem 1.25rem;
          border-top: 1px solid var(--panel-border);
          display: flex;
          gap: 0.5rem;
        }

        .add-input {
          flex: 1;
          background: var(--chip-bg);
          border: 1px solid var(--chip-border);
          border-radius: 0.375rem;
          padding: 0.375rem 0.625rem;
          font-size: 0.875rem;
          color: var(--text-primary);
          outline: none;
          transition: border-color 0.15s;
        }

        .add-input::placeholder {
          color: var(--text-muted);
        }

        .add-input:focus {
          border-color: var(--herb);
        }

        .add-btn {
          background: var(--herb);
          color: #fff;
          border: none;
          border-radius: 0.375rem;
          width: 2rem;
          font-size: 1.25rem;
          line-height: 1;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: opacity 0.15s;
          flex-shrink: 0;
        }

        .add-btn:hover {
          opacity: 0.85;
        }

        .chip-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          flex-shrink: 0;
        }

        .chip-dot-available {
          background: #2eaf62;
        }

        .chip-dot-unavailable {
          background: #d34b4b;
        }

        .chip-label {
          font-size: 0.875rem;
          color: var(--text-primary);
          line-height: 1.3;
          font-weight: 450;
        }

        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          min-height: 160px;
          text-align: center;
          padding: 1.5rem;
          gap: 0.75rem;
        }

        .empty-icon {
          width: 2.5rem;
          height: 2.5rem;
          color: var(--text-muted);
          opacity: 0.5;
        }

        .empty-text {
          font-size: 0.8125rem;
          color: var(--text-muted);
          line-height: 1.5;
          max-width: 18ch;
          text-wrap: balance;
          margin: 0;
        }

        .panel-count {
          flex-shrink: 0;
          padding: 0.75rem 1.5rem;
          border-top: 1px solid var(--panel-border);
          font-size: 0.75rem;
          color: var(--text-muted);
          min-height: 2.5rem;
          display: flex;
          align-items: center;
          font-variant-numeric: tabular-nums;
        }

        .panel-count strong {
          color: var(--herb);
          font-weight: 600;
        }

        /* Light theme tokens */
        :root {
          --panel-bg: rgba(255, 255, 255, 0.6);
          --panel-border: rgba(28, 22, 14, 0.08);
          --text-primary: #1c160e;
          --text-muted: #7c6e5a;
          --herb: #4a6e38;
          --chip-bg: rgba(74, 110, 56, 0.06);
          --chip-border: rgba(74, 110, 56, 0.15);
          --chip-bg-hover: rgba(74, 110, 56, 0.1);
          --chip-border-hover: rgba(74, 110, 56, 0.28);
        }

        @media (prefers-color-scheme: dark) {
          :root {
            --panel-bg: rgba(22, 20, 16, 0.7);
            --panel-border: rgba(255, 245, 220, 0.08);
            --text-primary: #f0e8d8;
            --text-muted: #8a7d6a;
            --herb: #7fb86a;
            --chip-bg: rgba(127, 184, 106, 0.08);
            --chip-border: rgba(127, 184, 106, 0.18);
            --chip-bg-hover: rgba(127, 184, 106, 0.14);
            --chip-border-hover: rgba(127, 184, 106, 0.32);
          }
        }

        :root[data-theme="light"] {
          --panel-bg: rgba(255, 255, 255, 0.6);
          --panel-border: rgba(28, 22, 14, 0.08);
          --text-primary: #1c160e;
          --text-muted: #7c6e5a;
          --herb: #4a6e38;
          --chip-bg: rgba(74, 110, 56, 0.06);
          --chip-border: rgba(74, 110, 56, 0.15);
          --chip-bg-hover: rgba(74, 110, 56, 0.1);
          --chip-border-hover: rgba(74, 110, 56, 0.28);
        }

        :root[data-theme="dark"] {
          --panel-bg: rgba(22, 20, 16, 0.7);
          --panel-border: rgba(255, 245, 220, 0.08);
          --text-primary: #f0e8d8;
          --text-muted: #8a7d6a;
          --herb: #7fb86a;
          --chip-bg: rgba(127, 184, 106, 0.08);
          --chip-border: rgba(127, 184, 106, 0.18);
          --chip-bg-hover: rgba(127, 184, 106, 0.14);
          --chip-border-hover: rgba(127, 184, 106, 0.32);
        }
      `}</style>
    </aside>
  );
}
