<script lang="ts">
    import { resolve } from '$app/paths';
    import { onMount } from 'svelte';
    import type { LayoutProps } from './$types';

    let { children }: LayoutProps = $props();

    onMount(() => {
        const h4s = document.querySelectorAll<HTMLElement>('h4');
        h4s.forEach((h4, idx) => {
            if (h4.textContent?.trim() !== 'Implementation steps') return;
            const ol = h4.nextElementSibling;
            if (!ol || ol.tagName !== 'OL') return;

            const key = `steps:${location.pathname}:${idx}`;
            const saved: Record<string, boolean> = JSON.parse(sessionStorage.getItem(key) ?? '{}');

            ol.querySelectorAll<HTMLElement>('li').forEach((li, i) => {
                const cb = document.createElement('input');
                cb.type = 'checkbox';
                cb.checked = !!saved[i];
                cb.className = 'checklist-cb';
                applyStyle(li, cb.checked);
                cb.addEventListener('change', () => {
                    saved[i] = cb.checked;
                    sessionStorage.setItem(key, JSON.stringify(saved));
                    applyStyle(li, cb.checked);
                });
                li.prepend(cb);
            });
        });
    });

    function applyStyle(li: HTMLElement, checked: boolean) {
        li.style.opacity = checked ? '0.4' : '';
        li.style.textDecoration = checked ? 'line-through' : '';
    }
</script>

<div class="prose prose-slate dark:prose-invert mx-auto px-4 py-12 max-w-3xl">
    {@render children()}
    <footer class="not-prose mt-12 border-t border-slate-200 pt-4">
        <a href={resolve('/build-guide')} class="font-mono text-sm text-slate-500 hover:text-slate-900">← revisions</a>
    </footer>
</div>

<style>
    :global(.checklist-cb) {
        appearance: auto;
        margin-right: 0.5rem;
        cursor: pointer;
        flex-shrink: 0;
        position: relative;
        top: 1px;
    }
</style>
